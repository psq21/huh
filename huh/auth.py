from email_validator import validate_email, EmailNotValidError
from flask import Blueprint, abort, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from huh import db
from huh.db import User

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/signup", methods=["GET", "POST"])
def signup():
    if not current_user.is_anonymous:
        return redirect(url_for("homepage"))

    if not request.form:
        return render_template("signup.html")

    errors = []
    normalised_email = None
    try:
        email, name, password = (
            request.form["email"],
            request.form["name"],
            request.form["password"],
        )
    except KeyError:
        abort(400)

    try:
        email_info = validate_email(email)
        normalised_email = email_info.normalized
    except EmailNotValidError as e:
        errors.append(str(e))

    if not 3 <= len(password) <= 64:
        errors.append("Password should be between 3 and 64 characters long")

    # do not proceed if there are errors
    if errors:
        return render_template("signup.html", error="\n".join(errors))


    hash = generate_password_hash(password)

    with db.connect() as conn:
        user = User.create(conn, normalised_email, name, hash)
        if not user:
            errors.append(f"The email address is taken")

        if errors:
            return render_template("signup.html", error="\n".join(errors))

        login_user(user)

    return redirect(url_for("homepage"))


@bp.route("/login", methods=["GET", "POST"])
def login():
    if not current_user.is_anonymous:
        return redirect(url_for("homepage"))

    if not request.form:
        return render_template("login.html")

    normalised_email = None
    try:
        email, password = request.form["email"], request.form["password"]
    except KeyError:
        abort(400)

    try:
        email_info = validate_email(email)
        normalised_email = email_info.normalized
    except EmailNotValidError as e:
        return render_template("login.html", error=str(e))

    with db.connect() as conn:
        user = next(User.by_column(conn, "email", normalised_email), None)

        if not user or not check_password_hash(user.hash, password):
            return render_template(
                "login.html", error="The email or the password is incorrect"
            )

        login_user(user)

    return redirect(url_for("homepage"))


@bp.route("logout")
def logout():
    logout_user()
    return redirect(url_for("homepage"))
