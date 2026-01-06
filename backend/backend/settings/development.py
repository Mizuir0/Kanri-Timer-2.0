"""
Django設定ファイル (開発環境)
"""

from .base import *

# デバッグモード有効
DEBUG = True

# 全ホストからのアクセスを許可
ALLOWED_HOSTS = ['*']

# 開発用の追加アプリ
INSTALLED_APPS += [
    # 'django_extensions',  # 必要に応じて追加
]

# 開発用のロギング設定
LOGGING['loggers']['apps']['level'] = 'DEBUG'
