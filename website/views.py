#user's view pages
import os
from flask import Blueprint, redirect, url_for,render_template, flash, request,jsonify,current_app
from flask_login import login_required, current_user
from .models import db,CourseSchedule,UserSchedule,UserTask, CourseContent, LessonProgress, Comment, Course, Posts, Tag, Upvote, Problem, ProblemComment, ProblemUpvote, post_tags
import json
from werkzeug.utils import secure_filename
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta


views = Blueprint('views', __name__)
# this formula is used to calculate the score of the posts, it is used to sort the posts in the main page, credit to reddit for the formula
# the score is calculated based on the number of upvotes, comments, and the age of the post
# Formula: score = (upvotes + 2 * comments) / ((age_in_hours + 2) ** gravity)
# gravity is a constant that determines how quickly the score decreases with age
def calculate_post_score(post, gravity=1.8):  # Increased gravity
    upvotes = len(post.upvotes)
    comments = len(post.comments)
    age_in_seconds = (datetime.utcnow() - post.timestamp).total_seconds()
    age_in_hours = age_in_seconds / 3600
    
    # Base score from interactions
    interaction_score = (upvotes + 2 * comments)
    
    # Time decay factor
    time_decay = pow((age_in_hours + 2), gravity)
    
    # Newer posts get a boost
    recency_boost = 1.0
    if age_in_hours < 24:  # Posts less than 24 hours old
        recency_boost = 2.0
    elif age_in_hours < 72:  # Posts less than 3 days old
        recency_boost = 1.5
    
    score = (interaction_score * recency_boost) / time_decay
    return score
# this formula use the same logic with main post score calculations, used to sort the problems in the problems page
def calculate_problem_score(problem, gravity=1.3):
    upvotes = problem.upvotes.count()
    comments = problem.comments.count()
    age_in_seconds = (datetime.utcnow() - problem.timestamp).total_seconds()
    age_in_hours = age_in_seconds / 3600
    score = (upvotes + 2 * comments) / ((age_in_hours + 2) ** gravity)
    return score

#home page, get n post would be used for later
@views.route('/home', methods=['GET', 'POST'])
def landing():
    courses = Course.query.filter_by(is_locked=False).order_by(Course.order).limit(3).all() #only letting guests see 3 of the courses
    posts = Posts.query.filter_by(is_locked=False).order_by(Posts.likes).limit(5).all() #only letting guests see 5 preview posts
    return render_template("home.html", user=current_user, courses = courses, posts = posts)


#main website, the bread and butter stuffs here
@views.route('/')
@login_required
def main():
    sort_by = request.args.get('sort_by', 'upvotes')  # Default sort by upvotes
    
    # always filter by approved posts and use joinedload for efficiency
    approved_posts = Posts.query.options(
        joinedload(Posts.comments), 
        joinedload(Posts.upvotes)
    ).filter_by(is_approved=True).all()
    
    # sort based on user preference
    if sort_by == 'recent':
        approved_posts.sort(key=lambda post: post.timestamp, reverse=True)
    else:  # default
        approved_posts.sort(key=lambda post: calculate_post_score(post), reverse=True)
    
    return render_template("main.html", posts=approved_posts, sort_by=sort_by)
#comments for posts
@views.route('/post/<int:post_id>', methods=['GET', 'POST'])
@login_required
def post_detail(post_id):
    post = Posts.query.get_or_404(post_id)
    comments = Comment.query.filter_by(post_id=post_id).order_by(Comment.timestamp.desc()).all()

    if request.method == 'POST':
        content = request.form.get('comment_content', '').strip()

        if not content:
            flash("Comment cannot be empty!", category="error")
        else:
            comment = Comment(content=content, user_id=current_user.id, post_id=post.id)
            db.session.add(comment)
            db.session.commit()
            flash("Comment added successfully!", category="success")
            return redirect(url_for('views.main', post_id=post.id))  # refresh to avoid re-POSTing on refresh

    return render_template('post_detail.html', post=post, comments=comments, user=current_user)

# courses route
@views.route('/main/courses')
@login_required
def main_courses():
    courses = Course.query.order_by(Course.order).all()  # fetch all courses in order
    return render_template("courses.html", user=current_user, courses=courses)


@views.route('/main/problems')  # problems forum
@login_required
def problems():
    sort_by = request.args.get('sort_by', 'recent')  # Default sort by recent

    # Fetch all approved problems
    approved_problems = Problem.query.filter_by(is_approved=True).all()

    #sort based on user preference
    if sort_by == 'upvotes':
        approved_problems.sort(key=lambda problem: calculate_problem_score(problem), reverse=True)
    else:  #default to sorting by recent
        approved_problems.sort(key=lambda problem: problem.timestamp, reverse=True)

    return render_template("problems.html", problems=approved_problems, sort_by=sort_by)

