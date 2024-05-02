from email_validator import validate_email, EmailNotValidError
from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from huh import db

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/signup", methods=["GET", "POST"])
def signup():
    if not current_user.is_anonymous:
        return redirect(url_for("homepage"))

    if not request.form:
        return render_template("signup.html")

    errors = []
    normalised_email = None
    email, name, password = (
        request.form["email"],
        request.form["name"],
        request.form["password"],
    )

    try:
        email_info = validate_email(email)
        normalised_email = email_info.normalized
    except EmailNotValidError as e:
        errors.append(str(e))

    if not 3 <= len(password) <= 64:
        errors.append("Password should be between 3 and 64 characters long")

    hash = generate_password_hash(password)

    with db.Connection() as conn:
        if not conn.add_user(normalised_email, name, hash):
            errors.append(f"The email address is taken")

        if errors:
            return render_template("signup.html", error="\n".join(errors))

        login_user(conn.get_user_by_email(normalised_email))

    return redirect(url_for("homepage"))


@bp.route("/login", methods=["GET", "POST"])
def login():
    if not current_user.is_anonymous:
        return redirect(url_for("homepage"))

    if not request.form:
        return render_template("login.html")

    normalised_email = None
    email, password = request.form["email"], request.form["password"]

    try:
        email_info = validate_email(email)
        normalised_email = email_info.normalized
    except EmailNotValidError as e:
        return render_template("login.html", error=str(e))

    with db.Connection() as conn:
        user = conn.get_user_by_email(normalised_email)

        if not user or not check_password_hash(user.hash, password):
            return render_template(
                "login.html", error="The email or the password is incorrect"
            )

        login_user(conn.get_user_by_email(normalised_email))

    return redirect(url_for("homepage"))


@bp.route("logout")
def logout():
    logout_user()
    return redirect(url_for("homepage"))
