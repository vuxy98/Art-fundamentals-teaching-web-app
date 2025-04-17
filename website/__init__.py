from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager
from flask_login import current_user
from flask_migrate import Migrate #migrate is used to update databases, without deleting them cuz ong its so tiring to re-add everything again

db = SQLAlchemy()
DB_NAME = "database.db"
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'touplis' #secret key for dev only
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    db.init_app(app)
    migrate.init_app(app, db)

    from .views import views
    from .auth import auth
    from .admin import admin

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(admin)

    from .models import User, Posts, Course

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))
    
    @app.context_processor
    def inject_user():
        return dict(user=current_user)

    create_database(app)

    return app

def create_database(app):
    db_path = 'website/' + DB_NAME
    if not path.exists(db_path):
        with app.app_context():
            db.create_all()
            print(f'Created Database at {db_path}')
    else:
        print('Database already exists at', db_path)

