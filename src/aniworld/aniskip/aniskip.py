try:
    from ..config import GLOBAL_SESSION, logger
except ImportError:
    from aniworld.config import GLOBAL_SESSION, logger


def search_mal(query: str):
    url = "https://myanimelist.net/search/prefix.json"
    params = {"type": "anime", "keyword": query}
    res = GLOBAL_SESSION.get(url, params=params)
    res.raise_for_status()
    return res.json()


def extract_items(results):
    items = []
    for cat in results.get("categories", []):
        items += cat.get("items", [])
    if "data" in results:
        items += results["data"]
    return items


def filter_seasons(results):
    seasons = []
    for entry in extract_items(results):
        if entry.get("type") == "anime":
            payload = entry.get("payload", {})
            if payload.get("media_type") == "TV":
                seasons.append(entry)
    return seasons


def aniskip():
    data = search_mal("kaguya sama love is war")
    seasons = filter_seasons(data)

    first_season = seasons[0]
    logger.info(first_season)


if __name__ == "__main__":
    aniskip()
