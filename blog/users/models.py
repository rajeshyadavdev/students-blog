import enum
from datetime import UTC, datetime

from flask import current_app
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer as Serializer
from itsdangerous.exc import BadData

from blog.extensions import db


class UserRole(enum.Enum):
    USER = "user"
    STUDENT = "student"
    MODERATOR = "moderator"
    ADMIN = "admin"


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    image_file = db.Column(db.String(64), nullable=False, default="default.jpg")
    password = db.Column(db.String(255), nullable=False)

    role = db.Column(
        db.Enum(UserRole),
        nullable=False,
        default=UserRole.USER,
        server_default="USER",
    )

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        server_default="1",
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=db.func.now(),
    )

    # Relationships
    posts = db.relationship(
        "Post",
        backref="author",
        lazy=True,
        cascade="all, delete-orphan",
    )

    student_profile = db.relationship(
        "Student",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # Role helper properties for routes and Jinja2 templates
    @property
    def is_student(self):
        return self.role == UserRole.STUDENT

    @property
    def is_moderator(self):
        return self.role in (UserRole.MODERATOR, UserRole.ADMIN)

    @property
    def is_admin(self):
        return self.role == UserRole.ADMIN

    # Password reset token generation & verification
    def get_reset_token(self):
        s = Serializer(current_app.config["SECRET_KEY"])
        return s.dumps({"user_id": self.id}, salt="password-reset")

    @staticmethod
    def verify_reset_token(token, expires_sec=1800):
        s = Serializer(current_app.config["SECRET_KEY"])
        try:
            user_id = s.loads(token, salt="password-reset", max_age=expires_sec)[
                "user_id"
            ]
        except (BadData, KeyError, TypeError):
            return None
        return db.session.get(User, user_id)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.role.value}')"
