from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from db import db_connection

routes = Blueprint("routes", __name__)


def form_value(*names):
    """Return the first form field that exists (handles email vs emailInput)."""
    for name in names:
        value = request.form.get(name)
        if value is not None:
            return value
    return ""


@routes.route("/home")
def index():
    username = session.get("username")

    if "email" not in session:
        return redirect(url_for("routes.account"))
    return render_template("index.html", username=username)
    

    



@routes.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        email = form_value("email", "emailInput").strip()
        password = form_value("password", "passwordInput")

        connection = db_connection()
        user = connection.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
        connection.close()

        if user and check_password_hash(user["password_hash"], password):
            session["email"] = user["email"]
            flash("Logged into account.", "success")
            return redirect(url_for("routes.account"))

        flash("Invalid email or password.", "error")
        return redirect(url_for("routes.login"))

    if "email" in session:
        flash("You are already logged in.", "alert")
        return redirect(url_for("routes.account"))
    return render_template("login.html")


@routes.route("/register", methods=["POST", "GET"])
def register():
    if "email" in session:
        flash("You are already logged in.", "alert")
        return redirect(url_for("routes.account"))

    if request.method == "POST":
        email = form_value("email", "emailInput").strip()
        password = form_value("password", "passwordInput")

        if not email or not password:
            flash("Please enter an email and password.", "error")
            return redirect(url_for("routes.register"))

        connection = db_connection()
        existing = connection.execute(
            "SELECT 1 FROM users WHERE email = ?", (email,)
        ).fetchone()
        if existing:
            connection.close()
            flash("An account with that email already exists.", "error")
            return redirect(url_for("routes.register"))

        connection.execute(
            "INSERT INTO users (email, password_hash) VALUES (?, ?)",
            (email, generate_password_hash(password)),
        )
        connection.commit()
        connection.close()

        session["email"] = email
        flash("Account created.", "success")
        return redirect(url_for("routes.account"))

    return render_template("register.html")


@routes.route("/account")
def account():
    if "email" not in session:
        return redirect(url_for("routes.login"))

    connection = db_connection()
    user = connection.execute(
        "SELECT * FROM users WHERE email = ?", (session["email"],)
    ).fetchone()
    connection.close()

    if user is None: 
        session.pop("email", None)
        return redirect(url_for("routes.login"))

    return render_template("account.html", user=user,)


@routes.route("/logout")
def logout():
    session.pop("email", None)
    return redirect(url_for("routes.login"))


@routes.route("/account/update", methods=["POST"])
def update_account():
    if "email" not in session:
        return redirect(url_for("routes.login"))

    new_username = request.form.get("username", "").strip()
    new_email = request.form.get("email", "").strip()
    new_password = request.form.get("password", "")

    connection = db_connection()
    user = connection.execute(
        "SELECT * FROM users WHERE email = ?", (session["email"],)
    ).fetchone()
    if user is None:
        connection.close()
        session.pop("email", None)
        return redirect(url_for("routes.login"))

    user_id = user["id"]  # update by id, never by email

    try:
        if new_username and new_username != user["username"]:
            taken = connection.execute(
                "SELECT 1 FROM users WHERE username = ? AND id != ?",
                (new_username, user_id),
            ).fetchone()
            if taken:
                flash("That username is already taken.", "error")
                return redirect(url_for("routes.account"))
            connection.execute(
                "UPDATE users SET username = ? WHERE id = ?",
                (new_username, user_id),
            )

            session["username"] = new_username

        if new_password:
            connection.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (generate_password_hash(new_password), user_id),
            )

        if new_email and new_email != user["email"]:
            taken = connection.execute(
                "SELECT 1 FROM users WHERE email = ? AND id != ?",
                (new_email, user_id),
            ).fetchone()
            if taken:
                flash("That email is already in use.", "error")
                return redirect(url_for("routes.account"))
            connection.execute(
                "UPDATE users SET email = ? WHERE id = ?",
                (new_email, user_id),
            )
            session["email"] = new_email

        connection.commit()
    except sqlite3.IntegrityError:
        connection.rollback()
        flash("That username or email is already in use.", "error")
        return redirect(url_for("routes.account"))
    finally:
        connection.close()

    flash("Account updated.", "success")
    return redirect(url_for("routes.account"))
