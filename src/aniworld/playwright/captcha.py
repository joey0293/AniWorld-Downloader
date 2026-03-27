import threading as _threading
import queue as _queue_module
import time as _time


_local = _threading.local()

# Active captcha sessions keyed by queue_id
_active_sessions = {}
_active_sessions_lock = _threading.Lock()

# Optional hooks set by app.py to avoid circular imports
_on_captcha_start = None  
_on_captcha_end = None    

# Global captcha state for status polling
_captcha_state_lock = _threading.Lock()
_captcha_state = None  

# Serialise concurrent solve attempts
_captcha_lock = _threading.Lock()


def is_captcha_page(html: str, status_code: int = 200) -> bool:
    """Detect Cloudflare challenge / CAPTCHA pages."""
    if status_code in (403, 503):
        return True

    lower = html.lower()
    indicators = [
        "just a moment",
        "cf-turnstile",
        "checking your browser",
        "enable javascript and cookies",
        "ddos protection by cloudflare",
        "<title>attention required",
        "cdn-cgi/challenge-platform",
        "challenges.cloudflare.com",
        "challenge-running",
        "cf_chl_",
        "jschl-answer",
        "<title>just a moment",
        "hcaptcha.com",
        "newassets.hcaptcha",
        "g-recaptcha",
        # legacy aniworld check kept for safety
        "<title>stream wird vorbereitet...</title>",
    ]
    return any(ind in lower for ind in indicators)


def get_captcha_status():
    """Return current captcha state dict for the web UI, or None."""
    with _captcha_state_lock:
        return dict(_captcha_state) if _captcha_state else None


def solve_captcha(url: str) -> bool:
    """
    Solve a CAPTCHA for *url*.

    - WebUI mode  (queue_id set in threading-local): streams screenshots to the
      Web UI so the user can click inside the browser; injects cookies afterwards.
    - CLI mode: opens a visible browser window and waits for the user to solve.

    After a successful solve all browser cookies are injected into GLOBAL_SESSION
    so subsequent requests work without re-solving.

    Returns True on success, False on timeout / error.
    """
    queue_id = getattr(_local, "queue_id", None)
    if queue_id is not None:
        return _solve_captcha_interactive(url, queue_id)
    return _solve_captcha_cli(url)


def _solve_captcha_cli(url: str) -> bool:
    """CLI mode captcha solver — opens a visible browser, injects cookies on success."""
    try:
        from patchright.sync_api import sync_playwright
    except ImportError:
        raise RuntimeError(
            "patchright ist nicht installiert. "
            "Bitte installieren mit: pip install patchright && patchright install chromium"
        )

    from ..config import GLOBAL_SESSION
    from ..logger import get_logger
    logger = get_logger(__name__)

    with _captcha_lock:
        global _captcha_state
        with _captcha_state_lock:
            _captcha_state = {"url": url, "started_at": _time.time(), "solved": False}

        logger.warning(f"CAPTCHA erkannt für {url} — Browser wird für manuelle Lösung geöffnet")

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=False,
                    args=["--disable-blink-features=AutomationControlled"],
                )
                context = browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/124.0.0.0 Safari/537.36"
                    )
                )
                page = context.new_page()
                page.goto(url, wait_until="domcontentloaded")

                timeout = 300  # 5 minutes
                start = _time.time()
                solved = False

                # Polling for cf_clearance cookie only - no auto-clicking that could interfere.
                while _time.time() - start < timeout:
                    cookies = context.cookies()
                    if any(c["name"] == "cf_clearance" for c in cookies):
                        solved = True
                        break
                    _time.sleep(1.5)

                if solved:
                    for cookie in context.cookies():
                        GLOBAL_SESSION.cookies.set(
                            cookie["name"],
                            cookie["value"],
                            domain=cookie.get("domain", "").lstrip("."),
                        )
                    logger.info("CAPTCHA gelöst — Cookies in Session injiziert")
                else:
                    logger.warning("CAPTCHA-Timeout nach 5 Minuten")

                browser.close()

            with _captcha_state_lock:
                _captcha_state = None

            return solved

        except Exception as e:
            logger.error(f"Fehler beim CAPTCHA-Lösen: {e}", exc_info=True)
            with _captcha_state_lock:
                _captcha_state = None
            return False


class CaptchaSession:
    """Holds state for an in-progress interactive captcha solve (web UI mode)."""

    def __init__(self):
        self._screenshot = b""
        self._screenshot_lock = _threading.Lock()
        self._click_queue = _queue_module.Queue()
        self.done = False
        self.result_url = None

    def get_screenshot(self) -> bytes:
        with self._screenshot_lock:
            return self._screenshot

    def _store_screenshot(self, data: bytes):
        with self._screenshot_lock:
            self._screenshot = data

    def enqueue_click(self, x: int, y: int):
        self._click_queue.put_nowait((x, y))


