from app import create_app
from app.extensions import db
from app.models import User, UserRole, Student
from werkzeug.security import generate_password_hash

app = create_app()


@app.cli.command("init-db")
def init_db():
    with app.app_context():
        db.create_all()
        print("Database tables created successfully.")


@app.cli.command("seed-data")
def seed_data():
    with app.app_context():
        if User.query.filter_by(username="admin01").first() is None:
            admin = User(
                username="admin01",
                password_hash=generate_password_hash("123456"),
                role=UserRole.ADMIN,
                is_active_account=True
            )
            db.session.add(admin)

        if User.query.filter_by(username="student01").first() is None:
            student_user = User(
                username="student01",
                password_hash=generate_password_hash("123456"),
                role=UserRole.STUDENT,
                is_active_account=True
            )
            db.session.add(student_user)
            db.session.flush()

            student = Student(
                user_id=student_user.id,
                student_code="SV001",
                full_name="Nguyen Van Student"
            )
            db.session.add(student)

        if User.query.filter_by(username="locked01").first() is None:
            locked_user = User(
                username="locked01",
                password_hash=generate_password_hash("123456"),
                role=UserRole.STUDENT,
                is_active_account=False
            )
            db.session.add(locked_user)

        db.session.commit()
        print("Seed data created successfully.")


if __name__ == "__main__":
    app.run(debug=True)