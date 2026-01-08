from config import logger, GLOBAL_SESSION


class AniworldSeries:
    """
    Attributes:
        url
        title
        description
        genres
        release_year
        poster_url
        directors
        actors
        producer
        country
        age_rating
        rating
        seasons
        _html
    """

    def __init__(self, url: str):
        self.url = url

        self.__html = None

        self.__title = None
        self.__description = None
        self.__genres = None
        self.__release_year = None
        self.__poster_url = None

        self.__directors = None
        self.__actors = None
        self.__producer = None
        self.__country = None
        self.__age_rating = None
        self.__rating = None
        self.__has_movies = None

        self.__seasons = None  # AniworldSeason objects (lazy-loaded)

    # -----------------------------
    # PUBLIC PROPERTIES (lazy load)
    # -----------------------------

    @property
    def _html(self) -> str:
        if self.__html is None:
            logger.debug(f"fetching ({self.url})...")
            resp = GLOBAL_SESSION.get(self.url)
            self.__html = resp.text
        return self.__html

    @property
    def title(self) -> str:
        if self.__title is None:
            self.__title = self.__extract_title()
        return self.__title

    @property
    def description(self) -> str:
        if self.__description is None:
            self.__description = self.__extract_description()
        return self.__description

    @property
    def genres(self) -> list[str]:
        if self.__genres is None:
            self.__genres = self.__extract_genres()
        return self.__genres

    @property
    def release_year(self) -> str:
        if self.__release_year is None:
            self.__release_year = self.__extract_release_year()
        return self.__release_year

    @property
    def poster_url(self) -> str:
        if self.__poster_url is None:
            self.__poster_url = self.__extract_poster_url()
        return self.__poster_url

    @property
    def directors(self) -> list[str]:
        if self.__directors is None:
            self.__directors = self.__extract_directors()
        return self.__directors

    @property
    def actors(self) -> list[str]:
        if self.__actors is None:
            self.__actors = self.__extract_actors()
        return self.__actors

    @property
    def producer(self) -> str:
        if self.__producer is None:
            self.__producer = self.__extract_producer()
        return self.__producer

    @property
    def country(self) -> str:
        if self.__country is None:
            self.__country = self.__extract_country()
        return self.__country

    @property
    def age_rating(self) -> str:
        if self.__age_rating is None:
            self.__age_rating = self.__extract_age_rating()
        return self.__age_rating

    @property
    def rating(self) -> str:
        if self.__rating is None:
            self.__rating = self.__extract_rating()
        return self.__rating

    @property
    def seasons(self):
        if self.__seasons is None:
            self.__seasons = self.__extract_seasons()
        return self.__seasons

    @property
    def has_movies(self):
        if self.__has_movies is None:
            self.__has_movies = self.__extract_has_movies()
        return self.__has_movies

    # -----------------------------
    # PRIVATE EXTRACTION FUNCTIONS
    # -----------------------------

    def __extract_title(self) -> str:
        """
        <div class="series-title">
            <h1 itemprop="name" title="Animes Stream: 哥布林猎人, Goburin Sureiyā, 고블린슬레이어, Goblin Katili" data-alternativetitles="哥布林猎人, Goburin Sureiyā, 고블린슬레이어, Goblin Katili"><span>Goblin Slayer</span></h1>
            <small> (<span itemprop="startDate"><a href="https://aniworld.to/animes/jahr/2018">2018</a></span> - <span itemprop="endDate"><a href="https://aniworld.to/animes/jahr/2023">2023</a></span>)</small>
            <div title="Empfohlene Altersfreigabe: 16 Jahre" data-fsk="16" class="fsk fsk16">Ab: <span>16</span></div>
            <a href="https://www.imdb.com/title/tt8690728" title="IMDB ID: " data-imdb="tt8690728" class="imdb-link" target="_blank" rel="noopener">IMDB</a>
        </div>
        """
        logger.debug("extracting title...")

        html = self._html

        start = html.find('<div class="series-title">')
        if start == -1:
            return None

        span_start = html.find("<span>", start)
        span_end = html.find("</span>", span_start)

        if span_start == -1 or span_end == -1:
            return None

        title = html[span_start + len("<span>") : span_end].strip()
        return title

    def __extract_description(self) -> str | None:
        """
        <p class="seri_des" itemprop="accessibilitySummary" data-description-type="review" data-full-description="Goblins - die schwächsten aller Monster. Mit der Stärke und dem Verstand von kleinen Kindern ausgestattet, können sie lediglich ihre immerwährende Überzahl zu ihren Stärken zählen. Doch so dumm die Goblins auch sein mögen, sie sind keine Narren und ihr kindliches Denken schlägt schnell ins Grausame und Brutale um, wenn sie glauben, dass ihnen Unrecht geschieht. Eine junge Priesterin, gerade einmal 15 Jahre alt, beschließt, ihren Tempel zu verlassen und als Abenteuerin die Welt etwas sicherer zu machen. Jeder fängt klein an und so schließt sie sich spontan einer Gruppe Abenteurer an, die gerade einen Quest angenommen hat, der sie gegen eben diese schwächsten aller Monster führt: Ein paar Mädchen wurden von Goblins entführt und bevor diese zu deren Spielzeugen werden, gilt es, die Goblins zu töten und die Mädchen zu retten!">Goblins - die schwächsten aller Monster. Mit der Stärke und dem Verstand von kleinen Kindern ausgestattet, können sie lediglich ihre immerwährende Überzahl zu ihren Stärken zählen. Doch so dumm die Goblins auch sein mögen, sie sind keine Narren und ihr kindliches Denken schlägt schnell ins...<span class="showMore">mehr anzeigen</span></p>
        """
        logger.debug("extracting description...")

        html = self._html

        marker = 'class="seri_des"'
        start = html.find(marker)
        if start == -1:
            return None

        attr = 'data-full-description="'
        attr_start = html.find(attr, start)
        if attr_start == -1:
            return None

        value_start = attr_start + len(attr)
        value_end = html.find('"', value_start)
        if value_end == -1:
            return None

        description = html[value_start:value_end].strip()
        return description

    def __extract_genres(self) -> list[str]:
        """
        <div class="genres">
            <ul data-main-genre="action">
                <li><a href="/genre/action" class="genreButton clearbutton" itemprop="genre">Action</a></li>
                <li><a href="/genre/abenteuer" class="genreButton clearbutton" itemprop="genre">Abenteuer</a></li>
                <li><a href="/genre/drama" class="genreButton clearbutton" itemprop="genre">Drama</a></li>
                <li><a href="/genre/engsub" class="genreButton clearbutton" itemprop="genre">EngSub</a></li>
                <li><a href="/genre/fantasy" class="genreButton clearbutton" itemprop="genre">Fantasy</a></li>
                <li><a href="/genre/ger" class="genreButton clearbutton" itemprop="genre">Ger</a></li>
                <li><a href="/genre/gersub" class="genreButton clearbutton" itemprop="genre">GerSub</a></li>
                <li><button class="hiddenArea">+ 2</button></li>
                <li><a href="/genre/horror" class="genreButton clearbutton" itemprop="genre">Horror</a></li>
                <li><a href="/genre/psychodrama" class="genreButton clearbutton" itemprop="genre">Psychodrama</a></li>
            </ul>
        </div>
        """
        logger.debug("extracting genres...")

        html = self._html

        genres = []

        block_start = html.find('<div class="genres">')
        if block_start == -1:
            return genres

        ul_start = html.find("<ul", block_start)
        ul_end = html.find("</ul>", ul_start)
        if ul_start == -1 or ul_end == -1:
            return genres

        ul_html = html[ul_start:ul_end]

        search_pos = 0
        marker = 'itemprop="genre"'

        while True:
            pos = ul_html.find(marker, search_pos)
            if pos == -1:
                break

            text_start = ul_html.find(">", pos) + 1
            text_end = ul_html.find("</a>", text_start)

            if text_start == -1 or text_end == -1:
                break

            genre = ul_html[text_start:text_end].strip()
            genres.append(genre)

            search_pos = text_end

        return genres

    def __extract_release_year(self) -> str:
        """
        <div class="series-title">
            <h1 itemprop="name" title="Animes Stream: 哥布林猎人, Goburin Sureiyā, 고블린슬레이어, Goblin Katili" data-alternativetitles="哥布林猎人, Goburin Sureiyā, 고블린슬레이어, Goblin Katili"><span>Goblin Slayer</span></h1>
            <small> (<span itemprop="startDate"><a href="https://aniworld.to/animes/jahr/2018">2018</a></span> - <span itemprop="endDate"><a href="https://aniworld.to/animes/jahr/2023">2023</a></span>)</small>
            <div title="Empfohlene Altersfreigabe: 16 Jahre" data-fsk="16" class="fsk fsk16">Ab: <span>16</span></div>
            <a href="https://www.imdb.com/title/tt8690728" title="IMDB ID: " data-imdb="tt8690728" class="imdb-link" target="_blank" rel="noopener">IMDB</a>
        </div>
        """
        logger.debug("extracting release year…")

        html = self._html

        div_start = html.find('<div class="series-title">')
        if div_start == -1:
            return None

        div_end = html.find("</div>", div_start)
        if div_end == -1:
            return None

        block = html[div_start:div_end]

        small_start = block.find("<small>")
        if small_start == -1:
            return None

        small_end = block.find("</small>", small_start)
        if small_end == -1:
            return None

        small_block = block[small_start:small_end]

        def extract_year(marker: str) -> str | None:
            pos = small_block.find(marker)
            if pos == -1:
                return None

            href_pos = small_block.find('href="', pos)
            if href_pos == -1:
                return None

            href_start = href_pos + len('href="')
            href_end = small_block.find('"', href_start)
            href = small_block[href_start:href_end]

            year = href.rstrip("/").split("/")[-1]
            return year if year.isdigit() else None

        start_year = extract_year('itemprop="startDate"')
        if not start_year:
            return None

        end_year = extract_year('itemprop="endDate"')
        if not end_year:
            return start_year

        return f"{start_year}-{end_year}"

    def __extract_poster_url(self) -> str:
        """
        <div class="seriesCoverBox"><img src="/public/img/cover/sentenced-to-be-a-hero-stream-cover-R6nfhysg9tvuw9XnflBmesyEmaLPrtp1_220x330.png" data-src="/public/img/cover/sentenced-to-be-a-hero-stream-cover-R6nfhysg9tvuw9XnflBmesyEmaLPrtp1_220x330.png" alt="Sentenced to Be a Hero, Cover, HD, Anime Stream, ganze Folge" itemprop="image" title="Cover Sentenced to Be a Hero AniWorld" class="loaded" data-was-processed="true"><noscript><img src="/public/img/cover/sentenced-to-be-a-hero-stream-cover-R6nfhysg9tvuw9XnflBmesyEmaLPrtp1_220x330.png" alt="Sentenced to Be a Hero, Cover, HD, Anime Stream, ganze Folge" itemprop="image" title="Cover Sentenced to Be a Hero AniWorld"></noscript></div>
        """
        logger.debug("extracting poster url...")

        html = self._html

        box_start = html.find('<div class="seriesCoverBox">')
        if box_start == -1:
            return None

        img_start = html.find("<img", box_start)
        if img_start == -1:
            return None

        attr = 'data-src="'
        src_start = html.find(attr, img_start)

        if src_start != -1:
            value_start = src_start + len(attr)
            value_end = html.find('"', value_start)
            rel_url = html[value_start:value_end].strip()
        else:
            attr = 'src="'
            src_start = html.find(attr, img_start)
            if src_start == -1:
                return None
            value_start = src_start + len(attr)
            value_end = html.find('"', value_start)
            rel_url = html[value_start:value_end].strip()

        return f"https://aniworld.to{rel_url}"

    def __extract_directors(self) -> list[str]:
        """
        <li class="seriesDirector"><strong>Regisseure:</strong>
            <ul>
                <li itemprop="director" itemscope="" itemtype="http://schema.org/Person"><a href="/animes/regisseur/mitsutoshi-ogura" itemprop="url"><span itemprop="name">Mitsutoshi Ogura</span></a></li>
                <li itemprop="director" itemscope="" itemtype="http://schema.org/Person"><a href="/animes/regisseur/noritomo-isogai" itemprop="url"><span itemprop="name">Noritomo Isogai</span></a></li>
            </ul>
            <div class="cf"></div>
        </li>
        """
        logger.debug("extracting directors...")

        html = self._html

        block_start = html.find('<li class="seriesDirector">')
        if block_start == -1:
            return []

        block_end = html.find("</li>", block_start)
        if block_end == -1:
            return []

        block = html[block_start:block_end]

        directors = []
        search_pos = 0
        marker = 'itemprop="name"'

        while True:
            pos = block.find(marker, search_pos)
            if pos == -1:
                break

            name_start = block.find(">", pos) + 1
            name_end = block.find("</span>", name_start)

            if name_start == -1 or name_end == -1:
                break

            name = block[name_start:name_end].strip()
            directors.append(name)

            search_pos = name_end

        return directors

    def __extract_actors(self) -> list[str]:
        """
        <li><strong style="float: left;" class="seriesActor">Schauspieler:</strong>
            <ul class="showHiddenArea">
                <li itemprop="actor" itemscope="" itemtype="http://schema.org/Person"><a href="/animes/schauspieler/yichir-umehara" itemprop="url"><span itemprop="name">Yūichirō Umehara</span></a></li>
                <li itemprop="actor" itemscope="" itemtype="http://schema.org/Person"><a href="/animes/schauspieler/yui-ogura" itemprop="url"><span itemprop="name">Yui Ogura</span></a></li>
                <li itemprop="actor" itemscope="" itemtype="http://schema.org/Person"><a href="/animes/schauspieler/yuichi-nakamura" itemprop="url"><span itemprop="name">Yuichi Nakamura</span></a></li>
                <li><button class="hiddenArea" style="display: none;"> &amp; 7 weitere</button></li>
                <li itemprop="actor" itemscope="" itemtype="http://schema.org/Person"><a href="/animes/schauspieler/tomokazu-sugita" itemprop="url"><span itemprop="name">Tomokazu Sugita</span></a></li>
                <li itemprop="actor" itemscope="" itemtype="http://schema.org/Person"><a href="/animes/schauspieler/nao-touyama" itemprop="url"><span itemprop="name">Nao Touyama</span></a></li>
                <li itemprop="actor" itemscope="" itemtype="http://schema.org/Person"><a href="/animes/schauspieler/yoko-hikasa" itemprop="url"><span itemprop="name">Yoko Hikasa</span></a></li>
                <li itemprop="actor" itemscope="" itemtype="http://schema.org/Person"><a href="/animes/schauspieler/aya-endo" itemprop="url"><span itemprop="name">Aya Endo</span></a></li>
                <li itemprop="actor" itemscope="" itemtype="http://schema.org/Person"><a href="/animes/schauspieler/maaya-uchida" itemprop="url"><span itemprop="name">Maaya Uchida</span></a></li>
                <li itemprop="actor" itemscope="" itemtype="http://schema.org/Person"><a href="/animes/schauspieler/yuka-iguchi" itemprop="url"><span itemprop="name">Yuka Iguchi</span></a></li>
                <li itemprop="actor" itemscope="" itemtype="http://schema.org/Person"><a href="/animes/schauspieler/yoshitsugu-matsuoka" itemprop="url"><span itemprop="name">Yoshitsugu Matsuoka</span></a></li>
            </ul>
            <div class="cf"></div>
        </li>
        """
        logger.debug("extracting actors...")

        html = self._html

        block_start = html.find('<strong style="float: left;" class="seriesActor">')
        if block_start == -1:
            return []

        ul_start = html.find("<ul", block_start)
        ul_end = html.find("</ul>", ul_start)
        if ul_start == -1 or ul_end == -1:
            return []

        ul_html = html[ul_start:ul_end]

        actors = []
        search_pos = 0
        marker = 'itemprop="name"'

        while True:
            pos = ul_html.find(marker, search_pos)
            if pos == -1:
                break

            name_start = ul_html.find(">", pos) + 1
            name_end = ul_html.find("</span>", name_start)

            if name_start == -1 or name_end == -1:
                break

            name = ul_html[name_start:name_end].strip()
            actors.append(name)

            search_pos = name_end

        return actors

    def __extract_producer(self) -> str:
        """
        <li><strong style="float: left;" class="seriesProducer">Produzent:</strong>
            <ul>
                <li itemprop="creator" itemscope="" itemtype="http://schema.org/Organization"><a href="/animes/produzent/white-fox" itemprop="url"><span itemprop="name">White Fox</span></a></li>
                <li itemprop="creator" itemscope="" itemtype="http://schema.org/Organization"><a href="/animes/produzent/lidenfilms" itemprop="url"><span itemprop="name">LIDENFILMS</span></a></li>
            </ul>
            <div class="cf"></div>
        </li>
        """
        logger.debug("extracting producer...")

        html = self._html

        block_start = html.find('<strong style="float: left;" class="seriesProducer">')
        if block_start == -1:
            return None

        ul_start = html.find("<ul", block_start)
        ul_end = html.find("</ul>", ul_start)
        if ul_start == -1 or ul_end == -1:
            return None

        ul_html = html[ul_start:ul_end]

        producers = []
        search_pos = 0
        marker = 'itemprop="name"'

        while True:
            pos = ul_html.find(marker, search_pos)
            if pos == -1:
                break

            name_start = ul_html.find(">", pos) + 1
            name_end = ul_html.find("</span>", name_start)
            if name_start == -1 or name_end == -1:
                break

            producers.append(ul_html[name_start:name_end].strip())
            search_pos = name_end

        return ", ".join(producers) if producers else None

    def __extract_country(self) -> str:
        """
        <li><strong style="float: left;" class="seriesCountry">Land:</strong>
            <ul>
                <li data-content-type="country" itemprop="countryOfOrigin" itemscope="" itemtype="http://schema.org/Country"><a href="/animes/aus/japan" itemprop="url"><span itemprop="name">Japan</span></a></li>
            </ul>
            <div class="cf"></div>
        </li>
        """
        logger.debug("extracting country...")

        html = self._html

        block_start = html.find('<strong style="float: left;" class="seriesCountry">')
        if block_start == -1:
            return None

        ul_start = html.find("<ul", block_start)
        ul_end = html.find("</ul>", ul_start)
        if ul_start == -1 or ul_end == -1:
            return None

        ul_html = html[ul_start:ul_end]

        marker = 'itemprop="name"'
        pos = ul_html.find(marker)
        if pos == -1:
            return None

        name_start = ul_html.find(">", pos) + 1
        name_end = ul_html.find("</span>", name_start)
        if name_start == -1 or name_end == -1:
            return None

        return ul_html[name_start:name_end].strip()

    def __extract_age_rating(self) -> str:
        """
        <div title="Empfohlene Altersfreigabe: 16 Jahre" data-fsk="16" class="fsk fsk16">Ab: <span>16</span></div>
        """
        logger.debug("extracting age rating...")

        html = self._html

        marker = 'data-fsk="'
        pos = html.find(marker)
        if pos == -1:
            return None

        start = pos + len(marker)
        end = html.find('"', start)
        if end == -1:
            return None

        return html[start:end].strip()

    def __extract_rating(self) -> str:
        logger.debug("extracting rating...")

        html = self._html

        marker_value = 'itemprop="ratingValue"'
        pos_value = html.find(marker_value)
        if pos_value == -1:
            return None

        start_value = html.find(">", pos_value) + 1
        end_value = html.find("</span>", start_value)
        if start_value == -1 or end_value == -1:
            return None

        rating_value = html[start_value:end_value].strip()

        marker_best = 'itemprop="bestRating"'
        pos_best = html.find(marker_best)
        if pos_best == -1:
            return rating_value  # fallback

        start_best = html.find(">", pos_best) + 1
        end_best = html.find("</span>", start_best)
        if start_best == -1 or end_best == -1:
            return rating_value

        best_rating = html[start_best:end_best].strip()

        return f"{rating_value}/{best_rating}"

    def __extract_seasons(self):
        """
        Extracts number of seasons from meta tag and creates AniworldSeason objects
        <meta itemprop="numberOfSeasons" content="3">
        """
        logger.debug("extracting seasons...")

        html = self._html

        # Import here to avoid circular import
        from AniworldSeason import AniworldSeason

        # Look for the numberOfSeasons meta tag
        marker = 'itemprop="numberOfSeasons"'
        pos = html.find(marker)
        if pos == -1:
            logger.debug("numberOfSeasons meta tag not found, defaulting to 1 season")
            return [AniworldSeason(f"{self.url}/staffel-1")]

        # Extract content attribute value
        content_marker = 'content="'
        content_pos = html.find(content_marker, pos)
        if content_pos == -1:
            logger.debug("content attribute not found, defaulting to 1 season")
            return [AniworldSeason(f"{self.url}/staffel-1")]

        content_start = content_pos + len(content_marker)
        content_end = html.find('"', content_start)
        if content_end == -1:
            logger.debug("content end not found, defaulting to 1 season")
            return [AniworldSeason(f"{self.url}/staffel-1")]

        num_seasons_str = html[content_start:content_end].strip()
        try:
            num_seasons = int(num_seasons_str)
        except ValueError:
            logger.debug(
                f"Could not parse number of seasons: {num_seasons_str}, defaulting to 1"
            )
            return [AniworldSeason(f"{self.url}/staffel-1")]

        logger.debug(f"Found {num_seasons} seasons (may include movies...)")

        # Check if movies are present and subtract from count if needed
        if self.has_movies:
            logger.debug("Movies detected, subtracting one from season count")
            num_seasons -= 1

        logger.debug(f"Final season count: {num_seasons}")

        self.season_count = num_seasons

        # Create season objects for each season
        seasons = []
        for season_num in range(1, num_seasons + 1):
            season_url = f"{self.url}/staffel-{season_num}"
            seasons.append(AniworldSeason(season_url))

        return seasons

    def __extract_has_movies(self):
        """
        Detects if the series has movies by looking for the Filme link
        <li><a href="/anime/stream/goblin-slayer/filme" title="Alle Filme">Filme</a></li>
        """
        logger.debug("checking for movies...")

        html = self._html

        # Look for the Filme link
        marker = 'title="Alle Filme">Filme</a>'
        pos = html.find(marker)
        has_movies = pos != -1

        logger.debug(f"Has movies: {has_movies}")
        return has_movies


if __name__ == "__main__":
    series = AniworldSeries("https://aniworld.to/anime/stream/kaguya-sama-love-is-war")

    # nothing should be loaded as passing url is required
    print(series.url)

    # should only fetch the html of url once even if called two times
    print(series.title)
    print(series.title)
    print(series._html[:34])

    # should reuse html which is already fetched from the series.title call
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

    print("-" * 25)
    print(series.seasons)

    for i in range(series.season_count):
        print(f"{'-' * 10}Season: {i + 1}{'-' * 10}")
        # print(f"Season: {series.seasons[i].season_number} -> Episodes: {series.seasons[i].episode_count}")
        print(series.seasons[i].series.title)
        print(series.seasons[i].url)
        print(series.seasons[i].season_number)
        print(series.seasons[i].episode_count)

        # Test caching: accessing episodes multiple times should not trigger new extractions
        episodes = series.seasons[i].episodes  # First access
        print(f"Extracted {len(episodes)} episodes")

        # Second access - should be cached
        episodes2 = series.seasons[i].episodes

        for j in range(series.seasons[i].episode_count):
            print(episodes[j].url)
            print("->", episodes[j].title_de)
            print()
        # print(series.seasons[i]._html[:95])
        print(f"{'-' * 25}\n")
