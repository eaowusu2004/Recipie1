import os
from dotenv import load_dotenv

load_dotenv()
from flask import Flask
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from Foodimg2Ing.models import db, User

app = Flask(__name__, template_folder='Templates')

# Security & Database Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-inverse-cooking-ai-2026')
db_path = os.path.join(app.root_path, 'users.db')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', f'sqlite:///{db_path}')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize Extensions
db.init_app(app)
csrf = CSRFProtect(app)

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please sign in to access this page.'
login_manager.login_message_category = 'warning'
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Register Blueprints & Routes
from Foodimg2Ing.auth import auth_bp
app.register_blueprint(auth_bp)

from Foodimg2Ing import routes

# Ensure database tables exist
with app.app_context():
    db.create_all()