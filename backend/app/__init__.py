# backend/app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import os
from dotenv import load_dotenv

# Đọc .env trước khi dùng bất kỳ biến nào
load_dotenv()

# Khởi tạo các extension ở module level
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)

    # Dùng .env hoặc fallback (an toàn hơn hardcode)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')

    CORS(app)
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    from . import models

    from .auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    from .routes import main_bp
    app.register_blueprint(main_bp)

    from .events import events_bp
    app.register_blueprint(events_bp, url_prefix='/api/events')
    
    @app.route('/health')
    def health_check():
        return {"status": "ok", "message": "Backend AIdoList is running!"}

    return app