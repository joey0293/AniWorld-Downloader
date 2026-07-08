from typing import List, Set

try:
    from ..config import GLOBAL_SESSION, logger
except ImportError:
    from aniworld.config import GLOBAL_SESSION, logger

JIKAN_SEARCH_URL = "https://api.jikan.moe/v4/anime"


def search_jikan(
    query: str, sfw: bool = False, page: int = 1, limit: int = 10
) -> List[dict]:
    """
    Search for anime using Jikan API v4, filtering by TV type.
    Returns a list of anime dictionaries (only type 'TV').
    """
    params = {
        "q": query,
        "type": "tv",
        "sfw": str(sfw).lower(),
        "page": page,
        "limit": limit,
        "order_by": "popularity",
        "sort": "desc",
    }

    try:
        res = GLOBAL_SESSION.get(JIKAN_SEARCH_URL, params=params)
        res.raise_for_status()
        data = res.json().get("data", [])
        # Filter for TV type just in case
        return [anime for anime in data if anime.get("type") == "TV"]
    except Exception as e:
        logger.error(f"Error searching Jikan API for query '{query}': {e}")
        return []


def get_anime_full_by_id(mal_id: int) -> dict:
    """
    Fetch full anime data from Jikan API for a given MAL ID.
    Includes all related entries in one request.
    """
    url = f"https://api.jikan.moe/v4/anime/{mal_id}/full"
    res = GLOBAL_SESSION.get(url)
    res.raise_for_status()
    return res.json().get("data", {})


def get_all_related_from_full(mal_id: int) -> List[int]:
    """
    Extract all related MAL IDs from the full anime data.
    Only includes relevant anime types (Sequel, Prequel, Side story, Parent story).
    """
    anime_data = get_anime_full_by_id(mal_id)
    relations = anime_data.get("relations", [])
    all_ids: Set[int] = {mal_id}

    for rel in relations:
        if rel.get("relation") in {"Sequel", "Prequel", "Parent story", "Side story"}:
            for entry in rel.get("entry", []):
                if entry.get("type") == "anime":
                    all_ids.add(entry["mal_id"])

    return list(all_ids)


def get_all_seasons_by_query(query: str) -> List[int]:
    """
    Return a list of all MAL IDs for all anime seasons related to the query.
    Uses the full endpoint to avoid recursive API calls.
    """
    seasons = search_jikan(query)
    if not seasons:
        logger.warning(f"No TV seasons found for query: {query}")
        return []

    all_ids: Set[int] = set()
    for season in seasons:
        mal_id = season["mal_id"]
        all_ids.update(get_all_related_from_full(mal_id))

    logger.info(f"All season MAL IDs found: {all_ids}")
    return list(all_ids)


if __name__ == "__main__":
    query = "love is war"
    all_seasons = get_all_seasons_by_query(query)
    print(all_seasons)
