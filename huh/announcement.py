from flask import Blueprint, render_template, request
import sqlite3

from huh import db

bp = Blueprint("announcement", __name__, url_prefix="/announcement")


@bp.route('/all', methods=['GET','POST'])
def allAnn():
    if request.method=='GET': #return page of all announcements
        conn = sqlite3.connect('app.db')
        conn.row_factory=sqlite3.Row
        cursor = conn.execute("""SELECT Announcement.rowid,title,name,timestamp,content FROM 
                              Announcement JOIN User ON Announcement.author_id=User.rowid""")
        data = cursor.fetchall()
        conn.close()
        return render_template('allAnn.html',anns=data)
    
@bp.route('/<annID>')
def oneAnn(annID):
    return render_template('oneAnn.html',)