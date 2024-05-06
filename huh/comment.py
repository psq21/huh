from flask_login import login_required, current_user
from flask import render_template, Blueprint, request, abort
from huh.db import Comment, connect

bp = Blueprint("comment", __name__, url_prefix="/comment")

@bp.route("/create", methods=["POST"])
@login_required
def create():
    author_id = current_user.id
    try:
        announcement_id, content = int(request.form["announcement_id"]), request.form["content"]
    except (KeyError, ValueError):
        abort(400)
    with connect() as conn:
        Comment.create(conn, author_id, announcement_id, content)

    return '', 201

@bp.route("/delete/<comment_id>", methods=["DELETE"])
@login_required
def delete(comment_id: str):
    
    with connect() as conn:
        comment = Comment.by_id(conn, int(comment_id))
        if comment is None:
            abort(404)
        comment.delete(conn)

    return '', 204


@bp.route("/update/<comment_id>", methods=["PUT"])
@login_required
def update(comment_id: str):
    try:
        content = request.form["content"]
    except KeyError:
        abort(400)
    
    with connect() as conn:
        
        comment = Comment.by_id(conn, int(comment_id))
        if comment is None:
            abort(404)
        comment.update(conn, content)

    return '', 204
    
