from flask import (
    Blueprint,
    abort,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from flask_login import current_user, login_required
from pathlib import Path
import os

from huh import db, util
from huh.db import Announcement, Attachment, Comment, User

bp = Blueprint("announcement", __name__, url_prefix="/announcement")

ATTACHMENT_DIR = Path(os.getenv("HUH_ATTACHMENT_DIR") or "./attachments").absolute()
os.makedirs(ATTACHMENT_DIR, exist_ok=True)


@bp.route("/all/")
def all():
    with db.connect() as conn:
        anns = list(Announcement.all(conn))
        names = (
            User.get_column_by_id(conn, "name", ann.author_id) for ann in reversed(anns)
        )

        return render_template("allAnn.html", anns=reversed(anns), names=names)


@bp.route("/<id>/")
@login_required
def one(id):
    id = util.check_id(id)

    with db.connect() as conn:
        ann = util.check_exists(Announcement.by_id(conn, id))

        name = User.get_column_by_id(conn, "name", ann.author_id)
        atts = Attachment.by_column(conn, "announcement_id", id)
        comms = list(Comment.by_column(conn, "announcement_id", id))
        comm_names = (
            User.get_column_by_id(conn, "name", comm.author_id) for comm in comms
        )

        return render_template(
            "oneAnn.html",
            ann=ann,
            name=name,
            comms=comms,
            comm_names=comm_names,
            atts=atts,
        )


@bp.route("/create/", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "GET":
        return render_template("crudAnn.html", prev=None)

    with db.connect() as conn:
        try:
            title, content = request.form["title"], request.form["content"]
        except KeyError:
            abort(400)

        ann = Announcement.create(conn, current_user.id, title, content)

        for upload in request.files.getlist("attachments"):
            if not upload.filename:
                continue

            upload_name = util.secure_filename(upload.filename)
            att = Attachment.create(conn, ann.id, upload_name)
            upload.save(ATTACHMENT_DIR / str(att.id))

    return redirect(url_for("announcement.one", id=ann.id))


@bp.route("/edit/<id>/", methods=["GET", "POST"])
@login_required
def edit(id):
    id = util.check_id(id)

    with db.connect() as conn:
        ann = util.check_exists(Announcement.by_id(conn, id))
        util.check_user(ann.author_id)

        if request.method == "GET":
            return render_template("crudAnn.html", prev=ann)

        try:
            title, content = request.form["title"], request.form["content"]
        except KeyError:
            abort(400)

        ann.update(conn, ("title", "content"), (title, content))

        att_map = None
        for upload in request.files.getlist("attachments"):
            if not upload.filename:
                continue

            if not att_map:
                att_map = dict(
                    (att.name, att)
                    for att in Attachment.by_column(conn, "announcement_id", ann.id)
                )

            upload_name = util.secure_filename(upload.filename)

            try:
                att = att_map[upload_name]
            except KeyError:
                att = Attachment.create(conn, ann.id, upload_name)

            upload.save(ATTACHMENT_DIR / str(att.id))

    return redirect(url_for("announcement.one", id=ann.id))


@bp.route("/delete/<id>/", methods=["GET"])
@login_required
def delete(id):
    id = util.check_id(id)

    with db.connect() as conn:
        ann = util.check_exists(Announcement.by_id(conn, id))
        util.check_user(ann.author_id)

        Comment.delete_by_column(conn, "announcement_id", ann.id)

        for att in Attachment.delete_by_column(conn, "announcement_id", ann.id):
            os.remove(ATTACHMENT_DIR / str(att.id))

        ann.delete(conn)

    return redirect("/announcement/all/")


@bp.route("/attachment/<id>/", methods=["GET"])
@login_required
def attachment(id):
    id = util.check_id(id)

    with db.connect() as conn:
        att = util.check_exists(Attachment.by_id(conn, id))

        return send_file(
            ATTACHMENT_DIR / str(id), as_attachment=True, download_name=att.name
        )
