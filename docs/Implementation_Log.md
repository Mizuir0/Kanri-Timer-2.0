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

#### 3. Django設定ファイルとモデル定義（完了） ✅

**実装日**: 2026-01-06

**作成したファイル（25個）**:

1. `backend/manage.py` - Django管理コマンド
2. `backend/backend/__init__.py` - Celery初期化
3. `backend/backend/celery.py` - Celeryアプリ設定
4. `backend/backend/settings/__init__.py` - 設定モジュール初期化
5. `backend/backend/settings/base.py` - 共通設定（最重要）
6. `backend/backend/settings/development.py` - 開発環境設定
7. `backend/backend/settings/production.py` - 本番環境設定
8. `backend/backend/urls.py` - URLルーティング
9. `backend/backend/asgi.py` - ASGI設定（WebSocket対応）
10. `backend/backend/wsgi.py` - WSGI設定
11. `backend/apps/members/__init__.py` - メンバーアプリ初期化
12. `backend/apps/members/apps.py` - アプリ設定
13. `backend/apps/members/models.py` - Memberモデル定義
14. `backend/apps/members/admin.py` - 管理画面設定
15. `backend/apps/timers/__init__.py` - タイマーアプリ初期化
16. `backend/apps/timers/apps.py` - アプリ設定
17. `backend/apps/timers/models.py` - Timer, TimerStateモデル定義
18. `backend/apps/timers/admin.py` - 管理画面設定
19. `backend/apps/timers/views.py` - タイマーAPI実装
20. `backend/apps/timers/serializers.py` - JSON変換
21. `backend/apps/timers/urls.py` - URLルーティング
22. `backend/apps/timers/tasks.py` - Celeryタスク
23. `backend/apps/line_integration/__init__.py` - LINE連携アプリ初期化
24. `backend/apps/line_integration/apps.py` - アプリ設定
25. `backend/requirements/base.txt` - パッケージリスト更新（dj-database-url追加）

**実装した機能**:
- Djangoプロジェクトの完全な設定
- Member, Timer, TimerStateモデル
- タイマー状態取得API（`GET /api/timer-state/`）
- タイマー開始API（`POST /api/timer-state/start/`）
- Celeryタスク（`update_timer_state` - 1秒ごと実行）
- Django管理画面設定

**Gitコミット**:
```
commit 3e53d93
feat: バックエンド設定とモデル定義を完了（MVP Step 1）
```

---

#### 4. Reactプロジェクト作成（完了） ✅

**実装日**: 2026-01-06

**作成したファイル（14個）**:

##### プロジェクト設定ファイル
1. `frontend/package.json` - npm パッケージ定義
   - **主な内容**: React 18, Vite 5, TailwindCSS 3, Zustand 4, Axios 1
   - **なぜ必要？**: フロントエンドのライブラリ依存関係を定義

2. `frontend/vite.config.js` - Vite（ビルドツール）設定
   - **主な内容**: Reactプラグイン、開発サーバーポート5173、ホットリロード設定
   - **なぜ必要？**: 開発サーバーとビルドプロセスを設定

3. `frontend/tailwind.config.js` - TailwindCSS設定
   - **主な内容**: JSX/TSXファイルをスキャン対象に設定
   - **なぜ必要？**: CSSクラスの生成範囲を指定

4. `frontend/postcss.config.js` - PostCSS設定
   - **主な内容**: TailwindCSSとAutoprefixerを有効化
   - **なぜ必要？**: TailwindCSSを処理するため

5. `frontend/.eslintrc.cjs` - ESLint設定
   - **主な内容**: React推奨ルール、未使用変数警告など
   - **なぜ必要？**: コード品質を維持

6. `frontend/index.html` - HTMLエントリポイント
   - **主な内容**: Reactアプリのマウントポイント（`<div id="root">`）
   - **なぜ必要？**: Reactアプリを描画する起点

##### 状態管理
7. `frontend/src/stores/timerStore.js` - Zustand Store（状態管理）
   - **主な内容**:
     ```javascript
     {
       currentTimer: null,        // 現在のタイマー情報
       remainingSeconds: 0,       // 残り秒数
       isRunning: false,          // 実行中フラグ
       isPaused: false,           // 一時停止フラグ
       updateTimerState: (state) => {} // 状態更新関数
     }
     ```
   - **なぜ必要？**: バックエンドから取得したタイマー状態をアプリ全体で共有

