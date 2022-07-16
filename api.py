import os
import json
import sqlite3
import bcrypt
import numpy as np
import time
import peewee

from flask import Blueprint, request, session, send_file
from hashlib import blake2b

from werkzeug.utils import secure_filename
from pathlib import Path
from PIL import Image

from helpers import (
    login_required_api,
    get_palette,
    api_error,
    db,
    get_user,
    current_user,
    allowed_file,
    palette_from_image,
    is_hex,
    delete_all_files_in_folder,
)
from helpers.db import SavedPalette, SavedColor, User, SavedPaletteColor
from helpers.palettes import Color
from helpers.apply import apply

api = Blueprint("api", __name__)

# Configure file uploads
UPLOAD_FOLDER = Path(__file__).parent / "uploads"
delete_all_files_in_folder(UPLOAD_FOLDER)

# Configure Pixabay API (if key.txt exists)
if os.path.exists(Path(__file__).parent / "key.txt"):
    with open(Path(__file__).parent / "key.txt", "r") as f:
        os.environ["PIXABAY_API_KEY"] = f.read().strip()


@api.route("/login", methods=["POST"])
def api_login():
    """API Login"""
    email = request.form.get("email")
    password = request.form.get("password")

    if not email:
        return api_error("No email provided", status=400, elements=["email"])

    if not password:
        return api_error("No password provided", status=400, elements=["password"])

    # Query database
    user = get_user(email=email)
    if user is None or not bcrypt.checkpw(password.encode(), user.password.encode()):
        return api_error(
            "Invalid credentials", status=400, elements=["email", "password"]
        )

    session["user_id"] = user.user_id

    if request.args.get("referer"):
        return {"redirect": request.args.get("referer")}

    return {}


@api.route("/register", methods=["POST"])
def api_register():
    """API Register"""
    email = request.form.get("email")
    password = request.form.get("password")
    password_confirm = request.form.get("password_confirm")

    if not email:
        return api_error("No email provided", status=400, elements=["email"])

    if not password:
        return api_error("No password provided", status=400, elements=["password"])

    if not password_confirm:
        return api_error(
            "No password confirmation provided",
            status=400,
            elements=["password_confirm"],
        )

    if password != password_confirm:
        return api_error(
            "Passwords do not match",
            status=400,
            elements=["password", "password_confirm"],
        )

    try:
        user = User.create(
            email=email, password=bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        )
    except peewee.IntegrityError:
        return api_error("E-Mail already used", status=400, elements=["email"])

    session["user_id"] = user.user_id

    if request.args.get("referer"):
        return {"redirect": request.args.get("referer")}

    return {}


@api.route("/generate", methods=["POST"])
def api_generate():
    """API to generate palette"""
    mode = request.form.get("mode", "auto")
    n = request.form.get("n", 5)
    initial_color = request.form.get("initial_color", None)

    p = get_palette(mode, n=n)

    return {"palette": p.json, "mode": p.mode}


@api.route("/generate/image", methods=["POST"])
def api_generate_image():
    """API to generate palette from image"""
    if "file" not in request.files:
        return api_error("No file provided", status=400)

    file = request.files["file"]
    if not file.filename:
        return api_error("No file provided", status=400)

    if not allowed_file(file.filename):
        return api_error("Invalid file format", status=400)

    # Save filename with unique filename
    filename = os.path.join(
        UPLOAD_FOLDER, str(time.time()) + secure_filename(file.filename)
    )
    file.save(filename)

    with Image.open(filename) as img:
        palette = palette_from_image(img, request.form.get("n", 5))

    # Convert palette to list of Color objects and sort by lightness
    palette = Color.batch(palette, format_in="rgb")
    palette = sorted(palette, key=lambda x: (x.lightness, x.hue))

    return {
        "palette": [
            {
                "name": c.name,
                "formats": {
                    "hex": c.hex,
                    "rgb": c.out("rgb"),
                    "hsl": c.out("hsl"),
                    "hsv": c.out("hsv"),
                },
                "lightness": c.lightness,
            }
            for c in palette
        ]
    }


