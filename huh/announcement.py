from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
import sqlite3

from huh.db import connect, Announcement

bp = Blueprint("announcement", __name__, url_prefix="/announcement")


@bp.route('/all/', methods=['GET','POST'])
def allAnn():
    if request.method=='GET': #return page of all announcements
        conn = connect()
        data = Announcement.all_ann_w_name(conn)
        if data['userID']==current_user.id:
            data['allowed_edit'] = True 
        else:
            data['allowed_edit'] = False
        conn.close()
        return render_template('allAnn.html',anns=data)

@login_required
@bp.route('/<annID>/', methods=['GET','POST'])
def oneAnn(annID):
    if request.method=='GET': #return page of one announcement
        conn = connect()
        ann = Announcement.one_ann(conn,annID)
        attachments = Announcement.one_ann_attachments(conn,annID)
        comments = Announcement.one_ann_comments(conn,annID)
        for comm in comments:
            if comm['author_id']==current_user.id:
                comm['allowed_edit'] = True 
            else:
                comm['allowed_edit'] = False
        conn.close()
    return render_template('oneAnn.html',ann=ann,comments=comments,attachments=attachments)
