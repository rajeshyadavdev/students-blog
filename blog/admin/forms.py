from flask_wtf import FlaskForm
from sqlalchemy import func
from wtforms import (
    FloatField,
    IntegerField,
    SelectChoice,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import (
    DataRequired,
    InputRequired,
    Length,
    NumberRange,
    Optional,
    Regexp,
    ValidationError,
)

from blog.extensions import db
from blog.students.models import Course, Student, Subject


class CourseForm(FlaskForm):
    name = StringField(
        "Course Name", validators=[DataRequired(), Length(min=2, max=100)]
    )
    duration_years = IntegerField(
        "Duration (Years)",
        default=4,
        validators=[DataRequired(), NumberRange(min=1, max=10)],
    )
    description = TextAreaField("Description", validators=[Optional()])
    submit = SubmitField("Save Course")

    def validate_name(self, name):
        cleaned = name.data.strip().lower()
        if db.session.scalar(
            db.select(Course).where(func.lower(Course.name) == cleaned)
        ):
            raise ValidationError("A course with this name already exists.")


class SubjectForm(FlaskForm):
    course_id = SelectField("Course", coerce=int, validators=[DataRequired()])
    code = StringField(
        "Subject Code (e.g. CS101)", validators=[DataRequired(), Length(min=2, max=20)]
    )
    name = StringField(
        "Subject Name", validators=[DataRequired(), Length(min=2, max=100)]
    )
    semester = IntegerField(
        "Semester", validators=[DataRequired(), NumberRange(min=1, max=12)]
    )
    submit = SubmitField("Add Subject")

    def validate_code(self, code):
        cleaned = code.data.strip().lower()
        if db.session.scalar(
            db.select(Subject).where(func.lower(Subject.code) == cleaned)
        ):
            raise ValidationError("This subject code already exists.")


class StudentEnrollmentForm(FlaskForm):
    user_id = SelectField(
        "Select User Account", coerce=int, validators=[DataRequired()]
    )
    course_id = SelectField("Course", coerce=int, validators=[DataRequired()])
    roll_number = StringField(
        "Roll Number", validators=[DataRequired(), Length(min=2, max=30)]
    )
    full_name = StringField(
        "Full Name", validators=[DataRequired(), Length(min=2, max=100)]
    )
    batch_year = IntegerField(
        "Batch Year", validators=[DataRequired(), NumberRange(min=2000, max=2100)]
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
        if db.session.scalar(db.select(Student).where(Student.user_id == user_id.data)):
            raise ValidationError("This user account is already enrolled as a student.")

    def validate_roll_number(self, roll_number):
        cleaned = roll_number.data.strip().lower()
        if db.session.scalar(
            db.select(Student).where(func.lower(Student.roll_number) == cleaned)
        ):
            raise ValidationError(
                "That roll number is already assigned to another student."
            )


class GradeForm(FlaskForm):
    student_id = SelectField("Student", coerce=int, validators=[DataRequired()])
    subject_id = SelectField("Subject", coerce=int, validators=[DataRequired()])
    exam_type = SelectField(
        "Exam Type",
        choices=[
            SelectChoice("Weekly", "Weekly"),
            SelectChoice("Midterm", "Midterm"),
            SelectChoice("Final", "Final"),
            SelectChoice("Assignment", "Assignment"),
            SelectChoice("Practical", "Practical"),
        ],
        validators=[DataRequired()],
    )
    marks_obtained = FloatField(
        "Marks Obtained", validators=[InputRequired(), NumberRange(min=0)]
    )
    max_marks = FloatField(
        "Maximum Marks", default=100.0, validators=[DataRequired(), NumberRange(min=1)]
    )
    submit = SubmitField("Save Grade")

    def validate_marks_obtained(self, marks_obtained):
        if (
            marks_obtained.data is not None
            and self.max_marks.data is not None
            and marks_obtained.data > self.max_marks.data
        ):
            raise ValidationError("Marks obtained cannot exceed maximum marks.")
