import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'student-analytics-super-secret-key-cse-2026')
    
    # MySQL Database Configuration
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = int(os.environ.get('DB_PORT', 3306))
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'Murugan@123')
    DB_NAME = os.environ.get('DB_NAME', 'student_analytics_db')
    
    # SQLite fallback database for zero-config demo / when MySQL service is off
    SQLITE_PATH = BASE_DIR / 'student_analytics.sqlite3'
    
    # Database mode: 'AUTO' (tries MySQL, falls back to SQLite), 'MYSQL', or 'SQLITE'
    DB_MODE = os.environ.get('DB_MODE', 'AUTO')

