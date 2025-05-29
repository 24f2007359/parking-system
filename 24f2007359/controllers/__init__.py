from flask import Blueprint

# Create blueprints
main = Blueprint('main', __name__)
from .api import api  # Import the API blueprint

# Import routes after blueprint creation to avoid circular imports
from . import routes 