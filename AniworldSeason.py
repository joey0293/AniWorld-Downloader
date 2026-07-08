import re

from config import logger, GLOBAL_SESSION
from AniworldSeries import AniworldSeries
from AniworldEpisode import AniworldEpisode


class AniworldSeason:
    """
    Represents a single season (or a movie collection) of an AniWorld anime series.

    Parameters:
        series:     Parent series object.
        url:        Required. The AniWorld URL for this season, e.g.
                    https://aniworld.to/anime/stream/highschool-dxd/staffel-1

    Attributes (Example):
        series:         <AniworldSeries object>
        url:            https://aniworld.to/anime/stream/highschool-dxd/staffel-1
        are_movies:     False
        season_number:  1
        episode_count:  12
        episodes:       [<AniworldEpisode object>, <AniworldEpisode object>, ...]
        _html:          <!doctype html> ...
    """

    def __init__(self, url, series=None):
        self._series = series
        self.url = url

        self.__are_movies = None
        self.__season_number = None
        self.__episode_count = None
        self.__episodes = (
            None  # TODO IMPORTANT: episode objects are not being created for movies
        )

        self.__html = None

    @property
    def series(self):
        if self._series is None:
            # Extract series URL from season URL by removing /staffel-X part
            series_url = self.url.split("/staffel-")[0]
            self._series = AniworldSeries(series_url)
        return self._series

    @property
    def _html(self):
        if self.__html is None:
            logger.debug(f"fetching ({self.url})...")
            resp = GLOBAL_SESSION.get(self.url)
            self.__html = resp.text
        return self.__html

    @property
    def are_movies(self):
        if self.__are_movies is None:
            self.__are_movies = self.__check_if_are_movies()
        return self.__are_movies

    @property
    def season_number(self):
        if self.__season_number is None:
            self.__season_number = self.__extract_season_number()
        return self.__season_number

    @property
    def episodes(self):
        if self.__episodes is None:
            self.__episodes = self.__extract_episodes()
        return self.__episodes

    @property
    def episode_count(self):
        if self.__episode_count is None:
            # If episodes are already extracted, use that count
            if self.__episodes is not None:
                self.__episode_count = len(self.__episodes)
            else:
                self.__episode_count = self.__extract_episode_count()
        return self.__episode_count

    # -----------------------------
    # Extraction helpers
    # -----------------------------

    def __check_if_are_movies(self):
        return (
            re.fullmatch(r"https://aniworld\.to/anime/stream/[^/]+/filme", self.url)
            is not None
        )

    def __extract_season_number(self):
        if self.are_movies:
            return 0

        match = re.search(r"staffel-(\d+)", self.url)
        if match:
            return int(match.group(1))
        return None

    # TODO: FIXXX - DOES NOT WORK
    def __extract_episodes(self):
        """
            <tbody id="season1">
            <tr class="" data-episode-id="2311" data-episode-season-id="1" itemprop="episode" itemscope="" itemtype="http://schema.org/Episode">
                <td class="season1EpisodeID">
                    <meta itemprop="episodeNumber" content="1"><a itemprop="url" href="/anime/stream/goblin-slayer/staffel-1/episode-1"> Folge 1 </a>
                </td>
                <td class="seasonEpisodeTitle"><a href="/anime/stream/goblin-slayer/staffel-1/episode-1"> <strong>Das Schicksal der Abenteurer</strong> - <span>The Fate of Particular Adventurers</span> </a></td>
                <td><a href="/anime/stream/goblin-slayer/staffel-1/episode-1"> <i class="icon VOE" title="VOE"></i><i class="icon Filemoon" title="Filemoon"></i><i class="icon Vidmoly" title="Vidmoly"></i> </a></td>
                <td class="editFunctions"><a href="/anime/stream/goblin-slayer/staffel-1/episode-1"> <img class="flag" src="/public/img/german.svg" alt="Deutsche Sprache, Flagge" title="Deutsch/German"> <img class="flag" src="/public/img/japanese-german.svg" alt="Deutsche Flagge, Untertitel, Flagge" title="Mit deutschem Untertitel"> <img class="flag" src="/public/img/japanese-english.svg" alt="Englische Sprache, Flagge" title="Englisch"> </a></td>
            </tr>
            <tr class="" data-episode-id="2312" data-episode-season-id="2" itemprop="episode" itemscope="" itemtype="http://schema.org/Episode">
                <td class="season1EpisodeID">
                    <meta itemprop="episodeNumber" content="2"><a itemprop="url" href="/anime/stream/goblin-slayer/staffel-1/episode-2"> Folge 2 </a>
                </td>
                <td class="seasonEpisodeTitle"><a href="/anime/stream/goblin-slayer/staffel-1/episode-2"> <strong>Dämonentöter</strong> - <span>Goblin Slayer</span> </a></td>
                <td><a href="/anime/stream/goblin-slayer/staffel-1/episode-2"> <i class="icon VOE" title="VOE"></i><i class="icon Filemoon" title="Filemoon"></i><i class="icon Vidmoly" title="Vidmoly"></i> </a></td>
                <td class="editFunctions"><a href="/anime/stream/goblin-slayer/staffel-1/episode-2"> <img class="flag" src="/public/img/german.svg" alt="Deutsche Sprache, Flagge" title="Deutsch/German"> <img class="flag" src="/public/img/japanese-german.svg" alt="Deutsche Flagge, Untertitel, Flagge" title="Mit deutschem Untertitel"> <img class="flag" src="/public/img/japanese-english.svg" alt="Englische Sprache, Flagge" title="Englisch"> </a></td>
            </tr>
            ...
        </tbody>
        """

        """
            TODO for Tobias:
            I have those entries like above this comment and I want to create episode objects for each episode lol

            you need to create a providers variable which holds languages and providers and this combo gives you a direct link
            
            after that count all languages that can be build using this:

            class Audio(Enum):
                JAPANESE = "Japanese"
                GERMAN = "German"
                ENGLISH = "English"


            class Subtitles(Enum):
                NONE = "None"
                GERMAN = "German"
                ENGLISH = "English"


            def parse_source(source: str):
                source = source.lower()

                # Audio
                if "dub" in source:
                    if "german" in source:
                        audio = Audio.GERMAN
                    elif "english" in source:
                        audio = Audio.ENGLISH
                    else:
                        audio = Audio.JAPANESE
                    subtitles = Subtitles.NONE

                # Subtitles
                elif "sub" in source:
                    audio = Audio.JAPANESE
                    if "german" in source:
                        subtitles = Subtitles.GERMAN
                    elif "english" in source:
                        subtitles = Subtitles.ENGLISH
                    else:
                        subtitles = Subtitles.NONE

                else:
                    raise ValueError(f"Unknown source format: {source}")

                return audio, subtitles


            for example if there only is German Dub available you need to somehow store this information in languages

            that will tell me that only audio german and no subtitles are possible

            but in a way that I am able to access this direct link using a language and provider pair when querying

            if ep_url and ep_num:
                episodes.append(
                    AniworldEpisode(
                        season=self,
                        url=ep_url,
                        episode_number=ep_num,
                        title_de=title_de,
                        title_en=title_en,
                        languages=languages,  # just pass all languages that are contained in the providers dict
                        providers=providers,
                    )
                )
        """

        from bs4 import BeautifulSoup

        episodes = []

        soup = BeautifulSoup(self._html, "html.parser")
        rows = soup.select("tbody#season1 tr")

        for row in rows:
            # Episode number
            ep_num = int(row.select_one("meta[itemprop='episodeNumber']")["content"])

            # Titles
            title_de = row.select_one("td.seasonEpisodeTitle strong").get_text(
                strip=True
            )
            title_en_span = row.select_one("td.seasonEpisodeTitle span")
            title_en = title_en_span.get_text(strip=True) if title_en_span else title_de

            # Generic episode URL
            ep_url = row.select_one("td.season1EpisodeID a")["href"]

            # Hosters and their direct links
            hoster_links = {}
            for i_tag in row.select("td a i.icon"):
                hoster_name = i_tag.get("title")
                if hoster_name:
                    hoster_links[hoster_name] = i_tag.find_parent("a")["href"]

            # Languages and providers mapping
            providers = {}
            languages_set = set()
            flags = [img["title"] for img in row.select("td.editFunctions img")]

            for flag in flags:
                if "Deutsch/German" in flag:
                    src_str = "German Dub"
                elif "Englisch" in flag and "Untertitel" not in flag:
                    src_str = "English Dub"
                elif "Mit deutschem Untertitel" in flag:
                    src_str = "German Sub"
                elif "Mit englischem Untertitel" in flag:
                    src_str = "English Sub"
                else:
                    continue

                # Parse audio/subtitle
                from config import parse_source

                audio, sub = parse_source(src_str)
                languages_set.add((audio, sub))

                # Map each hoster to its direct link
                for hoster_name, link in hoster_links.items():
                    providers[(audio, sub, hoster_name)] = link

            languages = list(languages_set)

            # Create episode object
            episodes.append(
                AniworldEpisode(
                    season=self,
                    url=ep_url,  # store the generic episode page URL
                    episode_number=ep_num,
                    title_de=title_de,
                    title_en=title_en,
                    languages=languages,
                    providers=providers,
                )
            )

            logger.warning(episodes[0].url)
            logger.warning(episodes[0].episode_number)
            logger.warning(episodes[0].languages)
            logger.warning(episodes[0].providers)

        return episodes

    def __extract_episode_count(self):
        """
        Counts episodes by counting episode markers in HTML without full extraction
        """
        logger.debug("counting episodes...")

        html = self._html

        marker = 'itemtype="http://schema.org/Episode"'
        count = 0
        pos = 0

        while True:
            pos = html.find(marker, pos)
            if pos == -1:
                break
            count += 1
            pos += 1

        return count


