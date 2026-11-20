from flask import Blueprint, flash, redirect, render_template, request, url_for

error_bp = Blueprint("error", __name__)


@error_bp.app_errorhandler(400)
def error_400(error):
    return render_template("errors/400.html"), 400


@error_bp.app_errorhandler(403)
def error_403(error):
    return render_template("errors/403.html"), 403


@error_bp.app_errorhandler(404)
def error_404(error):
    return render_template("errors/404.html"), 404


@error_bp.app_errorhandler(405)
def error_405(error):
    return render_template("errors/405.html"), 405

@error_bp.app_errorhandler(500)
def error_500(error):
    return render_template("errors/500.html"), 500




@error_bp.app_errorhandler(413)
def error_413(error):
    flash("File is too large! Maximum upload size is 10MB.", "danger")
    return redirect(request.referrer or url_for("users.account"))
