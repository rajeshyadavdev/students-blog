from datetime import date

import pytest

from blog import create_app
from blog.config import TestConfig
from blog.extensions import bcrypt, db
from blog.posts.models import Post
from blog.students.models import Attendance, Course, Grade, Student, Subject
from blog.users.models import User, UserRole


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()

        pw = bcrypt.generate_password_hash("password123").decode("utf-8")
        admin = User(username="admin1", email="admin@test.com", password=pw, role=UserRole.ADMIN)
        mod = User(username="mod1", email="mod@test.com", password=pw, role=UserRole.MODERATOR)
        stud_user = User(username="stud1", email="stud@test.com", password=pw, role=UserRole.STUDENT)
        reg_user = User(username="user1", email="user@test.com", password=pw, role=UserRole.USER)
        db.session.add_all([admin, mod, stud_user, reg_user])
        db.session.flush()

        course = Course(name="B.Tech CSE", duration_years=4)
        db.session.add(course)
        db.session.flush()

        subject = Subject(code="CS101", name="Data Structures", semester=3, course_id=course.id)
        db.session.add(subject)
        db.session.flush()

        student = Student(
            user_id=stud_user.id,
            course_id=course.id,
            roll_number="CSE001",
            full_name="Test Student",
            batch_year=2026,
            phone="9876543210",
        )
        db.session.add(student)
        db.session.flush()

        db.session.add(Attendance(student_id=student.id, subject_id=subject.id, date=date.today(), is_present=True))
        db.session.add(Grade(student_id=student.id, subject_id=subject.id, exam_type="Midterm", marks_obtained=45, max_marks=50))
        db.session.add(Post(title="Welcome Post", content="First test post content.", author=admin))
        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()
