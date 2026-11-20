from datetime import date

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user

from blog.admin.forms import (
    CourseForm,
    GradeForm,
    StudentEnrollmentForm,
    SubjectForm,
)
from blog.extensions import db
from blog.posts.models import Post
from blog.students.models import Attendance, Course, Grade, Student, Subject
from blog.users.models import User, UserRole
from blog.users.utils import role_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/")
@admin_bp.route("/dashboard")
@role_required(UserRole.ADMIN)
def dashboard():
    total_users = db.session.scalar(db.select(db.func.count(User.id)))
    total_posts = db.session.scalar(db.select(db.func.count(Post.id)))
    recent_users = db.session.scalars(
        db.select(User).order_by(User.id.desc()).limit(5)
    ).all()
    recent_posts = db.session.scalars(
        db.select(Post).order_by(Post.date_posted.desc()).limit(5)
    ).all()
    return render_template(
        "admin/dashboard.html",
        total_users=total_users,
        total_posts=total_posts,
        recent_users=recent_users,
        recent_posts=recent_posts,
    )


@admin_bp.route("/users")
@role_required(UserRole.ADMIN)
def manage_users():
    page = request.args.get("page", 1, type=int)
    users = db.paginate(db.select(User).order_by(User.id.asc()), page=page, per_page=10)
    return render_template("admin/users.html", users=users, UserRole=UserRole)


@admin_bp.route("/user/<int:user_id>/role", methods=["POST"])
@role_required(UserRole.ADMIN)
def change_user_role(user_id):
    user = db.session.get(User, user_id) or abort(404)

    # Prevent an admin from accidentally demoting themselves
    if user.id == current_user.id:
        flash("You cannot change your own role.", "warning")
        return redirect(url_for("admin.manage_users"))

    new_role_value = request.form.get("role")
    try:
        user.role = UserRole(new_role_value)
        db.session.commit()
        flash(f"Updated {user.username}'s role to {user.role.value}.", "success")
    except ValueError:
        flash("Invalid role selected.", "danger")

    return redirect(url_for("admin.manage_users"))


@admin_bp.route("/user/<int:user_id>/delete", methods=["POST"])
@role_required(UserRole.ADMIN)
def delete_user(user_id):
    user = db.session.get(User, user_id) or abort(404)

    if user.id == current_user.id:
        flash("You cannot delete your own admin account.", "danger")
        return redirect(url_for("admin.manage_users"))

    db.session.delete(user)
    db.session.commit()
    flash(f"User {user.username} has been deleted.", "success")
    return redirect(url_for("admin.manage_users"))


@admin_bp.route("/posts")
@role_required(UserRole.MODERATOR, UserRole.ADMIN)
def manage_posts():
    page = request.args.get("page", 1, type=int)
    posts = db.paginate(
        db.select(Post).order_by(Post.date_posted.desc()), page=page, per_page=10
    )
    return render_template("admin/posts.html", posts=posts)



@admin_bp.route("/post/<int:post_id>/delete", methods=["POST"])
@role_required(UserRole.MODERATOR, UserRole.ADMIN)
def delete_post(post_id):
    post = db.session.get(Post, post_id) or abort(404)
    db.session.delete(post)
    db.session.commit()
    flash(f'Post "{post.title}" has been deleted.', "success")
    return redirect(url_for("admin.manage_posts"))





# 1. Manage Courses & Subjects
@admin_bp.route("/courses", methods=["GET", "POST"])
@role_required(UserRole.ADMIN)
def manage_courses():
    course_form = CourseForm()
    subject_form = SubjectForm()

    courses = db.session.scalars(db.select(Course).order_by(Course.name)).all()
    subject_form.course_id.choices = [(c.id, c.name) for c in courses]

    if "submit" in request.form and course_form.validate_on_submit():
        course = Course(
            name=course_form.name.data.strip(),
            duration_years=course_form.duration_years.data,
            description=course_form.description.data.strip() or "No description available",
        )
        db.session.add(course)
        db.session.commit()
        flash(f'Course "{course.name}" added!', "success")
        return redirect(url_for("admin.manage_courses"))

    return render_template(
        "admin/courses.html",
        course_form=course_form,
        subject_form=subject_form,
        courses=courses,
    )