##### API通信
8. `frontend/src/services/api.js` - API通信サービス
   - **主な内容**:
     - `getTimerState()` - タイマー状態取得（GET /api/timer-state/）
     - `startTimer()` - タイマー開始（POST /api/timer-state/start/）
   - **なぜ必要？**: バックエンドAPIとの通信を一元管理

##### ユーティリティ
9. `frontend/src/utils/timeFormat.js` - 時間フォーマット関数
   - **主な内容**:
     ```javascript
     formatTime(seconds) => "MM:SS" // 例: 900秒 → "15:00"
     ```
   - **なぜ必要？**: 秒数を「分:秒」形式で表示

##### コンポーネント（共通）
10. `frontend/src/components/common/Button.jsx` - ボタンコンポーネント
    - **主な内容**: primary, success, warning, secondaryの4種類のスタイル
    - **なぜ必要？**: 統一されたボタンデザインを提供

##### コンポーネント（タイマー）
11. `frontend/src/components/timer/CurrentTimer.jsx` - 現在のタイマー表示
    - **主な内容**:
      - バンド名表示
      - 残り時間表示（8xlサイズ、MM:SS形式）
      - 状態バッジ（実行中🔴 / 一時停止⏸️ / 待機中）
      - メンバー名表示
    - **なぜ必要？**: リハーサル中にタイマーを大きく表示

12. `frontend/src/components/timer/TimerControls.jsx` - タイマー操作ボタン
    - **主な内容**:
      - 開始ボタン（`isRunning`がfalseの時のみ表示）
      - ※ 一時停止・スキップはStep 2で実装（コメントアウト済み）
    - **なぜ必要？**: タイマーの開始操作を提供

##### メインアプリ
13. `frontend/src/App.jsx` - Reactルートコンポーネント
    - **主な内容**:
      - **ポーリング処理**: 1秒ごとに`getTimerState()`を実行してタイマー状態を取得
      - **クライアント側カウントダウン**: 表示をスムーズにするため、クライアント側でも1秒ごとに残り秒数を減算
      - レイアウト: ヘッダー（KanriTimer 2.0）+ タイマー表示 + 操作ボタン
    - **なぜ必要？**: アプリ全体を統合し、ポーリングによるリアルタイム更新を実現

14. `frontend/src/main.jsx` - Reactエントリポイント
    - **主な内容**: ReactDOM.createRootでAppコンポーネントをマウント
    - **なぜ必要？**: Reactアプリを起動

15. `frontend/src/styles/index.css` - グローバルCSS
    - **主な内容**: TailwindCSSのディレクティブ（@tailwind base, components, utilities）
    - **なぜ必要？**: TailwindCSSを読み込み

**実装した機能**:
- **ポーリングベースの状態同期**: WebSocketの代わりに1秒ごとにAPIをポーリング（Step 4でWebSocketに移行予定）
- **クライアント側カウントダウン**: ポーリング間隔のラグを補完するため、クライアント側でも秒数を減算
- **レスポンシブUI**: TailwindCSSによる美しいデザイン
- **状態管理**: Zustandで軽量かつシンプルな状態管理

**技術的なポイント**:
- **二重のカウントダウン処理**:
  1. サーバー側: Celery Beatが1秒ごとに状態更新
  2. クライアント側: ポーリング（1秒）+ ローカルカウントダウン（1秒）で滑らかな表示
- **MVP Step 1の制約**:
  - WebSocket未実装のため、ポーリングで代替
  - 一時停止・スキップ機能はStep 2に延期
  - タイマー一覧表示もStep 2に延期

**Gitコミット**: 次のステップで実行予定

---

---

#### 5. 初期データ投入と動作確認（完了） ✅

**実装日**: 2026-01-06

**実施した作業**:

1. **Docker Composeで全サービス起動**
   - PostgreSQL 15 (db) - ✅ 起動・ヘルスチェック正常
   - Redis 7 (redis) - ✅ 起動・ヘルスチェック正常
   - Django (web) - ✅ ポート8000で起動
   - Celery Worker (celery) - ✅ バックグラウンドタスク実行
   - Celery Beat (celery-beat) - ✅ スケジューラー起動（1秒ごと実行）
   - React (frontend) - ✅ ポート5173で起動

