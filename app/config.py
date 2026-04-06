import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'app/static/uploads/properties')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16777216))
    WHATSAPP_NUMBER = os.environ.get('WHATSAPP_NUMBER', '2348000000000')
    WTF_CSRF_ENABLED = True
    CLOUDINARY_URL = os.environ.get('CLOUDINARY_URL')


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(
        os.path.abspath(os.path.dirname(__file__)), '..', 'instance', 'kingmac.db'
    )


class ProductionConfig(Config):
    DEBUG = False
    # Neon / Supabase / any PostgreSQL: set DATABASE_URL in Vercel env vars.
    # Vercel and Heroku use "postgres://" which SQLAlchemy needs as "postgresql://"
    _raw = os.environ.get('DATABASE_URL', '')
    SQLALCHEMY_DATABASE_URI = (
        'postgresql://' + _raw[len('postgres://'):]
        if _raw.startswith('postgres://')
        else (_raw if _raw else 'sqlite:////tmp/kingmac.db')
    )


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
