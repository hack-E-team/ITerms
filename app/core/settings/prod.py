import os
from .base import *

debug_env = os.getenv("DEBUG", "False").lower()
if debug_env in ("true", "1", "yes"):
    raise RuntimeError("DEBUG must be False in production!")

DEBUG = True

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("ALLOWED_HOSTS", "").split(",")
    if host.strip()
]

# RDS/MySQLなど本番DB設定

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

# セキュリティ強化設定

SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

# STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# AWS_STORAGE_BUCKET_NAME = "iterms-static"
# AWS_S3_REGION_NAME = "ap-northeast-1"

# # DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
# STATICFILES_STORAGE = "storages.backends.s3boto3.S3StaticStorage"

# INSTALLED_APPS = ["storages"] + INSTALLED_APPS

# AWS_CLOUDFRONT_DOMAIN = "d3t658gdoc1u83.cloudfront.net"
# AWS_LOCATION = 'static'
# STATIC_URL = f"https://{AWS_CLOUDFRONT_DOMAIN}/{AWS_LOCATION}/"

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")