if __name__ == "__main__":
    series = AniworldSeries("https://aniworld.to/anime/stream/kaguya-sama-love-is-war")

    print("\n" + "=" * 60)
    print(f"SEASON OVERVIEW — {series.title}")
    print("=" * 60)

    for season in series.seasons:
        fields = {
            "URL": season.url,
            "Are Movies": season.are_movies,
            "Season Number": season.season_number,
            "Episode Count": season.episode_count,
            "Episodes": season.episodes,
        }

        if season.are_movies:
            print("\nMovies")
        else:
            print(f"\nSeason {season.season_number}")

        print("-" * 60)

        max_key_len = max(len(k) for k in fields.keys())
        for key, value in fields.items():
            print(f"{key:<{max_key_len}} : {value}")

        """
        # Show first episode if available
        if season.episodes:
            ep = season.episodes[0]

            print("\n  First Episode")
            print("  " + "-" * 56)

            ep_fields = {
                "URL": ep.url,
                "Title DE": ep.title_de,
                "Title EN": ep.title_en,
                "Episode #": ep.episode_number,
                "Language": ep.language,
                "Is Movie": ep.is_movie,
            }

            max_ep_key_len = max(len(k) for k in ep_fields.keys())
            for key, value in ep_fields.items():
                print(f"  {key:<{max_ep_key_len}} : {value}")

        print("\n" + "-" * 60)
        """

    print("\n" + "=" * 60 + "\n")
