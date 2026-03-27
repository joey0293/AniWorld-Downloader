def playwright_get_page_url(url: str):
    try:
        from patchright.sync_api import sync_playwright
    except ImportError:
        raise ImportError(
            "Playwright is required for captcha handling. Please install it with 'pip install patchright' and run 'patchright install chromium'."
        )

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(url)

        for i in range(50):
            print(f"\nChecking for captcha... Attempt {i + 1}/50")
            if "<title>Stream wird vorbereitet...</title>" in page.content():
                print("Captcha detected on the page...")
                print(
                    f"\nPlease solve the captcha in the now opened playwright browser manually and press next:\n{url}"
                )
                page.wait_for_timeout(3000)

                # TODO: currently manually, but will be automated by click
                # click on <input type="checkbox"> somehow
            else:
                print("Captcha solved...")
                break

        page.wait_for_timeout(1000)
        browser.close()

        return page.url


if __name__ == "__main__":
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
