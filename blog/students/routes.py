from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user

from blog.extensions import db
from blog.students.forms import StudentProfileUpdateForm
from blog.students.models import Attendance, Grade, Subject
from blog.users.models import UserRole
from blog.users.utils import role_required

students_bp = Blueprint("students", __name__, url_prefix="/student")


@students_bp.route("/")
@students_bp.route("/dashboard")
@role_required(UserRole.STUDENT)
def dashboard():
    student = current_user.student_profile
    if not student:
        flash(
            "Your student profile has not been set up yet. Contact an admin.",
            "warning",
        )
        return redirect(url_for("main.home"))

    recent_grades = db.session.scalars(
        db.select(Grade)
        .filter_by(student_id=student.id)
        .order_by(Grade.id.desc())
        .limit(5)
    ).all()

    return render_template(
        "students/dashboard.html",
        title="Student Dashboard",
        student=student,
        recent_grades=recent_grades,
    )


@students_bp.route("/profile", methods=["GET", "POST"])
@role_required(UserRole.STUDENT)
def profile():
    student = current_user.student_profile
    if not student:
        flash("Student profile not found.", "warning")
        return redirect(url_for("main.home"))

    form = StudentProfileUpdateForm()
    if form.validate_on_submit():
        student.full_name = form.full_name.data.strip()
        student.phone = form.phone.data.strip() if form.phone.data else None
        db.session.commit()
        flash("Your student profile has been updated.", "success")
        return redirect(url_for("students.profile"))
    elif request.method == "GET":
        form.full_name.data = student.full_name
        form.phone.data = student.phone

    return render_template(
        "students/profile.html",
        title="Student Profile",
        form=form,
        student=student,
    )


@students_bp.route("/attendance")
@role_required(UserRole.STUDENT)
def attendance():
    student = current_user.student_profile
    if not student:
        flash("Student profile not found.", "warning")
        return redirect(url_for("main.home"))

    subjects = db.session.scalars(
        db.select(Subject)
        .filter_by(course_id=student.course_id)
        .order_by(Subject.semester, Subject.code)
    ).all()

    subject_stats = []
    for sub in subjects:
        records = [a for a in student.attendances if a.subject_id == sub.id]
        total = len(records)
        attended = sum(1 for r in records if r.is_present)
        pct = round((attended / total) * 100, 1) if total > 0 else 0.0
        subject_stats.append(
            {
                "subject": sub,
                "total": total,
                "attended": attended,
                "percentage": pct,
            }
        )

    recent_records = db.session.scalars(
        db.select(Attendance)
        .filter_by(student_id=student.id)
        .order_by(Attendance.date.desc())
        .limit(20)
    ).all()

    return render_template(
        "students/attendance.html",
        title="My Attendance",
        student=student,
        subject_stats=subject_stats,
        recent_records=recent_records,
    )


@students_bp.route("/grades")
@role_required(UserRole.STUDENT)
def grades():
    student = current_user.student_profile
    if not student:
        flash("Student profile not found.", "warning")
        return redirect(url_for("main.home"))

    all_grades = db.session.scalars(
        db.select(Grade)
        .join(Subject)
        .filter(Grade.student_id == student.id)
        .order_by(Subject.semester.asc(), Subject.code.asc())
    ).all()

    return render_template(
        "students/grades.html",
        title="My Grades",
        student=student,
        grades=all_grades,
    )
