# KanriTimer 2.0 要件定義書（最終確定版）

**作成日**: 2026-01-02
**プロジェクト**: KanriTimer 2.0
**目的**: ライブイベントのリハーサル進行管理システム

---

## 1. システム概要

### 1.1 システム名
**KanriTimer 2.0**

### 1.2 目的
ライブイベントのリハーサル進行を効率的に管理し、担当者への自動LINE通知により円滑な運営を実現する

### 1.3 ユーザー種類と権限

| ユーザー種類 | アクセス方法 | 権限 |
|--------------|--------------|------|
| **システム管理者** | `/admin` (Django Admin) | メンバー管理、全システム管理 |
| **管理者** | PC（通常画面） | タイマー管理操作 + タイマー実行操作 |
| **その他利用者** | スマホ（通常画面） | 閲覧のみ |

### 1.4 操作権限の詳細

#### PCからアクセス（管理者）
✅ **タイマー管理操作**
- タイマー作成（バンド名、管理1〜3の登録）
- タイマー編集
- タイマー削除
- タイマー順序変更（ドラッグ&ドロップ）

✅ **タイマー実行操作**
- 開始
- 一時停止
- 再開
- スキップ

#### スマホからアクセス（その他利用者）
✅ **閲覧のみ**
- 現在のタイマー表示
- 次のタイマー表示
- タイマー一覧表示
- ❌ 操作ボタン非表示

#### Django Admin（システム管理者）
✅ **メンバー管理**
- メンバー追加/編集/削除
- LINE User ID設定

### 1.5 アーキテクチャ
- **フロントエンド**: React 18 + Vite + TailwindCSS
- **バックエンド**: Django 4.2 + Django REST Framework
- **リアルタイム通信**: Django Channels + WebSocket
- **データベース**: PostgreSQL
- **認証**: **なし**（デバイス判定のみ）
- **インフラ**: Render

### 1.6 納期
**Phase 1: 10日以内**

---

## 2. 部局・担当者数の定義

| 部局 | 担当者数 | Phase 1 | Phase 2 |
|------|----------|---------|---------|
| 管理 | 3人 | ✅ 実装 | - |
| 渉外 | 2人 | - | ✅ 実装 |
| 合評 | 2人 | - | ✅ 実装 |
| 会計 | 1人 | - | ✅ 実装 |
| C協 | 1人 | - | ✅ 実装 |
| 書記 | 1人 | - | ✅ 実装 |
| **合計** | **10人/バンド** | **3人** | **10人** |

**Phase 1では管理部局（3人）のみを実装**

---

## 3. 機能要件

### 🔴 Phase 1: 必須機能（10日以内）

#### 3.1 タイマー状態の永続化
**要件**:
- サーバー側でタイマー状態を管理
- 開始時刻、一時停止時刻、経過時間をデータベースに保存
- ページリロードしても状態を復元
- ブラウザを閉じても状態を保持
- タイマー完了時に実際の経過時間を記録（押し巻き計算用）

**API**:
- `GET /api/timer-state/` - 現在のタイマー状態取得
- `POST /api/timer-state/start/` - タイマー開始
- `POST /api/timer-state/pause/` - タイマー一時停止
- `POST /api/timer-state/resume/` - タイマー再開
- `POST /api/timer-state/skip/` - タイマースキップ

#### 3.2 マルチデバイス対応（リアルタイム同期）
**要件**:
- WebSocketでリアルタイム配信
- 全デバイスで同じタイマー状態を表示
- デバイス判定（User-Agent）で自動的にUI切り替え
  - **PC**: 操作ボタン表示
  - **スマホ**: 操作ボタン非表示

**WebSocketイベント**:
- `timer.started` - タイマー開始
- `timer.paused` - タイマー一時停止
- `timer.resumed` - タイマー再開
- `timer.skipped` - タイマースキップ
- `timer.updated` - タイマー更新（1秒ごと）
- `timer.completed` - タイマー完了（次のタイマーに自動遷移）

#### 3.3 タイマー管理（管理部局のみ）
**Phase 1の範囲**:
- タイマーのCRUD操作（PC画面から）
- バンド名、持ち時間（一律15分）、管理部局の担当者3名
- 順序変更（ドラッグ&ドロップ）
- タイマー完了時に自動的に次のタイマーを開始