2. **データベースマイグレーション実行**
   ```bash
   python manage.py makemigrations members timers
   python manage.py migrate
   ```
   - `members.0001_initial` - Member モデル作成
   - `timers.0001_initial` - Timer, TimerState モデル作成

3. **スーパーユーザー作成**
   - ユーザー名: `admin`
   - パスワード: `admin123`
   - 管理画面アクセス: http://localhost:8000/admin

4. **テストデータ投入**
   - メンバー3件作成:
     - よんく
     - あお
     - キャロ
   - タイマー1件作成:
     - バンド名: Band A
     - 時間: 15分
     - メンバー: よんく・あお・キャロ
     - 順序: 1
   - TimerState初期化:
     - current_timer を Band A に設定

5. **動作確認完了** ✅
   - フロントエンド表示: http://localhost:5173
     - タイマー表示（Band A, 15:00） ✅
     - メンバー名表示 ✅
     - 開始ボタン表示 ✅
   - API動作確認:
     - `GET /api/timers/timer-state/` - 正常レスポンス ✅
   - タイマー動作確認:
     - 開始ボタンクリック ✅
     - カウントダウン開始（14:59, 14:58...） ✅
     - ポーリング更新（1秒間隔） ✅

**技術的なポイント**:
- **Singleton パターン**: TimerState は `pk=1` 固定でシングルトンを実現
- **ポーリング同期**: フロントエンドが1秒ごとにAPIをポーリングして状態更新
- **クライアント側カウントダウン**: ポーリング間隔の遅延を補完するため、クライアント側でも秒数を減算

**Gitコミット**: 次のステップで実行予定

---

---

## 📝 MVP Step 2 の詳細進捗

### ✅ 完了した作業（2026-01-06）

**実装日**: 2026-01-06

MVP Step 2では、タイマー一覧表示、全体の押し巻き表示、一時停止・スキップ機能、キーボードショートカットを実装しました。

#### Phase A: バックエンドAPI実装（完了） ✅

**編集したファイル**:

##### 1. `backend/apps/timers/views.py`
- **追加した機能**:
  - `get_timers()` - GET /api/timers/ - 全タイマー一覧取得（order順）
  - `pause_timer()` - POST /api/timers/timer-state/pause/ - 一時停止（経過時間を保存）
  - `resume_timer()` - POST /api/timers/timer-state/resume/ - 再開（started_atを調整）
  - `skip_timer()` - POST /api/timers/timer-state/skip/ - スキップして次のタイマーを自動開始
- **技術的なポイント**:
  - **Pause処理**: `elapsed_seconds = (now - started_at).total_seconds()` で経過時間を保存
  - **Resume処理**: `started_at = now - timedelta(seconds=elapsed_seconds)` で開始時刻を調整（経過時間を考慮）
  - **Skip処理**: 現在のタイマーを完了マーク → 次の未完了タイマーを自動開始

##### 2. `backend/apps/timers/urls.py`
- **追加したルート**:
  - `path('', views.get_timers, name='get_timers')` - タイマー一覧
  - `path('timer-state/pause/', views.pause_timer, name='pause_timer')`
  - `path('timer-state/resume/', views.resume_timer, name='resume_timer')`
  - `path('timer-state/skip/', views.skip_timer, name='skip_timer')`

---

#### Phase B: フロントエンドAPIサービス（完了） ✅

##### 1. `frontend/src/services/api.js`
- **追加した関数**:
  - `getTimers()` - GET /api/timers/ を呼び出し
  - `pauseTimer()` - POST /api/timers/timer-state/pause/ を呼び出し
  - `resumeTimer()` - POST /api/timers/timer-state/resume/ を呼び出し
  - `skipTimer()` - POST /api/timers/timer-state/skip/ を呼び出し

---

#### Phase C: フロントエンドコンポーネント（完了） ✅

**新規作成したファイル**:

##### 1. `frontend/src/components/timer/TimeDifferenceDisplay.jsx`
- **機能**: 全体の進行状況（押し巻き）を上部に大きく表示
- **主な内容**:
  - `totalTimeDifferenceDisplay` を timerStore から取得
  - 色分けロジック:
    - 「押し」を含む → 赤背景（text-red-600 bg-red-50 border-red-200）
    - 「巻き」を含む → 緑背景（text-green-600 bg-green-50 border-green-200）
    - その他 → グレー背景（text-gray-600 bg-gray-50 border-gray-200）
