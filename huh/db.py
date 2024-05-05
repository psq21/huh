from flask_login import UserMixin
from datetime import datetime
import sqlite3

DB_PATH = "app.db"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.executescript(
    """
    CREATE TABLE IF NOT EXISTS user (
        email         TEXT,
        name          TEXT,
        password_hash TEXT,
        admin         INTEGER,
        PRIMARY KEY (email)
    );
    CREATE TABLE IF NOT EXISTS announcement (
        author_id INTEGER,
        title     TEXT,
        timestamp INTEGER,
        content   TEXT,
        FOREIGN KEY (author_id) REFERENCES user(rowid)
    );
    CREATE TABLE IF NOT EXISTS attachment (
        announcement_id INTEGER,
        name            TEXT,
        FOREIGN KEY (announcement_id) REFERENCES announcements(rowid)
    );
    CREATE TABLE IF NOT EXISTS comment (
        author_id       INTEGER,
        announcement_id INTEGER,
        timestamp       INTEGER,
        content         TEXT,
        FOREIGN KEY (author_id)       REFERENCES user(rowid),
        FOREIGN KEY (announcement_id) REFERENCES announcements(rowid)
    );
    """
)

conn.commit()
conn.close()


def connect():
    return sqlite3.connect(DB_PATH)


class Entry:
    table_name = None

    def __init__(self, id):
        self.id = id

    def __eq__(self, other):
        return self.id == other.id

    def __ne__(self, other):
        return self.id != other.id

    @classmethod
    def by_column(cls, conn, field, value):
        cur = conn.cursor()
        res = cur.execute(
            f"SELECT rowid AS id, * FROM {cls.table_name} WHERE {field} = ?",
            (value,),
        )
        data = res.fetchone()

        return cls(*data) if data else None

    @classmethod
    def by_id(cls, conn, id):
        return cls.by_column(conn, "id", id)

    @classmethod
    def all(cls, conn):
        cur = conn.cursor()
        res = cur.execute(f"SELECT rowid AS id, * FROM {cls.table_name}", ())

        return (cls(*row) for row in res)
    
    @classmethod
    def all_ann(cls, conn):
        cur = conn.cursor()
        cur.row_factory = sqlite3.Row
        res = cur.execute(
            """
            SELECT Announcement.rowid,title,name,timestamp,content FROM 
            Announcement JOIN User ON Announcement.author_id=User.rowid
            """
            )
        return res.fetchall()  
    
    @classmethod
    def one_ann(cls,conn,annID):
        cur = conn.cursor()
        cur.row_factory = sqlite3.Row
        res = cur.execute(
            """
            SELECT Announcement.rowid,title,name,timestamp,content 
            FROM Announcement JOIN User ON Announcement.author_id=User.rowid
            WHERE Announcement.rowid=?
            """,
            (annID,)
            )
        return res.fetchone()
    
    @classmethod
    def one_ann_comments(cls,conn,annID):
        cur = conn.cursor()
        cur.row_factory = sqlite3.Row
        res = cur.execute(
            """
            SELECT * FROM Comment LEFT OUTER JOIN User ON Comment.author_id=User.rowid
            WHERE announcement_id=?
            """,
            (annID,)
            )
        return res.fetchall()
    
    @classmethod
    def one_ann_attachments(cls,conn,annID):
        cur = conn.cursor()
        cur.row_factory = sqlite3.Row
        res = cur.execute("SELECT * FROM Attachment WHERE announcement_id=?",(annID,))
        return res.fetchall()



class User(UserMixin, Entry):
    table_name = "user"

    def __init__(self, id, email, name, hash, admin):
        Entry.__init__(self, id)

        self.email = email
        self.name = name
        self.hash = hash
        self.admin = admin

    @staticmethod
    def create(conn, email, name, hash):
        cur = conn.cursor()

        try:
            res = cur.execute(
                "INSERT INTO user VALUES (?,?,?,?) RETURNING rowid",
                (email, name, hash, False),
            )
        except sqlite3.IntegrityError:
            return None

        id = res.fetchone()[0]
        conn.commit()

        return User(id, email, name, hash, False)

    @staticmethod
    def by_email(conn, email):
        cur = conn.cursor()
        res = cur.execute("SELECT rowid AS id, * FROM user WHERE email = ?", (email,))
        data = res.fetchone()

        return User(*data) if data else None

    def get_id(self):
        return str(self.id)


class Announcement(Entry):
    table_name = "announcement"

    def __init__(self, id, author_id, title, timestamp, content):
        Entry.__init__(self, id)

        self.author_id = author_id
        self.title = title
        self.timestamp = timestamp
        self.content = content

    @staticmethod
    def create(conn, author_id: int, title, content):
        cur = conn.cursor()
        timestamp = int(datetime.now().timestamp())

        res = cur.execute(
            "INSERT INTO announcement VALUES (?,?,?,?) RETURNING rowid",
            (author_id, title, timestamp, content),
        )
        id = res.fetchone()[0]
        conn.commit()

        return Announcement(id, author_id, title, timestamp, content)


class Attachment(Entry):
    table_name = "attachment"

    def __init__(self, id, announcement_id, name):
        Entry.__init__(self, id)

        self.announcement_id = announcement_id
        self.name = name

    @staticmethod
    def create(conn, *_):
        raise NotImplementedError


class Comment(Entry):
    table_name = "comment"

    def __init__(self, id, author_id, announcement_id, timestamp, content):
        Entry.__init__(self, id)

        self.author_id = author_id
        self.announcement_id = announcement_id
        self.timestamp = timestamp
        self.content = content

    @staticmethod
    def create(conn, author_id, announcement_id, content):
        cur = conn.cursor()
        timestamp = int(datetime.now().timestamp())

        res = cur.execute(
            "INSERT INTO comment VALUES (?,?,?,?) RETURNING rowid",
            (author_id, announcement_id, timestamp, content),
        )
        id = res.fetchone()[0]
        conn.commit()

        return Comment(id, author_id, announcement_id, timestamp, content)
