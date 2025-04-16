from flask import Blueprint, json, jsonify, render_template, redirect, request, flash, url_for, abort
from flask_login import login_required, current_user
from functools import wraps
from .models import Course, db

admin = Blueprint('admin', __name__, url_prefix='/admin')

# decorator to restrict access to admins only
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not getattr(current_user, "is_admin", False):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@admin.route('/') # route to admin dashboard, only accessible through /admin
@login_required
@admin_required
def dashboard():
    courses = Course.query.order_by(Course.order).all()
    return render_template("admin/dashboard.html", user=current_user, courses=courses)

@admin.route('/add-course', methods=['POST']) # admin can add courses here
@login_required
@admin_required
def add_course():
    course = Course(
        course_name=request.form.get('course_name'),
        description=request.form.get('description'),
        month=request.form.get('month'),
        order=int(request.form.get('order')),
        image_url=request.form.get('image_url'),
        is_locked=False
    )
    db.session.add(course)
    db.session.commit()
    flash("Course added successfully!", category="success")
    return redirect(url_for('admin.dashboard'))

@admin.route('/delete-course', methods=['POST'])
@login_required
@admin_required
def delete_course():
    data = json.loads(request.data)
    course_id = data['courseId']
    course = Course.query.get(course_id)
    if course:
        db.session.delete(course)
        db.session.commit()
        flash("Course deleted!", category="success")
    return jsonify({})