@admin_bp.route("/subjects/add", methods=["POST"])
@role_required(UserRole.ADMIN)
def add_subject():
    subject_form = SubjectForm()
    courses = db.session.scalars(db.select(Course).order_by(Course.name)).all()
    subject_form.course_id.choices = [(c.id, c.name) for c in courses]

    if subject_form.validate_on_submit():
        subject = Subject(
            course_id=subject_form.course_id.data,
            code=subject_form.code.data.strip().upper(),
            name=subject_form.name.data.strip(),
            semester=subject_form.semester.data,
        )
        db.session.add(subject)
        db.session.commit()
        flash(f'Subject "{subject.code} - {subject.name}" added!', "success")
    else:
        for field, errors in subject_form.errors.items():
            for err in errors:
                flash(f"{field}: {err}", "danger")

    return redirect(url_for("admin.manage_courses"))


# 2. Enroll & View Students
@admin_bp.route("/students/enroll", methods=["GET", "POST"])
@role_required(UserRole.ADMIN)
def enroll_student():
    form = StudentEnrollmentForm()

    # Only list users who aren't already students or admins
    available_users = db.session.scalars(
        db.select(User).where(User.student_profile == None, User.role == UserRole.USER)
    ).all()
    form.user_id.choices = [(u.id, f"{u.username} ({u.email})") for u in available_users]

    courses = db.session.scalars(db.select(Course).order_by(Course.name)).all()
    form.course_id.choices = [(c.id, c.name) for c in courses]

    if form.validate_on_submit():
        user = db.session.get(User, form.user_id.data) or abort(404)
        user.role = UserRole.STUDENT  # Promote User role to STUDENT

        student = Student(
            user_id=user.id,
            course_id=form.course_id.data,
            roll_number=form.roll_number.data.strip(),
            full_name=form.full_name.data.strip(),
            batch_year=form.batch_year.data,
            phone=form.phone.data.strip() if form.phone.data else None,
        )
        db.session.add(student)
        db.session.commit()
        flash(f"Enrolled {student.full_name} ({student.roll_number})!", "success")
        return redirect(url_for("admin.manage_students"))

    return render_template("admin/enroll_student.html", form=form)




# 3. Mark Daily Attendance (Bulk by Subject & Date)
@admin_bp.route("/attendance", methods=["GET", "POST"])
@role_required(UserRole.MODERATOR, UserRole.ADMIN)
def mark_attendance():
    subjects = db.session.scalars(db.select(Subject).order_by(Subject.code)).all()
    selected_subject_id = request.args.get("subject_id", type=int) or (subjects[0].id if subjects else None)
    selected_date_str = request.args.get("date") or date.today().isoformat()
    selected_date = date.fromisoformat(selected_date_str)

    selected_subject = db.session.get(Subject, selected_subject_id) if selected_subject_id else None
    students = []
    existing_map = {}

    if selected_subject:
        students = db.session.scalars(
            db.select(Student)
            .filter_by(course_id=selected_subject.course_id, is_active=True)
            .order_by(Student.roll_number)
        ).all()
        existing_records = db.session.scalars(
            db.select(Attendance).filter_by(subject_id=selected_subject.id, date=selected_date)
        ).all()
        existing_map = {r.student_id: r for r in existing_records}

    if request.method == "POST" and selected_subject:
        present_ids = {int(sid) for sid in request.form.getlist("present_students")}

        for student in students:
            is_present = student.id in present_ids
            if student.id in existing_map:
                existing_map[student.id].is_present = is_present
            else:
                db.session.add(
                    Attendance(
                        student_id=student.id,
                        subject_id=selected_subject.id,
                        date=selected_date,
                        is_present=is_present,
                    )
                )

        db.session.commit()
        flash(f"Attendance saved for {selected_subject.code} on {selected_date}!", "success")
        return redirect(url_for("admin.mark_attendance", subject_id=selected_subject.id, date=selected_date_str))

    return render_template(
        "admin/mark_attendance.html",
        subjects=subjects,
        selected_subject=selected_subject,
        selected_date=selected_date_str,
        students=students,
        existing_map=existing_map,
    )


