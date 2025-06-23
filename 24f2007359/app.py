import os
from flask import Flask
from flask_wtf.csrf import CSRFProtect

def create_app():
    # Initialize Flask app
    app = Flask(__name__,
                template_folder='24f2007359/templates',
                static_folder='24f2007359/static',
                static_url_path='/static')
    
    # Configure app
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev')
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize CSRF protection
    csrf = CSRFProtect(app)
    
    # Initialize database
    from models import init_db
    init_db(app)
    
    # Register blueprints
    from controllers import main
    from controllers.file1 import auth
    from controllers.file2 import admin
    from controllers.api import api  # Import the API blueprint
    app.register_blueprint(main)
    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(admin, url_prefix='/admin')
    app.register_blueprint(api)  # Register the API blueprint
    
    return app

# Create app instance
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)