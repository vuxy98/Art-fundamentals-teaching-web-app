#database models
from website import db
from flask_login import UserMixin
from sqlalchemy.sql import func

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    email = db.Column(db.String(150), unique = True)
    password = db.Column(db.String(150))
    posts = db.relationship('Posts', backref='author', lazy=True) # user's posts
    username = db.Column(db.String(150), unique=True, nullable=False)  # renamed from first_name
    user_image = db.Column(db.String(300), nullable=True)  # path to profile image
    is_admin = db.Column(db.Boolean, default=False) # check to see if this is an admin or not

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_name = db.Column(db.String(100), unique=True)
    description = db.Column(db.Text)
    month = db.Column(db.String(20))  # e.g., 'January'
    is_locked = db.Column(db.Boolean, default=True)  # guest-lock
    image_url = db.Column(db.String(200))  # thumbnail for the course
    order = db.Column(db.Integer, unique=True)  # sort by month or course order

#association table for tags and posts
post_tags = db.Table('post_tags',
    db.Column('post_id', db.Integer, db.ForeignKey('posts.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

class Posts(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    post_title = db.Column(db.String(150))
    timestamp = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # who posted it
    image_url = db.Column(db.String(300))  # link to the artwork (if it's an image post)
    content = db.Column(db.Text)  # description/caption
    likes = db.Column(db.Integer, default=0) # likes/upvotes, for sorting posts
    tags = db.relationship('Tag', secondary=post_tags, backref='posts')
    is_locked = db.Column(db.Boolean, default=True)
    is_approved = db.Column(db.Boolean, default=False) # check for a post to see if its approved or not
# tags of posts will be seperated to prevent issues like onlly 1 tag for each post
class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f'<Tag {self.name}>'