import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-in-production'
    # Database configuration (MySQL only)
    _database_url = os.environ.get('DATABASE_URL')
    if not _database_url:
        mysql_host = os.environ.get('MYSQL_HOST')
        mysql_db = os.environ.get('MYSQL_DB')
        mysql_user = os.environ.get('MYSQL_USER')
        mysql_password = os.environ.get('MYSQL_PASSWORD')
        mysql_port = os.environ.get('MYSQL_PORT') or '3306'
        if all(value for value in [mysql_host, mysql_db, mysql_user]):
            mysql_password = mysql_password or ''
            _database_url = f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_db}?charset=utf8mb4"
    if not _database_url or _database_url.startswith('sqlite'):
        raise RuntimeError(
            "A MySQL connection string is required. Set DATABASE_URL or MYSQL_* environment variables."
        )
    SQLALCHEMY_DATABASE_URI = _database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # WhatsApp API Configuration
    WHATSAPP_API_URL = os.environ.get('WHATSAPP_API_URL') or ''
    WHATSAPP_API_KEY = os.environ.get('WHATSAPP_API_KEY') or ''
    WHATSAPP_PHONE_NUMBER = os.environ.get('WHATSAPP_PHONE_NUMBER') or '7879501625'
    WHATSAPP_VERIFY_TOKEN = os.environ.get('WHATSAPP_VERIFY_TOKEN') or 'salon_verify_token'
    
    # Email Configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or ''
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or ''
    
    # Loyalty Points Configuration
    LOYALTY_POINTS_PER_RUPEE = 1  # 1 point per rupee spent
    LOYALTY_REDEMPTION_RATE = 100  # 100 points = 1 rupee discount

