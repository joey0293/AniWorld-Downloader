from aniworld.config import logger
from aniworld.extractors import provider_functions


def run_test(name, func, url):
    print("=" * 15 + f" {name} " + "=" * 15)
    logger.info(f"Testing {name} provider...")
    try:
        direct_link = func(url)
        if direct_link is not None:
            print(f"{name} direct link: {direct_link}")
            logger.info(f"{name} direct link: {direct_link}")
        else:
            print(f"{name} provider returned None")
            logger.warning(f"{name} provider returned None")
    except Exception as e:
        print(f"{name} provider test failed: {e}")
        logger.error(f"{name} provider test failed: {e}")
    print("=" * 40 + "\n")


def main():
    run_test(
        "Doodstream",
        provider_functions["get_direct_link_from_doodstream"],
        "https://dood.so/d/obx2lizzns385sm6gvbxwn56iu9maael",
    )
    run_test(
        "Vidmoly",
        provider_functions["get_direct_link_from_vidmoly"],
        "https://vidmoly.net/embed-zquo82b8dm1k.html",
    )
    run_test(
        "Vidoza",
        provider_functions["get_direct_link_from_vidoza"],
        "https://videzz.net/embed-xneznizpludf.html",
    )
    run_test(
        "VOE",
        provider_functions["get_direct_link_from_voe"],
        "https://voe.sx/e/oa16zsjaqohr",
    )


if __name__ == "__main__":
    main()