@views.route('/problem/<int:problem_id>', methods=['GET', 'POST']) #show details of the questions like replies and upvotes
@login_required
def problem_detail(problem_id):
    problem = Problem.query.get_or_404(problem_id)
    comments = ProblemComment.query.filter_by(problem_id=problem_id).order_by(ProblemComment.timestamp.desc()).all()

    if request.method == 'POST':
        content = request.form.get('comment_content', '').strip()

        if not content:
            flash("Comment cannot be empty!", category="error")
        else:
            comment = ProblemComment(content=content, user_id=current_user.id, problem_id=problem.id)
            db.session.add(comment)
            db.session.commit()
            flash("Comment added successfully!", category="success")
            return redirect(url_for('views.problem_detail', problem_id=problem.id))

    return render_template('problem_detail.html', problem=problem, comments=comments, user=current_user)

# create a question route
@views.route('/main/create_problem', methods=['GET', 'POST'])
@login_required
def create_problem():
    if request.method == "POST":
        title = request.form.get('post_title')
        content = request.form.get('content')
        raw_tags = request.form.get('tags')
        image_file = request.files.get('image_file')

        tags_list = []
        if raw_tags:
            tag_names = raw_tags.strip().split()
            for name in tag_names:
                cleaned_name = name.strip("#").lower()
                tag = Tag.query.filter_by(name=cleaned_name).first()
                if not tag:
                    tag = Tag(name=cleaned_name)
                    db.session.add(tag)
                tags_list.append(tag)

        image_url = None
        if image_file:
            filename = secure_filename(image_file.filename)
            upload_path = os.path.join(current_app.root_path, 'static/uploads', filename)
            os.makedirs(os.path.dirname(upload_path), exist_ok=True)
            image_file.save(upload_path)
            image_url = f'/static/uploads/{filename}'

        problem = Problem(
            title=title,
            description=content,  
            tags=tags_list,  
            image_url=image_url,
            user_id=current_user.id, 
            is_approved=False
        )
        db.session.add(problem)
        db.session.commit()
        flash('Question created! Your question will be moderated by admin before it is here!', category='success')
        return redirect(url_for('views.problems'))
    
    return render_template("create_problem.html", user=current_user)  # Added template rendering

# problem_upvote route
@views.route('/problem_upvote', methods=['POST'])
@login_required
def problem_upvote():
    problem_id = request.json.get('problem_id')
    problem = Problem.query.get_or_404(problem_id)

    existing_vote = ProblemUpvote.query.filter_by(user_id=current_user.id, problem_id=problem_id).first()
    if existing_vote:
        db.session.delete(existing_vote)
        db.session.commit()
        db.session.refresh(problem)
        return jsonify({'message': 'Unvoted', 'upvotes': problem.upvotes.count()})
    else:
        vote = ProblemUpvote(user_id=current_user.id, problem_id=problem_id)
        db.session.add(vote)
        db.session.commit()
        return jsonify({'message': 'Upvoted', 'upvotes': problem.upvotes.count()})

@views.route('/main/courses/<int:course_id>') # showing course details, depending on what the user choose
@login_required
def course_detail(course_id):
    course = Course.query.get_or_404(course_id)
    return render_template('course_detail.html', user=current_user, course=course)

