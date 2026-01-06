# KanriTimer 2.0 実装ログ

**開始日**: 2026-01-06
**実装アプローチ**: MVP型（最小構成から段階的に拡張）

---

## 📋 実装ステップ全体像

### ✅ Phase 1: 設計とルールの固定（完了）
- ディレクトリ構成の決定（案2：機能別モジュール構成）
- REST API インターフェース定義
- WebSocket イベント定義
- Celery タスク定義
- React コンポーネント構成定義
- 設計書を `docs/KanriTimer_v2_Design.md` に保存

### ✅ Phase 2: 実装の提案と決定（完了）
- 実装アプローチを3つ提案
- **案C（MVP型）を採用** - 最小構成から段階的に拡張

---

## 🚀 MVP実装ステップ

### MVP Step 1: 最小構成（タイマー表示+開始ボタン）【進行中】

**目標**: 1つのタイマーを表示して、開始ボタンを押したらカウントダウンが始まる

#### 実装内容
1. Docker Compose環境構築
2. Djangoプロジェクト作成
3. 最小限のAPI実装
4. Reactプロジェクト作成
5. 動作確認

---

### MVP Step 2: タイマー一覧と押し巻き表示【未着手】

**目標**: 複数のタイマーを表示し、全体の押し巻きを表示する

---

### MVP Step 3: CRUD機能（追加/編集/削除）【未着手】

**目標**: PC画面からタイマーを追加・編集・削除できる

---

### MVP Step 4: WebSocketリアルタイム同期【未着手】

**目標**: 全デバイスで同じタイマー状態をリアルタイム表示

---

### MVP Step 5: LINE連携と通知【未着手】

**目標**: 5分前にLINE通知を送信

---

## 📝 MVP Step 1 の詳細進捗

### ✅ 完了した作業

#### 1. Docker環境構築（完了）

**作成したファイル**:

##### `docker-compose.yml`
- **何をするファイル？**: Docker Composeの設定ファイル。全てのサービス（PostgreSQL、Redis、Django、Celery、React）を定義
- **主な内容**:
  - `db`: PostgreSQL 15 データベース
  - `redis`: Redis 7 キャッシュ/メッセージブローカー
  - `web`: Django Webサーバー（ポート8000）
  - `celery`: Celeryワーカー（バックグラウンドタスク実行）
  - `celery-beat`: Celery Beat（スケジューラー、1秒ごとのタスク実行）
  - `frontend`: React開発サーバー（ポート5173）
- **なぜ必要？**: 全てのサービスを一括で起動・停止できる

##### `.env.example` と `.env`
- **何をするファイル？**: 環境変数のテンプレートと実際の設定
- **主な内容**:
  - `SECRET_KEY`: Djangoのシークレットキー
  - `DATABASE_URL`: PostgreSQL接続情報
  - `REDIS_URL`: Redis接続情報
  - `CORS_ALLOWED_ORIGINS`: CORS設定（フロントエンドからのアクセス許可）
  - `LINE_CHANNEL_ACCESS_TOKEN`: LINE連携用（後で設定）
- **なぜ必要？**: 環境ごとに異なる設定を外部ファイルで管理するため

##### `.gitignore`
- **何をするファイル？**: Gitで管理しないファイルを指定
- **主な内容**:
  - `.env` - 環境変数（秘密情報を含むため）
  - `__pycache__/` - Pythonキャッシュ
  - `node_modules/` - Node.jsライブラリ
  - `db.sqlite3` - ローカルDB
- **なぜ必要？**: 秘密情報やビルド成果物をGitにコミットしないため

##### `docker/backend.Dockerfile`
- **何をするファイル？**: Djangoコンテナのビルド設定
- **主な内容**:
  - ベースイメージ: Python 3.11
  - PostgreSQLクライアントのインストール
  - Pythonパッケージのインストール（requirements/development.txt）
  - ポート8000を公開
- **なぜ必要？**: Djangoアプリを動かすコンテナイメージを作成するため

##### `docker/frontend.Dockerfile`
- **何をするファイル？**: Reactコンテナのビルド設定
- **主な内容**:
  - ベースイメージ: Node.js 20
  - npm installでライブラリインストール
  - ポート5173を公開（Vite開発サーバー）
- **なぜ必要？**: Reactアプリを動かすコンテナイメージを作成するため

---

#### 2. バックエンドディレクトリ構造作成（完了）

**作成したディレクトリ**:

```
backend/
├── backend/                    # Djangoプロジェクト設定
│   └── settings/               # 環境別設定ディレクトリ
├── apps/                       # Djangoアプリ（機能別）
│   ├── members/                # メンバー管理
│   ├── timers/                 # タイマー管理
│   └── line_integration/       # LINE連携
├── common/                     # 共通ユーティリティ
└── requirements/               # Pythonパッケージ定義
    ├── base.txt                # 共通パッケージ
    ├── development.txt         # 開発用パッケージ
    └── production.txt          # 本番用パッケージ
```

