import re
import threading
import uuid

from flask import Flask, jsonify, redirect, render_template, request, session, url_for

from ..config import LANG_LABELS, SUPPORTED_PROVIDERS
from ..logger import get_logger
from ..providers import resolve_provider
from ..search import query as aniworld_query

logger = get_logger(__name__)

# In-memory download status tracking
_downloads = {}
_downloads_lock = threading.Lock()

# Only match series-level links: /anime/stream/<slug> (no season/episode)
_SERIES_LINK_PATTERN = re.compile(r"^/anime/stream/[a-zA-Z0-9\-]+/?$", re.IGNORECASE)


def _run_download(download_id, episodes, language, provider):
    """Background worker that downloads episodes sequentially."""
    with _downloads_lock:
        _downloads[download_id]["status"] = "running"

    total = len(episodes)
    for i, ep_url in enumerate(episodes):
        with _downloads_lock:
            _downloads[download_id]["current"] = i + 1
            _downloads[download_id]["current_url"] = ep_url

        try:
            prov = resolve_provider(ep_url)
            episode = prov.episode_cls(
                url=ep_url,
                selected_language=language,
                selected_provider=provider,
            )
            episode.download()
        except Exception as e:
            logger.error(f"Download failed for {ep_url}: {e}")
            with _downloads_lock:
                _downloads[download_id].setdefault("errors", []).append(
                    {"url": ep_url, "error": str(e)}
                )

    with _downloads_lock:
        _downloads[download_id]["status"] = "completed"
        _downloads[download_id]["current"] = total