- **なぜ必要？**: リハーサル全体が定刻通りか、押しているか、巻いているかを一目で把握

##### 2. `frontend/src/components/timer/TimerListItem.jsx`
- **機能**: 個別タイマーの行表示
- **主な内容**:
  - 完了インジケータ: ✅（完了） / ▶️（実行中） / ⚪（待機中）
  - バンド名表示（完了時は打ち消し線）
  - 時間差表示（完了時のみ、+MM:SS 押し / -MM:SS 巻き / 定刻通り）
  - 現在のタイマーは青背景でハイライト（bg-blue-50 border-l-4 border-l-blue-500）
- **なぜ必要？**: 各バンドの進行状況を個別に確認

##### 3. `frontend/src/components/timer/TimerList.jsx`
- **機能**: 全タイマーをリスト表示
- **主な内容**:
  - ヘッダーに「タイマー一覧」と完了数（例: 2 / 5 完了）
  - `allTimers` を map して `TimerListItem` を表示
  - 現在のタイマーは `isCurrent` プロパティを渡す
  - 最大高さ96（max-h-96）でスクロール可能
- **なぜ必要？**: 全体の流れを把握し、どのバンドが終わったか確認

##### 4. `frontend/src/components/timer/TimerControls.jsx`（編集）
- **追加した機能**:
  - `handlePause()` - pauseTimer() を呼び出し
  - `handleResume()` - resumeTimer() を呼び出し
  - `handleSkip()` - 確認ダイアログ → skipTimer() を呼び出し
  - 条件付きボタン表示:
    - `!isRunning` → 開始ボタン
    - `isRunning && !isPaused` → 一時停止ボタン + スキップボタン
    - `isPaused` → 再開ボタン + スキップボタン
- **なぜ必要？**: 状態に応じた操作ボタンを提供

##### 5. `frontend/src/hooks/useKeyboard.js`
- **機能**: キーボードショートカット処理
- **主な内容**:
  - **スペースキー**:
    - タイマー未実行 → startTimer()
    - 実行中 → pauseTimer()
    - 一時停止中 → resumeTimer()
  - **右矢印キー**: skipTimer()（確認ダイアログ付き）
  - **無効化条件**:
    - モバイルデバイス（max-width: 768px）
    - 入力フィールドにフォーカスがある時
- **なぜ必要？**: PCユーザーが素早く操作できるようにするため

---

#### Phase D: 状態管理・統合（完了） ✅

##### 1. `frontend/src/stores/timerStore.js`（編集）
- **追加したフィールド**:
  - `allTimers: []` - 全タイマー配列
  - `totalTimeDifference: 0` - 全体の時間差（秒）
  - `totalTimeDifferenceDisplay: ''` - 表示用文字列（例: "+3:24 押し"）
- **追加したアクション**:
  - `setAllTimers(timers)` - タイマー配列をセット
  - `setTotalTimeDifference(diff)` - 時間差をセット
  - `setTotalTimeDifferenceDisplay(display)` - 表示文字列をセット
  - `updateTimerList(timers)` - タイマー配列から時間差を計算して一括更新
- **計算ロジック**:
  ```javascript
  totalDiff = timers.reduce((sum, timer) => sum + (timer.time_difference || 0), 0)
  ```
  - 正の値 → "+MM:SS 押し"（赤）
  - 負の値 → "-MM:SS 巻き"（緑）
  - 0 → "定刻通り"（グレー）

##### 2. `frontend/src/App.jsx`（編集）
- **追加した機能**:
  - `useKeyboard()` フックを使用（キーボードショートカット有効化）
  - タイマーリストのポーリング（1秒間隔で `getTimers()` を実行）
  - レスポンシブレイアウト:
    - PC版（lg以上）: 2カラム（`grid-cols-1 lg:grid-cols-2`）
      - 左カラム: CurrentTimer + TimerControls
      - 右カラム: TimerList
    - モバイル版: 縦積み（grid-cols-1）
  - 上部に TimeDifferenceDisplay を配置
- **技術的なポイント**:
  - 2つのポーリング処理を並行実行:
    1. タイマー状態（1秒間隔）
    2. タイマーリスト（1秒間隔）
  - Step 4のWebSocket実装でポーリングを置き換え予定

---

### 実装ファイル一覧（MVP Step 2）