@admin_bp.route("/grades", methods=["GET", "POST"])
@role_required(UserRole.MODERATOR, UserRole.ADMIN)
def manage_grades():
    form = GradeForm()

    students = db.session.scalars(db.select(Student).order_by(Student.roll_number)).all()
    subjects = db.session.scalars(db.select(Subject).order_by(Subject.code)).all()

    form.student_id.choices = [(s.id, f"{s.roll_number} - {s.full_name} ({s.course.name})") for s in students]
    form.subject_id.choices = [(sub.id, f"{sub.code} - {sub.name}") for sub in subjects]

    if form.validate_on_submit():
        if form.marks_obtained.data > form.max_marks.data:
            flash("Marks obtained cannot exceed maximum marks.", "danger")
            return redirect(url_for("admin.manage_grades"))

        # Update existing grade if same student, subject, and exam_type exist
        existing_grade = db.session.scalar(
            db.select(Grade).filter_by(
                student_id=form.student_id.data,
                subject_id=form.subject_id.data,
                exam_type=form.exam_type.data,
            )
        )
        if existing_grade:
            existing_grade.marks_obtained = form.marks_obtained.data
            existing_grade.max_marks = form.max_marks.data
            flash("Existing grade updated!", "info")
        else:
            db.session.add(
                Grade(
                    student_id=form.student_id.data,
                    subject_id=form.subject_id.data,
                    exam_type=form.exam_type.data,
                    marks_obtained=form.marks_obtained.data,
                    max_marks=form.max_marks.data,
                )
            )
            flash("Grade recorded successfully!", "success")

        db.session.commit()
        return redirect(url_for("admin.manage_grades"))

    recent_grades = db.session.scalars(
        db.select(Grade).order_by(Grade.id.desc()).limit(15)
    ).all()

    return render_template("admin/grades.html", form=form, recent_grades=recent_grades)




@admin_bp.route("/students")
@role_required(UserRole.ADMIN)
def manage_students():
    page = request.args.get("page", 1, type=int)
    q = request.args.get("q", "", type=str).strip()
    selected_course_id = request.args.get("course_id", type=int)

    stmt = db.select(Student).join(User).order_by(Student.roll_number.asc())

    if q:
        stmt = stmt.where(
            db.or_(
                Student.roll_number.ilike(f"%{q}%"),
                Student.full_name.ilike(f"%{q}%"),
                User.email.ilike(f"%{q}%"),
            )
        )
    if selected_course_id:
        stmt = stmt.where(Student.course_id == selected_course_id)

    students = db.paginate(stmt, page=page, per_page=10)
    courses = db.session.scalars(db.select(Course).order_by(Course.name)).all()

    return render_template(
        "admin/students.html",
        students=students,
        courses=courses,
        q=q,
        selected_course_id=selected_course_id,
    )


@admin_bp.route("/student/<int:student_id>/toggle-status", methods=["POST"])
@role_required(UserRole.ADMIN)
def toggle_student_status(student_id):
    student = db.session.get(Student, student_id) or abort(404)
    student.is_active = not student.is_active
    db.session.commit()
    status_text = "activated" if student.is_active else "deactivated"
    flash(f"Student {student.full_name} ({student.roll_number}) has been {status_text}.", "info")
    return redirect(url_for("admin.manage_students"))


@admin_bp.route("/student/<int:student_id>/remove", methods=["POST"])
@role_required(UserRole.ADMIN)
def unenroll_student(student_id):
    student = db.session.get(Student, student_id) or abort(404)
    user = student.user
    user.role = UserRole.USER  # Revert role back to standard user
    db.session.delete(student)
    db.session.commit()
    flash(f"Removed student enrollment for {student.full_name}.", "success")
    return redirect(url_for("admin.manage_students"))
