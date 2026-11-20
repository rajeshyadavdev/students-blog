from flask_wtf import FlaskForm
from sqlalchemy import func
from wtforms import IntegerField, SelectField, StringField, SubmitField
from wtforms.validators import (
    DataRequired,
    Length,
    NumberRange,
    Optional,
    Regexp,
    ValidationError,
)

from blog.extensions import db
from blog.students.models import Student


class StudentEnrollmentForm(FlaskForm):
    user_id = SelectField(
        "Select User Account", coerce=int, validators=[DataRequired()]
    )
    course_id = SelectField("Course", coerce=int, validators=[DataRequired()])
    roll_number = StringField(
        "Roll Number",
        validators=[DataRequired(), Length(min=2, max=30)],
    )
    full_name = StringField(
        "Full Name",
        validators=[DataRequired(), Length(min=2, max=100)],
    )
    batch_year = IntegerField(
        "Batch Year",
        validators=[DataRequired(), NumberRange(min=2000, max=2100)],
    )
    phone = StringField(
        "Phone Number",
        validators=[
            Optional(),
            Length(min=10, max=15),
            Regexp(r"^\+?[0-9\s\-]+$", message="Enter a valid phone number."),
        ],
    )
    submit = SubmitField("Enroll Student")

    def validate_user_id(self, user_id):
        existing_profile = db.session.scalar(
            db.select(Student).where(Student.user_id == user_id.data)
        )
        if existing_profile:
            raise ValidationError("This user account is already enrolled as a student.")

    def validate_roll_number(self, roll_number):
        cleaned_roll = roll_number.data.strip().lower()
        existing_student = db.session.scalar(
            db.select(Student).where(func.lower(Student.roll_number) == cleaned_roll)
        )
        if existing_student:
            raise ValidationError(
                "That roll number is already assigned to another student."
            )


class StudentProfileUpdateForm(FlaskForm):
    full_name = StringField(
        "Full Name",
        validators=[DataRequired(), Length(min=2, max=100)],
    )
    phone = StringField(
        "Phone Number",
        validators=[
            Optional(),
            Length(min=10, max=15),
            Regexp(r"^\+?[0-9\s\-]+$", message="Enter a valid phone number."),
        ],
    )
    submit = SubmitField("Update Profile")
