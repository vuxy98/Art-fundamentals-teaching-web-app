from website import create_app
from website.models import db, User
from werkzeug.security import generate_password_hash

#admin user is created here

app = create_app()
with app.app_context():
    existing = User.query.filter_by(email="admin@mail.com").first()
    if not existing:
        admin_user = User(
            email="admin@mail.com",
            first_name="Admin",
            password=generate_password_hash("xxxxxxxx", method="pbkdf2:sha256"),
            is_admin=True
        )
        db.session.add(admin_user)
        db.session.commit()
        print("✅ Admin user created.")
    else:
        print("⚠️ Admin user already exists.")