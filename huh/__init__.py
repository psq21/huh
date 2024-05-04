from flask import Flask, render_template
from flask_login import LoginManager
import secrets

from huh import auth, db
from huh.db import User

app = Flask(__name__)

app.secret_key = secrets.token_urlsafe(16)

app.register_blueprint(auth.bp)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def user_loader(id):
    with db.connect() as conn:
        return User.by_id(conn, int(id))


@app.route("/")
def homepage():
    return render_template("index.html")
