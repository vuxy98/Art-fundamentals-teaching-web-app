import os
from flask import Blueprint, current_app, json, jsonify, render_template, redirect, request, flash, url_for, abort
from flask_login import login_required, current_user
from functools import wraps
from .models import CourseContent, Course, db, Posts, Problem
from werkzeug.utils import secure_filename
import re

admin = Blueprint('admin', __name__, url_prefix='/admin')

# Decorator to restrict access to admins only
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not getattr(current_user, "is_admin", False):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

# Admin dashboard
@admin.route('/')
@login_required
@admin_required
def dashboard():
    courses = Course.query.order_by(Course.order).all()
    return render_template("admin/dashboard.html", user=current_user, courses=courses)

# add a new course
@admin.route('/add_course', methods=['POST'])
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
        if image_file.filename != '':
            filename = secure_filename(image_file.filename)
            upload_folder = os.path.join(current_app.static_folder, 'uploads', 'course_thumbnails')
            os.makedirs(upload_folder, exist_ok=True)
            file_path = os.path.join(upload_folder, filename)
            image_file.save(file_path)
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

# Delete a course
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

# Edit a course
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

# Add a lesson to a course
# Convert YouTube URL to embed format
def convert_youtube_url_to_embed(url):
    match = re.match(r'.*youtu(?:\.be/|be\.com/watch\?v=)([\w-]+)', url)
    if match:
        video_id = match.group(1)
        return f'https://www.youtube.com/embed/{video_id}'
    return url

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

        # Convert YouTube URL
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

#delete lesson from a course
@admin.route('/course/<int:course_id>/delete_lesson', methods=['POST'])
@login_required
@admin_required
def delete_lesson(course_id):
    data = json.loads(request.data)
    lesson_id = data.get('lessonId')
    lesson = CourseContent.query.get(lesson_id)

    if lesson:
        db.session.delete(lesson)
        db.session.commit()
        flash('Lesson deleted successfully!', 'success')
    else:
        flash('Lesson not found.', 'danger')

    return jsonify({})


# moderation page for posts and problems
@admin.route('/moderate')
@login_required
@admin_required
def moderate():
    moderation_type = request.args.get('type', 'posts')  # default to posts
    sort_by = request.args.get('sort_by', 'newest')  # default to newest

    if moderation_type == 'posts':
        items = Posts.query.filter_by(is_approved=False).all()
        if sort_by == 'newest':
            items.sort(key=lambda post: post.timestamp, reverse=True)
        elif sort_by == 'oldest':
            items.sort(key=lambda post: post.timestamp, reverse=False)
    elif moderation_type == 'problems':
        items = Problem.query.filter_by(is_approved=False).all()
        if sort_by == 'newest':
            items.sort(key=lambda problem: problem.timestamp, reverse=True)
        elif sort_by == 'oldest':
            items.sort(key=lambda problem: problem.timestamp, reverse=False)
    else:
        items = []

    return render_template('admin/moderate.html', items=items, moderation_type=moderation_type, sort_by=sort_by)

# approve a post
@admin.route('/approve-post', methods=['POST'])
@login_required
@admin_required
def approve_post():
    data = request.get_json()
    post_id = data.get('id')
    post = Posts.query.get(post_id)
    if post:
        post.is_approved = True
        db.session.commit()
        return jsonify({'message': 'Post approved successfully!'}), 200
    return jsonify({'error': 'Post not found'}), 404

# reject a post
@admin.route('/reject-post', methods=['POST'])
@login_required
@admin_required
def reject_post():
    data = request.get_json()
    post_id = data.get('id')
    post = Posts.query.get(post_id)
    if post:
        db.session.delete(post)
        db.session.commit()
        return jsonify({'message': 'Post rejected successfully!'}), 200
    return jsonify({'error': 'Post not found'}), 404

# approve a problem
@admin.route('/approve-problem', methods=['POST'])
@login_required
@admin_required
def approve_problem():
    data = request.get_json()
    problem_id = data.get('id')
    problem = Problem.query.get(problem_id)
    if problem:
        problem.is_approved = True
        db.session.commit()
        return jsonify({'message': 'Problem approved successfully!'}), 200
    return jsonify({'error': 'Problem not found'}), 404

# reject a problem
@admin.route('/reject-problem', methods=['POST'])
@login_required
@admin_required
def reject_problem():
    data = request.get_json()
    problem_id = data.get('id')
    problem = Problem.query.get(problem_id)
    if problem:
        db.session.delete(problem)
        db.session.commit()
        return jsonify({'message': 'Problem rejected successfully!'}), 200
    return jsonify({'error': 'Problem not found'}), 404