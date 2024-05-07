from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import sqlite3, os

from huh.db import connect, Announcement, Attachment, Comment

bp = Blueprint("announcement", __name__, url_prefix="/announcement")


@bp.route('/all/', methods=['GET','POST'])
def allAnn():
    if request.method=='GET': #return page of all announcements
        conn = connect()
        data = Announcement.all_ann_w_name(conn)
        data['allowed_edit'] = True if data['userID']==current_user.id else False
        conn.close()

        return render_template('allAnn.html', anns=data)

@login_required
@bp.route('/<annID>/', methods=['GET','POST'])
def oneAnn(annID):
    if request.method=='GET': #return page of one announcement
        conn = connect()
        ann = Announcement.one_ann(conn, annID)
        attachments = Announcement.one_ann_attachments(conn, annID)
        comments = Announcement.one_ann_comments(conn, annID)
        for comm in comments:
            comm['allowed_edit'] = True if comm['author_id']==current_user.id else False
        conn.close()
        
        return render_template('oneAnn.html', ann=ann, comments=comments, attachments=attachments)

@login_required
@bp.route('/create/', methods=['GET','POST'])
def createAnn():
    if request.method=='GET':
        return render_template('cudAnn.html')
    
    elif request.method=='POST':
        userID = current_user.id
        conn = connect()
        formData = request.form
        fileData = request.files

        ann = Announcement.create(conn, userID, formData['title'], formData['content'])
        for att in fileData['attachments']:
            attName = secure_filename(att.filename)
            att.save(url_for('attachments', filename=attName))
            Attachment.create(conn, ann.id, attName)
        conn.close()

        return redirect(url_for('allAnn'))
    
@login_required
@bp.route('/edit/<annID>/', methods=['GET','POST'])
def editAnn(annID):
    if request.method=='GET':
        conn = connect()
        data = Announcement.one_ann(conn, annID)
        conn.close()

        return render_template('cudAnn.html', prev=data)
    
    elif request.method=='POST': 
        conn = connect()
        formData = request.form
        fileData = request.files
        userID = current_user.id

        #delete old announcement, comments and attachments
        Announcement.delete_w_ann(annID)
        Comment.delete_w_ann(annID)
        delFiles = Attachment.delete_w_ann(annID)
        for filename in delFiles:
            os.remove(url_for('attachments',filename=filename))
        
        newAnn = Announcement.create(conn, userID, formData['title'], formData['content'])
        for att in fileData['attachments']:
            attName = secure_filename(att.filename)
            att.save(url_for('attachments', filename=attName))
            Attachment.create(conn, annID, attName)
    
        return render_template('allAnn.html')
    
@login_required
@bp.route('/delete/<annID>/', methods=["GET","POST"])
def delAnn(annID):
    if request.method=='GET':
        Announcement.delete_w_ann(annID)
        Comment.delete_w_ann(annID)
        delFiles = Attachment.delete_w_ann(annID)
        for filename in delFiles:
            os.remove(url_for('attachments',filename=filename))

        return redirect(url_for(allAnn))

