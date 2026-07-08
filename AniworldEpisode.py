import re

from config import logger, GLOBAL_SESSION
from AniworldSeries import AniworldSeries


class AniworldEpisode:
    """
    Represents a single episode (or movie entry) of an AniWorld anime series.

    Parameters:
        season:         Parent season object this episode belongs to.
        url:            Required. The AniWorld URL for this episode, e.g.
                        https://aniworld.to/anime/stream/highschool-dxd/staffel-1/episode-1
        episode_number: Episode index within the season. Movies may use a special numbering.
        title_de:       German episode title.
        title_en:       English episode title, if available.
        languages:      Optional. List of available language options (e.g. ['German', 'Subbed']).

    Attributes (Example):
        season:         <AniworldSeason object>
        series:         <AniworldSeries object>
        url:            https://aniworld.to/anime/stream/highschool-dxd/staffel-1/episode-1
        title_de:       "Wir machen einen Ausflug ans Meer!"
        title_en:       "Going Sunbathing [Special]"
        episode_number: 1
        _language:
        _providers:
        _is_movie:      False
        _html:          <!doctype html> ...
    """

    def __init__(
        self, season, url, episode_number, title_de, title_en, languages, providers
    ):
        self.season = season
        self.series = season.series
        self.url = url

        self.title_de = title_de
        self.title_en = title_en
        self.episode_number = episode_number

        self.__languages = languages
        self.__providers = providers

        self.__is_movie = None

        self.__html = None

    @property
    def _html(self):
        if self.__html is None:
            logger.debug(f"fetching ({self.url})...")
            resp = GLOBAL_SESSION.get(self.url)
            self.__html = resp.text
        return self.__html

    @property
    def is_movie(self):
        if self.__is_movie is None:
            self.__is_movie = self._extract_is_movie()
        return self.__is_movie

    # -----------------------------
    # Extraction helpers
    # -----------------------------

    def _extract_is_movie(self):
        pattern = r"^https://aniworld\.to/anime/stream/[^/]+/filme/film-\d+/?$"
        return re.match(pattern, self.url) is not None


if __name__ == "__main__":
    """
        series = AniworldSeries("https://aniworld.to/anime/stream/goblin-slayer")
        print(series.url)
        print(series.title)
        print(series.description)
        print(series.genres)
        print(series.release_year)
        print(series.poster_url)
        print(series.directors)
        print(series.actors)
        print(series.producer)
        print(series.country)
        print(series.age_rating)
        print(series.rating)
        print(series.seasons)

        input(f"\n{'=' * 40}\nENTER TO QUIT\n{'=' * 40}\n")
    """

    series = AniworldSeries("https://aniworld.to/anime/stream/highschool-dxd")
    print(f"Testing Series: {series.title}")
    print(f"Series URL: {series.url}")
    print(f"Has movies: {series.has_movies}")
    print(f"Number of seasons: {len(series.seasons)}")

    print("\n--- Testing Seasons ---")
    for i, season in enumerate(series.seasons, 1):
        print(f"\nSeason {i}:")
        print(f"  URL: {season.url}")
        # print(f"  Season Number: {season.season_number}")
        # print(f"  Episode Count: {season.episode_count}")
        # print(f"  Episodes: {len(season.episodes)} objects")
        if season.episodes:
            print(f"  First Episode: {season.episodes[0].title_de}")
            print(f"  First Episode: {season.episodes[0].language}")

    """
    TODO:
    
    - Add hosting_links section with language/ provider mapping
    - Copy provider extractors from next
    - Add .watch() .download() and .syncplay() function
    
    """