@api.route("/palettes")
@login_required_api
def api_palettes():
    """API to retrieve all saved palettes"""

    palettes = (
        SavedPalette.select()
        .where(SavedPalette.user_id == current_user())
        .order_by(SavedPalette.created.desc())
    )

    return {"palettes": [p.to_dict for p in palettes]}


@api.route("/palette", methods=["POST"])
@login_required_api
def api_palette_save():
    """API to save new palette"""

    palette = request.form.getlist("palette[]")
    if not palette:
        return api_error("Missing palette", status=400)

    saved_palette = SavedPalette.create(user_id=current_user())

    for c in palette:
        color = SavedPaletteColor.create(palette_id=saved_palette.palette_id, hex=c)

    return {"palette_id": saved_palette.palette_id}


@api.route("/palette/<int:palette_id>/delete")
@login_required_api
def api_palette_delete(palette_id: int):
    """API to delete palette"""

    palette = SavedPalette.get_or_none(
        SavedPalette.palette_id == palette_id,
        SavedPalette.user_id == current_user(),
    )

    if palette is None:
        return api_error("Palette does not exist", status=400)

    palette.delete_instance()

    return {}


@api.route("/colors")
@login_required_api
def api_colors():
    """API to retrieve all saved colors"""

    colors = (
        SavedColor.select()
        .where(SavedColor.user_id == current_user())
        .order_by(SavedColor.created.desc())
    )

    return {"colors": [c.to_dict for c in colors]}


@api.route("/color", methods=["POST"])
@login_required_api
def api_color_save():
    """API to save new color"""

    color = request.form.get("color")
    if not color:
        return api_error("Missing color", status=400)

    if not is_hex(color):
        return api_error("Invalid color", status=400)

    saved_color = SavedColor.create(user_id=current_user(), hex=color)

    return {"color_id": saved_color.color_id}


@api.route("/color/<int:color_id>/delete")
@login_required_api
def api_color_delete(color_id: int):
    """API to delete color"""

    color = SavedColor.get_or_none(
        SavedColor.color_id == color_id,
        SavedColor.user_id == current_user(),
    )

    if color is None:
        return api_error("Color does not exist", status=400)

    color.delete_instance()

    return {}


@api.route("/apply", methods=["POST"])
def api_apply_image():
    """API to apply palette to image"""
    palette = request.args.get("p")

    # Validate palette
    if palette:
        palette = palette.split(",")

    if not palette or not all([is_hex(c) for c in palette]):
        palette = None

    if palette is None:
        return api_error("Invalid palette provided", status=400)

    # Validate file
    if "file" not in request.files:
        return api_error("No file provided", status=400)

    file = request.files["file"]
    if not file.filename:
        return api_error("No file provided", status=400)

    if not allowed_file(file.filename):
        return api_error("Invalid file format", status=400)

    # Save file with unique filename
    filename = os.path.join(
        UPLOAD_FOLDER, str(time.time()) + secure_filename(file.filename)
    )
    file.save(filename)

    # Open image
    with Image.open(filename) as img:
        source = palette_from_image(img, len(palette))

    # Convert source to list of Color objects and then to list of RGB tuples
    source = Color.batch(source, format_in="rgb")
    source = sorted(source, key=lambda x: (x.lightness, x.hue))
    source_rgb = list(map(lambda x: x.out("rgb"), source))

    # Convert target to list of Color objects and then to list of RGB tuples
    target = Color.batch(palette, format_in="hex")
    target = sorted(target, key=lambda x: (x.lightness, x.hue))
    target_rgb = list(map(lambda x: x.out("rgb"), target))
    
    # Open original image again
    with Image.open(filename) as img:
        img = img.convert("RGB")
        result = apply(np.array(img), source_rgb, target_rgb)
    
    # Save file, return filename to load through JavaScript
    out = Image.fromarray(result)
    filename = blake2b(f"{time.time()}".encode(), digest_size=16).hexdigest()

    out.save(os.path.join(UPLOAD_FOLDER, filename + ".jpg"))

    return {
        "file": filename
    }

@api.route("/apply/<image>")
def api_get_apply_image(image):
    path = os.path.join(UPLOAD_FOLDER, image + ".jpg")
    if not os.path.exists(path):
        return api_error("File does not exist")

    return send_file(path)