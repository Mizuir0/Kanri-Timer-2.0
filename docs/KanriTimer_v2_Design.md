# KanriTimer 2.0 設計書（Design Document）

**作成日**: 2026-01-06
**バージョン**: 1.0
**ステータス**: Phase 1 設計完了

---

## 📋 目次

1. [プロジェクト概要](#1-プロジェクト概要)
2. [ディレクトリ構成](#2-ディレクトリ構成)
3. [REST API インターフェース](#3-rest-api-インターフェース)
4. [WebSocket インターフェース](#4-websocket-インターフェース)
5. [Celery タスク](#5-celery-タスク)
6. [React コンポーネント](#6-react-コンポーネント)
7. [技術スタック](#7-技術スタック)
8. [開発環境](#8-開発環境)

---

## 1. プロジェクト概要

### 1.1 システム名
**KanriTimer 2.0**

### 1.2 アーキテクチャパターン
- **フロントエンド**: React 18 + Vite + TailwindCSS（SPA）
- **バックエンド**: Django 4.2 + DRF（REST API + WebSocket）
- **リアルタイム通信**: Django Channels + WebSocket + Redis
- **バックグラウンド処理**: Celery + Celery Beat + Redis
- **データベース**: PostgreSQL

### 1.3 通信フロー

```
【操作（ボタンクリック）】
PC (React)
    ↓ REST API
Django (処理)
    ↓ WebSocket
全デバイス (React) - 画面更新

【定期更新（1秒ごと）】
Celery Task
    ↓ WebSocket
全デバイス (React) - 画面更新
```

---

## 2. ディレクトリ構成

### 2.1 採用した構成

**案2: 機能別モジュール構成（拡張性重視）**

```
kanri-timer-v2/
├── backend/
│   ├── manage.py
│   ├── backend/
│   │   ├── __init__.py
│   │   ├── settings/
│   │   │   ├── __init__.py
│   │   │   ├── base.py          # 共通設定
│   │   │   ├── development.py   # 開発環境
│   │   │   └── production.py    # 本番環境
│   │   ├── urls.py
│   │   ├── asgi.py
│   │   └── wsgi.py
│   ├── apps/
│   │   ├── __init__.py
│   │   ├── members/             # メンバー管理
│   │   │   ├── __init__.py
│   │   │   ├── models.py
│   │   │   ├── views.py
│   │   │   ├── serializers.py
│   │   │   ├── admin.py
│   │   │   ├── urls.py
│   │   │   └── apps.py
│   │   ├── timers/              # タイマー管理
│   │   │   ├── __init__.py
│   │   │   ├── models.py
│   │   │   ├── views.py
│   │   │   ├── serializers.py
│   │   │   ├── consumers.py     # WebSocket
│   │   │   ├── tasks.py         # Celery Tasks
│   │   │   ├── admin.py
│   │   │   ├── urls.py
│   │   │   └── apps.py
│   │   └── line_integration/    # LINE連携
│   │       ├── __init__.py
│   │       ├── views.py
│   │       ├── webhook.py
│   │       ├── urls.py
│   │       └── apps.py
│   ├── common/                  # 共通ユーティリティ
│   │   ├── __init__.py
│   │   └── utils.py
│   └── requirements/
│       ├── base.txt
│       ├── development.txt
│       └── production.txt
│
├── frontend/
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── common/          # 共通コンポーネント
│   │   │   │   ├── Button.jsx
│   │   │   │   ├── Modal.jsx
│   │   │   │   └── LoadingSpinner.jsx
│   │   │   ├── timer/           # タイマー関連
│   │   │   │   ├── CurrentTimer.jsx
│   │   │   │   ├── NextTimer.jsx
│   │   │   │   ├── TimerControls.jsx
│   │   │   │   ├── TimerList.jsx
│   │   │   │   ├── TimerListItem.jsx
│   │   │   │   ├── TimeDisplay.jsx
│   │   │   │   └── TimeDifferenceDisplay.jsx
│   │   │   └── admin/           # 管理機能（PC専用）
│   │   │       ├── TimerForm.jsx
│   │   │       ├── TimerFormModal.jsx
│   │   │       └── MemberSelect.jsx
│   │   ├── stores/              # Zustand 状態管理
│   │   │   ├── timerStore.js
│   │   │   └── memberStore.js
│   │   ├── services/            # API/WebSocket通信
│   │   │   ├── api.js
│   │   │   └── websocket.js
│   │   ├── hooks/               # カスタムフック
│   │   │   ├── useTimer.js
│   │   │   ├── useWebSocket.js
│   │   │   ├── useKeyboard.js
│   │   │   └── useDeviceDetect.js
│   │   ├── utils/               # ユーティリティ
│   │   │   ├── timeFormat.js
│   │   │   └── constants.js
│   │   └── styles/
│   │       └── index.css
│   ├── public/
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   └── index.html
│
├── docker/
│   ├── backend.Dockerfile
│   ├── frontend.Dockerfile
│   └── nginx.conf
│
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.example
├── .gitignore
├── README.md
├── CLAUDE.md
├── prompt.md
└── docs/
    ├── KanriTimer_v2_Requirements.md
    └── KanriTimer_v2_Design.md (このファイル)
```

### 2.2 設計の理由

- **機能別モジュール分離**: Phase 2での拡張が容易
- **環境別設定**: development/production で設定を分離
- **requirements分離**: 開発用と本番用のライブラリを分離
- **コンポーネント分離**: 共通/タイマー/管理でディレクトリを分離

---

## 3. REST API インターフェース

### 3.1 メンバー管理 API

#### `GET /api/members/`
**目的**: アクティブなメンバー一覧を取得

**レスポンス** (200 OK):
```json
[
  {
    "id": 1,
    "name": "よんく",
    "is_active": true,
    "has_line_linked": true
  }
]
```

---

### 3.2 タイマー管理 API

#### `GET /api/timers/`
**目的**: タイマー一覧を取得（order順）

**レスポンス** (200 OK):
```json
[
  {
    "id": 1,
    "band_name": "Band A",
    "minutes": 15,
    "members": [
      {"id": 1, "name": "よんく"},
      {"id": 2, "name": "あお"},
      {"id": 3, "name": "キャロ"}
    ],
    "order": 1,
    "actual_seconds": 923,
    "time_difference": "+2:23",
    "completed_at": "2026-01-02T10:15:23Z",
    "is_completed": true
  }
]
```

#### `POST /api/timers/`
**目的**: 新しいタイマーを作成

**リクエスト**:
```json
{
  "band_name": "Band A",
  "minutes": 15,
  "member1_id": 1,
  "member2_id": 2,
  "member3_id": 3
}
```

**バリデーション**:
- `band_name`: 必須、最大50文字
- `minutes`: 必須、正の整数（デフォルト15）
- `member1_id`, `member2_id`, `member3_id`: 必須、存在するメンバーID

**レスポンス** (201 Created):
```json
{
  "id": 4,
  "band_name": "Band A",
  "minutes": 15,
  "members": [
    {"id": 1, "name": "よんく"},
    {"id": 2, "name": "あお"},
    {"id": 3, "name": "キャロ"}
  ],
  "order": 4,
  "is_completed": false
}
```

#### `PUT /api/timers/{id}/`
**目的**: タイマーを更新

**制約**:
- 実行中のタイマーは編集不可
- 完了済みのタイマーは編集不可

#### `DELETE /api/timers/{id}/`
**目的**: タイマーを削除

**制約**:
- 実行中のタイマーは削除不可

#### `POST /api/timers/reorder/`
**目的**: タイマーの順序を変更（ドラッグ&ドロップ用）

**リクエスト**:
```json
{
  "timer_ids": [3, 1, 2, 4]
}
```

---

### 3.3 タイマー操作 API

#### `GET /api/timer-state/`
**目的**: 現在のタイマー状態を取得

**レスポンス** (200 OK):
```json
{
  "current_timer": {
    "id": 1,
    "band_name": "Band A",
    "minutes": 15,
    "members": ["よんく", "あお", "キャロ"]
  },
  "next_timer": {
    "id": 2,
    "band_name": "Band B",
    "members": ["いぶき", "そら", "茈"]
  },
  "started_at": "2026-01-02T10:00:00Z",
  "paused_at": null,
  "elapsed_seconds": 300,
  "remaining_seconds": 600,
  "is_running": true,
  "is_paused": false,
  "total_time_difference": "+3:24",
  "total_time_difference_display": "+3:24 押し🔴"
}
```

#### `POST /api/timer-state/start/`
**目的**: タイマーを開始

**リクエスト**:
```json
{
  "timer_id": 1  // オプション。指定しない場合は最初の未完了タイマー
}
```

**処理**:
1. `TimerState.current_timer` に指定タイマーをセット
2. `started_at` に現在時刻
3. `is_running = True`
4. WebSocketで全クライアントに `timer.started` イベント送信

#### `POST /api/timer-state/pause/`
**目的**: タイマーを一時停止

#### `POST /api/timer-state/resume/`
**目的**: タイマーを再開

#### `POST /api/timer-state/skip/`
**目的**: タイマーをスキップして次へ

---

### 3.4 LINE連携 API

#### `POST /api/line/webhook/`
**目的**: LINE Messaging APIからのWebhook受信

**処理**:
1. 署名検証（`X-Line-Signature`）
2. メッセージテキストで `Member` を検索
3. 一致したら `line_user_id` を更新
4. 返信メッセージを送信

---

## 4. WebSocket インターフェース

### 4.1 接続

**エンドポイント**: `ws://localhost:8000/ws/timer/`（開発環境）

**接続グループ**: `timer_updates`

### 4.2 Server → Client イベント

#### `timer.started` - タイマー開始

**データ形式**:
```json
{
  "type": "timer.started",
  "data": {
    "timer_id": 1,
    "band_name": "Band A",
    "minutes": 15,
    "members": ["よんく", "あお", "キャロ"],
    "started_at": "2026-01-02T10:00:00Z",
    "next_timer": {
      "id": 2,
      "band_name": "Band B",
      "members": ["いぶき", "そら", "茈"]
    }
  }
}
```

#### `timer.updated` - タイマー更新（1秒ごと）

**データ形式**:
```json
{
  "type": "timer.updated",
  "data": {
    "timer_id": 1,
    "elapsed_seconds": 300,
    "remaining_seconds": 600,
    "remaining_display": "10:00",
    "total_time_difference": "+3:24",
    "total_time_difference_display": "+3:24 押し🔴"
  }
}
```

#### `timer.paused` - タイマー一時停止

**データ形式**:
```json
{
  "type": "timer.paused",
  "data": {
    "timer_id": 1,
    "paused_at": "2026-01-02T10:05:00Z",
    "elapsed_seconds": 300,
    "remaining_seconds": 600
  }
}
```

#### `timer.resumed` - タイマー再開

**データ形式**:
```json
{
  "type": "timer.resumed",
  "data": {
    "timer_id": 1,
    "resumed_at": "2026-01-02T10:07:00Z",
    "elapsed_seconds": 300,
    "remaining_seconds": 600
  }
}
```

#### `timer.skipped` - タイマースキップ

**データ形式**:
```json
{
  "type": "timer.skipped",
  "data": {
    "skipped_timer": {
      "id": 1,
      "band_name": "Band A",
      "actual_seconds": 600,
      "time_difference": "+2:00"
    },
    "next_timer": {
      "id": 2,
      "band_name": "Band B",
      "minutes": 15,
      "members": ["いぶき", "そら", "茈"]
    },
    "started_at": "2026-01-02T10:10:00Z"
  }
}
```

#### `timer.completed` - タイマー完了（自動遷移）

**データ形式**:
```json
{
  "type": "timer.completed",
  "data": {
    "completed_timer": {
      "id": 1,
      "band_name": "Band A",
      "actual_seconds": 923,
      "time_difference": "+2:23",
      "completed_at": "2026-01-02T10:15:23Z"
    },
    "next_timer": {
      "id": 2,
      "band_name": "Band B",
      "minutes": 15,
      "members": ["いぶき", "そら", "茈"],
      "started_at": "2026-01-02T10:15:23Z"
    },
    "total_time_difference": "+3:24",
    "total_time_difference_display": "+3:24 押し🔴"
  }
}
```

#### `timer.all_completed` - 全タイマー完了

**データ形式**:
```json
{
  "type": "timer.all_completed",
  "data": {
    "completed_timer": {
      "id": 4,
      "band_name": "Band D",
      "actual_seconds": 880,
      "time_difference": "-0:40",
      "completed_at": "2026-01-02T11:00:00Z"
    },
    "total_time_difference": "+5:12",
    "total_time_difference_display": "+5:12 押し🔴",
    "summary": {
      "total_timers": 4,
      "total_planned_seconds": 3600,
      "total_actual_seconds": 3912
    }
  }
}
```

#### `timer.list_updated` - タイマー一覧更新

**データ形式**:
```json
{
  "type": "timer.list_updated",
  "data": {
    "action": "created",  // "created", "updated", "deleted", "reordered"
    "timers": [
      {
        "id": 1,
        "band_name": "Band A",
        "minutes": 15,
        "members": ["よんく", "あお", "キャロ"],
        "order": 1,
        "is_completed": false
      }
    ]
  }
}
```

---

## 5. Celery タスク

### 5.1 タスク定義

#### タスク1: `update_timer_state`

**実行頻度**: 1秒ごと（Celery Beat）

**処理内容**:
1. タイマーが実行中か確認
2. 残り時間を計算
3. WebSocketで全デバイスに `timer.updated` イベント送信
4. タイマーが0:00になったら `complete_current_timer` を呼び出し

**ファイル**: `backend/apps/timers/tasks.py`

```python
@shared_task
def update_timer_state():
    """
    タイマー状態を更新し、WebSocketで配信する
    Celery Beatで1秒ごとに実行される
    """
    try:
        timer_state = TimerState.objects.first()

        if not timer_state or not timer_state.is_running or timer_state.is_paused:
            return

        elapsed = (timezone.now() - timer_state.started_at).total_seconds()
        total_seconds = timer_state.current_timer.minutes * 60
        remaining = total_seconds - elapsed

        # WebSocketで配信
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'timer_updates',
            {
                'type': 'timer.updated',
                'data': {
                    'timer_id': timer_state.current_timer.id,
                    'elapsed_seconds': int(elapsed),
                    'remaining_seconds': int(remaining),
                    'remaining_display': format_time(remaining),
                    'total_time_difference': timer_state.total_time_difference_display
                }
            }
        )

        # タイマー完了チェック
        if remaining <= 0:
            complete_current_timer(timer_state)

    except Exception as e:
        logger.error(f"update_timer_state error: {e}")
```

---

#### タスク2: `check_and_send_line_notifications`

**実行頻度**: 1秒ごと（Celery Beat）

**処理内容**:
1. タイマーが実行中か確認
2. 次のタイマーまで残り5分（300秒）か確認
3. YES → 次のタイマーの担当者にLINE通知
4. 重複通知を防ぐ（キャッシュで通知済みフラグ）

**ファイル**: `backend/apps/timers/tasks.py`

```python
@shared_task
def check_and_send_line_notifications():
    """
    次のタイマーまで残り5分になったらLINE通知を送信
    Celery Beatで1秒ごとに実行される
    """
    try:
        timer_state = TimerState.objects.first()

        if not timer_state or not timer_state.is_running or timer_state.is_paused:
            return

        elapsed = (timezone.now() - timer_state.started_at).total_seconds()
        total_seconds = timer_state.current_timer.minutes * 60
        remaining = total_seconds - elapsed

        # 残り5分（300秒）のタイミングか確認（299〜301秒の範囲）
        if not (299 <= remaining <= 301):
            return

        next_timer = Timer.objects.filter(
            order__gt=timer_state.current_timer.order,
            completed_at__isnull=True
        ).first()

        if not next_timer:
            return

        # 通知済みフラグをチェック
        cache_key = f'notification_sent_{next_timer.id}'
        if cache.get(cache_key):
            return

        # 担当者にLINE通知を送信
        line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
        members = [next_timer.member1, next_timer.member2, next_timer.member3]

        for member in members:
            if member.line_user_id:
                message = (
                    f'【KanriTimer】\n'
                    f'次は「{next_timer.band_name}」の担当です。\n'
                    f'あと5分で開始します🎵'
                )
                line_bot_api.push_message(
                    member.line_user_id,
                    TextSendMessage(text=message)
                )

        # 通知済みフラグを設定（10分間有効）
        cache.set(cache_key, True, timeout=600)

    except Exception as e:
        logger.error(f"check_and_send_line_notifications error: {e}")
```

---

#### タスク3: `complete_current_timer`

**実行タイミング**: `update_timer_state` から呼び出される

**処理内容**:
1. 現在のタイマーに実際の経過時間を記録
2. 完了時刻を記録
3. 次のタイマーがあれば自動開始
4. WebSocketで `timer.completed` または `timer.all_completed` イベント送信

---

### 5.2 Celery Beat スケジュール

**設定ファイル**: `backend/backend/settings/base.py`

```python
CELERY_BEAT_SCHEDULE = {
    'update-timer-state': {
        'task': 'apps.timers.tasks.update_timer_state',
        'schedule': 1.0,  # 1秒ごと
    },
    'check-line-notifications': {
        'task': 'apps.timers.tasks.check_and_send_line_notifications',
        'schedule': 1.0,  # 1秒ごと
    },
}
```

---

## 6. React コンポーネント

### 6.1 コンポーネント構成

```
components/
├── common/                      # 共通コンポーネント
│   ├── Button.jsx
│   ├── Modal.jsx
│   └── LoadingSpinner.jsx
├── timer/                       # タイマー関連
│   ├── CurrentTimer.jsx         # 現在のタイマー表示
│   ├── NextTimer.jsx            # 次のタイマー表示
│   ├── TimerControls.jsx        # 操作ボタン（PC専用）
│   ├── TimerList.jsx            # タイマー一覧
│   ├── TimerListItem.jsx        # タイマー一覧の1項目
│   ├── TimeDisplay.jsx          # 時間表示（MM:SS）
│   └── TimeDifferenceDisplay.jsx # 押し巻き表示
└── admin/                       # 管理機能（PC専用）
    ├── TimerForm.jsx            # タイマー作成/編集フォーム
    ├── TimerFormModal.jsx       # タイマーフォームモーダル
    └── MemberSelect.jsx         # メンバー選択ドロップダウン
```

### 6.2 主要コンポーネント

#### `App.jsx`

**役割**: アプリ全体の構造とレイアウト

**処理**:
- デバイス判定（PC/スマホ）
- WebSocket接続の初期化
- キーボードショートカットの設定

```jsx
function App() {
  useWebSocket();
  useKeyboard();

  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-blue-600 text-white p-4">
        <h1 className="text-2xl font-bold">KanriTimer 2.0</h1>
      </header>

      <main className="container mx-auto p-4">
        {isMobile ? (
          <div className="space-y-4">
            <CurrentTimer />
            <TimeDifferenceDisplay />
            <NextTimer />
            <TimerList />
          </div>
        ) : (
          <div className="grid grid-cols-3 gap-4">
            <div className="col-span-2 space-y-4">
              <CurrentTimer />
              <TimerControls />
              <NextTimer />
              <TimeDifferenceDisplay />
            </div>
            <div>
              <TimerList />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
```

---

#### `CurrentTimer.jsx`

**役割**: 現在実行中のタイマーを大きく表示

**表示内容**:
- バンド名
- 残り時間（MM:SS）
- 担当者（3名）
- 状態（実行中🔴/一時停止⏸️/待機中）

---

#### `TimerControls.jsx`

**役割**: タイマーの操作ボタン（開始/一時停止/再開/スキップ）

**表示条件**: `isMobile === false` の時のみ

---

#### `TimerList.jsx`

**役割**: 全タイマーの一覧表示とドラッグ&ドロップ順序変更

**機能**:
- タイマー一覧表示
- ドラッグ&ドロップで順序変更（PC専用）
- タイマー追加ボタン（PC専用）

---

### 6.3 Zustand Store

#### `timerStore.js`

```javascript
export const useTimerStore = create((set) => ({
  // 状態
  currentTimer: null,
  nextTimer: null,
  timers: [],
  remainingSeconds: 0,
  isRunning: false,
  isPaused: false,
  totalTimeDifference: '+0:00 定刻通り⚪',

  // アクション
  setCurrentTimer: (timer) => set({ currentTimer: timer }),
  setNextTimer: (timer) => set({ nextTimer: timer }),
  setTimers: (timers) => set({ timers }),
  setRemainingSeconds: (seconds) => set({ remainingSeconds: seconds }),
  setIsRunning: (isRunning) => set({ isRunning }),
  setIsPaused: (isPaused) => set({ isPaused }),
  setTotalTimeDifference: (diff) => set({ totalTimeDifference: diff }),

  // WebSocketから受信した状態を更新
  updateFromWebSocket: (data) => set((state) => ({
    ...state,
    ...data
  })),
}));
```

---

### 6.4 カスタムフック

#### `useWebSocket.js`

**役割**: WebSocket接続とメッセージ受信処理

```javascript
function useWebSocket() {
  const wsRef = useRef(null);
  const { updateFromWebSocket } = useTimerStore();

  useEffect(() => {
    const connect = () => {
      const ws = new WebSocket(WS_URL);

      ws.onopen = () => {
        console.log('WebSocket接続完了');
      };

      ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        handleWebSocketMessage(message);
      };

      ws.onclose = () => {
        console.log('WebSocket切断。5秒後に再接続...');
        setTimeout(connect, 5000);
      };

      wsRef.current = ws;
    };

    connect();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);
}
```

---

#### `useKeyboard.js`

**役割**: キーボードショートカット（PCのみ）

**ショートカット**:
- **スペースキー**: タイマー開始/一時停止/再開
- **右矢印キー**: タイマースキップ

```javascript
function useKeyboard() {
  const { isRunning, isPaused } = useTimerStore();

  useEffect(() => {
    if (isMobile) return;

    const handleKeyDown = async (e) => {
      if (e.code === 'Space') {
        e.preventDefault();

        if (!isRunning) {
          await startTimer();
        } else if (isPaused) {
          await resumeTimer();
        } else {
          await pauseTimer();
        }
      }

      if (e.code === 'ArrowRight') {
        e.preventDefault();

        if (isRunning) {
          await skipTimer();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isRunning, isPaused]);
}
```

---

## 7. 技術スタック

### 7.1 フロントエンド

| 技術 | バージョン | 用途 |
|------|-----------|------|
| React | 18 | UIフレームワーク |
| Vite | 最新 | ビルドツール |
| TailwindCSS | 最新 | スタイリング |
| Zustand | 最新 | 状態管理 |
| Axios | 最新 | HTTP通信 |
| react-device-detect | 最新 | デバイス判定 |
| @dnd-kit/core | 最新 | ドラッグ&ドロップ |

### 7.2 バックエンド

| 技術 | バージョン | 用途 |
|------|-----------|------|
| Django | 4.2.20 | Webフレームワーク |
| Django REST Framework | 3.14.0 | REST API |
| Django Channels | 4.0.0 | WebSocket |
| Daphne | 4.0.0 | ASGIサーバー |
| channels-redis | 4.1.0 | WebSocketバックエンド |
| Celery | 5.3.4 | タスクキュー |
| Redis | 5.0.1 | キャッシュ/メッセージブローカー |
| PostgreSQL | 最新 | データベース |
| line-bot-sdk | 3.5.0 | LINE連携 |

---

## 8. 開発環境

### 8.1 Docker Compose構成

```yaml
services:
  db:
    image: postgres:15

  redis:
    image: redis:7

  web:
    build: ./backend
    depends_on:
      - db
      - redis

  celery:
    build: ./backend
    command: celery -A backend worker -l info
    depends_on:
      - db
      - redis

  celery-beat:
    build: ./backend
    command: celery -A backend beat -l info
    depends_on:
      - db
      - redis

  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
```

### 8.2 環境変数

```bash
# Django
SECRET_KEY=<ランダム生成>
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://user:password@db:5432/kanritimer

# Redis
REDIS_URL=redis://redis:6379/0

# LINE
LINE_CHANNEL_ACCESS_TOKEN=<LINE Developers Console>
LINE_CHANNEL_SECRET=<LINE Developers Console>

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:5173
```

---

## 9. 実装の次のステップ

この設計書に基づいて、以下の順番で実装を進めます：

### Phase 2: 実装の提案と決定

1. ✅ ディレクトリ構成の確定
2. ✅ インターフェースの先行定義
3. 🔄 実装の提案（複数案）
4. ⏳ 人間の意思決定
5. ⏳ 実装開始

---

**ドキュメント終了**
