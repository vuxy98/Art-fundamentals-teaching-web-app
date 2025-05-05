import os
from flask import Blueprint,current_app, json, jsonify, render_template, redirect, request, flash, url_for, abort
from flask_login import login_required, current_user
from functools import wraps
from .models import CourseContent, Course, db
from werkzeug.utils import secure_filename
from .models import Posts
import re

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
    
    # check if image was uploaded
    if 'image_file' in request.files:
        image_file = request.files['image_file']
        
        # check if the file has a name (was actually uploaded)
        if image_file.filename != '':
            filename = secure_filename(image_file.filename)
            # create the upload path
            upload_folder = os.path.join(current_app.static_folder, 'uploads', 'course_thumbnails')
            os.makedirs(upload_folder, exist_ok=True)
            
            # save the file
            file_path = os.path.join(upload_folder, filename)
            image_file.save(file_path)
            
            # store the URL for the database (relative path from static folder)
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
# deleting course will redirect you here
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
# editing course
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
        
        # handle image upload
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

# admin will be moderating user posts before they are shown
@admin.route('/moderate_posts')
@login_required
def moderate_posts():
    if not current_user.is_admin:
        abort(403)
    pending_posts = Posts.query.filter_by(is_approved=False).all()
    return render_template("moderate_posts.html", posts=pending_posts)

@admin.route('/admin/approve_post/<int:post_id>')
@login_required
def approve_post(post_id):
    if not current_user.is_admin:
        abort(403)
    post = Posts.query.get_or_404(post_id)
    post.is_approved = True
    db.session.commit()
    flash('Post approved!', 'success')
    return redirect(url_for('admin.moderate_posts'))

@admin.route('/admin/delete_post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    if not current_user.is_admin:
        abort(403)
    post = Posts.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash('Post deleted.', 'danger')
    return redirect(url_for('admin.moderate_posts'))

def convert_youtube_url_to_embed(url):
    """Convert regular YouTube URL to embed URL"""
    match = re.match(r'.*youtu(?:\.be/|be\.com/watch\?v=)([\w-]+)', url)
    if match:
        video_id = match.group(1)
        return f'https://www.youtube.com/embed/{video_id}'
    return url  # return original if pattern not matched

@admin.route('/course/<int:course_id>/add_lesson', methods=['GET', 'POST'])
@login_required
@admin_required
def add_lesson(course_id):
    course = Course.query.get_or_404(course_id)

    if request.method == 'POST':
        title = request.form['title']
        text = request.form['text']
        video_url = request.form.get('video_url')
        order = request.form.get('order', 0)

        try:
            order = int(order)
        except ValueError:
            flash("Order must be a number.", "danger")
            return redirect(request.url)

        # convert ytb URL
        if video_url:
            video_url = convert_youtube_url_to_embed(video_url)

        lesson = CourseContent(
            title=title,
            text=text,
            video_url=video_url if video_url else None,
            order=order,
            course=course
        )
        db.session.add(lesson)
        db.session.commit()
        flash('Lesson added!', 'success')
        return redirect(url_for('admin.dashboard'))

    return render_template('admin/add_lesson.html', user=current_user, course=course)