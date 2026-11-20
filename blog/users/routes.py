from urllib.parse import urlparse

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import func, select

from blog.extensions import bcrypt, db
from blog.posts.models import Post
from blog.users.forms import (
    AccountUpdateForm,
    LoginForm,
    RegistrationForm,
    RequestResetForm,
    ResetPasswordForm,
)
from blog.users.models import User
from blog.users.utils import save_picture, send_reset_email

user_bp = Blueprint("users", __name__)


@user_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode(
            "utf-8"
        )
        user = User(
            username=form.username.data.strip(),
            email=form.email.data.strip().lower(),
            password=hashed_password,
        )
        db.session.add(user)
        db.session.commit()
        flash("Your account has been created! You are now able to sign in.", "success")
        return redirect(url_for("users.login"))
    return render_template("users/register.html", title="Register", form=form)


@user_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))
    form = LoginForm()
    if form.validate_on_submit():
        email_input = form.email.data.strip().lower()
        user = db.session.scalar(
            select(User).where(func.lower(User.email) == email_input)
        )
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            if not user.is_active:
                flash("Your account is deactivated. Please contact support.", "warning")
                return redirect(url_for("users.login"))

            login_user(user, remember=form.remember.data)
            next_page = request.args.get("next")
            # Prevent open-redirect attacks by ensuring next_page is a local path
            if (
                next_page
                and not urlparse(next_page).netloc
                and not urlparse(next_page).scheme
            ):
                return redirect(next_page)
            return redirect(url_for("main.home"))
        flash("Login unsuccessful. Please check email and password.", "danger")
    return render_template("users/login.html", title="Login", form=form)


@user_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.home"))


@user_bp.route("/account", methods=["GET", "POST"])
@login_required
def account():
    form = AccountUpdateForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data, current_user.image_file)
            current_user.image_file = picture_file
        current_user.username = form.username.data.strip()
        current_user.email = form.email.data.strip().lower()
        db.session.commit()
        flash("Your account has been updated!", "success")
        return redirect(url_for("users.account"))
    elif request.method == "GET":
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for("static", filename="profile_pic/" + current_user.image_file)
    return render_template(
        "users/account.html", title="Account", image_file=image_file, form=form
    )


@user_bp.route("/user/<string:username>/post")
@login_required
def user_posts(username):
    page = request.args.get("page", 1, type=int)
    user = db.first_or_404(select(User).where(User.username == username))
    posts = db.paginate(
        select(Post).where(Post.author == user).order_by(Post.date_posted.desc()),
        page=page,
        per_page=5,
    )
    return render_template(
        "posts/user_post.html", title="Posts", posts=posts, user=user
    )


@user_bp.route("/reset_password", methods=["GET", "POST"])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))
    form = RequestResetForm()
    if form.validate_on_submit():
        email_input = form.email.data.strip().lower()
        user = db.session.scalar(
            select(User).where(func.lower(User.email) == email_input)
        )
        if user:
            send_reset_email(user)
        flash(
            "If an account exists with that email, instructions to reset your password have been sent.",
            "info",
        )
        return redirect(url_for("users.login"))
    return render_template(
        "users/reset_request.html", title="Reset Password", form=form
    )


@user_bp.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))
    user = User.verify_reset_token(token)
    if user is None:
        flash("That is an invalid or expired token!", "warning")
        return redirect(url_for("users.reset_request"))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode(
            "utf-8"
        )
        user.password = hashed_password
        db.session.commit()
        flash("Your password has been updated! You are now able to sign in.", "success")
        return redirect(url_for("users.login"))
    return render_template("users/reset_token.html", title="Reset Password", form=form)
