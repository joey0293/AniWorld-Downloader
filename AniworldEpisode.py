from config import logger, GLOBAL_SESSION
from AniworldSeries import AniworldSeries


class AniworldEpisode:
    """
    Attributes:
    series
    season
    url
    title_de
    title_en
    episode_number
    language
    is_movie
    _html
    """

    def __init__(self, season, url, episode_number, title_de, title_en):
        self.series = season.series
        self.season = season
        self.url = url

        self.episode_number = episode_number
        self.title_de = title_de
        self.title_en = title_en

        self.__html = None
        self.__language = None
        self.__is_movie = None

    @property
    def _html(self):
        if self.__html is None:
            logger.debug(f"fetching ({self.url})...")
            resp = GLOBAL_SESSION.get(self.url)
            self.__html = resp.text
        return self.__html

    @property
    def language(self):
        if self.__language is None:
            self.__language = self._extract_language()
        return self.__language

    @property
    def is_movie(self):
        if self.__is_movie is None:
            self.__is_movie = self._extract_is_movie()
        return self.__is_movie

    # -----------------------------
    # Extraction helpers
    # -----------------------------

    def _extract_language(self):
        # TODO: parse flags from episode page
        return "German"

    def _extract_is_movie(self):
        # TODO: detect movie episodes (specials)
        return False


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
        print(f"  Season Number: {season.season_number}")
        print(f"  Episode Count: {season.episode_count}")
        print(f"  Episodes: {len(season.episodes)} objects")
        if season.episodes:
            print(f"  First Episode: {season.episodes[0].title_de}")

    """
    TODO:
    
    - Add hosting_links section with language/ provider mapping
    - Copy provider extractors from next
    - Add .watch() .download() and .syncplay() function
    
    """
