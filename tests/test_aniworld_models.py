import json

from aniworld.models import (
    AniworldEpisode,
    AniworldSeason,
    AniworldSeries,
)


def object_to_json(obj):
    cls = obj.__class__
    mangled_prefix = f"_{cls.__name__}__"

    data = {}

    for name in vars(obj):
        # unmangle private names
        clean_name = (
            name[len(mangled_prefix) :] if name.startswith(mangled_prefix) else name
        )

        # skip parent objects and _html
        if clean_name.startswith(("_series", "_season", "html")):
            continue

        # access via clean name to trigger lazy-loading if needed
        value = getattr(obj, clean_name, None)

        # ensure JSON serializable (fallback to string)
        try:
            json.dumps(value)
            data[clean_name] = value
        except TypeError:
            data[clean_name] = str(value)

    return json.dumps(data, indent=4, ensure_ascii=False)


def test_aniworld_models_aniworld_series():
    series = AniworldSeries("https://aniworld.to/anime/stream/highschool-dxd")
    print(object_to_json(series))


def test_aniworld_models_aniworld_season():
    season = AniworldSeason("https://aniworld.to/anime/stream/highschool-dxd/staffel-1")
    print(object_to_json(season))


def test_aniworld_models_aniworld_episode():
    episode = AniworldEpisode(
        "https://aniworld.to/anime/stream/highschool-dxd/staffel-1/episode-1"
    )
    print(object_to_json(episode))


if __name__ == "__main__":
    print("=" * 80)
    test_aniworld_models_aniworld_series()
    print("=" * 80)

    print("=" * 80)
    test_aniworld_models_aniworld_season()
    print("=" * 80)

    print("=" * 80)
    test_aniworld_models_aniworld_episode()
    print("=" * 80)
