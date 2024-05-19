from flask_login import current_user, login_required
from flask import Blueprint, abort, request

from huh import db, util
from huh.db import Comment

bp = Blueprint("comment", __name__, url_prefix="/comment")


@bp.route("/create/", methods=["POST"])
@login_required
def create():
    try:
        ann_id, content = (
            request.form["announcement_id"],
            request.form["content"],
        )
    except KeyError:
        abort(400)

    ann_id = util.check_id(ann_id)

    with db.connect() as conn:
        Comment.create(conn, current_user.id, ann_id, content)

    return "", 201


@bp.route("/delete/<id>/", methods=["DELETE"])
@login_required
def delete(id):
    id = util.check_id(id)

    with db.connect() as conn:
        comm = util.check_exists(Comment.by_id(conn, id))
        comm.delete(conn)

    return "", 204


@bp.route("/update/<id>/", methods=["PUT"])
@login_required
def update(id):
    id = util.check_id(id)

    try:
        content = request.form["content"]
    except KeyError:
        abort(400)

    with db.connect() as conn:
        comm = util.check_exists(Comment.by_id(conn, id))
        util.check_user(comm.author_id)

        comm.update(conn, ("content",), (content,))

    return "", 204
