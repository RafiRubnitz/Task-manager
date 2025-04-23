# app/__init__.py
from flask import Flask
from flask_pymongo import PyMongo
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from config import Config
import os
import datetime # Add datetime import

mongo = PyMongo()
login_manager = LoginManager()
bcrypt = Bcrypt()

# Define user_loader callback AFTER login_manager is initialized
@login_manager.user_loader
def load_user(user_id):
    # Import here to avoid circular dependency
    from app.models.user import User
    return User.get(user_id)

login_manager.login_view = 'auth.login' # Specify the login route

def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True) # Set instance_relative_config=True
    app.config.from_object(config_class)

    # Initialize extensions
    mongo.init_app(app)
    try:
        mongo.db.command('ping')
        print("MongoDB connection successful!")
    except Exception as e:
        print(f"MongoDB connection failed: {e}")
    login_manager.init_app(app)
    bcrypt.init_app(app)

    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Create necessary directories relative to app root and instance path
    # Static files are typically served from the static folder in the app root
    os.makedirs(os.path.join(app.root_path, 'static', 'css'), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, 'static', 'js'), exist_ok=True)
    # Templates are typically in the templates folder in the app root
    os.makedirs(os.path.join(app.root_path, 'templates'), exist_ok=True)
    # Routes and models are Python packages within the app
    os.makedirs(os.path.join(app.root_path, 'routes'), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, 'models'), exist_ok=True)
    # Gemini directory outside the app package
    os.makedirs(os.path.join(app.root_path, '..', 'gemini'), exist_ok=True)

    # Create __init__.py files if they don't exist to make them packages
    open(os.path.join(app.root_path, 'routes', '__init__.py'), 'a').close()
    open(os.path.join(app.root_path, 'models', '__init__.py'), 'a').close()

    # Register blueprints
    from app.routes.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.routes.tasks import bp as tasks_bp
    app.register_blueprint(tasks_bp) # Register tasks at root URL '/' or specify prefix

    # Add context processor for injecting 'now' into templates
    @app.context_processor
    def inject_now():
        return {'now': datetime.datetime.utcnow}

    # Ensure the models module is created before trying to import from it in user_loader
    # But models themselves will be imported within routes or other functions as needed

    return app 