**なぜこの構成？**:
- **機能別モジュール分離**: Phase 2で他部局を追加する時に拡張しやすい
- **環境別設定**: 開発環境と本番環境で異なる設定を使い分け
- **requirements分離**: 開発ツールを本番環境に含めない

**作成したファイル**:

##### `backend/requirements/base.txt`
- **何をするファイル？**: 全環境共通のPythonパッケージリスト
- **主な内容**:
  - `Django==4.2.20` - Webフレームワーク
  - `djangorestframework==3.14.0` - REST API
  - `django-cors-headers==4.3.1` - CORS設定
  - `channels==4.0.0` - WebSocket対応
  - `celery==5.3.4` - バックグラウンドタスク
  - `psycopg2-binary==2.9.9` - PostgreSQL接続
  - `line-bot-sdk==3.5.0` - LINE連携
- **なぜ必要？**: Djangoアプリの動作に必要なライブラリを定義

##### `backend/requirements/development.txt`
- **何をするファイル？**: 開発環境専用のパッケージリスト
- **主な内容**:
  - `-r base.txt` - base.txtを継承
  - `ipython==8.18.1` - 対話型Python（デバッグ用）
  - `django-debug-toolbar==4.2.0` - デバッグツール
  - `pytest==7.4.3` - テストフレームワーク
- **なぜ必要？**: 開発時のデバッグやテストツールを追加

##### `backend/requirements/production.txt`
- **何をするファイル？**: 本番環境専用のパッケージリスト
- **主な内容**:
  - `-r base.txt` - base.txtを継承
  - `gunicorn==21.2.0` - 本番用WSGIサーバー
- **なぜ必要？**: 本番環境で必要なサーバーを追加

---

### 🔄 次にやること（MVP Step 1の残り作業）

#### 3. Django設定ファイル作成【次の作業】

**作成するファイル**:

##### `backend/manage.py`
- **何をするファイル？**: Djangoの管理コマンドを実行するスクリプト
- **使い方**: `python manage.py runserver`（サーバー起動）、`python manage.py migrate`（マイグレーション）など
- **なぜ必要？**: Djangoの全ての操作の起点

##### `backend/backend/__init__.py`
- **何をするファイル？**: Pythonパッケージとして認識させるための空ファイル
- **なぜ必要？**: Pythonの仕様

##### `backend/backend/settings/__init__.py`
- **何をするファイル？**: 環境変数に応じて適切な設定ファイルを読み込む
- **内容例**: `DJANGO_SETTINGS_MODULE` が `development` なら `development.py` を読み込む
- **なぜ必要？**: 開発/本番で設定を自動切り替え

##### `backend/backend/settings/base.py` 【重要！】
- **何をするファイル？**: 全環境共通のDjango設定
- **主な内容**:
  - `INSTALLED_APPS`: 使用するDjangoアプリ（members, timers, line_integration）
  - `DATABASES`: PostgreSQL接続設定
  - `CELERY_BEAT_SCHEDULE`: Celeryタスクのスケジュール（1秒ごとの実行）
  - `CORS_ALLOWED_ORIGINS`: フロントエンドからのアクセス許可
- **なぜ必要？**: Djangoの動作を制御する最重要ファイル

##### `backend/backend/settings/development.py`
- **何をするファイル？**: 開発環境専用の設定
- **主な内容**:
  - `DEBUG = True` - デバッグモード有効
  - `ALLOWED_HOSTS = ['*']` - 全ホストからのアクセス許可
- **なぜ必要？**: 開発時のみデバッグ機能を有効化

##### `backend/backend/settings/production.py`
- **何をするファイル？**: 本番環境専用の設定
- **主な内容**:
  - `DEBUG = False` - デバッグモード無効
  - `ALLOWED_HOSTS` - 許可されたホストのみ
  - セキュリティ設定強化
- **なぜ必要？**: 本番環境のセキュリティを確保

##### `backend/backend/urls.py`
- **何をするファイル？**: URLルーティング設定
- **主な内容**:
  - `/admin/` → Django管理画面
  - `/api/members/` → メンバーAPI
  - `/api/timers/` → タイマーAPI
  - `/api/timer-state/` → タイマー操作API
  - `/api/line/webhook/` → LINE Webhook
- **なぜ必要？**: URLとビュー関数を紐付け

##### `backend/backend/asgi.py`
- **何をするファイル？**: ASGI（非同期サーバー）設定
- **なぜ必要？**: WebSocketを使うために必要

##### `backend/backend/wsgi.py`
- **何をするファイル？**: WSGI（同期サーバー）設定
- **なぜ必要？**: 本番環境でGunicornから呼び出される

---

#### 4. モデル定義【次の作業】

**作成するファイル**:

