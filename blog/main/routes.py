from flask import Blueprint, render_template, request

from blog.posts.models import Post

main_bp = Blueprint('main',__name__)

@main_bp.route("/")
@main_bp.route("/home")
def home():
    page = request.args.get("page", 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
    return render_template("main/home.html", title="Home", posts=posts)


@main_bp.route("/about")
def about():
    return render_template("main/about.html", title="About")