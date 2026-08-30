# KanriTimer 2.0

ライブイベントのリハーサル進行を管理するタイマーシステムです。バンドごとの持ち時間を管理し、PCからの開始・一時停止・再開・スキップ操作、複数端末でのリアルタイム同期、担当者へのLINE自動通知までを行います。

前身である [kanri-timer](https://github.com/Mizuir0/kanri-timer)（Celery/Channels導入版・未完成）・[kanri-timer1.0](https://github.com/Mizuir0/kanri-timer1.0)（素のJavaScript実装版）の後継として、`docs/KanriTimer_v2_Requirements.md` の要件定義に基づき**設計からコードまで全てAIが実装**しました。人間はPM兼CTOとして要件・設計判断を担当しています（詳細は `CLAUDE.md` 参照）。

## 主な機能

- **タイマーCRUD**：バンド名・予定時間（分）・担当者3名を指定してタイマーを作成・編集・削除。ドラッグ&ドロップ（`@dnd-kit`）で実行順を変更可能。
- **タイマー実行制御**：開始・一時停止・再開・スキップ。一時停止時間は「押し／巻き」として累積計算され、予定時間との差分が表示されます。
- **自動進行**：現在のタイマーが0:00になると、Celery Beat（1秒間隔）のタスクが自動的に次のタイマーへ進めます。
- **複数端末でのリアルタイム同期**：タイマー操作やCelery Beatの更新は Django Channels（WebSocket, `timer_updates` グループ）で全接続クライアントに配信され、フロントエンドはこれを信頼して表示を更新します（クライアント単独でのカウントダウンは行いません）。
- **PC/モバイルでの権限出し分け**：`useDeviceDetect`（画面幅768px判定）により、モバイル表示では操作ボタン（開始/一時停止/再開/スキップ）が非表示になり閲覧専用になります。
- **LINE通知（LINE Messaging API）**：
  - 次のタイマー開始5分前に、担当者へLINEで通知（Celery Beatで1秒間隔チェック、重複送信防止あり）
  - リハーサル開始時・終了時（全タイマー完了時）に、LINE連携済み全メンバーへ通知
  - LINE Webhookで、ユーザーが自分の名前をLINEに送信すると `Member` レコードと自動的に紐付け（`line_user_id` 登録）
  - フロントエンドからLINE通知のオン/オフを切り替え可能
- **Django管理画面**：メンバー（担当者）・タイマー・LINE通知履歴の管理。

## 技術スタック

| 分類 | 技術 |
|---|---|
| フロントエンド | React 18 + Vite + TailwindCSS、状態管理は Zustand、並べ替えは `@dnd-kit` |
| バックエンド | Django 4.2 + Django REST Framework |
| リアルタイム通信 | Django Channels（Daphne）+ WebSocket |
| 非同期タスク | Celery + Celery Beat（1秒間隔でタイマー更新・LINE通知チェック） |
| データベース | PostgreSQL（本番は Supabase） |
| メッセージブローカー/キャッシュ | Redis |
| 外部API | LINE Messaging API（`line-bot-sdk`） |
| 本番インフラ | バックエンド: Railway、フロントエンド: Netlify、DB: Supabase、死活監視: UptimeRobot |

## ディレクトリ構成

```
.
├── backend/
│   ├── backend/            # プロジェクト設定（settings/base,development,production, urls, asgi, celery）
│   ├── apps/
│   │   ├── timers/         # タイマーCRUD・実行制御・WebSocket配信・自動進行タスク
│   │   ├── members/        # 担当者マスタ
│   │   └── line_integration/  # LINE Webhook・通知タスク
│   ├── requirements/       # base / development / production
│   └── manage.py
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── timer/      # CurrentTimer, TimerControls, TimerList, TimeDifferenceDisplay など
│       │   └── admin/      # TimerFormModal, MemberSelect（タイマー追加・編集）
│       ├── stores/          # timerStore.js（Zustand）
│       ├── services/        # api.js（REST）, websocket.js（WebSocketクライアント）
│       └── hooks/           # useDeviceDetect, useKeyboard
├── docker/                  # backend.Dockerfile, frontend.Dockerfile
├── docker-compose.yml       # db / redis / web / celery / celery-beat / frontend
└── docs/
    ├── KanriTimer_v2_Requirements.md   # 要件定義書
    ├── KanriTimer_v2_Design.md         # 設計書
    ├── Implementation_Log.md           # 実装ログ（各Stepの詳細・デプロイ手順・発生した問題と解決策）
    └── Feature_*.md                     # 将来機能の提案書（下記「未実装の機能提案」参照）
```

## データモデル（概要）

- **Timer**（`apps.timers`）：バンド名・予定時間・担当者1〜3（`Member` への外部キー）・実行順序・実績時間・完了時刻。
- **TimerState**（`apps.timers`）：現在進行中のタイマー状態を保持するシングルトン（`pk=1` 固定、削除不可）。実行中/一時停止中フラグ、開始・一時停止時刻、累積一時停止秒数、LINE通知有効フラグなどを持ちます。
- **Member**（`apps.members`）：担当者名・LINE User ID・有効フラグ。
- **LineNotification**（`apps.line_integration`）：通知種別（5分前／リハーサル開始／終了）ごとの送信履歴。`unique_together` で同一タイマー・同一種別の重複送信を防止。

## 主なAPIエンドポイント

| メソッド | パス | 説明 |
|---|---|---|
| GET | `/api/timers/` | タイマー一覧取得 |
| POST | `/api/timers/create/` | タイマー作成 |
| PUT | `/api/timers/<id>/` | タイマー更新（完了済み・実行中は不可） |
| DELETE | `/api/timers/<id>/delete/` | タイマー削除（完了済み・実行中は不可） |
| POST | `/api/timers/reorder/` | 並べ替え（全タイマーIDを指定） |
| POST | `/api/timers/delete-all/` | 全タイマー削除（全完了時のみ） |
| GET | `/api/timers/timer-state/` | 現在のタイマー状態取得 |
| POST | `/api/timers/timer-state/start/` | 開始 |
| POST | `/api/timers/timer-state/pause/` | 一時停止 |
| POST | `/api/timers/timer-state/resume/` | 再開 |
| POST | `/api/timers/timer-state/skip/` | スキップ（次のタイマーへ自動進行） |
| GET | `/api/members/` | 有効な担当者一覧取得 |
| POST | `/api/line/webhook/` | LINE Webhook（名前送信による連携） |
| POST | `/api/settings/` | LINE通知オン/オフ設定 |
| GET/HEAD | `/health/` | ヘルスチェック（Supabase自動停止防止用、DBに実クエリを発行） |

WebSocket: `ws(s)://<host>/ws/timer/`（グループ `timer_updates`。`timer_state_updated` / `timer_list_updated` イベントを配信）

## セットアップ（Docker Compose）

1. リポジトリを取得し、環境変数を用意します。

   ```bash
   git clone git@github.com:Mizuir0/Kanri-Timer-2.0.git
   cd Kanri-Timer-2.0
   cp .env.example .env
   ```

   `.env.example` の内容（DB/Redis接続情報、CORS、LINE連携キーなど）を必要に応じて編集してください。LINE通知を使わない場合は `LINE_CHANNEL_ACCESS_TOKEN` / `LINE_CHANNEL_SECRET` は空でも起動できます。

2. コンテナを起動します。

   ```bash
   docker compose up --build
   ```

   `db`（PostgreSQL）・`redis`・`web`（Daphne, :8000）・`celery`・`celery-beat`・`frontend`（Vite, :5173）が起動します。

3. マイグレーションと管理ユーザーを作成します。

   ```bash
   docker compose exec web python manage.py migrate
   docker compose exec web python manage.py createsuperuser
   ```

4. ブラウザでアクセスします。

   - フロントエンド（メイン画面）: http://localhost:5173
   - バックエンドAPI: http://localhost:8000/api/
   - Django管理画面: http://localhost:8000/admin/

   管理画面から `Member`（担当者）を登録した上で、フロントエンド右上（または管理用UI）からタイマーを作成してください。

## 未実装の機能提案

`docs/` 配下の以下のドキュメントは、将来追加を検討している機能の提案書であり、**コードとしては未実装**です（該当する実装をリポジトリ内に確認できませんでした）。

- `Feature_AutoWorkAssignment.md`：バンドの出演順から各部局の担当者を自動割り当てる機能
- `Feature_BulkTimerImport.md`：タイマーの一括インポート機能
- `Feature_MemberManagement.md`：メンバー管理機能の拡張案
- `Feature_OfflineSupport.md`：オフライン対応
- `Feature_UserManagement.md`：ユーザー管理機能の拡張案

## デプロイ

`docs/Implementation_Log.md` に、Railway（バックエンド/Celery）・Netlify（フロントエンド）・Supabase（DB）・UptimeRobotを用いた本番デプロイの手順と、実際に発生した問題（Rustコンパイラエラー、Supabase接続、CORS、Celeryのメモリ不足、CSRF、UptimeRobotの405エラーなど）とその対処が詳しく記録されています。デプロイ作業時は先にこのログを参照してください。

## 注意事項

- `TimerState` はシングルトンモデルで、`delete()` は無効化されています（`pk=1` 固定）。
- `.env` はリポジトリに含まれていません（`.gitignore` 対象）。ローカル・本番いずれも `.env.example` を基に別途作成してください。