# users can create them posts here, as long as they are logged in ofc
@views.route('/main/create_post', methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        title = request.form.get('post_title')
        content = request.form.get('content')
        raw_tags = request.form.get('tags')
        image_file = request.files.get('image_file')

        tags_list = []
        if raw_tags:
            tag_names = raw_tags.strip().split()
            for name in tag_names:
                cleaned_name = name.strip("#").lower()
                tag = Tag.query.filter_by(name=cleaned_name).first()
                if not tag:
                    tag = Tag(name=cleaned_name)
                    db.session.add(tag)
                tags_list.append(tag)

        image_url = None
        if image_file:
            filename = secure_filename(image_file.filename)
            upload_path = os.path.join(current_app.root_path, 'static/uploads', filename)
            os.makedirs(os.path.dirname(upload_path), exist_ok=True)
            image_file.save(upload_path)
            image_url = f'/static/uploads/{filename}'

        post = Posts(
            post_title=title,
            content=content,
            tags=tags_list,  
            image_url=image_url,
            author=current_user,
            is_approved=False
        )
        db.session.add(post)
        db.session.commit()
        flash('Post created! Your post will be moderated by admin before it is here!', category='success')
        return redirect(url_for('views.main'))

    return render_template("create_post.html", user=current_user)

@views.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        image_file = request.files.get('user_image')

        if image_file:
            filename = secure_filename(image_file.filename)
            upload_folder = os.path.join(current_app.root_path, 'static/uploads/user_images')
            os.makedirs(upload_folder, exist_ok=True)
            image_path = os.path.join(upload_folder, filename)
            image_file.save(image_path)

            current_user.user_image = f'/static/uploads/user_images/{filename}'
            db.session.commit()
            flash('Profile picture updated!', 'success')
            return redirect(url_for('views.edit_profile'))

    return render_template("edit_profile.html", user=current_user)

@views.route('/upvote', methods=['POST'])
@login_required
def upvote_post():
    post_id = request.json.get('post_id')  # Accept ID from JSON body
    post = Posts.query.get_or_404(post_id)

    existing_vote = Upvote.query.filter_by(user_id=current_user.id, post_id=post_id).first()
    if existing_vote:
        db.session.delete(existing_vote)
        db.session.commit()
        db.session.refresh(post)
        return jsonify({'message': 'Unvoted', 'upvotes': len(post.upvotes)})
    else:
        vote = Upvote(user_id=current_user.id, post_id=post_id)
        db.session.add(vote)
        db.session.commit()
        return jsonify({'message': 'Upvoted', 'upvotes': len(post.upvotes)})

@views.route('/search')
def search():
    # 1. Get the tag from the query parameter
    tag_query = request.args.get('tag', '').strip().lower()  # Default is empty string if missing

    # 2. If the tag is empty, return to main with a message
    if not tag_query:
        flash("Please enter a tag to search.", category="error")
        return redirect(url_for('views.main'))

    # 3. Filter posts where the tag exists in the tags field (assuming tags is a comma-separated string)
    # Note: I use ilike for case-insensitive partial matching
    matching_posts = Posts.query \
        .join(post_tags) \
        .join(Tag) \
        .filter(Tag.name.ilike(f"%{tag_query}%")) \
        .all()
    # 4. Sort posts by:
    #    - Number of upvotes (descending)
    #    - Timestamp (descending) as a tiebreaker
    matching_posts.sort(key=lambda post: (len(post.upvotes), post.timestamp), reverse=True)

    # 5. Render a search results page
    return render_template("search_results.html", posts=matching_posts, search_tag=tag_query)

@views.route('/delete_post')
@login_required
def delete_post_page():
    # Show only posts by current user
    user_posts = Posts.query.filter_by(user_id=current_user.id).order_by(Posts.timestamp.desc()).all()
    return render_template("delete_post.html", posts=user_posts)

# Route to handle actual deletion
@views.route('/delete_post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Posts.query.get_or_404(post_id)
    
    # Ensure the current user owns the post
    if post.user_id != current_user.id:
        flash("You are not authorized to delete this post.", category="error")
        return redirect(url_for('views.delete_post_page'))
    
    # delete upvotes, comments associated with the post before deleting the post
    upvotes = Upvote.query.filter_by(post_id=post_id).all()
    for upvote in upvotes:
        db.session.delete(upvote)

    comments = Comment.query.filter_by(post_id=post_id).all()
    for comment in comments:
        db.session.delete(comment) 
    
    # delete the post
    db.session.delete(post)
    db.session.commit()
    
    flash("Post deleted successfully!", category="success")
    return redirect(url_for('views.delete_post_page'))

@views.route('main/tools')
@login_required
def tools():
    return render_template("tools.html", user=current_user)

@views.route('/lesson/<int:lesson_id>', methods=['GET', 'POST'])
@login_required
def lesson_view(lesson_id):
    lesson = CourseContent.query.get_or_404(lesson_id)
    progress = LessonProgress.query.filter_by(
        user_id=current_user.id,
        lesson_id=lesson_id
    ).first()
    
    if not progress:
        progress = LessonProgress(user_id=current_user.id, lesson_id=lesson_id)
        db.session.add(progress)
    
    progress.last_accessed = datetime.utcnow()
    db.session.commit()
    
    return render_template(
        'lesson_view.html',
        lesson=lesson,
        progress=progress,
        user=current_user
    )

@views.route('/mark_lesson_complete/<int:lesson_id>', methods=['POST'])
@login_required
def mark_lesson_complete(lesson_id):
    progress = LessonProgress.query.filter_by(
        user_id=current_user.id,
        lesson_id=lesson_id
    ).first()
    
    if not progress:
        progress = LessonProgress(user_id=current_user.id, lesson_id=lesson_id)
        db.session.add(progress)
    
    progress.completed = True
    db.session.commit()
    
    return jsonify({'status': 'success'})
