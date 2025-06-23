# Parking System

## Project Overview
This is a Smart Parking Management System built with Flask. It supports user and admin dashboards, parking lot and spot management, and reservation features.

## Requirements
- **Python 3.10 or 3.11** (Python 3.13 is not supported by SQLAlchemy and Flask as of now)
- pip (Python package manager)

## Setup Instructions

### 1. Clone the Repository
```
git clone <your-repo-url>
cd "Mad 1 Project/parking-system/24f2007359"
```

### 2. Create and Activate a Virtual Environment
**Windows:**
```
python -m venv venv
.\venv\Scripts\activate
```
**Linux/macOS:**
```
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```
pip install -r requirements.txt
```

### 4. Run the Application
```
python app.py
```

## Directory Structure
- `app.py` - Main Flask application
- `models/` - Database models
- `controllers/` - Application logic and routes
- `templates/` - Jinja2 HTML templates
- `static/` - Static files (CSS, JS, images)

## Troubleshooting
- **ImportError: attempted relative import with no known parent package**
  - Make sure you are using absolute imports in `app.py`.
- **SQLAlchemy AssertionError or TypingOnly error**
  - Downgrade to Python 3.11 or 3.10.
- **ModuleNotFoundError: No module named 'flask'**
  - Run `pip install -r requirements.txt` in your activated virtual environment.

## Notes
- Always activate your virtual environment before running or installing anything.
- If you change Python versions, recreate your virtual environment and reinstall dependencies.

---
For further help, contact the project maintainer. 