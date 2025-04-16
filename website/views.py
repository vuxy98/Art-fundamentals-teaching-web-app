#user's view pages
from flask import Blueprint, redirect, url_for,render_template, flash, request,jsonify
from flask_login import login_required, current_user
from .models import db, Course, Posts
import json

views = Blueprint('views', __name__)
#home page, get n post would be used for later
@views.route('/', methods=['GET', 'POST'])
def landing():
    courses = Course.query.filter_by(is_locked=False).order_by(Course.order).limit(3).all() #only letting guests see 3 of the courses
    posts = Posts.query.filter_by(is_locked=False).order_by(Posts.likes).limit(5).all() #only letting guests see 5 preview posts
    return render_template("home.html", user=current_user, courses = courses, posts = posts)


#main website, the bread and butter stuffs here
@views.route('/main')
@login_required
def main():
    posts = Posts.query.order_by(Posts.timestamp.desc()).all()
    return render_template('main.html', posts=posts, user=current_user)

@views.route('/main/courses')
@login_required
def main_courses():
    courses = Course.query.order_by(Course.order).all()  # fetch all courses in order
    return render_template("courses.html", user=current_user, courses=courses)


@views.route('/main/problems')#problems forum
@login_required
def main_problems():
    return render_template("problems.html", user=current_user)


@views.route('/main/tools')#tools like white board, 3d custom pose, etc
@login_required
def main_tools():
    return render_template("tools.html", user=current_user)

@views.route('/main/courses/<int:course_id>')
@login_required
def course_detail(course_id):
    course = Course.query.get_or_404(course_id)
    return render_template('course_detail.html', user=current_user, course=course)

# users can create them posts here, as long as they are logged in ofc
@views.route('/main/create-post', methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        title = request.form.get('post_title')
        content = request.form.get('content')
        image_url = request.form.get('image_url')
        tags = request.form.get('tags')
        # check for eligible post
        if not title or not content:
            flash('Post must have a title and content.', category='error')
        else:
            new_post = Posts(
                post_title=title,
                content=content,
                image_url=image_url,
                tags=tags,
                user_id=current_user.id
            )
            db.session.add(new_post)
            db.session.commit()
            flash('Post created!', category='success')
            return redirect(url_for('views.main'))

    return render_template("create_post.html", user=current_user)
