import re
import threading
import uuid

from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from flask_wtf.csrf import CSRFProtect

from ..config import LANG_KEY_MAP, LANG_LABELS, SUPPORTED_PROVIDERS
from ..extractors import provider_functions
from ..logger import get_logger
from ..providers import resolve_provider
from ..search import query as aniworld_query

logger = get_logger(__name__)


def _get_working_providers():
    """Return only providers whose extractors are actually implemented."""
    working = []
    for p in SUPPORTED_PROVIDERS:
        func_name = f"get_direct_link_from_{p.lower()}"
        if func_name not in provider_functions:
            continue
        try:
            provider_functions[func_name]("")
        except NotImplementedError:
            continue
        except Exception:
            working.append(p)
    return tuple(working)


WORKING_PROVIDERS = _get_working_providers()

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


def create_app(auth_enabled=False, sso_enabled=False, force_sso=False):
    import os

    app = Flask(__name__)

    base_url = os.environ.get("ANIWORLD_WEB_BASE_URL", "").strip().rstrip("/")
    if base_url:
        from urllib.parse import urlparse

        parsed = urlparse(base_url)
        scheme = parsed.scheme or "https"
        host = parsed.netloc

        # WSGI middleware that overrides scheme/host before Flask sees the request
        _inner_wsgi = app.wsgi_app

        def _proxy_wsgi(environ, start_response):
            environ["wsgi.url_scheme"] = scheme
            if host:
                environ["HTTP_HOST"] = host
            return _inner_wsgi(environ, start_response)

        app.wsgi_app = _proxy_wsgi

    if auth_enabled:
        from .auth import (
            auth_bp,
            get_current_user,
            get_or_create_secret_key,
            init_oidc,
            login_required,
            refresh_session_role,
        )
        from .db import has_any_admin, init_db

        app.secret_key = get_or_create_secret_key()
        app.config["SESSION_COOKIE_HTTPONLY"] = True
        app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
        if base_url.startswith("https"):
            app.config["SESSION_COOKIE_SECURE"] = True
        app.config["PERMANENT_SESSION_LIFETIME"] = 86400  # 24 hours

        csrf = CSRFProtect()

        init_db()
        app.register_blueprint(auth_bp)
        csrf.init_app(app)

        if sso_enabled:
            init_oidc(app, force_sso=force_sso)
        else:
            app.config["OIDC_ENABLED"] = False
            app.config["OIDC_DISPLAY_NAME"] = "SSO"
            app.config["OIDC_ADMIN_USER"] = None
            app.config["OIDC_ADMIN_SUBJECT"] = None
            app.config["FORCE_SSO"] = False

        @app.before_request
        def _check_setup():
            if request.endpoint and request.endpoint.startswith("auth."):
                return None
            if request.endpoint == "static":
                return None
            if not app.config.get("FORCE_SSO", False) and not has_any_admin():
                return redirect(url_for("auth.setup"))
            return None

        @app.before_request
        def _refresh_role():
            return refresh_session_role()

        @app.context_processor
        def _inject_auth():
            return {
                "current_user": get_current_user(),
                "auth_enabled": True,
                "oidc_enabled": app.config.get("OIDC_ENABLED", False),
                "oidc_display_name": app.config.get("OIDC_DISPLAY_NAME", "SSO"),
                "force_sso": app.config.get("FORCE_SSO", False),
            }
    else:

        @app.context_processor
        def _inject_no_auth():
            return {
                "current_user": None,
                "auth_enabled": False,
                "oidc_enabled": False,
                "oidc_display_name": "SSO",
                "force_sso": False,
            }

    @app.after_request
    def _set_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        return response

    @app.route("/")
    def index():
        return render_template(
            "index.html",
            lang_labels=LANG_LABELS,
            supported_providers=WORKING_PROVIDERS,
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

            # Build a reverse map: (Audio, Subtitles) -> lang_label
            lang_tuple_to_label = {}
            for key, (audio, subtitles) in LANG_KEY_MAP.items():
                label = LANG_LABELS.get(key)
                if label:
                    lang_tuple_to_label[(audio.value, subtitles.value)] = label

            provider_info = {}
            for (audio, subtitles), providers in pd._data.items():
                label = lang_tuple_to_label.get((audio.value, subtitles.value))
                if not label:
                    continue
                # Only include providers that have working extractors
                working = [p for p in providers.keys() if p in WORKING_PROVIDERS]
                if working:
                    provider_info[label] = working

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
        _exempt = {
            "static", "auth.login", "auth.logout", "auth.setup",
            "auth.oidc_login", "auth.oidc_callback",
        }
        for endpoint, view_func in list(app.view_functions.items()):
            if endpoint not in _exempt:
                app.view_functions[endpoint] = login_required(view_func)

        # Exempt JSON API routes from CSRF (they use Content-Type: application/json
        # which provides implicit cross-origin protection via CORS preflight)
        for endpoint in list(app.view_functions):
            if endpoint.startswith("api_") or endpoint.startswith("auth.admin_"):
                csrf.exempt(app.view_functions[endpoint])

    return app


def start_web_ui(host="127.0.0.1", port=5000, open_browser=True,
                 auth_enabled=False, sso_enabled=False, force_sso=False):
    """Start the Flask web UI server."""
    import os
    import threading
    import webbrowser

    # Allow env var overrides (Docker-friendly)
    force_sso = force_sso or os.getenv("ANIWORLD_WEB_FORCE_SSO", "0") == "1"
    sso_enabled = sso_enabled or force_sso or os.getenv("ANIWORLD_WEB_SSO", "0") == "1"
    auth_enabled = auth_enabled or force_sso or os.getenv("ANIWORLD_WEB_AUTH", "0") == "1"

    app = create_app(auth_enabled=auth_enabled, sso_enabled=sso_enabled, force_sso=force_sso)
    url = f"http://{'localhost' if host in ('0.0.0.0', '127.0.0.1') else host}:{port}"
    print(f"Starting AniWorld Web UI on {url}")

    if open_browser:
        threading.Timer(0.5, webbrowser.open, args=(url,)).start()

    app.run(host=host, port=port, debug=False)
