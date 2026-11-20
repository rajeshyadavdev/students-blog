from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from blog.extensions import db
from blog.posts.forms import PostForm
from blog.posts.models import Post

post_bp = Blueprint("posts", __name__)


@post_bp.route("/post/create-post", methods=["GET", "POST"])
@login_required
def create_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(
            title=form.title.data.strip(),
            content=form.content.data.strip(),
            author=current_user,
        )
        db.session.add(post)
        db.session.commit()
        flash("Your post has been created!", "success")
        return redirect(url_for("main.home"))
    return render_template(
        "posts/create_post.html",
        title="New Post",
        form=form,
        legend="New Post",
    )


@post_bp.route("/post/<int:post_id>")
def post(post_id):
    post = db.get_or_404(Post, post_id)
    return render_template("posts/post.html", title=post.title, post=post)


@post_bp.route("/post/<int:post_id>/update", methods=["GET", "POST"])
@login_required
def update_post(post_id):
    post = db.get_or_404(Post, post_id)
    if post.author != current_user:
        abort(403)

    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data.strip()
        post.content = form.content.data.strip()
        db.session.commit()
        flash("Your post has been updated!", "success")
        return redirect(url_for("posts.post", post_id=post.id))
    elif request.method == "GET":
        form.title.data = post.title
        form.content.data = post.content

    return render_template(
        "posts/create_post.html",
        title=post.title,
        form=form,
        legend="Update Post",
    )


@post_bp.route("/post/<int:post_id>/delete", methods=["POST"])
@login_required
def delete_post(post_id):
    post = db.get_or_404(Post, post_id)
    if post.author != current_user and not current_user.is_moderator:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash("Your post has been deleted!", "success")
    return redirect(url_for("main.home"))
