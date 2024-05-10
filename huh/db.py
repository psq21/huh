from flask_login import UserMixin
from datetime import datetime
import sqlite3
from typing import Any, Self
from werkzeug.datastructures import ImmutableMultiDict, FileStorage
from werkzeug.utils import secure_filename
import os

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
        assert isinstance(other, self.__class__)
        return self.id == other.id

    def __ne__(self, other: Self):
        assert isinstance(other, self.__class__)
        return self.id != other.id

    @classmethod
    def by_column(cls, conn: sqlite3.Connection, column: str, value: Any):
        cur = conn.cursor()
        res = cur.execute(
            f"SELECT rowid AS id, * FROM {cls.table_name} WHERE {column} = ?",
            (value,),
        )

        return (cls(*row) for row in res)

    @classmethod
    def by_id(cls, conn: sqlite3.Connection, id: int):
        return next(cls.by_column(conn, "id", id), None)

    @classmethod
    def id_exists(cls, conn: sqlite3.Connection, id: int):
        cur = conn.cursor()
        res = cur.execute(
            f"SELECT 1 FROM {cls.table_name} WHERE rowid = ?",
            (id,),
        )

        return False if res.fetchone() is None else True

    @classmethod
    def get_columns_by_id(cls, conn: sqlite3.Connection, columns: list[str], id: int):
        cur = conn.cursor()
        res = cur.execute(
            f"SELECT {', '.join(columns)} FROM {cls.table_name} WHERE rowid = ?",
            (id,),
        )

        return res.fetchone()

    @classmethod
    def get_column_by_id(cls, conn: sqlite3.Connection, column: str, id: int):
        return cls.get_columns_by_id(cls, conn, [column], id)

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
    def delete_w_ann(conn: sqlite3.Connection, id: int):
        cur = conn.cursor()
        cur.execute("DELETE FROM Announcement WHERE rowid=?", (id))
        conn.commit()

    @staticmethod
    def all_ann_w_name(conn: sqlite3.Connection):
        cur = conn.cursor()
        cur.row_factory = sqlite3.Row
        res = cur.execute(
            """
            SELECT Announcement.rowid as annID,title,timestamp,content, User.rowid as userID, name
            FROM Announcement JOIN User ON Announcement.author_id=User.rowid
            """
        )

        return [dict(row) for row in res.fetchall()]

    @staticmethod
    def one_ann(conn: sqlite3.Connection, annID: int):
        cur = conn.cursor()
        cur.row_factory = sqlite3.Row
        res = cur.execute(
            """
            SELECT Announcement.rowid as annID,title,timestamp,content, User.name
            FROM Announcement JOIN User ON Announcement.author_id=User.rowid
            WHERE Announcement.rowid=?
            """,
            (annID,),
        )
        return dict(res.fetchone())

    @staticmethod
    def one_ann_comments(conn: sqlite3.Connection, annID: int):
        cur = conn.cursor()
        cur.row_factory = sqlite3.Row
        res = cur.execute(
            """
            SELECT * FROM Comment LEFT OUTER JOIN User ON Comment.author_id=User.rowid
            WHERE announcement_id=?
            """,
            (annID,),
        )
        return [dict(row) for row in res.fetchall()]

    @staticmethod
    def one_ann_attachments(conn: sqlite3.Connection, annID: int):
        cur = conn.cursor()
        cur.row_factory = sqlite3.Row
        res = cur.execute("SELECT * FROM Attachment WHERE announcement_id=?", (annID,))
        return [dict(row) for row in res.fetchall()]

    @staticmethod
    def update_announcement(
        conn: sqlite3.Connection,
        annID: int,
        title: str,
        content: str,
        attachments: ImmutableMultiDict[str, FileStorage] | None,
    ):
        cur = conn.cursor()
        cur.execute(
            "UPDATE Announcement SET title=?, content=? WHERE rowid=?",
            (title, content, annID),
        )

        # perform a diffing operation to determine which files to delete

        existing = Attachment.by_column(conn, "announcement_id", annID)
        existing_files = {att.name for att in existing}

        new_files = set([secure_filename(att.filename) for att in attachments.values()])

        del_files = existing_files - new_files
        add_files = new_files - existing_files

        print(del_files, add_files)
        for filename in del_files:
            cur.execute(
                "DELETE FROM Attachment WHERE announcement_id=? AND name=?",
                (annID, filename),
            )
            os.remove(os.path.join(os.getcwd(), "attachments", str(annID), filename))

        for filename in add_files:
            att = attachments.get(filename)
            print(att)
            att.save(os.path.join(os.getcwd(), "attachments", str(annID), filename))
            Attachment.create(conn, annID, filename)

        conn.commit()
        return


class Attachment(Entry):
    table_name = "attachment"

    def __init__(self, id: int, announcement_id: int, name: str):
        Entry.__init__(self, id)

        self.announcement_id = announcement_id
        self.name = name

    @staticmethod
    def create(conn: sqlite3.Connection, annID: int, name: str):
        cur = conn.cursor()
        res = cur.execute(
            "INSERT INTO Attachment VALUES (?,?) RETURNING rowid", (annID, name)
        )

        id = res.fetchone()[0]
        conn.commit()

        return Attachment(id, annID, name)

    @staticmethod
    def get_file(annID: int, name: str):
        return os.path.join(os.getcwd(), "attachments", str(annID), name)

    @staticmethod
    def delete_w_ann(conn: sqlite3.Connection, annID: int):
        cur = conn.cursor()
        res = cur.execute(
            "DELETE FROM Attachment WHERE announcement_id=? RETURNING name", (annID,)
        )
        conn.commit()

        delFiles = [row[0] for row in res.fetchall()]
        return delFiles


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

    @staticmethod
    def delete_w_ann(conn: sqlite3.Connection, annID: int):
        cur = conn.cursor()
        cur.execute("DELETE FROM Comment WHERE author_id=?", (annID,))
        conn.commit()

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
