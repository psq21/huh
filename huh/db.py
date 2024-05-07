from flask_login import UserMixin
from datetime import datetime
import sqlite3
from typing import Any, Self

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

    def __init__(self, id: int):
        self.id = id

    def __eq__(self, other: Self):
        return self.id == other.id

    def __ne__(self, other: Self):
        return self.id != other.id

    @classmethod
    def by_column(cls, conn: sqlite3.Connection, field: str, value: Any):
        cur = conn.cursor()
        res = cur.execute(
            f"SELECT rowid AS id, * FROM {cls.table_name} WHERE {field} = ?",
            (value,),
        )
        data = res.fetchone()

        return cls(*data) if data else None

    @classmethod
    def by_id(cls, conn: sqlite3.Connection, id: int):
        return cls.by_column(conn, "id", id)

    @classmethod
    def all(cls, conn: sqlite3.Connection):
        cur = conn.cursor()
        res = cur.execute(f"SELECT rowid AS id, * FROM {cls.table_name}", ())

        return (cls(*row) for row in res)


class User(UserMixin, Entry):
    table_name = "user"

    def __init__(self, id: int, email: str, name: str, hash: str, admin: bool):
        Entry.__init__(self, id)

        self.email = email
        self.name = name
        self.hash = hash
        self.admin = admin

    @staticmethod
    def create(conn: sqlite3.Connection, email: str, name: str, hash: str):
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
    def by_email(conn: sqlite3.Connection, email: str):
        cur = conn.cursor()
        res = cur.execute("SELECT rowid AS id, * FROM user WHERE email = ?", (email,))
        data = res.fetchone()

        return User(*data) if data else None

    def get_id(self):
        return str(self.id)


class Announcement(Entry):
    table_name = "announcement"

    def __init__(
        self, id: int, author_id: int, title: str, timestamp: int, content: str
    ):
        Entry.__init__(self, id)

        self.author_id = author_id
        self.title = title
        self.timestamp = timestamp
        self.content = content

    @staticmethod
    def create(conn: sqlite3.Connection, author_id: int, title: str, content: str):
        cur = conn.cursor()
        timestamp = int(datetime.now().timestamp())

        res = cur.execute(
            "INSERT INTO announcement VALUES (?,?,?,?) RETURNING rowid",
            (author_id, title, timestamp, content),
        )
        id = res.fetchone()[0]
        conn.commit()

        return Announcement(id, author_id, title, timestamp, content)
    
    @staticmethod
    def all_ann_w_name(conn):
        cur = conn.cursor()
        cur.row_factory = sqlite3.Row
        res = cur.execute(
            """
            SELECT Announcement.rowid as annID,title,timestamp,content, User.rowid as userID, name
            FROM Announcement JOIN User ON Announcement.author_id=User.rowid
            """
            )
        return res.fetchall()  
    
    @staticmethod
    def one_ann(conn,annID):
        cur = conn.cursor()
        cur.row_factory = sqlite3.Row
        res = cur.execute(
            """
            SELECT Announcement.rowid,title,timestamp,content, User.name
            FROM Announcement JOIN User ON Announcement.author_id=User.rowid
            WHERE Announcement.rowid=?
            """,
            (annID,)
            )
        return res.fetchone()
    
    @staticmethod
    def one_ann_comments(conn,annID):
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
    
    @staticmethod
    def one_ann_attachments(conn,annID):
        cur = conn.cursor()
        cur.row_factory = sqlite3.Row
        res = cur.execute("SELECT * FROM Attachment WHERE announcement_id=?",(annID,))
        return res.fetchall()


class Attachment(Entry):
    table_name = "attachment"

    def __init__(self, id: int, announcement_id: int, name: str):
        Entry.__init__(self, id)

        self.announcement_id = announcement_id
        self.name = name

    @staticmethod
    def create(conn, *_):
        raise NotImplementedError


class Comment(Entry):
    table_name = "comment"

    def __init__(
        self,
        id: int,
        author_id: int,
        announcement_id: int,
        timestamp: int,
        content: str,
    ):
        Entry.__init__(self, id)

        self.author_id = author_id
        self.announcement_id = announcement_id
        self.timestamp = timestamp
        self.content = content

    @staticmethod
    def create(
        conn: sqlite3.Connection, author_id: int, announcement_id: int, content: str
    ):
        cur = conn.cursor()
        timestamp = int(datetime.now().timestamp())

        res = cur.execute(
            "INSERT INTO comment VALUES (?,?,?,?) RETURNING rowid",
            (author_id, announcement_id, timestamp, content),
        )
        id = res.fetchone()[0]
        conn.commit()

        return Comment(id, author_id, announcement_id, timestamp, content)

    def update(self, conn: sqlite3.Connection, content: str):
        cur = conn.cursor()
        cur.execute(
            "UPDATE comment SET content = ? WHERE rowid = ?", (content, self.id)
        )
        conn.commit()

        self.content = content

    def delete(self, conn: sqlite3.Connection):
        cur = conn.cursor()
        cur.execute("DELETE FROM comment WHERE rowid = ?", (self.id,))
        conn.commit()
