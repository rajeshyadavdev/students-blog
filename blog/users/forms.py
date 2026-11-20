from flask_login import current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from sqlalchemy import func, select
from wtforms import (
    BooleanField,
    EmailField,
    PasswordField,
    StringField,
    SubmitField,
    ValidationError,
)
from wtforms.validators import DataRequired, Email, EqualTo, Length

from blog.extensions import db
from blog.users.models import User


class RegistrationForm(FlaskForm):
    username = StringField(
        label="Username", validators=[DataRequired(), Length(min=2, max=20)]
    )
    email = EmailField(label="Email", validators=[DataRequired(), Email()])
    password = PasswordField(
        label="Password", validators=[DataRequired(), Length(min=6, max=72)]
    )
    confirm_password = PasswordField(
        label="Confirm Password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField(label="Sign Up")

    def validate_username(self, username):
        user = db.session.scalar(
            select(User).where(func.lower(User.username) == username.data.lower())
        )
        if user:
            raise ValidationError(
                "That username is taken. Please choose a different one."
            )

    def validate_email(self, email):
        user = db.session.scalar(
            select(User).where(func.lower(User.email) == email.data.lower())
        )
        if user:
            raise ValidationError("That email is taken. Please choose a different one.")


class LoginForm(FlaskForm):
    email = EmailField(label="Email", validators=[DataRequired(), Email()])
    password = PasswordField(label="Password", validators=[DataRequired()])
    remember = BooleanField(label="Remember Me")
    submit = SubmitField(label="Login")


class AccountUpdateForm(FlaskForm):
    username = StringField(
        label="Update Username", validators=[DataRequired(), Length(min=2, max=20)]
    )
    email = EmailField(label="Update Email", validators=[DataRequired(), Email()])
    picture = FileField(
        label="Update Profile Picture",
        validators=[FileAllowed(["jpg", "jpeg", "png"])],
    )
    submit = SubmitField(label="Update")

    def validate_username(self, username):
        if username.data.lower() != current_user.username.lower():
            user = db.session.scalar(
                select(User).where(func.lower(User.username) == username.data.lower())
            )
            if user:
                raise ValidationError(
                    "That username is taken. Please choose a different one."
                )

    def validate_email(self, email):
        if email.data.lower() != current_user.email.lower():
            user = db.session.scalar(
                select(User).where(func.lower(User.email) == email.data.lower())
            )
            if user:
                raise ValidationError(
                    "That email is taken. Please choose a different one."
                )


class RequestResetForm(FlaskForm):
    email = EmailField(label="Email", validators=[DataRequired(), Email()])
    submit = SubmitField(label="Request Password Reset")


class ResetPasswordForm(FlaskForm):
    password = PasswordField(
        label="Password", validators=[DataRequired(), Length(min=6, max=72)]
    )
    confirm_password = PasswordField(
        label="Confirm Password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField(label="Reset Password")
