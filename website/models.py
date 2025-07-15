#database models
from datetime import datetime
from website import db
from flask_login import UserMixin
from sqlalchemy.sql import func

#------------------------------------------------------------------------------------------------------------------------
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    email = db.Column(db.String(150), unique = True)
    password = db.Column(db.String(150))
    posts = db.relationship('Posts', backref='author', lazy=True) # user's posts
    username = db.Column(db.String(150), unique=True, nullable=False)  # renamed from first_name
    user_image = db.Column(db.String(300), nullable=True)  # path to profile image
    is_admin = db.Column(db.Boolean, default=False) # check to see if this is an admin or not
    lesson_progress = db.relationship('LessonProgress', backref='user', lazy=True) #user's lesson progress, tracked by watching the tutorial video in the lesson
#------------------------------------------------------------------------------------------------------------------------
class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_name = db.Column(db.String(100), unique=True)
    description = db.Column(db.Text)
    month = db.Column(db.String(20))  # e.g., 'January'
    is_locked = db.Column(db.Boolean, default=True)  # guest-lock
    image_url = db.Column(db.String(200))  # thumbnail for the course
    order = db.Column(db.Integer, unique=True)  # sort by month or course order

class CourseContent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)

    title = db.Column(db.String(100), nullable=False)
    text = db.Column(db.Text)  # description, notes, etc.
    video_url = db.Column(db.String(300))  # YouTube video link
    order = db.Column(db.Integer)  # order the contents like Lesson 1, Lesson 2...

    course = db.relationship('Course', backref=db.backref('contents', lazy=True, cascade="all, delete"))

#association table for tags and posts
post_tags = db.Table('post_tags',
    db.Column('post_id', db.Integer, db.ForeignKey('posts.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)
#lesson progress model to track user's progress in each lesson
class LessonProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    lesson_id = db.Column(db.Integer, db.ForeignKey('course_content.id'))
    completed = db.Column(db.Boolean, default=False)
    last_accessed = db.Column(db.DateTime, default=datetime.utcnow)
    watch_time = db.Column(db.Integer, default=0)  # Store time spent in seconds
    notes = db.Column(db.Text, nullable=True)  # Optional user notes
#------------------------------------------------------------------------------------------------------------------------
problem_tags = db.Table('problem_tags',
    db.Column('problem_id', db.Integer, db.ForeignKey('problem.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

class Problem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(300), nullable=True)
    is_approved = db.Column(db.Boolean, default=False)

    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='problems')
    tags = db.relationship('Tag', secondary=problem_tags, backref='problems')

    upvotes = db.relationship('ProblemUpvote', backref='problem', lazy='dynamic')
    comments = db.relationship('ProblemComment', backref='problem', lazy='dynamic')

class Posts(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    post_title = db.Column(db.String(150))
    timestamp = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # who posted it
    image_url = db.Column(db.String(300))  # the artwork (if it's an image post)
    content = db.Column(db.Text)  # description/caption
    likes = db.Column(db.Integer, default=0) # likes/upvotes, for sorting posts
    tags = db.relationship('Tag', secondary=post_tags, backref='posts')
    is_locked = db.Column(db.Boolean, default=True)
    is_approved = db.Column(db.Boolean, default=False) # check for a post to see if its approved or not
    comments = db.relationship('Comment', backref='post', lazy=True)  # link comments to the post
# tags of posts will be seperated to prevent issues like onlly 1 tag for each post
class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
            
    def __repr__(self):
        return f'<Tag {self.name}>'
#------------------------------------------------------------------------------------------------------------------------    
class Upvote(db.Model): # posts upvote
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)

    user = db.relationship('User', backref='upvotes')
    post = db.relationship('Posts', backref='upvotes')

    #This table tracks each upvote as a combination of a user and a post. The unique constraint ensures that one user can upvote a post only once.
    __table_args__ = (
        db.UniqueConstraint('user_id', 'post_id', name='unique_user_post_upvote'),
    )

class ProblemUpvote(db.Model): #problems upvote
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    problem_id = db.Column(db.Integer, db.ForeignKey('problem.id'), nullable=False)

    __table_args__ = (db.UniqueConstraint('user_id', 'problem_id', name='unique_user_problem_upvote'),)
#------------------------------------------------------------------------------------------------------------------------
class Comment(db.Model): #posts comments
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)  # comment text
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  # when the comment was made  

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False) 
    
# display user info on comments
    user = db.relationship('User', backref='comments')

class ProblemComment(db.Model): #problems comment
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    problem_id = db.Column(db.Integer, db.ForeignKey('problem.id'), nullable=False)

    user = db.relationship('User', backref='problem_comments')

#------------------------------------------------------------------------------------------------------------------------
# schedule stuffs here
class CourseSchedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    title = db.Column(db.String(100))
    description = db.Column(db.Text)
    duration_weeks = db.Column(db.Integer)
    created_by_admin = db.Column(db.Boolean, default=True)
    
    # Relationships
    tasks = db.relationship('ScheduleTask', backref='schedule', cascade='all, delete')
    course = db.relationship('Course', backref='schedules')

class ScheduleTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    schedule_id = db.Column(db.Integer, db.ForeignKey('course_schedule.id'))
    title = db.Column(db.String(100))
    description = db.Column(db.Text)
    day_number = db.Column(db.Integer)  # 1-7 week days
    week_number = db.Column(db.Integer)
    duration_minutes = db.Column(db.Integer)
    lesson_id = db.Column(db.Integer, db.ForeignKey('course_content.id'), nullable=True)
    
    # Optional link to specific lesson
    lesson = db.relationship('CourseContent')

class UserSchedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    base_schedule_id = db.Column(db.Integer, db.ForeignKey('course_schedule.id'))
    title = db.Column(db.String(100))
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    tasks = db.relationship('UserTask', backref='schedule', cascade='all, delete')
    user = db.relationship('User', backref='schedules')
    base_schedule = db.relationship('CourseSchedule')

class UserTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_schedule_id = db.Column(db.Integer, db.ForeignKey('user_schedule.id'))
    title = db.Column(db.String(100))
    description = db.Column(db.Text)
    planned_date = db.Column(db.DateTime)
    completed = db.Column(db.Boolean, default=False)
    completed_date = db.Column(db.DateTime, nullable=True)
    duration_minutes = db.Column(db.Integer)
    lesson_id = db.Column(db.Integer, db.ForeignKey('course_content.id'), nullable=True)
    
    # Optional link to specific lesson 
    lesson = db.relationship('CourseContent')
