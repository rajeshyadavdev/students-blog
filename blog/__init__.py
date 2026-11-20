import os

from flask import Flask

from blog.config import Config, DevConfig, ProdConfig, TestConfig
from blog.extensions import csrf, db, login_manager, mail, migrate


def create_app(config_class: Config) -> Flask:

    app = Flask(__name__)

    if config_class is None:
        env = os.environ.get("WORK_ENV", "DEV").upper()
        config_map = {"PROD": ProdConfig, "TEST": TestConfig, "DEV": DevConfig}
        config_class = config_map.get(env, DevConfig)
    app.config.from_object(obj=config_class)

    db.init_app(app=app)
    migrate.init_app(app=app, db=db)
    mail.init_app(app=app)
    csrf.init_app(app=app)

    """
    The session_protection attribute of the LoginManager object can be set to None,'basic', or 'strong' to provide different levels of security against user session tam‐pering. With the 'strong' setting, Flask-Login will keep track of the client’s IP address and browser agent and will log the user out if it detects a change
    """
    login_manager.session_protection = "strong"
    login_manager.init_app(app=app)
    login_manager.login_view = "users.login"
    login_manager.login_message = "You must log in to access this page."
    login_manager.login_message_category = "info"

    from blog.admin.routes import admin_bp
    from blog.errors.handlers import error_bp
    from blog.main.routes import main_bp
    from blog.posts.routes import post_bp
    from blog.students.routes import students_bp
    from blog.users.routes import user_bp

    app.register_blueprint(user_bp)
    app.register_blueprint(post_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(error_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(students_bp)

    from blog.posts.models import Post
    from blog.students.models import Attendance, Course, Grade, Student, Subject
    from blog.users.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    return app
