from flask import Flask, request, render_template
import sqlite3

app = Flask(__name__)

@app.route('/announcement/all/', methods=['GET','POST'])
def allAnn():
    if request.method=='GET': #return page of all announcements
        conn = sqlite3.connect('announcements.db')
        conn.row_factory=sqlite3.Row
        cursor = conn.execute("""SELECT Announcement.rowid,title,name,timestamp,content FROM 
                              Announcement JOIN User ON Announcement.author_id=User.rowid""")
        data = cursor.fetchall()
        conn.close()
        return render_template('allAnn.html',anns=data)
    
@app.route('/announcement/<annID>/')
def oneAnn(annID):
    return render_template('oneAnn.html',)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
    