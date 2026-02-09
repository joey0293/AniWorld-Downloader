import os
import secrets
from functools import wraps

from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from ..config import ANIWORLD_CONFIG_DIR
from .db import (
    create_user,
    delete_user,
    has_any_admin,
    list_users,
    update_user_role,
    verify_user,
)

_SECRET_KEY_PATH = ANIWORLD_CONFIG_DIR / ".flask_secret"


def get_or_create_secret_key():
    ANIWORLD_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if _SECRET_KEY_PATH.exists():
        return _SECRET_KEY_PATH.read_bytes()
    key = secrets.token_bytes(32)
    _SECRET_KEY_PATH.write_bytes(key)
    os.chmod(str(_SECRET_KEY_PATH), 0o600)
    return key


def get_current_user():
    uid = session.get("user_id")
    if uid is None:
        return None
    return {
        "id": uid,
        "username": session.get("user_name", ""),
        "role": session.get("user_role", "user"),
    }


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("user_id") is None:
            if request.is_json or request.path.startswith("/api/"):
                return jsonify({"error": "authentication required"}), 401
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("user_id") is None:
            if request.is_json or request.path.startswith("/api/"):
                return jsonify({"error": "authentication required"}), 401
            return redirect(url_for("auth.login"))
        if session.get("user_role") != "admin":
            if request.is_json or request.path.startswith("/api/"):
                return jsonify({"error": "admin access required"}), 403
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated


# ---------------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------------

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if not has_any_admin():
        return redirect(url_for("auth.setup"))

    error = None
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        user = verify_user(username, password)
        if user:
            session["user_id"] = user["id"]
            session["user_name"] = user["username"]
            session["user_role"] = user["role"]
            return redirect(url_for("index"))
        error = "Invalid username or password."

    return render_template("login.html", error=error)


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))


@auth_bp.route("/setup", methods=["GET", "POST"])
def setup():
    if has_any_admin():
        return redirect(url_for("auth.login"))

    error = None
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        confirm = request.form.get("confirm") or ""

        if not username:
            error = "Username is required."
        elif len(password) < 4:
            error = "Password must be at least 4 characters."
        elif password != confirm:
            error = "Passwords do not match."
        else:
            uid = create_user(username, password, role="admin")
            session["user_id"] = uid
            session["user_name"] = username
            session["user_role"] = "admin"
            return redirect(url_for("index"))

    return render_template("setup.html", error=error)


# ---------------------------------------------------------------------------
# Admin dashboard + API
# ---------------------------------------------------------------------------

@auth_bp.route("/admin")
@admin_required
def admin_dashboard():
    return render_template("admin.html")


@auth_bp.route("/admin/api/users")
@admin_required
def admin_list_users():
    return jsonify({"users": list_users()})


@auth_bp.route("/admin/api/users", methods=["POST"])
@admin_required
def admin_create_user():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    role = data.get("role", "user")

    if not username:
        return jsonify({"error": "Username is required"}), 400
    if len(password) < 4:
        return jsonify({"error": "Password must be at least 4 characters"}), 400
    if role not in ("admin", "user"):
        return jsonify({"error": "Invalid role"}), 400

    try:
        uid = create_user(username, password, role)
        return jsonify({"id": uid, "username": username, "role": role})
    except Exception as e:
        return jsonify({"error": str(e)}), 409


@auth_bp.route("/admin/api/users/<int:user_id>", methods=["DELETE"])
@admin_required
def admin_delete_user(user_id):
    ok, err = delete_user(user_id)
    if not ok:
        return jsonify({"error": err}), 400
    return jsonify({"ok": True})


@auth_bp.route("/admin/api/users/<int:user_id>/role", methods=["PUT"])
@admin_required
def admin_update_role(user_id):
    data = request.get_json(silent=True) or {}
    new_role = data.get("role", "")
    ok, err = update_user_role(user_id, new_role)
    if not ok:
        return jsonify({"error": err}), 400
    return jsonify({"ok": True})
