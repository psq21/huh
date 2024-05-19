from flask import abort
from flask_login import current_user
from typing import Any
import hashlib
import werkzeug.utils


def check_exists(value: Any):
    if value is None:
        abort(404)
    return value


def check_id(id: Any) -> int:
    try:
        id_ = int(id)
    except ValueError:
        abort(400)
    return id_


def check_user(id: int):
    if id != current_user.id:
        abort(403)


def secure_filename(name: str):
    name_ = werkzeug.utils.secure_filename(name)
    if not name_:
        name_ = hashlib.sha256(name.encode("UTF-8"), usedforsecurity=False).hexdigest()
    return name_
