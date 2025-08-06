import os
from .base import *

debug_env = os.getenv("DEBUG", "False").lower()
if debug_env in ("true", "1", "yes"):
    raise RuntimeError("DEBUG must be False in production!")

DEBUG = False

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

SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "True") == "True"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

INSTALLED_APPS += ['storages']

AWS_STORAGE_BUCKET_NAME = 'iterms-static'
AWS_S3_REGION_NAME = 'ap-northeast-1'

AWS_CLOUDFRONT_DOMAIN = "d3t658gdoc1u83.cloudfront.net"
STATIC_URL = f"https://{AWS_CLOUDFRONT_DOMAIN}/"

STATICFILES_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"