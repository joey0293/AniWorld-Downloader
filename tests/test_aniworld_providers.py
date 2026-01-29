from aniworld.config import logger
from aniworld.extractors import provider_functions


def run_test(name, func, url):
    logger.info(f"Testing {name} provider...")
    try:
        print("=" * 15 + f" {name} " + "=" * 15)
        direct_link = func(url)
        logger.info(f"{name} direct link: {direct_link}")
    except Exception as e:
        logger.error(f"{name} provider test failed: {e}")
    finally:
        print("=" * 40, "\n")


def test_aniworld_providers():
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
    test_aniworld_providers()