**データモデル**:
```python
class Member(models.Model):
    """メンバーマスタ"""
    name = CharField(max_length=20, unique=True)
    line_user_id = CharField(max_length=100, blank=True, null=True)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'メンバー'
        verbose_name_plural = 'メンバー'

class Timer(models.Model):
    """タイマー（バンドごと）"""
    band_name = CharField(max_length=50)
    minutes = IntegerField(default=15)  # 予定時間（分）
    member1 = ForeignKey(Member, related_name='timer_member1', on_delete=models.PROTECT)
    member2 = ForeignKey(Member, related_name='timer_member2', on_delete=models.PROTECT)
    member3 = ForeignKey(Member, related_name='timer_member3', on_delete=models.PROTECT)
    order = IntegerField()  # 実行順序
    actual_seconds = IntegerField(null=True, blank=True)  # 実際にかかった時間（秒）
    completed_at = DateTimeField(null=True, blank=True)  # 完了時刻
    created_at = DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']
        verbose_name = 'タイマー'
        verbose_name_plural = 'タイマー'

    @property
    def time_difference(self):
        """予定時間との差分（秒）"""
        if self.actual_seconds is None:
            return 0
        return self.actual_seconds - (self.minutes * 60)

class TimerState(models.Model):
    """タイマー状態（Singleton）"""
    current_timer = ForeignKey(Timer, null=True, blank=True, on_delete=models.SET_NULL)
    started_at = DateTimeField(null=True, blank=True)
    paused_at = DateTimeField(null=True, blank=True)
    elapsed_seconds = IntegerField(default=0)  # 一時停止時の経過時間
    is_running = BooleanField(default=False)
    is_paused = BooleanField(default=False)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'タイマー状態'
        verbose_name_plural = 'タイマー状態'

    @property
    def total_time_difference(self):
        """全体の押し巻き（秒）"""
        completed_timers = Timer.objects.filter(actual_seconds__isnull=False)
        return sum(timer.time_difference for timer in completed_timers)

    @property
    def total_time_difference_display(self):
        """全体の押し巻きを表示用フォーマットで返す"""
        diff = self.total_time_difference
        sign = '+' if diff >= 0 else '-'
        abs_diff = abs(diff)
        minutes = abs_diff // 60
        seconds = abs_diff % 60

        if diff > 0:
            status = '押し🔴'
        elif diff < 0:
            status = '巻き🟢'
        else:
            status = '定刻通り⚪'

        return f"{sign}{minutes}:{seconds:02d} {status}"
```

#### 3.4 押し巻き表示
**要件**:
- 全体でどのくらい押している（巻いている）かを常に表示
- 各バンドの実際の時間を記録（システム内部で保持）
- 個別バンドの押し巻きは表示しない
- 全体の合計のみ表示

**表示ルール**:
- **プラス（+）**: 🔴 押し（遅れている）
- **マイナス（-）**: 🟢 巻き（早い）
- **±0**: ⚪ 定刻通り

**計算方法**:
```
Band A: 予定15分 → 実際17:23 → +2:23（押し）
Band B: 予定15分 → 実際16:01 → +1:01（押し）
全体: +2:23 + 1:01 = +3:24（押し）🔴
```

#### 3.5 LINE通知機能（Messaging API・名前ベース連携）
**要件**:
- 次のバンドの開始**5分前**に管理部局の担当者3名に通知
- LINE Messaging API使用
- 名前ベースで自動連携

**LINE連携フロー**:
1. システム管理者がDjango Adminでメンバーを登録
2. メンバーがLINE Botを友達追加
3. メンバーが自分の名前を送信（例: 「よんく」）
4. Webhookで受信 → 名前でメンバーを検索
5. 一致したメンバーのLINE User IDを自動更新
6. 連携完了メッセージを送信

**通知内容**:
```
【KanriTimer】
次は「Band A」の担当です。
あと5分で開始します🎵
```

**技術実装**:
- Celery Beatで1秒ごとにタイマー状態をチェック
- 次のタイマーまで残り5分（300秒）になったらプッシュ通知
- 通知済みフラグで重複防止

