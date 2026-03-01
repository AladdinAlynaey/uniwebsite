from flask import Flask
import os
import json
from flask_cors import CORS
from markupsafe import Markup
import re

# Patch Flask-Markdown to use markupsafe.Markup instead of flask.Markup
import sys
sys.modules['flask.Markup'] = Markup
from flaskext.markdown import Markdown

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    # Initialize Markdown
    Markdown(app)
    
    # Add custom filters
    @app.template_filter('nl2br')
    def nl2br_filter(s):
        if s is None or not isinstance(s, str):
            return Markup('')
        return Markup(re.sub(r'\n', '<br>', s))
    
    # Configuration
    app.config['SECRET_KEY'] = 'your-secret-key'
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
    app.config['DATA_DIR'] = os.path.join(os.path.dirname(app.root_path), 'data')
    app.config['TELEGRAM_BOT_USERNAME'] = 'your_bot_username'
    
    # Ensure the upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Ensure data directory exists
    os.makedirs(app.config['DATA_DIR'], exist_ok=True)
    
    # Load Telegram configuration if exists
    telegram_config_path = os.path.join(app.config['DATA_DIR'], 'telegram_config.json')
    try:
        with open(telegram_config_path, 'r') as f:
            telegram_config = json.load(f)
            if 'username' in telegram_config:
                app.config['TELEGRAM_BOT_USERNAME'] = telegram_config['username']
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    
    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.admin import admin_bp
    from app.routes.student import student_bp
    from app.routes.api import api_bp
    from app.routes.superadmin import superadmin_bp
    from app.routes.faculty_head import faculty_bp
    from app.routes.teacher import teacher_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(student_bp, url_prefix='/student')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(superadmin_bp, url_prefix='/superadmin')
    app.register_blueprint(faculty_bp, url_prefix='/faculty')
    app.register_blueprint(teacher_bp, url_prefix='/teacher')
    
    # Initialize Elasticsearch and migrate JSON data (idempotent)
    try:
        from app.utils.elasticsearch_client import migrate_json_to_es, migrate_hierarchy
        migrate_json_to_es()
        migrate_hierarchy()
    except Exception as e:
        print(f"⚠️  Elasticsearch migration warning: {e}")
    
    return app 