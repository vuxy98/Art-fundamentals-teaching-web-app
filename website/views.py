#user's view pages
from flask import Blueprint,render_template, flash, request,jsonify
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
    return render_template("main.html", user=current_user)

@views.route('/main/courses')
@login_required
def main_courses():
    courses = Course.query.order_by(Course.order).all()  # fetch all courses in order
    return render_template("courses.html", user=current_user, courses=courses)

@views.route('/main/stream')#guests should be able to see this, but can't interact unless they are logged in
@login_required
def main_mainstream():
    return render_template("mainstream.html", user=current_user)

@views.route('/main/problems')#problems forum
@login_required
def main_problems():
    return render_template("problems.html", user=current_user)


@views.route('/main/tools')#tools like white board, 3d custom pose, etc
@login_required
def main_tools():
    return render_template("tools.html", user=current_user)

