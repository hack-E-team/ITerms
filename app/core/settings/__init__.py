from .base import *

# 強制上書き（Noneで上書きされてもここで潰す）
DATABASES['default'].update({
    'ENGINE': 'django.db.backends.mysql',
    'NAME': 'iterms',
    'USER': 'root',
    'PASSWORD': '',           # ← rootにパスがあるなら実値に
    'HOST': '127.0.0.1',
    'PORT': '3306',
    'OPTIONS': {'charset': 'utf8mb4'},
})
