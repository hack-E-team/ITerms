from .base import *
from dotenv import load_dotenv

load_dotenv(dotenv_path=BASE_DIR / '.env.dev')

DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv("DB_NAME"),
        'USER': os.getenv("DB_USER"),
        'PASSWORD': os.getenv("DB_PASSWORD"),
        'HOST': os.getenv("DB_HOST"),
        'PORT': os.getenv("DB_PORT", "3306"),
    }
}