import os
from flask import Blueprint,current_app, json, jsonify, render_template, redirect, request, flash, url_for, abort
from flask_login import login_required, current_user
from functools import wraps
from .models import Course, db
from werkzeug.utils import secure_filename

admin = Blueprint('admin', __name__, url_prefix='/admin')

# decorator to restrict access to admins only
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not getattr(current_user, "is_admin", False):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@admin.route('/') # route to admin dashboard, only accessible through '/admin'
@login_required
@admin_required
def dashboard():
    courses = Course.query.order_by(Course.order).all()
    return render_template("admin/dashboard.html", user=current_user, courses=courses)

@admin.route('admin/add_course', methods=['POST'])
@login_required
@admin_required
def add_course():
    course_name = request.form.get('course_name')
    month = request.form.get('month')
    order = request.form.get('order')
    description = request.form.get('description')
    
    # Check if image was uploaded
    if 'image_file' in request.files:
        image_file = request.files['image_file']
        
        # Check if the file has a name (was actually uploaded)
        if image_file.filename != '':
            filename = secure_filename(image_file.filename)
            # Create the upload path
            upload_folder = os.path.join(current_app.static_folder, 'uploads', 'course_thumbnails')
            os.makedirs(upload_folder, exist_ok=True)
            
            # Save the file
            file_path = os.path.join(upload_folder, filename)
            image_file.save(file_path)
            
            # Store the URL for the database (relative path from static folder)
            image_url = f'/static/uploads/course_thumbnails/{filename}'
        else:
            image_url = None
    else:
        image_url = None

    new_course = Course(
        course_name=course_name,
        month=month,
        order=int(order),
        description=description,
        image_url=image_url
    )
    db.session.add(new_course)
    db.session.commit()
    flash('Course added successfully!', 'success')
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

@admin.route('/edit-course/<int:course_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_course(course_id):
    course = Course.query.get_or_404(course_id)

    if request.method == 'POST':
        course.course_name = request.form['course_name']
        course.description = request.form['description']
        course.month = request.form['month']
        course.is_locked = 'is_locked' in request.form
        course.order = request.form['order']
        
        # Handle image upload
        if 'image_file' in request.files:
            image_file = request.files['image_file']
            if image_file.filename != '':
                filename = secure_filename(image_file.filename)
                upload_folder = os.path.join(current_app.static_folder, 'uploads', 'course_thumbnails')
                os.makedirs(upload_folder, exist_ok=True)
                file_path = os.path.join(upload_folder, filename)
                image_file.save(file_path)
                course.image_url = f'/static/uploads/course_thumbnails/{filename}'

        db.session.commit()
        flash('Course updated successfully!', category='success')
        return redirect(url_for('admin.dashboard'))

    return render_template('admin/edit_course.html', user=current_user, course=course)