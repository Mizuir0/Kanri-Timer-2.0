import os
from celery import Celery

# Django設定モジュールを指定
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings.development')

app = Celery('backend')

# Django設定からCelery設定を読み込む
app.config_from_object('django.conf:settings', namespace='CELERY')

# 全てのアプリからtasksを自動検出
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
