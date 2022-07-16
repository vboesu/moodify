import re
import json
import shutil
import os
import urllib.parse

from flask import redirect, session, render_template, make_response, request

from functools import wraps

from .user import current_user

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}


def json_filter(value):
    """Format value as valid json."""
    return json.dumps(value)


def is_hex(string):
    """Check if string is a six digit hexadecimal string"""
    return bool(re.search(r"^[A-Fa-f0-9]{6}$", string.lstrip("#")))


def allowed_file(filename):
    """Check if file extension is in ALLOWED_EXTENSIONS"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def camel_to_snake(name):
    # Source: https://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-snake-case
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()

def delete_all_files_in_folder(path):
    if os.path.exists(path):
        shutil.rmtree(path, ignore_errors=False, onerror=None)
    os.makedirs(path)


def template(file, *args, **kwargs):
    env = {
        "logged_in": bool(current_user()),
    }

    return render_template(file, *args, env=env, **kwargs)


def api_error(message, status=404, **kwargs):
    response = {"message": message, **kwargs}
    return make_response(response, status)


# Taken from CS50 finance p-set, adapted
def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user() is None:
            return redirect(f"/login?referer={urllib.parse.quote(request.path + request.query_string.decode())}")
        return f(*args, **kwargs)

    return decorated_function


# Taken from CS50 finance p-set, adapted
def login_required_api(f):
    """
    Decorate routes to require login for API.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user() is None:
            return api_error("Unauthorized", status=401)
        return f(*args, **kwargs)

    return decorated_function