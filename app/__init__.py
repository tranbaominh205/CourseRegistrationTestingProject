from flask import Flask
from app.config import Config
from app.extensions import db, login_manager


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)

    login_manager.login_view = "auth.login"

    from app.routes.main_routes import main_bp
    from app.routes.auth_routes import auth_bp
    from app.routes.student_routes import student_bp

    app.register_blueprint(student_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)

    return app