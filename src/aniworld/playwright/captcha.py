def playwright_get_page_url(url: str):
    """Open the page and return the final URL."""
    try:
        from patchright.sync_api import sync_playwright
    except ImportError:
        raise ImportError(
            "Playwright is required for captcha handling. Please install it with 'pip install patchright' and run 'patchright install chromium'."
        )

    with sync_playwright() as p:
        # needs to be non-headless to solve let the captcha load and be solvable
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(url)

        for i in range(50):
            print(f"\nChecking for captcha... Attempt {i + 1}/50")

            if "<title>Stream wird vorbereitet...</title>" in page.content():
                print("Captcha detected on the page...")

                try:
                    # checkbox
                    checkbox = page.frame_locator("iframe").locator(
                        'input[type="checkbox"]'
                    )
                    checkbox.wait_for(state="visible", timeout=5000)
                    checkbox.click()

                    # submit button
                    page.wait_for_timeout(3000)
                    weiter_button = page.locator('button[type="submit"]')
                    weiter_button.wait_for(state="visible", timeout=5000)
                    weiter_button.click()
                except Exception as e:
                    print(f"Could not click captcha automatically: {e}")
                    print(
                        f"\nPlease solve the captcha in the opened browser manually:\n{url}"
                    )

                page.wait_for_timeout(3000)
            else:
                print("Captcha solved...")
                break

        final_url = page.url
        page.wait_for_timeout(1000)
        browser.close()

        return final_url


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