**編集したファイル（5個）**:
1. `backend/apps/timers/views.py` - 4つのエンドポイント追加
2. `backend/apps/timers/urls.py` - ルート登録
3. `frontend/src/services/api.js` - 4つのAPI関数追加
4. `frontend/src/stores/timerStore.js` - 状態フィールド追加
5. `frontend/src/App.jsx` - レイアウト統合

**新規作成したファイル（4個）**:
1. `frontend/src/components/timer/TimeDifferenceDisplay.jsx`
2. `frontend/src/components/timer/TimerListItem.jsx`
3. `frontend/src/components/timer/TimerList.jsx`
4. `frontend/src/hooks/useKeyboard.js`

**変更行数**: 約600行追加

---

### 実装した機能まとめ

✅ **バックエンド**:
- タイマー一覧API（GET /api/timers/）
- 一時停止API（POST /api/timers/timer-state/pause/）
- 再開API（POST /api/timers/timer-state/resume/）
- スキップAPI（POST /api/timers/timer-state/skip/）

✅ **フロントエンド**:
- 全タイマー一覧表示（完了状態、時間差、現在のタイマーをハイライト）
- 全体の押し巻き表示（上部バナー、色分け）
- 一時停止・再開・スキップボタン（状態に応じた表示切替）
- キーボードショートカット（Space: 一時停止/再開、→: スキップ）
- レスポンシブレイアウト（PC: 2カラム、モバイル: 縦積み）

---

### 動作確認結果（2026-01-06）

**確認項目**:
- ✅ タイマーリストが表示される
- ✅ 現在のタイマーが青背景でハイライト
- ✅ 完了タイマーに時間差（押し/巻き）が表示される
- ✅ 全体の押し巻きが上部に表示される（色分け）
- ✅ 一時停止ボタンが動作する
- ✅ 再開ボタンが動作する
- ✅ スキップボタンが次のタイマーに進む
- ✅ キーボードショートカット（Space、→）が動作する
- ✅ レスポンシブレイアウトが機能する

**ユーザー確認**: 「問題なさそうです」（2026-01-06）

---

## 📊 全体の進捗率

- **Phase 1（設計）**: 100% ✅
- **Phase 2（実装アプローチ決定）**: 100% ✅
- **MVP Step 1**: 100% ✅ **完了！**
  - ✅ Docker環境構築
  - ✅ バックエンドディレクトリ構造
  - ✅ Django設定ファイル
  - ✅ モデル定義
  - ✅ API実装（最小限）
  - ✅ Celeryタスク
  - ✅ Reactプロジェクト
  - ✅ 初期データ投入
  - ✅ 動作確認
- **MVP Step 2**: 100% ✅ **完了！**
  - ✅ バックエンドAPI実装（pause/resume/skip/timers一覧）
  - ✅ フロントエンドAPIサービス
  - ✅ フロントエンドコンポーネント（5個）
  - ✅ 状態管理・統合
  - ✅ キーボードショートカット
  - ✅ レスポンシブレイアウト
  - ✅ 動作確認

---

## 🎯 次のアクション

**選択肢**:

1. **MVP Step 3: CRUD機能（タイマーの追加/編集/削除）**
   - タイマー作成フォーム
   - タイマー編集機能
   - タイマー削除機能
   - メンバー管理機能

2. **MVP Step 4: WebSocketリアルタイム同期**
   - ポーリングをWebSocketに置き換え
   - 全デバイスで同じ状態を即座に反映
   - パフォーマンス改善

3. **MVP Step 5: LINE連携と通知**
   - LINE Webhook設定
   - 5分前通知機能
   - リハーサル開始/終了通知

---

## 📚 参考情報

### 作成済みドキュメント
- `docs/KanriTimer_v2_Requirements.md` - 要件定義書
- `docs/KanriTimer_v2_Design.md` - 設計書
- `docs/Implementation_Log.md` - このファイル（実装ログ）

### 作成済みファイル（バックエンド）
- Django設定ファイル: 10個
- モデル定義: 2個（Member, Timer/TimerState）
- API実装: 3個（views, serializers, urls）
- Celeryタスク: 1個
- 管理画面設定: 2個
- Docker設定: 2個（docker-compose.yml, Dockerfile）
- 環境設定: 2個（.env.example, requirements）

---

**最終更新**: 2026-01-06（バックエンド完了）