#### 3.6 デバイス判定
**要件**:
- User-Agentでデバイスを自動判定
- フロントエンドで判定 → PC/スマホで異なるUIを表示

**実装**:
```javascript
// react-device-detect ライブラリ使用
import { isMobile } from 'react-device-detect';

// PCの場合のみ操作ボタンを表示
{!isMobile && (
  <div>
    <button>一時停止</button>
    <button>スキップ</button>
  </div>
)}
```

#### 3.7 キーボードショートカット（PCのみ）
**要件**:
- **スペースキー**: タイマー開始/一時停止/再開
- **右矢印キー**: タイマースキップ

---

### 🟡 Phase 2: 将来的な拡張

#### 3.8 全部局のメンバー管理
**要件**:
- 渉外、合評、会計、C協、書記の追加
- Departmentモデル実装
- TimerAssignmentモデルで部局ごとの担当管理

**データモデル拡張**:
```python
class Department(models.Model):
    name = CharField(max_length=20)  # 管理、渉外、合評、会計、C協、書記
    required_members = IntegerField()  # 必要人数（1〜3）

class Member(models.Model):
    # 既存フィールド
    department = ForeignKey(Department)  # 追加

class TimerAssignment(models.Model):
    timer = ForeignKey(Timer)
    department = ForeignKey(Department)
    member = ForeignKey(Member)
    order = IntegerField()  # 担当1, 2, 3...
```

#### 3.9 バンドメンバー管理
**要件**:
- バンドの登録
- 出演メンバーの登録（平均4人、最大6人、最少3人）
- 仕事割生成時に使用

**データモデル**:
```python
class Band(models.Model):
    name = CharField(max_length=50)

class BandMember(models.Model):
    band = ForeignKey(Band)
    member = ForeignKey(Member)
```

#### 3.10 エクセルインポート機能
**要件**:
- エクセルファイルをアップロード
- 自動でタイマー・担当者データを生成

**エクセルフォーマット**:
```
| バンド名 | 渉外1 | 渉外2 | 管理1 | 管理2 | 管理3 | 合評1 | 合評2 | 会計1 | C協1 | 書記1 |
|----------|-------|-------|-------|-------|-------|-------|-------|-------|------|-------|
| Band A   | 〇〇  | △△   | よんく | あお  | キャロ | ××   | ◇◇   | ☆☆   | ◎◎  | ●●   |
```

#### 3.11 仕事割自動生成
**制約条件**:
1. **バンドメンバーは前後1バンドの仕事に入らない**（最優先）
   - 例: Band Bのメンバーは、Band A、Band B、Band Cの仕事NG
2. 全員の仕事量が均等
3. できるだけ同じ人が同じバンドを担当

**アルゴリズム案**:
```python
def generate_assignments(bands, members):
    for i, band in enumerate(bands):
        # 前後1バンドのメンバーをブラックリスト化
        blacklist = set()
        if i > 0:
            blacklist.update(bands[i-1].members)
        blacklist.update(band.members)
        if i < len(bands) - 1:
            blacklist.update(bands[i+1].members)

        # 部局ごとに担当者を割り当て
        for dept in departments:
            available = [m for m in members if m.department == dept and m not in blacklist]
            # 仕事量が少ない順にソート
            available.sort(key=lambda m: m.assignment_count)
            # 割り当て
            assign_members(band, dept, available, dept.required_members)
```

#### 3.12 履歴・統計機能
- 過去のリハーサル記録
- メンバーごとの仕事回数集計
- バンドごとの押し巻き傾向

---

## 4. 技術スタック

### 4.1 フロントエンド
- **フレームワーク**: React 18
- **ビルドツール**: Vite
- **スタイリング**: TailwindCSS
- **状態管理**: Zustand
- **HTTP通信**: Axios
- **WebSocket**: Socket.IO Client または native WebSocket
- **ルーティング**: React Router
- **デバイス判定**: react-device-detect
- **ドラッグ&ドロップ**: @dnd-kit/core