def _solve_captcha_interactive(url: str, queue_id: int) -> bool:
    """WebUI mode: stream screenshots, accept clicks, inject cookies on success."""
    try:
        from patchright.sync_api import sync_playwright
    except ImportError:
        raise RuntimeError(
            "patchright ist nicht installiert. "
            "Bitte installieren mit: pip install patchright && patchright install chromium"
        )

    from ..config import GLOBAL_SESSION
    from ..logger import get_logger
    logger = get_logger(__name__)

    session = CaptchaSession()
    with _active_sessions_lock:
        _active_sessions[queue_id] = session

    if _on_captcha_start is not None:
        try:
            _on_captcha_start(queue_id, url)
        except Exception:
            pass

    global _captcha_state
    try:
        with sync_playwright() as p:
            # headless=False required for Cloudflare/Turnstile to work.
            # Window pushed off-screen to avoid visible popup on server desktops.
            browser = p.chromium.launch(
                headless=False,
                args=["--window-position=-32000,-32000", "--window-size=1280,720"],
            )
            context = browser.new_context(viewport={"width": 1280, "height": 720})
            page = context.new_page()
            page.goto(url)

            with _captcha_state_lock:
                _captcha_state = {"url": url, "started_at": _time.time(), "solved": False}

            solved = False
            for _ in range(300):  # up to ~5 minutes
                # Stream screenshot to Web UI
                try:
                    shot = page.screenshot(type="jpeg", quality=65)
                    session._store_screenshot(shot)
                except Exception:
                    pass

                # Forward pending click events from Web UI
                while not session._click_queue.empty():
                    try:
                        cx, cy = session._click_queue.get_nowait()
                        page.mouse.click(cx, cy)
                        page.wait_for_timeout(400)
                    except Exception:
                        pass

                # Check if captcha resolved
                try:
                    content = page.content()
                    if not is_captcha_page(content):
                        solved = True
                        break
                except Exception:
                    pass

                # Check for cf_clearance cookie
                if any(c["name"] == "cf_clearance" for c in context.cookies()):
                    solved = True
                    break

                # Try auto-solve: checkbox
                try:
                    checkbox = page.frame_locator("iframe").locator('input[type="checkbox"]')
                    checkbox.wait_for(state="visible", timeout=2000)
                    checkbox.click()
                    page.wait_for_timeout(1500)
                except Exception:
                    pass

                # Always try Weiter button independently
                try:
                    weiter_button = page.locator('button[type="submit"]')
                    weiter_button.wait_for(state="visible", timeout=2000)
                    weiter_button.click()
                    page.wait_for_timeout(1500)
                except Exception:
                    pass

                page.wait_for_timeout(1000)

            # Final screenshot
            try:
                shot = page.screenshot(type="jpeg", quality=65)
                session._store_screenshot(shot)
            except Exception:
                pass

            if solved:
                for cookie in context.cookies():
                    GLOBAL_SESSION.cookies.set(
                        cookie["name"],
                        cookie["value"],
                        domain=cookie.get("domain", "").lstrip("."),
                    )
                logger.info("CAPTCHA gelöst — Cookies in Session injiziert")
            else:
                logger.warning("CAPTCHA-Timeout nach 5 Minuten")

            final_url = page.url
            page.wait_for_timeout(400)
            browser.close()

        session.result_url = final_url
        session.done = True

        with _captcha_state_lock:
            _captcha_state = None

        return solved

    finally:
        if _on_captcha_end is not None:
            try:
                _on_captcha_end(queue_id)
            except Exception:
                pass
        with _active_sessions_lock:
            _active_sessions.pop(queue_id, None)


def playwright_get_page_url(url: str) -> str:
    """
    Legacy helper: open *url* in a browser, solve any captcha, return the final URL.
    Prefer calling solve_captcha() + GLOBAL_SESSION.get() directly for cookie injection.
    """
    solve_captcha(url)
    from ..config import GLOBAL_SESSION
    return GLOBAL_SESSION.get(url).url


if __name__ == "__main__":
    # Use test.py instead :)

    """
    import niquests

    from aniworld.config import Audio, Subtitles
    from aniworld.models import SerienstreamEpisode

    ep = SerienstreamEpisode("https://s.to/serie/mr-pickles/staffel-1/episode-1")

    language = (Audio.GERMAN, Subtitles.NONE)
    provider = "VOE"

    provider_link = ep.provider_link(language=language, provider=provider)

    print(f"Redirect Link: {provider_link}")

    final_url = niquests.get(provider_link)

    if "<title>Stream wird vorbereitet...</title>" in final_url.text:
        print("Captcha detected, solving with Playwright...")
        url = playwright_get_page_url(provider_link)
    else:
        url = final_url.url

    print(f"Final URL: {url}")
    """
