import os
from .base import *

debug_env = os.getenv("DEBUG", "False").lower()
if debug_env in ("true", "1", "yes"):
    raise RuntimeError("DEBUG must be False in production!")

DEBUG =False

SECRET_KEY = os.getenv("SECRET_KEY")

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("ALLOWED_HOSTS", "").split(",")
    if host.strip()
]

INSTALLED_APPS = ["storages"] + INSTALLED_APPS

STATICFILES_DIRS = [
    BASE_DIR / "app" / "static"
]

FIXTURE_DIRS = [
    BASE_DIR / 'app' / 'fixture',
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

# ------ Static files を S3 へ ----------
AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME")
AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME", "ap-northeast-1")
AWS_S3_SIGNATURE_VERSION = "s3v4"
AWS_DEFAULT_ACL = None
AWS_S3_FILE_OVERWRITE = False
AWS_S3_OBJECT_PARAMETERS = {
    # CloudFront 経由で長期キャッシュ & 変更検知はハッシュ付きファイル名で
    "CacheControl": "public, max-age=31536000, s-maxage=31536000, immutable"
}

# S3 上の静的ファイルのプレフィックス（バケット直下に 'static/' 配下で管理）
AWS_LOCATION = "static"

# CloudFront のドメイン
AWS_CLOUDFRONT_DOMAIN = os.getenv("AWS_CLOUDFRONT_DOMAIN")
AWS_S3_CUSTOM_DOMAIN = AWS_CLOUDFRONT_DOMAIN

# django-storages（S3）を staticfiles のバックエンドに
STORAGES = {
    "staticfiles": {
        "BACKEND": "storages.backends.s3boto3.S3ManifestStaticStorage",
        "OPTIONS": {
            "bucket_name": AWS_STORAGE_BUCKET_NAME,
            "custom_domain": AWS_S3_CUSTOM_DOMAIN,
            "region_name": AWS_S3_REGION_NAME,
            "location": AWS_LOCATION,
        },
    },
    # "default": {...}  # MEDIA もS3にしたいなら別途
}

# STATIC_URL を CloudFront へ向ける
STATIC_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/{AWS_LOCATION}/"


# セキュリティ強化設定
def _as_https_origin(host: str | None) -> list[str]:
    if not host:
        return []
    host = host.strip()
    return [host] if host.startswith(("http://", "https://")) else [f"https://{host}"]

origins: list[str] = []
origins += _as_https_origin(AWS_CLOUDFRONT_DOMAIN)
origins += [o for h in ALLOWED_HOSTS for o in _as_https_origin(h)]
origins += ["https://i-terms.com"]
# 順序維持で重複削除
CSRF_TRUSTED_ORIGINS = list(dict.fromkeys(origins))

CSRF_COOKIE_SAMESITE = "Lax"
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True