### 4.2 バックエンド
- **フレームワーク**: Django 4.2.20
- **REST API**: Django REST Framework
- **WebSocket**: Django Channels + Daphne + Redis
- **データベース**: PostgreSQL
- **タスクキュー**: Celery + Celery Beat + Redis
- **CORS**: django-cors-headers
- **認証**: **なし**

### 4.3 外部API
- **LINE通知**: LINE Messaging API

### 4.4 インフラ
- **ホスティング**: Render
  - Web Service: Django (Gunicorn + Daphne)
  - PostgreSQL Database
  - Redis

### 4.5 開発環境
- Docker Compose
  - web: Django
  - db: PostgreSQL
  - redis: Redis
  - celery: Celery Worker
  - celery-beat: Celery Beat
  - frontend: Vite dev server (開発時のみ)

---

## 5. API設計（Phase 1）

### 5.1 REST API（認証なし）

#### メンバー管理（読み取りのみ）
```
GET /api/members/
```
**レスポンス**:
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

#### タイマー管理
```
GET /api/timers/
POST /api/timers/
GET /api/timers/{id}/
PUT /api/timers/{id}/
DELETE /api/timers/{id}/
POST /api/timers/reorder/
```

**タイマー作成リクエスト**:
```json
{
  "band_name": "Band A",
  "minutes": 15,
  "member1_id": 1,
  "member2_id": 2,
  "member3_id": 3
}
```

**順序変更リクエスト**:
```json
{
  "timer_ids": [3, 1, 2, 4]
}
```

#### タイマー操作
```
GET /api/timer-state/
POST /api/timer-state/start/
POST /api/timer-state/pause/
POST /api/timer-state/resume/
POST /api/timer-state/skip/
```

**タイマー状態レスポンス**:
```json
{
  "current_timer": {
    "id": 1,
    "band_name": "Band A",
    "minutes": 15,
    "members": ["よんく", "あお", "キャロ"]
  },
  "started_at": "2026-01-02T10:00:00Z",
  "elapsed_seconds": 300,
  "remaining_seconds": 600,
  "is_running": true,
  "is_paused": false,
  "total_time_difference": "+3:24 押し🔴"
}
```

#### LINE連携
```
POST /api/line/webhook/
```

### 5.2 WebSocket

#### 接続
```javascript
const socket = io('wss://kanritimer.onrender.com');
```

#### イベント（Server → Client）
```javascript
// タイマー開始
{
  type: 'timer.started',
  data: {
    timer_id: 1,
    band_name: 'Band A',
    started_at: '2026-01-02T10:00:00Z'
  }
}

// タイマー更新（1秒ごと）
{
  type: 'timer.updated',
  data: {
    timer_id: 1,
    elapsed_seconds: 300,
    remaining_seconds: 600,
    total_time_difference: '+3:24 押し🔴'
  }
}

// タイマー一時停止
{
  type: 'timer.paused',
  data: {
    timer_id: 1,
    paused_at: '2026-01-02T10:05:00Z',
    elapsed_seconds: 300
  }
}

// タイマー完了（次のタイマーに自動遷移）
{
  type: 'timer.completed',
  data: {
    completed_timer_id: 1,
    next_timer_id: 2,
    actual_seconds: 923,
    time_difference: '+2:23'
  }
}
```

---

## 6. 画面構成（Phase 1）

### 6.1 PC版

#### メイン画面 `/`

```
┌──────────────────────────────────────────────┐
│ KanriTimer 2.0                               │
├──────────────────────────────────────────────┤
│                                              │
│  ┌────────────────────────┐  ┌────────────┐ │
│  │ 現在のタイマー [実行中🔴]│  │タイマー一覧│ │
│  │                        │  │            │ │
│  │     Band C             │  │✓ Band A    │ │
│  │     12:34              │  │✓ Band B    │ │
│  │                        │  │▶ Band C    │ │
│  │  いぶき、そら、茈      │  │  Band D    │ │
│  │                        │  │            │ │
│  │ ─────────────────────│  │[＋追加]    │ │
│  │ 全体: +3:24 押し🔴     │  └────────────┘ │
│  │ ─────────────────────│               │
│  │                        │               │
│  │ [一時停止] [スキップ]  │               │
│  └────────────────────────┘               │
│                                              │
│  次のタイマー:                               │
│  Band D (〇〇、△△、××)                    │
│                                              │
└──────────────────────────────────────────────┘
```

