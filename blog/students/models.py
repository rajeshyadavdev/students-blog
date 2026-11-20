from datetime import UTC, date, datetime

from blog.extensions import db


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)  # e.g., "B.Tech CSE"
    duration_years = db.Column(db.Integer, nullable=False, default=4)
    description = db.Column(db.Text, nullable=True, default="No description available")

    students = db.relationship("Student", back_populates="course", lazy=True)
    subjects = db.relationship(
        "Subject", back_populates="course", lazy=True, cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"Course('{self.name}')"


class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)  # e.g., "CS101"
    name = db.Column(db.String(100), nullable=False)
    semester = db.Column(db.Integer, nullable=False)
    course_id = db.Column(
        db.Integer,
        db.ForeignKey("course.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    course = db.relationship("Course", back_populates="subjects")
    attendances = db.relationship(
        "Attendance", back_populates="subject", lazy=True, cascade="all, delete-orphan"
    )
    grades = db.relationship(
        "Grade", back_populates="subject", lazy=True, cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"Subject('{self.code}', '{self.name}')"


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    course_id = db.Column(
        db.Integer, db.ForeignKey("course.id"), nullable=False, index=True
    )
    roll_number = db.Column(db.String(30), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(100), nullable=False)
    batch_year = db.Column(db.Integer, nullable=False)
    phone = db.Column(db.String(15), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True, server_default="1")
    enrolled_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=db.func.now(),
    )

    user = db.relationship("User", back_populates="student_profile")
    course = db.relationship("Course", back_populates="students")
    attendances = db.relationship(
        "Attendance", back_populates="student", lazy=True, cascade="all, delete-orphan"
    )
    grades = db.relationship(
        "Grade", back_populates="student", lazy=True, cascade="all, delete-orphan"
    )

    @property
    def attendance_percentage(self):
        if not self.attendances:
            return 0.0
        attended = sum(1 for a in self.attendances if a.is_present)
        return round((attended / len(self.attendances)) * 100, 1)

    def __repr__(self):
        return f"Student('{self.roll_number}', '{self.full_name}')"


class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(
        db.Integer,
        db.ForeignKey("student.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subject_id = db.Column(
        db.Integer,
        db.ForeignKey("subject.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    date = db.Column(db.Date, nullable=False, default=date.today, index=True)
    is_present = db.Column(db.Boolean, nullable=False, default=False)

    # Prevent duplicate attendance records for the same student, subject, and date
    __table_args__ = (
        db.UniqueConstraint(
            "student_id", "subject_id", "date", name="uq_student_subject_date"
        ),
    )

    student = db.relationship("Student", back_populates="attendances")
    subject = db.relationship("Subject", back_populates="attendances")

    def __repr__(self):
        return f"Attendance(student={self.student_id}, subject={self.subject_id}, date={self.date}, present={self.is_present})"


class Grade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(
        db.Integer,
        db.ForeignKey("student.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subject_id = db.Column(
        db.Integer,
        db.ForeignKey("subject.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    exam_type = db.Column(
        db.String(30), nullable=False, default="Final"
    )  # e.g., "Midterm", "Final"
    marks_obtained = db.Column(db.Float, nullable=False)
    max_marks = db.Column(db.Float, nullable=False, default=100.0)

    # Prevent duplicate grade entries for the same student, subject, and exam type
    __table_args__ = (
        db.UniqueConstraint(
            "student_id", "subject_id", "exam_type", name="uq_student_subject_exam"
        ),
    )

    student = db.relationship("Student", back_populates="grades")
    subject = db.relationship("Subject", back_populates="grades")

    @property
    def percentage(self):
        if not self.max_marks:
            return 0.0
        return round((self.marks_obtained / self.max_marks) * 100, 1)

    @property
    def letter_grade(self):
        pct = self.percentage
        if pct >= 90:
            return "A+"
        elif pct >= 80:
            return "A"
        elif pct >= 70:
            return "B"
        elif pct >= 60:
            return "C"
        elif pct >= 50:
            return "D"
        return "F"

    def __repr__(self):
        return f"Grade(student={self.student_id}, subject={self.subject_id}, exam='{self.exam_type}', {self.marks_obtained}/{self.max_marks})"
