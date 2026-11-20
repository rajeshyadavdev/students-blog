from datetime import date

from blog.extensions import db
from blog.posts.models import Post
from blog.students.models import Attendance, Course, Grade, Student, Subject
from blog.users.models import User, UserRole


def login(client, email, password="password123"):
    return client.post(
        "/login", data={"email": email, "password": password}, follow_redirects=True
    )


def logout(client):
    return client.get("/logout", follow_redirects=True)


# --- 1. Public & Access Control Tests ---


def test_public_pages(client):
    assert client.get("/").status_code == 200
    assert client.get("/about").status_code == 200
    assert client.get("/nonexistent-page").status_code == 404


def test_role_access_guards(client):
    login(client, "user@test.com")
    assert client.get("/student/dashboard").status_code == 403
    assert client.get("/admin/dashboard").status_code == 403


def test_moderator_vs_admin_permissions(client):
    login(client, "mod@test.com")
    assert client.get("/admin/attendance").status_code == 200
    assert client.get("/admin/grades").status_code == 200
    assert client.get("/admin/posts").status_code == 200
    assert client.get("/admin/users").status_code == 403
    assert client.get("/admin/courses").status_code == 403


def test_student_portal_routes(client):
    login(client, "stud@test.com")
    for url in [
        "/student/dashboard",
        "/student/attendance",
        "/student/grades",
        "/student/profile",
    ]:
        assert client.get(url).status_code == 200


def test_admin_full_access(client):
    login(client, "admin@test.com")
    for url in [
        "/admin/dashboard",
        "/admin/users",
        "/admin/courses",
        "/admin/students",
        "/admin/students/enroll",
    ]:
        assert client.get(url).status_code == 200


# --- 2. Post CRUD & Ownership POST Tests ---


def test_post_create_update_and_permissions(client, app):
    # Regular user creates a post
    login(client, "user@test.com")
    res = client.post(
        "/post/create-post",
        data={
            "title": "My Algebra Notes",
            "content": "Linear equations and matrix determinants explained.",
        },
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert b"Your post have been created!" in res.data or b"Your post has been created!" in res.data

    with app.app_context():
        post = db.session.scalar(db.select(Post).where(Post.title == "My Algebra Notes"))
        assert post is not None
        post_id = post.id

    # Author updates their own post
    res = client.post(
        f"/post/{post_id}/update",
        data={
            "title": "Updated Algebra Notes",
            "content": "Updated content with eigenvalues.",
        },
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert b"Updated Algebra Notes" in res.data

    # Another regular user (student) cannot edit or delete someone else's post
    logout(client)
    login(client, "stud@test.com")
    assert client.post(
        f"/post/{post_id}/update",
        data={"title": "Hacked", "content": "Hacked content here."},
    ).status_code == 403
    assert client.post(f"/post/{post_id}/delete").status_code == 403

    # Moderator CAN delete the post
    logout(client)
    login(client, "mod@test.com")
    res = client.post(f"/post/{post_id}/delete", follow_redirects=True)
    assert res.status_code == 200

    with app.app_context():
        assert db.session.get(Post, post_id) is None


# --- 3. Student Profile Update POST Test ---


def test_student_profile_update(client, app):
    login(client, "stud@test.com")
    res = client.post(
        "/student/profile",
        data={"full_name": "Updated Student Name", "phone": "9123456789"},
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert b"Your student profile has been updated." in res.data

    with app.app_context():
        student = db.session.scalar(db.select(Student).where(Student.roll_number == "CSE001"))
        assert student.full_name == "Updated Student Name"
        assert student.phone == "9123456789"


# --- 4. Admin Courses, Enrollment, Attendance & Grades POST Tests ---


def test_admin_academic_workflows(client, app):
    login(client, "admin@test.com")

    # 1. Create a new Course
    res = client.post(
        "/admin/courses",
        data={
            "name": "B.Sc Mathematics",
            "duration_years": 3,
            "description": "Undergraduate mathematics degree",
            "submit": "Save Course",
        },
        follow_redirects=True,
    )
    assert res.status_code == 200

    with app.app_context():
        math_course = db.session.scalar(db.select(Course).where(Course.name == "B.Sc Mathematics"))
        assert math_course is not None
        math_course_id = math_course.id

    # 2. Add a Subject to that Course
    res = client.post(
        "/admin/subjects/add",
        data={
            "course_id": math_course_id,
            "code": "MATH201",
            "name": "Real Analysis",
            "semester": 2,
        },
        follow_redirects=True,
    )
    assert res.status_code == 200

    with app.app_context():
        math_sub = db.session.scalar(db.select(Subject).where(Subject.code == "MATH201"))
        assert math_sub is not None
        math_sub_id = math_sub.id
        reg_user = db.session.scalar(db.select(User).where(User.email == "user@test.com"))
        reg_user_id = reg_user.id

    # 3. Enroll regular user as a Student (promotes role to STUDENT)
    res = client.post(
        "/admin/students/enroll",
        data={
            "user_id": reg_user_id,
            "course_id": math_course_id,
            "roll_number": "MATH202601",
            "full_name": "Priya Verma",
            "batch_year": 2026,
            "phone": "9988776655",
        },
        follow_redirects=True,
    )
    assert res.status_code == 200

    with app.app_context():
        enrolled = db.session.scalar(db.select(Student).where(Student.roll_number == "MATH202601"))
        assert enrolled is not None
        assert enrolled.user.role == UserRole.STUDENT
        enrolled_id = enrolled.id

    # 4. Bulk-mark Attendance (present)
    today_str = date.today().isoformat()
    res = client.post(
        f"/admin/attendance?subject_id={math_sub_id}&date={today_str}",
        data={"present_students": [str(enrolled_id)]},
        follow_redirects=True,
    )
    assert res.status_code == 200

    with app.app_context():
        att = db.session.scalar(
            db.select(Attendance).where(
                Attendance.student_id == enrolled_id,
                Attendance.subject_id == math_sub_id,
            )
        )
        assert att is not None
        assert att.is_present is True

    # 5. Record & Update Exam Grade (tests upsert logic too)
    res = client.post(
        "/admin/grades",
        data={
            "student_id": enrolled_id,
            "subject_id": math_sub_id,
            "exam_type": "Final",
            "marks_obtained": 88.0,
            "max_marks": 100.0,
        },
        follow_redirects=True,
    )
    assert res.status_code == 200

    # Re-submit same student/subject/exam_type with updated marks
    res = client.post(
        "/admin/grades",
        data={
            "student_id": enrolled_id,
            "subject_id": math_sub_id,
            "exam_type": "Final",
            "marks_obtained": 92.5,
            "max_marks": 100.0,
        },
        follow_redirects=True,
    )
    assert res.status_code == 200

    with app.app_context():
        grades = db.session.scalars(
            db.select(Grade).where(
                Grade.student_id == enrolled_id,
                Grade.subject_id == math_sub_id,
                Grade.exam_type == "Final",
            )
        ).all()
        assert len(grades) == 1
        assert grades[0].marks_obtained == 92.5