**機能**:
- 現在のタイマー表示（大きく）
- 次のタイマー表示
- タイマー一覧（ドラッグ&ドロップで順序変更可能）
- 操作ボタン（開始/一時停止/再開/スキップ）
- タイマー追加ボタン
- 各タイマーの編集/削除（一覧のホバー時に表示）

### 6.2 スマホ版

#### メイン画面（閲覧専用） `/`

```
┌─────────────────┐
│ KanriTimer 2.0  │
├─────────────────┤
│                 │
│ 現在のタイマー   │
│   [実行中🔴]     │
│                 │
│   Band C        │
│   12:34         │
│                 │
│ いぶき、そら、茈│
│                 │
│ ───────────────│
│ 全体: +3:24 押し│
│       🔴        │
│ ───────────────│
│                 │
│ 次のタイマー:   │
│ Band D          │
│ (〇〇、△△、××) │
│                 │
│ ───────────────│
│ タイマー一覧    │
│ ✓ Band A        │
│ ✓ Band B        │
│ ▶ Band C        │
│   Band D        │
│                 │
└─────────────────┘
```

**機能**:
- 現在のタイマー表示
- 次のタイマー表示
- タイマー一覧（縦スクロール）
- **操作ボタンなし**
- **タイマー追加/編集/削除ボタンなし**

---

## 7. 実装スケジュール（10日間・Phase 1のみ）

### Day 1: 環境構築
- [ ] プロジェクト構成作成
  - `/backend` - Django
  - `/frontend` - React + Vite
- [ ] Docker Compose設定
  - PostgreSQL, Redis, Django, Celery, React
- [ ] Django + DRF セットアップ
- [ ] React + Vite + TailwindCSS セットアップ
- [ ] 基本的な通信確認

### Day 2: データモデル・管理画面
- [ ] モデル実装（Member, Timer, TimerState）
- [ ] Django Admin設定（メンバー管理用）
- [ ] マイグレーション
- [ ] 初期データ投入（テスト用メンバー）

### Day 3: タイマーAPI実装
- [ ] タイマーCRUD API
- [ ] タイマー操作API（start/pause/resume/skip）
- [ ] TimerState管理ロジック
- [ ] 押し巻き計算ロジック
- [ ] 自動次タイマー開始ロジック

### Day 4: WebSocket + Celery
- [ ] Django Channels設定
- [ ] WebSocket Consumer実装
- [ ] タイマー状態のリアルタイム配信
- [ ] Celery + Celery Beat設定
- [ ] タイマー更新タスク（1秒ごと）
- [ ] 5分前通知タスク実装

### Day 5: フロントエンド（基本UI）
- [ ] React + Vite + TailwindCSS セットアップ
- [ ] デバイス判定実装
- [ ] メイン画面レイアウト
- [ ] タイマー表示コンポーネント
- [ ] 状態管理（Zustand）セットアップ

### Day 6: フロントエンド（タイマー機能）
- [ ] WebSocket接続・リアルタイム更新
- [ ] タイマー操作ボタン実装（PCのみ）
- [ ] タイマー一覧表示
- [ ] キーボードショートカット（スペース、矢印）
- [ ] 押し巻き表示

### Day 7: フロントエンド（タイマー管理）
- [ ] タイマー追加フォーム
- [ ] タイマー編集/削除機能
- [ ] ドラッグ&ドロップ順序変更
- [ ] メンバー選択ドロップダウン

### Day 8: LINE連携
- [ ] LINE Bot作成（LINE Developers Console）
- [ ] Webhook実装（名前ベース連携）
- [ ] プッシュ通知実装（5分前）
- [ ] 連携状態の表示

### Day 9: レスポンシブ対応
- [ ] スマホ版UI実装（閲覧専用）
- [ ] PC/スマホ判定
- [ ] エラーハンドリング
- [ ] ローディング状態の実装

### Day 10: テスト・デプロイ
- [ ] 総合テスト
- [ ] バグ修正
- [ ] Renderにデプロイ
  - PostgreSQL Database作成
  - Redis作成
  - Web Service作成（Django）
  - 環境変数設定
  - 静的ファイル設定

