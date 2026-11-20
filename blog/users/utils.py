import os
import secrets
from functools import wraps

from flask import abort, current_app, url_for
from flask_login import current_user, login_required
from flask_mail import Message
from PIL import Image

from blog.extensions import mail
from blog.users.models import UserRole


def role_required(*roles: UserRole):
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if current_user.role not in roles:
                abort(403)  # Triggers your custom 403.html error page!
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, file_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + file_ext

    # 1. Point to the main app's static directory, not the users blueprint folder
    picture_dir = os.path.join(current_app.root_path, "static", "profile_pic")

    # 2. Create ONLY the folder, not the filename
    os.makedirs(picture_dir, exist_ok=True)

    # 3. Join the folder and filename afterward
    picture_path = os.path.join(picture_dir, picture_fn)

    output_size = (120, 120)
    i = Image.open(form_picture)
    i.thumbnail(output_size)

    i.save(picture_path)
    return picture_fn


def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message(
        subject="Password Reset Request",
        sender=current_app.config["MAIL_DEFAULT_SENDER"],
        recipients=[user.email],
    )
    msg.body = f"""To reset your password, visit the following link:
{url_for("users.reset_token", token=token, _external=True)}

If you did not make this request, simply ignore this email.
"""
    mail.send(msg)