def create_app(auth_enabled=False):
    app = Flask(__name__)

    if auth_enabled:
        from .auth import auth_bp, get_current_user, get_or_create_secret_key, login_required
        from .db import has_any_admin, init_db

        app.secret_key = get_or_create_secret_key()
        init_db()
        app.register_blueprint(auth_bp)

        @app.before_request
        def _check_setup():
            if request.endpoint and request.endpoint.startswith("auth."):
                return None
            if request.endpoint == "static":
                return None
            if not has_any_admin():
                return redirect(url_for("auth.setup"))
            return None

        @app.context_processor
        def _inject_auth():
            return {"current_user": get_current_user(), "auth_enabled": True}
    else:

        @app.context_processor
        def _inject_no_auth():
            return {"current_user": None, "auth_enabled": False}

    @app.route("/")
    def index():
        return render_template(
            "index.html",
            lang_labels=LANG_LABELS,
            supported_providers=SUPPORTED_PROVIDERS,
        )

    @app.route("/api/search", methods=["POST"])
    def api_search():
        data = request.get_json(silent=True) or {}
        keyword = (data.get("keyword") or "").strip()
        if not keyword:
            return jsonify({"error": "keyword is required"}), 400

        results = []

        # AniWorld search
        aw_results = aniworld_query(keyword) or []
        if isinstance(aw_results, dict):
            aw_results = [aw_results]
        for item in aw_results:
            link = item.get("link", "")
            if _SERIES_LINK_PATTERN.match(link):
                title = (
                    item.get("title", "Unknown")
                    .replace("<em>", "")
                    .replace("</em>", "")
                )
                results.append(
                    {
                        "title": title,
                        "url": f"https://aniworld.to{link}",
                    }
                )

        return jsonify({"results": results})

    @app.route("/api/series")
    def api_series():
        url = request.args.get("url", "").strip()
        if not url:
            return jsonify({"error": "url is required"}), 400

        try:
            prov = resolve_provider(url)
            series = prov.series_cls(url=url)
            return jsonify(
                {
                    "title": series.title,
                    "poster_url": getattr(series, "poster_url", None),
                    "description": getattr(series, "description", ""),
                    "genres": getattr(series, "genres", []),
                    "release_year": getattr(series, "release_year", ""),
                }
            )
        except Exception as e:
            logger.error(f"Series fetch failed: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500

    @app.route("/api/seasons")
    def api_seasons():
        url = request.args.get("url", "").strip()
        if not url:
            return jsonify({"error": "url is required"}), 400

        try:
            prov = resolve_provider(url)
            series = prov.series_cls(url=url)
            seasons_data = []
            for season in series.seasons:
                seasons_data.append(
                    {
                        "url": season.url,
                        "season_number": season.season_number,
                        "episode_count": season.episode_count,
                        "are_movies": getattr(season, "are_movies", False),
                    }
                )
            return jsonify({"seasons": seasons_data})
        except Exception as e:
            logger.error(f"Seasons fetch failed: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500

    @app.route("/api/episodes")
    def api_episodes():
        url = request.args.get("url", "").strip()
        if not url:
            return jsonify({"error": "url is required"}), 400

        try:
            prov = resolve_provider(url)
            season = prov.season_cls(url=url)
            episodes_data = []
            for ep in season.episodes:
                episodes_data.append(
                    {
                        "url": ep.url,
                        "episode_number": ep.episode_number,
                        "title_de": getattr(ep, "title_de", ""),
                        "title_en": getattr(ep, "title_en", ""),
                    }
                )
            return jsonify({"episodes": episodes_data})
        except Exception as e:
            logger.error(f"Episodes fetch failed: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500

    @app.route("/api/providers")
    def api_providers():
        url = request.args.get("url", "").strip()
        if not url:
            return jsonify({"error": "url is required"}), 400

        try:
            prov = resolve_provider(url)
            episode = prov.episode_cls(url=url)
            pd = episode.provider_data

            provider_info = {}
            for (audio, subtitles), providers in pd._data.items():
                lang_key = f"{audio.value}/{subtitles.value}"
                provider_info[lang_key] = list(providers.keys())

            return jsonify({"providers": provider_info})
        except Exception as e:
            logger.error(f"Providers fetch failed: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500

    @app.route("/api/download", methods=["POST"])
    def api_download():
        data = request.get_json(silent=True) or {}
        episodes = data.get("episodes", [])
        language = data.get("language", "German Dub")
        provider = data.get("provider", "VOE")

        if not episodes:
            return jsonify({"error": "episodes list is required"}), 400

        download_id = str(uuid.uuid4())
        with _downloads_lock:
            _downloads[download_id] = {
                "status": "queued",
                "total": len(episodes),
                "current": 0,
                "current_url": None,
                "errors": [],
            }

        thread = threading.Thread(
            target=_run_download,
            args=(download_id, episodes, language, provider),
            daemon=True,
        )
        thread.start()

        return jsonify({"download_id": download_id})

    @app.route("/api/download/status")
    def api_download_status():
        download_id = request.args.get("id", "").strip()

        if download_id:
            with _downloads_lock:
                info = _downloads.get(download_id)
            if info is None:
                return jsonify({"error": "unknown download_id"}), 404
            return jsonify({"id": download_id, **info})

        # Return all downloads
        with _downloads_lock:
            all_downloads = {
                did: dict(info) for did, info in _downloads.items()
            }
        return jsonify({"downloads": all_downloads})

    if auth_enabled:
        # Wrap all non-auth, non-static view functions with login_required
        _exempt = {"static", "auth.login", "auth.logout", "auth.setup"}
        for endpoint, view_func in list(app.view_functions.items()):
            if endpoint not in _exempt:
                app.view_functions[endpoint] = login_required(view_func)

    return app


def start_web_ui(host="127.0.0.1", port=5000, open_browser=True, auth_enabled=False):
    """Start the Flask web UI server."""
    import threading
    import webbrowser

    app = create_app(auth_enabled=auth_enabled)
    url = f"http://{'localhost' if host in ('0.0.0.0', '127.0.0.1') else host}:{port}"
    print(f"Starting AniWorld Web UI on {url}")

    if open_browser:
        threading.Timer(0.5, webbrowser.open, args=(url,)).start()

    app.run(host=host, port=port, debug=False)