---

## 8. LINE Messaging API セットアップ

### 8.1 LINE Bot作成手順

1. **LINE Developers Console**にアクセス
   - https://developers.line.biz/console/

2. **Messaging API チャネル**を作成
   - Provider作成（例: KanriTimer）
   - Channel作成（例: KanriTimer Bot）

3. **Channel Access Token**を発行
   - 長期トークンを発行してコピー

4. **Webhook URL**を設定
   - `https://kanritimer.onrender.com/api/line/webhook/`

5. **Webhook**を有効化

6. **Bot情報**をメモ
   - QRコード
   - Bot Basic ID

### 8.2 名前ベース連携の実装

**Webhook処理**:
```python
from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage

line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(settings.LINE_CHANNEL_SECRET)

@api_view(['POST'])
@csrf_exempt
def line_webhook(request):
    signature = request.META['HTTP_X_LINE_SIGNATURE']
    body = request.body.decode('utf-8')

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return HttpResponse(status=400)

    return HttpResponse(status=200)

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    message_text = event.message.text

    # 名前でメンバーを検索
    try:
        member = Member.objects.get(name=message_text, is_active=True)
        member.line_user_id = user_id
        member.save()

        # 連携完了メッセージ
        reply_message = f'{member.name}さん、LINE連携が完了しました！\nリハーサルの5分前に通知が届きます🎵'
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_message)
        )
    except Member.DoesNotExist:
        reply_message = '該当するメンバーが見つかりませんでした。\n正しい名前を送信してください。'
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_message)
        )
    except Member.MultipleObjectsReturned:
        reply_message = '同じ名前のメンバーが複数います。\n管理者にお問い合わせください。'
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_message)
        )
```

### 8.3 5分前通知の実装

**Celery Task**:
```python
from celery import shared_task
from linebot import LineBotApi
from linebot.models import TextSendMessage

@shared_task
def check_and_send_notifications():
    """1秒ごとに実行されるタスク"""
    timer_state = TimerState.objects.first()

    if not timer_state or not timer_state.is_running or timer_state.is_paused:
        return

    # 残り時間を計算
    elapsed = (timezone.now() - timer_state.started_at).total_seconds()
    remaining = (timer_state.current_timer.minutes * 60) - elapsed

    # 残り5分（300秒）になったら通知
    if 299 <= remaining <= 301:  # 1秒の誤差を考慮
        # 次のタイマーを取得
        next_timer = Timer.objects.filter(
            order__gt=timer_state.current_timer.order
        ).first()

        if next_timer:
            # 次のタイマーの担当者に通知
            members = [next_timer.member1, next_timer.member2, next_timer.member3]
            line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)

            for member in members:
                if member.line_user_id:
                    message = f'【KanriTimer】\n次は「{next_timer.band_name}」の担当です。\nあと5分で開始します🎵'
                    line_bot_api.push_message(
                        member.line_user_id,
                        TextSendMessage(text=message)
                    )
```

**Celery Beat設定**:
```python
# settings.py
CELERY_BEAT_SCHEDULE = {
    'check-notifications': {
        'task': 'home.tasks.check_and_send_notifications',
        'schedule': 1.0,  # 1秒ごと
    },
}
```

---

## 9. Renderデプロイ設定

### 9.1 必要なサービス

1. **PostgreSQL Database**
   - 名前: kanritimer-db
   - Plan: Starter (無料)

2. **Redis**
   - 名前: kanritimer-redis
   - Plan: Starter (無料)

3. **Web Service**
   - 名前: kanritimer
   - Runtime: Python 3.11
   - Build Command: `pip install -r requirements.txt && python backend/manage.py collectstatic --noinput && python backend/manage.py migrate`
   - Start Command: `daphne -b 0.0.0.0 -p $PORT backend.asgi:application`

### 9.2 環境変数

```bash
DATABASE_URL=<Render提供>
REDIS_URL=<Render提供>
SECRET_KEY=<ランダム生成>
DEBUG=False
ALLOWED_HOSTS=kanritimer.onrender.com
CORS_ALLOWED_ORIGINS=https://kanritimer.onrender.com
LINE_CHANNEL_ACCESS_TOKEN=<LINE Developers Console>
LINE_CHANNEL_SECRET=<LINE Developers Console>
```

