# =========================
# routes/auth.py
# =========================

import re
import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models.user import User

auth = Blueprint("auth", __name__)
logger = logging.getLogger(__name__)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username     = request.form.get("username", "").strip()
        email        = request.form.get("email", "").strip().lower()
        password     = request.form.get("password", "").strip()
        display_name = request.form.get("display_name", "").strip()

        # ---- バリデーション ----
        if not username or not email or not password:
            flash("ユーザー名・メールアドレス・パスワードは必須です。", "error")
            return render_template("register.html")

        if len(username) < 3:
            flash("ユーザー名は3文字以上で入力してください。", "error")
            return render_template("register.html")

        if not EMAIL_RE.match(email):
            flash("メールアドレスの形式が正しくありません。", "error")
            return render_template("register.html")

        if len(password) < 6:
            flash("パスワードは6文字以上で入力してください。", "error")
            return render_template("register.html")

        if User.query.filter_by(username=username).first():
            flash("このユーザー名はすでに使われています。", "error")
            return render_template("register.html")

        if User.query.filter_by(email=email).first():
            flash("このメールアドレスはすでに登録されています。", "error")
            return render_template("register.html")

        # ---- 登録 ----
        user = User(
            username=username,
            email=email,
            password=generate_password_hash(password),
            display_name=display_name or username,
        )
        db.session.add(user)
        db.session.commit()
        logger.info("REGISTER user_id=%s username=%s", user.id, user.username)
        login_user(user)
        flash("アカウントを作成しました！", "success")
        return redirect(url_for("main.index"))

    return render_template("register.html")


@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()
        user     = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            logger.info("LOGIN user_id=%s", user.id)
            next_page = request.args.get("next", "/")
            return redirect(next_page)
        else:
            logger.warning("LOGIN_FAIL email=%s", email)
            flash("メールアドレスまたはパスワードが正しくありません。", "error")

    return render_template("login.html")


@auth.route("/logout")
@login_required
def logout():
    logger.info("LOGOUT user_id=%s", current_user.id)
    logout_user()
    return redirect(url_for("main.index"))
