import re
from typing import Optional
from config import logger, GLOBAL_SESSION
from AniworldSeries import AniworldSeries
from AniworldEpisode import AniworldEpisode


class AniworldSeason:
    """
    Attributes:
        series
        url
        season_number
        episode_count
        episodes
        _html
    """

    def __init__(self, url: str, series: Optional[AniworldSeries] = None):
        self._series = series
        self.url = url

        self.__html = None

        self.__season_number = None
        self.__episode_count = None  # lazy-loaded episode count
        self.__episodes = None  # lazy-loaded list of AniworldEpisode

    @property
    def series(self):
        if self._series is None:
            # Extract series URL from season URL by removing /staffel-X part
            series_url = self.url.split("/staffel-")[0]
            self._series = AniworldSeries(series_url)
        return self._series

    @property
    def _html(self) -> str:
        if self.__html is None:
            logger.debug(f"fetching ({self.url})...")
            resp = GLOBAL_SESSION.get(self.url)
            self.__html = resp.text
        return self.__html

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

    def __extract_season_number(self):
        match = re.search(r"staffel-(\d+)", self.url)
        if match:
            return int(match.group(1))
        return None

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
            <tr class="" data-episode-id="2313" data-episode-season-id="3" itemprop="episode" itemscope="" itemtype="http://schema.org/Episode">
                <td class="season1EpisodeID">
                    <meta itemprop="episodeNumber" content="3"><a itemprop="url" href="/anime/stream/goblin-slayer/staffel-1/episode-3"> Folge 3 </a>
                </td>
                <td class="seasonEpisodeTitle"><a href="/anime/stream/goblin-slayer/staffel-1/episode-3"> <strong>Unerwarteter Besuch</strong> - <span>Unexpected Visitors</span> </a></td>
                <td><a href="/anime/stream/goblin-slayer/staffel-1/episode-3"> <i class="icon VOE" title="VOE"></i><i class="icon Filemoon" title="Filemoon"></i><i class="icon Vidmoly" title="Vidmoly"></i> </a></td>
                <td class="editFunctions"><a href="/anime/stream/goblin-slayer/staffel-1/episode-3"> <img class="flag" src="/public/img/german.svg" alt="Deutsche Sprache, Flagge" title="Deutsch/German"> <img class="flag" src="/public/img/japanese-german.svg" alt="Deutsche Flagge, Untertitel, Flagge" title="Mit deutschem Untertitel"> <img class="flag" src="/public/img/japanese-english.svg" alt="Englische Sprache, Flagge" title="Englisch"> </a></td>
            </tr>
            <tr class="" data-episode-id="2314" data-episode-season-id="4" itemprop="episode" itemscope="" itemtype="http://schema.org/Episode">
                <td class="season1EpisodeID">
                    <meta itemprop="episodeNumber" content="4"><a itemprop="url" href="/anime/stream/goblin-slayer/staffel-1/episode-4"> Folge 4 </a>
                </td>
                <td class="seasonEpisodeTitle"><a href="/anime/stream/goblin-slayer/staffel-1/episode-4"> <strong>Die Starken</strong> - <span>The Strong</span> </a></td>
                <td><a href="/anime/stream/goblin-slayer/staffel-1/episode-4"> <i class="icon VOE" title="VOE"></i><i class="icon Filemoon" title="Filemoon"></i><i class="icon Vidmoly" title="Vidmoly"></i> </a></td>
                <td class="editFunctions"><a href="/anime/stream/goblin-slayer/staffel-1/episode-4"> <img class="flag" src="/public/img/german.svg" alt="Deutsche Sprache, Flagge" title="Deutsch/German"> <img class="flag" src="/public/img/japanese-german.svg" alt="Deutsche Flagge, Untertitel, Flagge" title="Mit deutschem Untertitel"> <img class="flag" src="/public/img/japanese-english.svg" alt="Englische Sprache, Flagge" title="Englisch"> </a></td>
            </tr>
            <tr class="" data-episode-id="2315" data-episode-season-id="5" itemprop="episode" itemscope="" itemtype="http://schema.org/Episode">
                <td class="season1EpisodeID">
                    <meta itemprop="episodeNumber" content="5"><a itemprop="url" href="/anime/stream/goblin-slayer/staffel-1/episode-5"> Folge 5 </a>
                </td>
                <td class="seasonEpisodeTitle"><a href="/anime/stream/goblin-slayer/staffel-1/episode-5"> <strong>Abenteuer und Alltag</strong> - <span>Adventures and Daily Life</span> </a></td>
                <td><a href="/anime/stream/goblin-slayer/staffel-1/episode-5"> <i class="icon VOE" title="VOE"></i><i class="icon Filemoon" title="Filemoon"></i><i class="icon Vidmoly" title="Vidmoly"></i> </a></td>
                <td class="editFunctions"><a href="/anime/stream/goblin-slayer/staffel-1/episode-5"> <img class="flag" src="/public/img/german.svg" alt="Deutsche Sprache, Flagge" title="Deutsch/German"> <img class="flag" src="/public/img/japanese-german.svg" alt="Deutsche Flagge, Untertitel, Flagge" title="Mit deutschem Untertitel"> <img class="flag" src="/public/img/japanese-english.svg" alt="Englische Sprache, Flagge" title="Englisch"> </a></td>
            </tr>
            <tr class="" data-episode-id="2316" data-episode-season-id="6" itemprop="episode" itemscope="" itemtype="http://schema.org/Episode">
                <td class="season1EpisodeID">
                    <meta itemprop="episodeNumber" content="6"><a itemprop="url" href="/anime/stream/goblin-slayer/staffel-1/episode-6"> Folge 6 </a>
                </td>
                <td class="seasonEpisodeTitle"><a href="/anime/stream/goblin-slayer/staffel-1/episode-6"> <strong>Goblintöten in Wasserstadt</strong> - <span>Goblin Slayer in the Water Town</span> </a></td>
                <td><a href="/anime/stream/goblin-slayer/staffel-1/episode-6"> <i class="icon VOE" title="VOE"></i><i class="icon Filemoon" title="Filemoon"></i><i class="icon Vidmoly" title="Vidmoly"></i> </a></td>
                <td class="editFunctions"><a href="/anime/stream/goblin-slayer/staffel-1/episode-6"> <img class="flag" src="/public/img/german.svg" alt="Deutsche Sprache, Flagge" title="Deutsch/German"> <img class="flag" src="/public/img/japanese-german.svg" alt="Deutsche Flagge, Untertitel, Flagge" title="Mit deutschem Untertitel"> <img class="flag" src="/public/img/japanese-english.svg" alt="Englische Sprache, Flagge" title="Englisch"> </a></td>
            </tr>
            <tr class="" data-episode-id="2317" data-episode-season-id="7" itemprop="episode" itemscope="" itemtype="http://schema.org/Episode">
                <td class="season1EpisodeID">
                    <meta itemprop="episodeNumber" content="7"><a itemprop="url" href="/anime/stream/goblin-slayer/staffel-1/episode-7"> Folge 7 </a>
                </td>
                <td class="seasonEpisodeTitle"><a href="/anime/stream/goblin-slayer/staffel-1/episode-7"> <strong>Auf in den Tod</strong> - <span>Onward Unto Death</span> </a></td>
                <td><a href="/anime/stream/goblin-slayer/staffel-1/episode-7"> <i class="icon VOE" title="VOE"></i><i class="icon Filemoon" title="Filemoon"></i><i class="icon Vidmoly" title="Vidmoly"></i> </a></td>
                <td class="editFunctions"><a href="/anime/stream/goblin-slayer/staffel-1/episode-7"> <img class="flag" src="/public/img/german.svg" alt="Deutsche Sprache, Flagge" title="Deutsch/German"> <img class="flag" src="/public/img/japanese-german.svg" alt="Deutsche Flagge, Untertitel, Flagge" title="Mit deutschem Untertitel"> <img class="flag" src="/public/img/japanese-english.svg" alt="Englische Sprache, Flagge" title="Englisch"> </a></td>
            </tr>
            <tr class="" data-episode-id="2318" data-episode-season-id="8" itemprop="episode" itemscope="" itemtype="http://schema.org/Episode">
                <td class="season1EpisodeID">
                    <meta itemprop="episodeNumber" content="8"><a itemprop="url" href="/anime/stream/goblin-slayer/staffel-1/episode-8"> Folge 8 </a>
                </td>
                <td class="seasonEpisodeTitle"><a href="/anime/stream/goblin-slayer/staffel-1/episode-8"> <strong>Flüstern, Gebete und Gesänge</strong> - <span>Whispers and Prayers and Chants</span> </a></td>
                <td><a href="/anime/stream/goblin-slayer/staffel-1/episode-8"> <i class="icon VOE" title="VOE"></i><i class="icon Filemoon" title="Filemoon"></i><i class="icon Vidmoly" title="Vidmoly"></i> </a></td>
                <td class="editFunctions"><a href="/anime/stream/goblin-slayer/staffel-1/episode-8"> <img class="flag" src="/public/img/german.svg" alt="Deutsche Sprache, Flagge" title="Deutsch/German"> <img class="flag" src="/public/img/japanese-german.svg" alt="Deutsche Flagge, Untertitel, Flagge" title="Mit deutschem Untertitel"> <img class="flag" src="/public/img/japanese-english.svg" alt="Englische Sprache, Flagge" title="Englisch"> </a></td>
            </tr>
            <tr class="" data-episode-id="2319" data-episode-season-id="9" itemprop="episode" itemscope="" itemtype="http://schema.org/Episode">
                <td class="season1EpisodeID">
                    <meta itemprop="episodeNumber" content="9"><a itemprop="url" href="/anime/stream/goblin-slayer/staffel-1/episode-9"> Folge 9 </a>
                </td>
                <td class="seasonEpisodeTitle"><a href="/anime/stream/goblin-slayer/staffel-1/episode-9"> <strong>Hin und zurück</strong> - <span>There and Back Again</span> </a></td>
                <td><a href="/anime/stream/goblin-slayer/staffel-1/episode-9"> <i class="icon VOE" title="VOE"></i><i class="icon Filemoon" title="Filemoon"></i><i class="icon Vidmoly" title="Vidmoly"></i> </a></td>
                <td class="editFunctions"><a href="/anime/stream/goblin-slayer/staffel-1/episode-9"> <img class="flag" src="/public/img/german.svg" alt="Deutsche Sprache, Flagge" title="Deutsch/German"> <img class="flag" src="/public/img/japanese-german.svg" alt="Deutsche Flagge, Untertitel, Flagge" title="Mit deutschem Untertitel"> <img class="flag" src="/public/img/japanese-english.svg" alt="Englische Sprache, Flagge" title="Englisch"> </a></td>
            </tr>
            <tr class="" data-episode-id="2320" data-episode-season-id="10" itemprop="episode" itemscope="" itemtype="http://schema.org/Episode">
                <td class="season1EpisodeID">
                    <meta itemprop="episodeNumber" content="10"><a itemprop="url" href="/anime/stream/goblin-slayer/staffel-1/episode-10"> Folge 10 </a>
                </td>
                <td class="seasonEpisodeTitle"><a href="/anime/stream/goblin-slayer/staffel-1/episode-10"> <strong>Schlummer</strong> - <span>Dozing</span> </a></td>
                <td><a href="/anime/stream/goblin-slayer/staffel-1/episode-10"> <i class="icon VOE" title="VOE"></i><i class="icon Filemoon" title="Filemoon"></i><i class="icon Vidmoly" title="Vidmoly"></i> </a></td>
                <td class="editFunctions"><a href="/anime/stream/goblin-slayer/staffel-1/episode-10"> <img class="flag" src="/public/img/german.svg" alt="Deutsche Sprache, Flagge" title="Deutsch/German"> <img class="flag" src="/public/img/japanese-german.svg" alt="Deutsche Flagge, Untertitel, Flagge" title="Mit deutschem Untertitel"> <img class="flag" src="/public/img/japanese-english.svg" alt="Englische Sprache, Flagge" title="Englisch"> </a></td>
            </tr>
            <tr class="" data-episode-id="2321" data-episode-season-id="11" itemprop="episode" itemscope="" itemtype="http://schema.org/Episode">
                <td class="season1EpisodeID">
                    <meta itemprop="episodeNumber" content="11"><a itemprop="url" href="/anime/stream/goblin-slayer/staffel-1/episode-11"> Folge 11 </a>
                </td>
                <td class="seasonEpisodeTitle"><a href="/anime/stream/goblin-slayer/staffel-1/episode-11"> <strong>Ein Festmahl für Abenteurer</strong> - <span>A Gathering of Adventurers</span> </a></td>
                <td><a href="/anime/stream/goblin-slayer/staffel-1/episode-11"> <i class="icon VOE" title="VOE"></i><i class="icon Filemoon" title="Filemoon"></i><i class="icon Vidmoly" title="Vidmoly"></i> </a></td>
                <td class="editFunctions"><a href="/anime/stream/goblin-slayer/staffel-1/episode-11"> <img class="flag" src="/public/img/german.svg" alt="Deutsche Sprache, Flagge" title="Deutsch/German"> <img class="flag" src="/public/img/japanese-german.svg" alt="Deutsche Flagge, Untertitel, Flagge" title="Mit deutschem Untertitel"> <img class="flag" src="/public/img/japanese-english.svg" alt="Englische Sprache, Flagge" title="Englisch"> </a></td>
            </tr>
            <tr class="" data-episode-id="2322" data-episode-season-id="12" itemprop="episode" itemscope="" itemtype="http://schema.org/Episode">
                <td class="season1EpisodeID">
                    <meta itemprop="episodeNumber" content="12"><a itemprop="url" href="/anime/stream/goblin-slayer/staffel-1/episode-12"> Folge 12 </a>
                </td>
                <td class="seasonEpisodeTitle"><a href="/anime/stream/goblin-slayer/staffel-1/episode-12"> <strong>Vom Ende eines Abenteurers</strong> - <span>The Fate of an Adventurer</span> </a></td>
                <td><a href="/anime/stream/goblin-slayer/staffel-1/episode-12"> <i class="icon VOE" title="VOE"></i><i class="icon Filemoon" title="Filemoon"></i><i class="icon Vidmoly" title="Vidmoly"></i> </a></td>
                <td class="editFunctions"><a href="/anime/stream/goblin-slayer/staffel-1/episode-12"> <img class="flag" src="/public/img/german.svg" alt="Deutsche Sprache, Flagge" title="Deutsch/German"> <img class="flag" src="/public/img/japanese-german.svg" alt="Deutsche Flagge, Untertitel, Flagge" title="Mit deutschem Untertitel"> <img class="flag" src="/public/img/japanese-english.svg" alt="Englische Sprache, Flagge" title="Englisch"> </a></td>
            </tr>
        </tbody>
        """
        logger.debug("extracting episodes...")

        html = self._html
        episodes = []

        marker = 'itemtype="http://schema.org/Episode"'
        pos = 0

        while True:
            pos = html.find(marker, pos)
            if pos == -1:
                break

            tr_start = html.rfind("<tr", 0, pos)
            tr_end = html.find("</tr>", pos)
            if tr_start == -1 or tr_end == -1:
                break

            tr_html = html[tr_start:tr_end]

            # Episode number
            ep_num = None
            meta_pos = tr_html.find('itemprop="episodeNumber"')
            if meta_pos != -1:
                c_start = tr_html.find('content="', meta_pos) + 9
                c_end = tr_html.find('"', c_start)
                ep_num = int(tr_html[c_start:c_end])

            # Episode URL
            ep_url = None
            url_pos = tr_html.find('itemprop="url"')
            if url_pos != -1:
                h_start = tr_html.find('href="', url_pos) + 6
                h_end = tr_html.find('"', h_start)
                ep_url = tr_html[h_start:h_end]
                if ep_url.startswith("/"):
                    ep_url = "https://aniworld.to" + ep_url

            # Titles
            title_de = None
            s_start = tr_html.find("<strong>")
            if s_start != -1:
                s_start += 8
                s_end = tr_html.find("</strong>", s_start)
                title_de = tr_html[s_start:s_end].strip()

            title_en = None
            span_start = tr_html.find("<span>")
            if span_start != -1:
                span_start += 6
                span_end = tr_html.find("</span>", span_start)
                title_en = tr_html[span_start:span_end].strip()

            if ep_url and ep_num:
                episodes.append(
                    AniworldEpisode(
                        season=self,
                        url=ep_url,
                        episode_number=ep_num,
                        title_de=title_de,
                        title_en=title_en,
                    )
                )

            pos = tr_end

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
    print("TODO: Add test")