### 9.3 requirements.txt

```
Django==4.2.20
djangorestframework==3.14.0
django-cors-headers==4.3.1
channels==4.0.0
daphne==4.0.0
channels-redis==4.1.0
redis==5.0.1
celery==5.3.4
psycopg2-binary==2.9.9
gunicorn==21.2.0
line-bot-sdk==3.5.0
```

---

## 10. 実際の使用フロー

### 10.1 事前準備フェーズ（リハーサルの数日前）

#### ステップ1: システム管理者がメンバーを登録
- Django Admin (`/admin`) にアクセス
- 管理部局のメンバー全員を登録（よんく、あお、キャロ、etc.）

#### ステップ2: メンバーがLINE連携
- KanriTimer公式LINE Botを友達追加
- 自分の名前を送信（例: 「よんく」）
- 連携完了メッセージを受信

#### ステップ3: 管理者がタイマーを作成
- PC画面でメイン画面にアクセス
- 全バンド分のタイマーを作成
- ドラッグ&ドロップで順序調整

### 10.2 リハーサル当日

#### ステップ4: リハーサル開始前
- 管理者：PC画面を大型モニターに投影
- その他利用者：スマホで画面を閲覧

#### ステップ5: タイマー開始（Band A）
- 管理者が「開始」ボタンをクリック
- 全デバイスで即座に更新

#### ステップ6: 【10分経過】次の担当者にLINE通知
- タイマー残り5分になると自動通知
- 次のバンド（Band B）の担当者3名に通知

#### ステップ7: 【15分経過】Band A終了 → Band B自動開始
- Band Aのタイマーが0:00になると自動的にBand Bに切り替わり開始

#### ステップ8: 【トラブル対応】一時停止・再開
- 管理者が「一時停止」ボタンをクリック
- 全デバイスで停止状態を表示
- 問題解決後、「再開」ボタンで再開

#### ステップ9: リハーサル終了
- 全バンドのタイマーが完了
- 全体の押し巻きを確認

---

## 11. 注意事項・制約

### 11.1 Phase 1の制約
- 管理部局（3人）のみ実装
- 他の部局（渉外、合評、会計、C協、書記）はPhase 2
- エクセルインポートはPhase 2
- 仕事割自動生成はPhase 2

### 11.2 認証について
- ログイン機能なし
- PCとスマホの判定のみで権限を制御
- セキュリティが必要な場合はPhase 2で実装

### 11.3 LINE連携について
- 同姓同名のメンバーがいる場合は連携できない
- その場合はDjango AdminでLINE User IDを手動設定

### 11.4 データの再利用
- 次回のリハーサルは同じ構成でやることはない
- タイマーデータは毎回作り直す想定

---

## 12. 今後の拡張方針

### Phase 2以降で実装予定
1. 全部局のメンバー管理
2. バンドメンバー管理
3. エクセルインポート機能
4. 仕事割自動生成
5. 履歴・統計機能
6. カレンダー統合
7. 複数イベント管理
8. 認証機能（必要に応じて）

---

## 付録A: データベーススキーマ図

```
┌─────────────┐
│   Member    │
├─────────────┤
│ id (PK)     │
│ name        │
│ line_user_id│
│ is_active   │
│ created_at  │
└─────────────┘
       ↑
       │ FK (member1, member2, member3)
       │
┌─────────────────┐
│     Timer       │
├─────────────────┤
│ id (PK)         │
│ band_name       │
│ minutes         │
│ member1_id (FK) │
│ member2_id (FK) │
│ member3_id (FK) │
│ order           │
│ actual_seconds  │
│ completed_at    │
│ created_at      │
└─────────────────┘
       ↑
       │ FK (current_timer)
       │
┌─────────────────┐
│   TimerState    │
├─────────────────┤
│ id (PK)         │
│ current_timer   │
│ started_at      │
│ paused_at       │
│ elapsed_seconds │
│ is_running      │
│ is_paused       │
│ updated_at      │
└─────────────────┘
```

---

**ドキュメント終了**