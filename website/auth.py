#authentication stuffs
from flask import Blueprint, render_template, request,flash,redirect, url_for
from .models import User
from werkzeug.security import generate_password_hash, check_password_hash
from website import db
from flask_login import login_user, login_required, logout_user, current_user

auth = Blueprint('auth', __name__)

@auth.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                flash('You are now logged in!', category='success')
                login_user(user, remember=True)
                return render_template("main.html")
            else:
                flash('Incorrect password, please try again', category='error')
        else:
            flash('Incorrect email, please try again', category='error')

    return render_template("login.html", user=current_user)

@auth.route("/logout", methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash('You have been logged out!', category='success')
    return redirect(url_for('auth.login'))

@auth.route("/register", methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('firstName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already registered!', category='error')
        elif len(email) < 4:
            flash('Your email must be longer than 4 characters', category='error')
        elif len(first_name) < 2:
            flash('Your first name must be longer than 1 characters', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match', category='error' )
        elif len(password1) < 7:
            flash('Password must be longer than 6 characters', category='error')
            
        else:
           new_user = User(email=email, first_name=first_name, password=generate_password_hash(password1, method='pbkdf2:sha256'))
           db.session.add(new_user)
           db.session.commit()
           flash('You have been signed up!', category='success')
           return redirect(url_for('views.main'))

    return render_template("register.html", user=current_user)