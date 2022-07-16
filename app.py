import os

from flask import Flask, redirect, request, session, url_for
from flask_session import Session

from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import (
    login_required,
    template,
    get_palette,
    current_user,
    is_hex,
    json_filter,
    api_error,
)
from helpers.palettes import Color
from helpers.search import get_search

from api import api, api_palettes, api_colors

# Configure application
app = Flask(__name__)
app.register_blueprint(api, url_prefix="/api")
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom jinja filters
app.jinja_env.filters["json"] = json_filter

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.route("/")
def index():
    """Homepage"""
    return template("index.html")


@app.route("/favorites")
@login_required
def favorites():
    """Favorites Page"""
    return template(
        "favorites.html",
        palettes=api_palettes()["palettes"],
        colors=api_colors()["colors"],
    )


@app.route("/login")
def login():
    """Login Page"""
    if current_user() is not None:
        return redirect("/")

    referer = request.args.get("referer")
    if (
        referer is None 
        and request.host_url in request.referrer 
        and request.referrer.lstrip(request.host_url)
    ):
        # Refer to previous page after login
        return redirect(f"/login?referer={'/' + request.referrer.lstrip(request.host_url)}")

    return template("login.html", referer=referer)


@app.route("/logout")
def logout():
    """Logout"""
    session["user_id"] = None
    return redirect("/")


@app.route("/register")
def register():
    """Register Page"""
    if current_user() is not None:
        return redirect("/")
    return template("register.html")


@app.route("/generate")
def generate():
    """Generate Palette"""
    return template("generate.html")


@app.route("/apply")
@login_required
def apply():
    """Apply Palette to Image"""
    palette = request.args.get("p")

    if palette:
        palette = palette.split(",")

    if not palette or not all([is_hex(c) for c in palette]):
        palette = None

    if current_user() is not None:
        palettes = api_palettes()["palettes"]
        for p in palettes:
            p["colors"] = [c["hex"] for c in p["colors"]]
    else:
        palettes = None

    return template("apply.html", palette=palette, palettes=palettes)


@app.route("/search")
def search():
    """Mood Search"""

    query = request.args.get("q")
    palette = request.args.get("p")

    if palette:
        palette = palette.split(",")

    if not palette or not all([is_hex(c) for c in palette]):
        palette = None

    if not query:
        query = None

    if None not in [query, palette]:
        # Create new search
        search = get_search(query=query, palette=palette)
        return template("results.html", search=search)

    if current_user() is not None:
        palettes = api_palettes()["palettes"]
        for p in palettes:
            p["colors"] = [c["hex"] for c in p["colors"]]
    else:
        palettes = None

    return template("search.html", palette=palette, palettes=palettes)


# This API function is in app because it needs to access
# the same version of search.py
@app.route("/search/<search_id>")
def search_status(search_id):
    """Mood Search Status"""
    search = get_search(search_id=search_id)
    if search is None:
        return api_error("Invalid search")

    if search.status == "done":
        return {
            "status": "done",
            "progress": 1.0,
            "images": [i.json for i in search.ranked_images],
        }
    elif search.status in ["initialized", "fetching_data"]:
        return {"status": "active", "progress": search.progress / search.hits}
    else:
        return {"status": search.status}
