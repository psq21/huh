from flask import Flask, render_template
from flask_login import LoginManager
import secrets

from huh import auth, db

app = Flask(__name__)

app.secret_key = secrets.token_urlsafe(16)

app.register_blueprint(auth.bp)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def user_loader(id):
    return db.Connection().get_user_by_id(id)


@app.route("/")
def homepage():
    return render_template("index.html")
