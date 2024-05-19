from datetime import datetime
from flask import Flask, render_template
from flask_login import LoginManager
import secrets

from huh import auth, db, announcement, comment
from huh.db import User

app = Flask(__name__)

app.secret_key = secrets.token_urlsafe(16)

app.register_blueprint(auth.bp)
app.register_blueprint(announcement.bp)
app.register_blueprint(comment.bp)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def user_loader(id):
    with db.connect() as conn:
        return User.by_id(conn, int(id))


@app.route("/")
def homepage():
    return render_template("index.html")


@app.template_filter("format_timestamp")
def format_timestamp(timestamp):
    return datetime.fromtimestamp(timestamp)


app.jinja_env.globals.update(zip=zip)
