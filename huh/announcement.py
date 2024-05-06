from flask import Blueprint, render_template, request
import sqlite3

from huh import db
from db import * 

bp = Blueprint("announcement", __name__, url_prefix="/announcement")


@bp.route('/all/', methods=['GET','POST'])
def allAnn():
    if request.method=='GET': #return page of all announcements
        conn = connect()
        data = Entry.all_ann_w_name(conn)
        conn.close()
        return render_template('allAnn.html',anns=data)
    
@bp.route('/<annID>/', methods=['GET','POST'])
def oneAnn(annID):
    if request.method=='GET': #return page of one announcement
        conn = connect()
        ann = Entry.one_ann(conn,annID)
        comments = Entry.one_ann_comments(conn,annID)
        attachments = Entry.one_ann_attachments(conn,annID)
        conn.close()
    return render_template('oneAnn.html',ann=ann,comments=comments,attachments=attachments)
