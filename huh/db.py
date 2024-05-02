from flask_login import UserMixin
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


class Connection:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)

    def __del__(self):
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.conn.close()

    def get_user_by_id(self, id):
        cur = self.conn.cursor()
        res = cur.execute("SELECT rowid AS id, * FROM user WHERE rowid = ?", (id,))
        data = next(res, None)
        return User(*data) if data else None

    def get_user_by_email(self, email):
        cur = self.conn.cursor()
        res = cur.execute("SELECT rowid AS id, * FROM user WHERE email = ?", (email,))
        data = next(res, None)
        return User(*data) if data else None

    def add_user(self, email, name, hash):
        cur = self.conn.cursor()

        try:
            cur.execute("INSERT INTO user VALUES (?,?,?,?)", (email, name, hash, False))
        except sqlite3.IntegrityError:
            return False

        self.conn.commit()
        return True


class User(UserMixin):
    def __init__(self, id, email, name, hash, admin):
        self.id = id
        self.email = email
        self.name = name
        self.hash = hash
        self.admin = admin

    def get_id(self):
        return str(self.id)
