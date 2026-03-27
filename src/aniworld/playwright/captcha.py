from patchright.sync_api import sync_playwright


def playwright_get_page_url(url: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(url)

        content = page.content()
        if "captcha" in content.lower():
            print("Captcha detected on the page.")

        for i in range(50):
            print(f"\nChecking for captcha... Attempt {i + 1}/50")
            if "captcha" in page.content().lower():
                print("Captcha still detected, waiting...")
                page.wait_for_timeout(2000)
            else:
                # TODO: currently manually, but will be automated by click
                print("Captcha resolved.")
                break

        page.wait_for_timeout(5000)
        browser.close()

        return page.content()


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
        final_url = playwright_get_page_url(provider_link)

    print(f"Final URL: {final_url}")
