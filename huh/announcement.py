from flask import Blueprint, render_template, redirect, url_for, request, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import sqlite3, os

from huh.db import connect, Announcement, Attachment, Comment

bp = Blueprint("announcement", __name__, url_prefix="/announcement")


def opener(path, flags):
    return os.open(path, flags, 0o777)


os.umask(
    0
)  # Without this, the created file will have 0o777 - 0o022 (default umask) = 0o755 permissions


@bp.route("/all/", methods=["GET", "POST"])
def allAnn():
    if request.method == "GET":  # return page of all announcements
        conn = connect()
        data = Announcement.all_ann_w_name(conn)
        for ann in data:
            if not current_user.is_authenticated:
                ann["allowed_edit"] = False

            elif ann["userID"] == current_user.id:
                ann["allowed_edit"] = True
            else:
                ann["allowed_edit"] = False
        conn.close()
        return render_template("allAnn.html", anns=data)


@login_required
@bp.route("/<annID>/", methods=["GET", "POST"])
def oneAnn(annID):
    if request.method == "GET":  # return page of one announcement
        conn = connect()
        ann = Announcement.one_ann(conn, annID)
        attachments = Announcement.one_ann_attachments(conn, annID)
        comments = Announcement.one_ann_comments(conn, annID)

        for comm in comments:
            if not current_user.is_authenticated:
                comm["allowed_edit"] = False
            elif comm["author_id"] == current_user.id:
                comm["allowed_edit"] = True
            else:
                comm["allowed_edit"] = False

        conn.close()
        return render_template(
            "oneAnn.html", ann=ann, comments=comments, attachments=attachments
        )


@login_required
@bp.route("/create/", methods=["GET", "POST"])
def createAnn():
    if request.method == "GET":
        prev = {"title": "", "content": ""}
        return render_template("cudAnn.html", prev=prev)

    elif request.method == "POST":

        userID = current_user.id
        conn = connect()
        formData = request.form
        fileData = request.files

        ann = Announcement.create(conn, userID, formData["title"], formData["content"])
        upload_dir = os.path.join(os.getcwd(), "attachments", str(ann.id))

        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        # check if there are attachments\
        # [<FileStorage: '' ('application/octet-stream')>] if no attachments
        if fileData.getlist("attachments")[0].stream.read() == b"":
            conn.close()
            return redirect(url_for("announcement.allAnn"))
        for att in fileData.getlist("attachments"):
            attName = secure_filename(att.filename)
            fp = os.path.join(upload_dir, attName)

            att.save(fp)
            Attachment.create(conn, ann.id, attName)
        conn.close()

        return redirect(url_for("announcement.allAnn"))


@login_required
@bp.route("/edit/<annID>/", methods=["GET", "POST"])
def editAnn(annID):
    if request.method == "GET":
        conn = connect()
        data = Announcement.one_ann(conn, annID)
        conn.close()

        return render_template("cudAnn.html", prev=data)

    elif request.method == "POST":
        formData = request.form
        fileData = request.files
        try:
            title, content = formData["title"], formData["content"]
        except KeyError:
            abort(400)
        conn = connect()
        
        if fileData.getlist("attachments")[0].stream.read() == b"":
            fileData = None
        
        Announcement.update_announcement(conn, annID, title, content, fileData)


        '''
        # delete old announcement, comments and attachments
        Announcement.delete_w_ann(annID)
        Comment.delete_w_ann(annID)
        delFiles = Attachment.delete_w_ann(annID)
        for filename in delFiles:
            os.remove(url_for("attachments", filename=filename))

        newAnn = Announcement.create(
            conn, userID, formData["title"], formData["content"]
        )
        for att in fileData["attachments"]:
            attName = secure_filename(att.filename)
            att.save(url_for("attachments", filename=attName))
            Attachment.create(conn, annID, attName)
        '''

        return render_template("allAnn.html")


@login_required
@bp.route("/delete/<annID>/", methods=["GET", "POST"])
def delAnn(annID: str):
    if not annID.isdigit():
        abort(400)

    if request.method == "GET":

        with connect() as conn:
            Announcement.delete_w_ann(conn, annID)
            Comment.delete_w_ann(conn, annID)
            delFiles = Attachment.delete_w_ann(conn, annID)
        for filename in delFiles:
            os.remove(url_for("attachments", filename=filename))

        return redirect("/announcement/all/")