##### `backend/apps/members/models.py`
- **何をするファイル？**: メンバーテーブルの定義
- **主な内容**:
  ```python
  class Member(models.Model):
      name = models.CharField(max_length=20, unique=True)
      line_user_id = models.CharField(max_length=100, blank=True, null=True)
      is_active = models.BooleanField(default=True)
      created_at = models.DateTimeField(auto_now_add=True)
  ```
- **なぜ必要？**: メンバー情報をデータベースに保存

##### `backend/apps/timers/models.py`
- **何をするファイル？**: タイマーとタイマー状態のテーブル定義
- **主な内容**:
  - `Timer`: バンドごとのタイマー（band_name, minutes, member1〜3, order）
  - `TimerState`: 現在のタイマー状態（current_timer, started_at, is_running, is_paused）
- **なぜ必要？**: タイマー情報と現在の状態をデータベースに保存

##### 各アプリの `__init__.py`, `apps.py`, `admin.py`
- **何をするファイル？**: Djangoアプリの初期化と管理画面設定
- **なぜ必要？**: Djangoの仕様

---

#### 5. API実装【次の作業】

**作成するファイル**:

##### `backend/apps/timers/views.py`
- **何をするファイル？**: タイマーAPIのビュー関数
- **主な内容**:
  - `GET /api/timer-state/` - タイマー状態取得
  - `POST /api/timer-state/start/` - タイマー開始
- **なぜ必要？**: フロントエンドからのAPIリクエストを処理

##### `backend/apps/timers/serializers.py`
- **何をするファイル？**: モデルとJSONの変換
- **主な内容**:
  - `TimerStateSerializer`: TimerStateをJSON形式に変換
- **なぜ必要？**: REST APIでJSONを返すため

---

#### 6. Celeryタスク実装【次の作業】

**作成するファイル**:

##### `backend/apps/timers/tasks.py`
- **何をするファイル？**: バックグラウンドタスクの定義
- **主な内容**:
  - `update_timer_state()`: 1秒ごとにタイマー状態を更新
- **なぜ必要？**: カウントダウンを自動実行

---

#### 7. React プロジェクト作成【次の作業】

**作成するファイル**:

##### `frontend/package.json`
- **何をするファイル？**: Node.jsパッケージの定義
- **主な内容**:
  - `react`, `react-dom` - React本体
  - `vite` - ビルドツール
  - `tailwindcss` - CSSフレームワーク
  - `zustand` - 状態管理
  - `axios` - HTTP通信
- **なぜ必要？**: Reactアプリの依存ライブラリを定義

##### `frontend/src/App.jsx`
- **何をするファイル？**: Reactのルートコンポーネント
- **主な内容**:
  - タイマー表示コンポーネント
  - 開始ボタンコンポーネント
- **なぜ必要？**: 画面を表示するため

---

### 8. 初期データ投入【次の作業】

**やること**:
- Django管理画面でメンバーを1件登録（例: よんく）
- タイマーを1件登録（例: Band A、よんく・あお・キャロ、15分）

**なぜ必要？**: 動作確認するためのテストデータ

---

### 9. 動作確認【最終ステップ】

**確認内容**:
1. Docker Composeで全サービス起動
2. ブラウザで `http://localhost:5173` を開く
3. タイマー表示（15:00）
4. 開始ボタンクリック
5. カウントダウン開始（14:59, 14:58...）

---

## 📊 全体の進捗率

- **Phase 1（設計）**: 100% ✅
- **Phase 2（実装アプローチ決定）**: 100% ✅
- **MVP Step 1**: 30%（Docker環境とディレクトリ構造のみ完了）
  - ✅ Docker環境構築
  - ✅ バックエンドディレクトリ構造
  - ⏳ Django設定ファイル
  - ⏳ モデル定義
  - ⏳ API実装
  - ⏳ Celeryタスク
  - ⏳ Reactプロジェクト
  - ⏳ 動作確認

---

## 🎯 次のアクション

**Step 1-3: Django設定ファイルとモデル定義**

選択肢：
- **選択肢A**: 重要なファイルだけ先に作成 → 動作確認 → 残りを作成
- **選択肢B**: 全ファイルを一気に作成 → 動作確認

ユーザーの決定待ち。

---

## 📚 参考情報

### 作成済みドキュメント
- `docs/KanriTimer_v2_Requirements.md` - 要件定義書
- `docs/KanriTimer_v2_Design.md` - 設計書
- `docs/Implementation_Log.md` - このファイル（実装ログ）

### 作成済み設定ファイル
- `docker-compose.yml` - Docker環境定義
- `.env.example` - 環境変数テンプレート
- `backend/requirements/base.txt` - Pythonパッケージ
- `docker/backend.Dockerfile` - Djangoコンテナ
- `docker/frontend.Dockerfile` - Reactコンテナ

---

**最終更新**: 2026-01-06
