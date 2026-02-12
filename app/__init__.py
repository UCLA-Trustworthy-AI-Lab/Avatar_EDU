from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
login_manager = LoginManager()

def create_app(config_class=Config):
    import os
    # Get the absolute path to the project root
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    template_dir = os.path.join(basedir, 'templates')
    static_dir = os.path.join(basedir, 'static')
    
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    app.config.from_object(config_class)
    
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    CORS(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.query.get(int(user_id))
    
    from app.routes.main import bp as main_bp
    from app.routes.auth import bp as auth_bp
    from app.routes.reading import bp as reading_bp
    from app.routes.conversation import bp as conversation_bp
    from app.routes.speaking import speaking_bp
    from app.routes.listening import bp as listening_bp
    from app.routes.writing import bp as writing_bp
    from app.routes.memory import bp as memory_bp
    # Other routes would be imported here when implemented

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(reading_bp, url_prefix='/api/reading')
    app.register_blueprint(conversation_bp)
    app.register_blueprint(speaking_bp)
    app.register_blueprint(listening_bp, url_prefix='/api/listening')
    app.register_blueprint(writing_bp, url_prefix='/api/writing')
    app.register_blueprint(memory_bp)
    # Other route registrations would be here when implemented
    
    return app

from app import models
from app.models import reading