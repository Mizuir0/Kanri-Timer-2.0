# メンバー管理機能

## 概要

サークルに所属する全メンバーとバンドを管理し、リハーサルの出番ごとに担当者を割り当て、通知対象を柔軟に制御する機能。

---

## 背景

### 現状
- Memberモデルには「管理」部局のメンバーのみ登録
- バンド名はタイマー作成時に直接入力
- LINE通知は全体ON/OFFのみ

### 課題
- サークル全員を管理できない
- バンドメンバーへの通知ができない
- 部局ごとの通知制御ができない

### 目標
- サークル全員をメンバー管理
- バンドとメンバーの紐付け
- リハーサルの出番ごとに担当者を割り当て
- 通知対象を細かく制御（バンドメンバー・各部局）

---

## 組織構造

```
軽音サークル
│
├── 部局（1人1つ所属）
│   ├── 管理    ← リハ進行担当（3人/バンド）
│   ├── 渉外    ← （2人/バンド）
│   ├── 合評    ← リハ仕事なし（2人/バンド）
│   ├── 会計    ← リハ仕事なし（1人/バンド）
│   ├── C協     ← リハ仕事なし（1人/バンド）
│   └── 書記    ← （1人/バンド）
│
└── バンド（1人が複数所属可）
    ├── バンドA（コピー元: BUMP OF CHICKEN）
    ├── バンドB（コピー元: Official髭男dism）
    └── ...
```

---

## データモデル

### Member（メンバー）

サークルに所属する全員を管理。

```python
class Member(models.Model):
    DEPARTMENT_CHOICES = [
        ('kanri', '管理'),
        ('shougai', '渉外'),
        ('gouhyou', '合評'),
        ('kaikei', '会計'),
        ('ckyou', 'C協'),
        ('shoki', '書記'),
    ]

    name = models.CharField(max_length=100)
    line_user_id = models.CharField(max_length=100, blank=True, null=True)
    department = models.CharField(max_length=20, choices=DEPARTMENT_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### Band（バンド）

サークル内のバンドを管理。

```python
class Band(models.Model):
    name = models.CharField(max_length=100)
    original_artist = models.CharField(max_length=100, blank=True)  # コピー元アーティスト
    members = models.ManyToManyField(Member, related_name='bands', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.original_artist:
            return f"{self.name} ({self.original_artist})"
        return self.name
```

### Timer（タイマー）※既存モデルを修正

```python
class Timer(models.Model):
    # 既存フィールド
    # band_name = models.CharField(max_length=100)  ← 削除

    # 新規フィールド
    band = models.ForeignKey(Band, on_delete=models.CASCADE, related_name='timers')

    minutes = models.PositiveIntegerField(default=15)
    order = models.PositiveIntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    actual_duration = models.DurationField(null=True, blank=True)
    # ... その他既存フィールド
```

### TimerStaff（出番担当）

各タイマー（出番）に割り当てられた担当者。

```python
class TimerStaff(models.Model):
    ROLE_CHOICES = [
        ('kanri', '管理'),
        ('shougai', '渉外'),
        ('gouhyou', '合評'),
        ('kaikei', '会計'),
        ('ckyou', 'C協'),
        ('shoki', '書記'),
    ]

    timer = models.ForeignKey(Timer, on_delete=models.CASCADE, related_name='staff')
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    class Meta:
        unique_together = ['timer', 'member', 'role']
```

### NotificationSettings（通知設定）※既存TimerStateを拡張

```python
class TimerState(SingletonModel):
    # 既存フィールド
    current_timer = models.ForeignKey(Timer, ...)
    is_running = models.BooleanField(default=False)
    is_paused = models.BooleanField(default=False)
    line_notifications_enabled = models.BooleanField(default=True)

    # 新規フィールド（通知対象設定）
    notify_band_members = models.BooleanField(default=True)
    notify_kanri = models.BooleanField(default=True)
    notify_shougai = models.BooleanField(default=True)
    notify_gouhyou = models.BooleanField(default=False)  # リハ仕事なし
    notify_kaikei = models.BooleanField(default=False)   # リハ仕事なし
    notify_ckyou = models.BooleanField(default=False)    # リハ仕事なし
    notify_shoki = models.BooleanField(default=True)
```

---

## 通知仕様

### 通知タイミング
- 5分前通知（既存機能）
- リハーサル開始通知（既存機能）
- リハーサル終了通知（既存機能）

### 通知対象の決定ロジック

```python
def get_notification_targets(timer):
    targets = []
    settings = TimerState.load()

    # バンドメンバー
    if settings.notify_band_members:
        targets.extend(timer.band.members.exclude(line_user_id=''))

    # 担当者（部局ごと）
    for staff in timer.staff.all():
        if staff.role == 'kanri' and settings.notify_kanri:
            targets.append(staff.member)
        elif staff.role == 'shougai' and settings.notify_shougai:
            targets.append(staff.member)
        elif staff.role == 'gouhyou' and settings.notify_gouhyou:
            targets.append(staff.member)
        elif staff.role == 'kaikei' and settings.notify_kaikei:
            targets.append(staff.member)
        elif staff.role == 'ckyou' and settings.notify_ckyou:
            targets.append(staff.member)
        elif staff.role == 'shoki' and settings.notify_shoki:
            targets.append(staff.member)

    # 重複排除（バンドメンバーかつ担当者の場合）
    return list(set(targets))
```

### 通知メッセージフォーマット

**バンドメンバー向け:**
```
次は「青春パンクス (BUMP OF CHICKEN)」のリハーサルです。
```

**担当者向け:**
```
次は「青春パンクス (BUMP OF CHICKEN)」の担当です。
管理: 山田、佐藤、鈴木
渉外: 田中、高橋
書記: 中村
```

**メッセージ生成ロジック:**
```python
def create_staff_notification_message(timer):
    band_display = str(timer.band)  # "バンド名 (コピー元)"

    message = f'次は「{band_display}」の担当です。\n'

    # 部局ごとにグループ化
    staff_by_role = {}
    for staff in timer.staff.all():
        role_display = staff.get_role_display()
        if role_display not in staff_by_role:
            staff_by_role[role_display] = []
        staff_by_role[role_display].append(staff.member.name)

    # 表示順序
    role_order = ['管理', '渉外', '合評', '会計', 'C協', '書記']
    for role in role_order:
        if role in staff_by_role:
            names = '、'.join(staff_by_role[role])
            message += f'{role}: {names}\n'

    return message.strip()
```

---

## UI設計

### 通知設定（LINE通知トグルの近く）

```
┌─────────────────────────────────────────────────┐
│ 設定                                            │
├─────────────────────────────────────────────────┤
│                                                 │
│ LINE通知                               [ON/OFF] │
│ 5分前通知・リハーサル開始/終了通知              │
│                                                 │
│ ─────────────────────────────────────────────── │
│                                                 │
│ 通知対象                                        │
│                                                 │
│ バンドメンバー                         [ON/OFF] │
│                                                 │
│ 担当者                                          │
│   管理                                 [ON/OFF] │
│   渉外                                 [ON/OFF] │
│   合評                                 [ON/OFF] │
│   会計                                 [ON/OFF] │
│   C協                                  [ON/OFF] │
│   書記                                 [ON/OFF] │
│                                                 │
└─────────────────────────────────────────────────┘
```

### タイマー作成/編集モーダル（将来実装）

```
┌─────────────────────────────────────────────────┐
│ タイマー作成                              [×]   │
├─────────────────────────────────────────────────┤
│                                                 │
│ バンド                                          │
│ ┌─────────────────────────────────────────┐    │
│ │ 青春パンクス (BUMP OF CHICKEN)      ▼   │    │
│ └─────────────────────────────────────────┘    │
│ [+ 新規バンド作成]                              │
│                                                 │
│ 持ち時間                                        │
│ ┌─────────────────────────────────────────┐    │
│ │ 15                                 分   │    │
│ └─────────────────────────────────────────┘    │
│                                                 │
│ 担当者                                          │
│ ┌─────────────────────────────────────────┐    │
│ │ 管理                                    │    │
│ │ [山田 ▼] [佐藤 ▼] [鈴木 ▼]              │    │
│ ├─────────────────────────────────────────┤    │
│ │ 渉外                                    │    │
│ │ [田中 ▼] [高橋 ▼]                       │    │
│ ├─────────────────────────────────────────┤    │
│ │ 書記                                    │    │
│ │ [中村 ▼]                                │    │
│ └─────────────────────────────────────────┘    │
│                                                 │
│              [キャンセル]  [作成]               │
│                                                 │
└─────────────────────────────────────────────────┘
```

### バンド作成モーダル（将来実装）

```
┌─────────────────────────────────────────────────┐
│ バンド作成                                [×]   │
├─────────────────────────────────────────────────┤
│                                                 │
│ バンド名                                        │
│ ┌─────────────────────────────────────────┐    │
│ │ 青春パンクス                            │    │
│ └─────────────────────────────────────────┘    │
│                                                 │
│ コピー元アーティスト                            │
│ ┌─────────────────────────────────────────┐    │
│ │ BUMP OF CHICKEN                         │    │
│ └─────────────────────────────────────────┘    │
│                                                 │
│ メンバー                                        │
│ ┌─────────────────────────────────────────┐    │
│ │ [山田 ×] [佐藤 ×] [鈴木 ×]               │    │
│ │                                         │    │
│ │ [+ メンバー追加 ▼]                      │    │
│ └─────────────────────────────────────────┘    │
│                                                 │
│              [キャンセル]  [作成]               │
│                                                 │
└─────────────────────────────────────────────────┘
```

### メンバー管理画面（将来実装）

```
┌─────────────────────────────────────────────────┐
│ メンバー管理                      [+ 新規追加]  │
├─────────────────────────────────────────────────┤
│                                                 │
│ 部局で絞り込み: [全て ▼]                        │
│                                                 │
│ ┌─────────────────────────────────────────────┐ │
│ │ 名前         │ 部局   │ LINE連携 │ 操作    │ │
│ ├─────────────────────────────────────────────┤ │
│ │ 山田 太郎    │ 管理   │ ✓        │ [編集]  │ │
│ │ 佐藤 花子    │ 管理   │ ✓        │ [編集]  │ │
│ │ 鈴木 一郎    │ 管理   │ ✗        │ [編集]  │ │
│ │ 田中 次郎    │ 渉外   │ ✓        │ [編集]  │ │
│ │ 高橋 三郎    │ 渉外   │ ✗        │ [編集]  │ │
│ │ ...                                         │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## タイマー一覧の表示

### 現在の表示
```
1. バンド名  15:00
```

### 新しい表示
```
1. 青春パンクス (BUMP OF CHICKEN)  15:00
   管理: 山田、佐藤、鈴木
```

または折りたたみ式:
```
1. 青春パンクス (BUMP OF CHICKEN)  15:00  [詳細 ▼]
```

---

## 実装フェーズ

### Phase 1: データモデル拡張

**優先度: 高**

1. Bandモデル作成
2. TimerStaffモデル作成
3. Memberモデルにdepartment追加
4. TimerモデルをBand外部キーに変更
5. TimerStateに通知対象設定を追加
6. マイグレーション作成・実行

**変更ファイル:**
- `backend/apps/members/models.py`
- `backend/apps/timers/models.py`
- `backend/apps/bands/models.py`（新規アプリ）

### Phase 2: 通知設定UI

**優先度: 高**

1. 通知対象設定のAPIエンドポイント
2. フロントエンドに通知設定UI追加
3. 既存LINE通知トグルとの統合

**変更ファイル:**
- `backend/apps/timers/views.py`
- `backend/apps/timers/serializers.py`
- `frontend/src/App.jsx`
- `frontend/src/components/settings/NotificationSettings.jsx`（新規）

### Phase 3: バンド管理

**優先度: 中**

1. バンドCRUD API
2. バンド一覧・作成・編集UI
3. タイマー作成時のバンド選択

**変更ファイル:**
- `backend/apps/bands/views.py`
- `backend/apps/bands/serializers.py`
- `frontend/src/components/bands/`（新規ディレクトリ）

### Phase 4: 担当者割り当て

**優先度: 中**

1. TimerStaff CRUD API
2. タイマー作成/編集時の担当者選択UI
3. タイマー一覧での担当者表示

**変更ファイル:**
- `backend/apps/timers/views.py`
- `frontend/src/components/timer/TimerFormModal.jsx`
- `frontend/src/components/timer/TimerList.jsx`

### Phase 5: 通知ロジック更新

**優先度: 中**

1. 通知対象決定ロジックの実装
2. メッセージフォーマットの実装
3. バンドメンバー/担当者への個別通知

**変更ファイル:**
- `backend/apps/line_integration/tasks.py`
- `backend/apps/line_integration/utils.py`

### Phase 6: メンバー管理UI

**優先度: 低（後で検討）**

1. メンバー一覧画面
2. メンバー追加・編集・削除UI
3. 部局での絞り込み
4. 一括登録機能

---

## 移行計画

### 既存データの移行

1. 現在のTimer.band_nameからBandを自動生成
2. 現在のMemberはdepartment='kanri'を設定
3. TimerStaffは空（手動で設定が必要）

```python
# 移行スクリプト例
def migrate_existing_data():
    # 既存タイマーからバンドを作成
    for timer in Timer.objects.all():
        band, created = Band.objects.get_or_create(
            name=timer.band_name,
            defaults={'original_artist': ''}
        )
        timer.band = band
        timer.save()

    # 既存メンバーに部局を設定
    Member.objects.filter(department='').update(department='kanri')
```

---

## API設計

### バンド関連

| Method | Endpoint | 説明 |
|--------|----------|------|
| GET | `/api/bands/` | バンド一覧 |
| POST | `/api/bands/create/` | バンド作成 |
| PUT | `/api/bands/<id>/` | バンド更新 |
| DELETE | `/api/bands/<id>/delete/` | バンド削除 |

### 担当者関連

| Method | Endpoint | 説明 |
|--------|----------|------|
| GET | `/api/timers/<id>/staff/` | 担当者一覧 |
| POST | `/api/timers/<id>/staff/` | 担当者追加 |
| DELETE | `/api/timers/<id>/staff/<member_id>/` | 担当者削除 |

### 通知設定

| Method | Endpoint | 説明 |
|--------|----------|------|
| GET | `/api/settings/notifications/` | 通知設定取得 |
| POST | `/api/settings/notifications/` | 通知設定更新 |

---

## LINEからのバンド登録

### フローチャート

```
LINE登録済みユーザー → 「バンド登録」と送信
                          │
                          ▼
                   コピー元アーティストを聞く
                          │
                          ▼
                   ユーザーがアーティスト名を入力
                          │
                          ▼
                   バンド名を自動生成（RADWIMPS1 等）
                          │
                          ▼
                   メンバーを聞く
                          │
                          ▼
                   ユーザーがメンバー名をカンマ区切りで入力
                          │
                   ┌──────┴──────┐
                   ▼              ▼
            全員見つかった    見つからないメンバーあり
                   │              │
                   ▼              ▼
            バンド作成完了    エラーで中断
```

### 会話状態の管理

バンド登録は複数ステップの会話が必要なため、ユーザーごとの状態を管理する。

```python
# ユーザーの会話状態を保存（Redis または DBで管理）
# 簡易実装例: セッションストレージ

BAND_REGISTRATION_STATE = {}  # {line_user_id: {'step': 'artist', 'artist': '...', ...}}

def get_user_state(line_user_id):
    return BAND_REGISTRATION_STATE.get(line_user_id)

def set_user_state(line_user_id, state):
    BAND_REGISTRATION_STATE[line_user_id] = state

def clear_user_state(line_user_id):
    BAND_REGISTRATION_STATE.pop(line_user_id, None)
```

### 実装コード

```python
def handle_text_message(event):
    """テキストメッセージの処理"""
    line_user_id = event.source.user_id
    text = event.message.text.strip()

    # 会話状態を確認
    user_state = get_user_state(line_user_id)

    if user_state:
        # 会話中の場合は状態に応じて処理
        handle_conversation(event, user_state)
        return

    # 「バンド登録」コマンドの処理
    if text == 'バンド登録':
        handle_band_registration_start(event)
        return

    # 「部局登録」コマンドの処理
    if text == '部局登録':
        handle_department_registration(event)
        return

    # 通常のメッセージ処理（名前登録など）
    # ... 既存処理 ...


def handle_band_registration_start(event):
    """バンド登録開始"""
    line_user_id = event.source.user_id

    # 登録済みか確認
    member = Member.objects.filter(line_user_id=line_user_id).first()
    if not member:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="先に名前を登録してください。\n\n名前を送信すると登録できます。")
        )
        return

    # 会話状態をセット
    set_user_state(line_user_id, {'step': 'artist'})

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="コピー元のアーティスト名を入力してください。\n\n例: RADWIMPS")
    )


def handle_conversation(event, user_state):
    """会話状態に応じた処理"""
    line_user_id = event.source.user_id
    text = event.message.text.strip()
    step = user_state.get('step')

    # キャンセル処理
    if text == 'キャンセル':
        clear_user_state(line_user_id)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="バンド登録をキャンセルしました。")
        )
        return

    if step == 'artist':
        # アーティスト名を受け取り、バンド名を自動生成
        artist_name = text
        band_name = generate_band_name(artist_name)

        # 状態を更新
        set_user_state(line_user_id, {
            'step': 'members',
            'artist': artist_name,
            'band_name': band_name
        })

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=f"バンド名: {band_name}\n"
                     f"コピー元: {artist_name}\n\n"
                     f"メンバーの名前をカンマ区切りで入力してください。\n\n"
                     f"例: 山田,佐藤,鈴木\n\n"
                     f"キャンセルする場合は「キャンセル」と送信"
            )
        )

    elif step == 'members':
        # メンバー名を受け取り、バンドを作成
        member_names = [name.strip() for name in text.split(',')]
        artist_name = user_state.get('artist')
        band_name = user_state.get('band_name')

        # メンバーを検索
        members = []
        not_found = []
        for name in member_names:
            member = Member.objects.filter(name=name).first()
            if member:
                members.append(member)
            else:
                not_found.append(name)

        if not_found:
            # 見つからないメンバーがいる場合はエラー
            clear_user_state(line_user_id)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=f"以下のメンバーが見つかりませんでした。\n\n"
                         f"・{'、'.join(not_found)}\n\n"
                         f"メンバー登録を確認してから再度お試しください。"
                )
            )
            return

        # バンド作成
        band = Band.objects.create(
            name=band_name,
            original_artist=artist_name
        )
        band.members.set(members)

        clear_user_state(line_user_id)

        member_display = '、'.join([m.name for m in members])
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=f"バンド登録が完了しました！\n\n"
                     f"バンド名: {band_name}\n"
                     f"コピー元: {artist_name}\n"
                     f"メンバー: {member_display}"
            )
        )


def generate_band_name(artist_name):
    """コピー元アーティスト名から仮バンド名を生成"""
    import re

    # 既存のバンドを検索（RADWIMPS1, RADWIMPS2...）
    existing_bands = Band.objects.filter(
        name__startswith=artist_name
    ).values_list('name', flat=True)

    # 使用済み番号を抽出
    used_numbers = []
    for name in existing_bands:
        suffix = name.replace(artist_name, '')
        if suffix.isdigit():
            used_numbers.append(int(suffix))

    # 次の番号を決定
    next_number = 1
    while next_number in used_numbers:
        next_number += 1

    return f"{artist_name}{next_number}"
```

### メッセージ例

**コピー元アーティスト入力:**
```
コピー元のアーティスト名を入力してください。

例: RADWIMPS
```

**メンバー入力:**
```
バンド名: RADWIMPS1
コピー元: RADWIMPS

メンバーの名前をカンマ区切りで入力してください。

例: 山田,佐藤,鈴木

キャンセルする場合は「キャンセル」と送信
```

**登録完了:**
```
バンド登録が完了しました！

バンド名: RADWIMPS1
コピー元: RADWIMPS
メンバー: 山田、佐藤、鈴木
```

**メンバーが見つからない場合:**
```
以下のメンバーが見つかりませんでした。

・田中、高橋

メンバー登録を確認してから再度お試しください。
```

**未登録ユーザーの場合:**
```
先に名前を登録してください。

名前を送信すると登録できます。
```

---

## LINEからのバンド編集

### フローチャート

```
LINE登録済みユーザー → 「バンド編集」と送信
                          │
                          ▼
                   編集するバンド名を聞く
                          │
                          ▼
                   ユーザーがバンド名を入力
                          │
                   ┌──────┴──────┐
                   ▼              ▼
            バンドが見つかった  見つからない
                   │              │
                   ▼              ▼
            ユーザーは        「バンドが
            メンバー？        見つかりません」
              ／  ＼
           YES    NO
            │      │
            ▼      ▼
      編集メニュー 「このバンドを
        表示     編集する権限が
                  ありません」
            │
            ▼
   [バンド名変更] [メンバー追加] [メンバー削除]
            │
            ▼
      選択に応じて処理
```

### 編集メニュー

```
「RADWIMPS1」の編集

現在のメンバー: 山田、佐藤、鈴木

[バンド名変更] [メンバー追加] [メンバー削除]  ← Quick Reply
```

### 実装コード

```python
def handle_text_message(event):
    """テキストメッセージの処理"""
    line_user_id = event.source.user_id
    text = event.message.text.strip()

    # 会話状態を確認
    user_state = get_user_state(line_user_id)

    if user_state:
        # 会話中の場合は状態に応じて処理
        handle_conversation(event, user_state)
        return

    # 「バンド編集」コマンドの処理
    if text == 'バンド編集':
        handle_band_edit_start(event)
        return

    # 「バンド登録」コマンドの処理
    if text == 'バンド登録':
        handle_band_registration_start(event)
        return

    # ... 既存処理 ...


def handle_band_edit_start(event):
    """バンド編集開始"""
    line_user_id = event.source.user_id

    # 登録済みか確認
    member = Member.objects.filter(line_user_id=line_user_id).first()
    if not member:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="先に名前を登録してください。\n\n名前を送信すると登録できます。")
        )
        return

    # 会話状態をセット
    set_user_state(line_user_id, {
        'mode': 'band_edit',
        'step': 'select_band',
        'member_id': member.id
    })

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="編集するバンド名を入力してください。\n\nキャンセルする場合は「キャンセル」と送信")
    )


def handle_conversation(event, user_state):
    """会話状態に応じた処理"""
    line_user_id = event.source.user_id
    text = event.message.text.strip()
    mode = user_state.get('mode')
    step = user_state.get('step')

    # キャンセル処理
    if text == 'キャンセル':
        clear_user_state(line_user_id)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="キャンセルしました。")
        )
        return

    # バンド登録モード
    if mode == 'band_registration':
        handle_band_registration_conversation(event, user_state)
        return

    # バンド編集モード
    if mode == 'band_edit':
        handle_band_edit_conversation(event, user_state)
        return


def handle_band_edit_conversation(event, user_state):
    """バンド編集の会話処理"""
    line_user_id = event.source.user_id
    text = event.message.text.strip()
    step = user_state.get('step')
    member_id = user_state.get('member_id')

    member = Member.objects.get(id=member_id)

    if step == 'select_band':
        # バンド名を入力された
        band = Band.objects.filter(name=text).first()

        if not band:
            clear_user_state(line_user_id)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"「{text}」というバンドは見つかりませんでした。")
            )
            return

        # メンバーかどうか確認
        if member not in band.members.all():
            clear_user_state(line_user_id)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="このバンドを編集する権限がありません。\n\nバンドメンバーのみ編集できます。")
            )
            return

        # 編集メニューを表示
        set_user_state(line_user_id, {
            'mode': 'band_edit',
            'step': 'select_action',
            'member_id': member_id,
            'band_id': band.id
        })

        member_names = '、'.join([m.name for m in band.members.all()])

        quick_reply = QuickReply(items=[
            QuickReplyButton(action=PostbackAction(label='バンド名変更', data='band_edit:rename')),
            QuickReplyButton(action=PostbackAction(label='メンバー追加', data='band_edit:add')),
            QuickReplyButton(action=PostbackAction(label='メンバー削除', data='band_edit:remove')),
            QuickReplyButton(action=PostbackAction(label='キャンセル', data='band_edit:cancel')),
        ])

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=f"「{band.name}」の編集\n\n"
                     f"コピー元: {band.original_artist}\n"
                     f"メンバー: {member_names}\n\n"
                     f"操作を選んでください",
                quick_reply=quick_reply
            )
        )

    elif step == 'rename':
        # 新しいバンド名を入力された
        band = Band.objects.get(id=user_state.get('band_id'))
        new_name = text

        # 重複チェック
        if Band.objects.filter(name=new_name).exclude(id=band.id).exists():
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"「{new_name}」は既に使用されています。\n\n別の名前を入力してください。")
            )
            return

        old_name = band.name
        band.name = new_name
        band.save()

        clear_user_state(line_user_id)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"バンド名を変更しました。\n\n{old_name} → {new_name}")
        )

    elif step == 'add_member':
        # 追加するメンバー名を入力された
        band = Band.objects.get(id=user_state.get('band_id'))
        member_names = [name.strip() for name in text.split(',')]

        added = []
        not_found = []
        already_member = []

        for name in member_names:
            m = Member.objects.filter(name=name).first()
            if not m:
                not_found.append(name)
            elif m in band.members.all():
                already_member.append(name)
            else:
                band.members.add(m)
                added.append(name)

        clear_user_state(line_user_id)

        result_message = ""
        if added:
            result_message += f"追加しました: {', '.join(added)}\n"
        if already_member:
            result_message += f"既にメンバー: {', '.join(already_member)}\n"
        if not_found:
            result_message += f"見つかりません: {', '.join(not_found)}\n"

        current_members = '、'.join([m.name for m in band.members.all()])
        result_message += f"\n現在のメンバー: {current_members}"

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=result_message.strip())
        )

    elif step == 'remove_member':
        # 削除するメンバー名を入力された
        band = Band.objects.get(id=user_state.get('band_id'))
        member_names = [name.strip() for name in text.split(',')]

        removed = []
        not_found = []
        not_member = []

        for name in member_names:
            m = Member.objects.filter(name=name).first()
            if not m:
                not_found.append(name)
            elif m not in band.members.all():
                not_member.append(name)
            else:
                # 最後の1人かチェック
                if band.members.count() <= 1:
                    clear_user_state(line_user_id)
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="メンバーが0人になるため削除できません。\n\n最低1人のメンバーが必要です。")
                    )
                    return
                band.members.remove(m)
                removed.append(name)

        clear_user_state(line_user_id)

        result_message = ""
        if removed:
            result_message += f"削除しました: {', '.join(removed)}\n"
        if not_member:
            result_message += f"メンバーではありません: {', '.join(not_member)}\n"
        if not_found:
            result_message += f"見つかりません: {', '.join(not_found)}\n"

        current_members = '、'.join([m.name for m in band.members.all()])
        result_message += f"\n現在のメンバー: {current_members}"

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=result_message.strip())
        )


def handle_postback(event):
    """Postbackイベントの処理"""
    line_user_id = event.source.user_id
    data = event.postback.data

    # 部局選択
    if data.startswith('dept:'):
        # ... 既存処理 ...
        pass

    # バンド編集
    if data.startswith('band_edit:'):
        action = data.replace('band_edit:', '')
        user_state = get_user_state(line_user_id)

        if not user_state:
            return

        band = Band.objects.get(id=user_state.get('band_id'))

        if action == 'cancel':
            clear_user_state(line_user_id)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="キャンセルしました。")
            )

        elif action == 'rename':
            set_user_state(line_user_id, {
                **user_state,
                'step': 'rename'
            })
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"新しいバンド名を入力してください。\n\n現在: {band.name}")
            )

        elif action == 'add':
            set_user_state(line_user_id, {
                **user_state,
                'step': 'add_member'
            })
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="追加するメンバーの名前をカンマ区切りで入力してください。\n\n例: 田中,高橋")
            )

        elif action == 'remove':
            set_user_state(line_user_id, {
                **user_state,
                'step': 'remove_member'
            })
            member_names = '、'.join([m.name for m in band.members.all()])
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=f"削除するメンバーの名前をカンマ区切りで入力してください。\n\n"
                         f"現在のメンバー: {member_names}"
                )
            )
```

### メッセージ例

**バンド選択:**
```
編集するバンド名を入力してください。

キャンセルする場合は「キャンセル」と送信
```

**編集メニュー:**
```
「RADWIMPS1」の編集

コピー元: RADWIMPS
メンバー: 山田、佐藤、鈴木

操作を選んでください

[バンド名変更] [メンバー追加] [メンバー削除] [キャンセル]  ← Quick Reply
```

**バンド名変更:**
```
新しいバンド名を入力してください。

現在: RADWIMPS1
```

**バンド名変更完了:**
```
バンド名を変更しました。

RADWIMPS1 → RADWIMPS新バンド
```

**メンバー追加:**
```
追加するメンバーの名前をカンマ区切りで入力してください。

例: 田中,高橋
```

**メンバー追加完了:**
```
追加しました: 田中、高橋

現在のメンバー: 山田、佐藤、鈴木、田中、高橋
```

**メンバー削除:**
```
削除するメンバーの名前をカンマ区切りで入力してください。

現在のメンバー: 山田、佐藤、鈴木、田中、高橋
```

**メンバー削除完了:**
```
削除しました: 田中

現在のメンバー: 山田、佐藤、鈴木、高橋
```

**権限エラー:**
```
このバンドを編集する権限がありません。

バンドメンバーのみ編集できます。
```

**最後の1人削除エラー:**
```
メンバーが0人になるため削除できません。

最低1人のメンバーが必要です。
```

**バンドが見つからない:**
```
「RADWIMPS99」というバンドは見つかりませんでした。
```

---

## バンド登録・編集時のメンバー通知

### 概要

バンド登録時またはメンバー追加時に、追加されたメンバーにLINE通知を送る。
※登録操作を行った本人には通知しない（登録完了メッセージで確認済みのため）

### 通知対象

| 操作 | 通知対象 |
|------|----------|
| バンド登録 | 登録されたメンバー全員（登録者本人を除く） |
| メンバー追加 | 追加されたメンバー（追加操作者を除く） |

### 通知メッセージ

```
「RADWIMPS1」にメンバーとして登録されました。

コピー元: RADWIMPS
メンバー: 山田、佐藤、鈴木
```

### 実装コード

```python
def notify_band_members(band, added_members, exclude_user_id=None):
    """
    バンドメンバーに通知を送る

    Args:
        band: Band インスタンス
        added_members: 追加されたメンバーのリスト
        exclude_user_id: 通知から除外するLINE user ID（操作者）
    """
    member_names = '、'.join([m.name for m in band.members.all()])

    message = (
        f"「{band.name}」にメンバーとして登録されました。\n\n"
        f"コピー元: {band.original_artist}\n"
        f"メンバー: {member_names}"
    )

    for member in added_members:
        # LINE ID未登録のメンバーはスキップ
        if not member.line_user_id:
            continue

        # 操作者本人はスキップ
        if member.line_user_id == exclude_user_id:
            continue

        try:
            line_bot_api.push_message(
                member.line_user_id,
                TextSendMessage(text=message)
            )
        except Exception as e:
            logger.error(f"Failed to notify member {member.name}: {e}")
```

### バンド登録時の通知

```python
def handle_conversation(event, user_state):
    # ... 既存処理 ...

    elif step == 'members':
        # メンバー名を受け取り、バンドを作成
        member_names = [name.strip() for name in text.split(',')]
        artist_name = user_state.get('artist')
        band_name = user_state.get('band_name')

        # メンバーを検索
        members = []
        not_found = []
        for name in member_names:
            member = Member.objects.filter(name=name).first()
            if member:
                members.append(member)
            else:
                not_found.append(name)

        if not_found:
            # ... エラー処理 ...
            return

        # バンド作成
        band = Band.objects.create(
            name=band_name,
            original_artist=artist_name
        )
        band.members.set(members)

        # メンバーに通知（登録者本人を除く）
        notify_band_members(band, members, exclude_user_id=line_user_id)

        clear_user_state(line_user_id)
        # ... 完了メッセージ ...
```

### メンバー追加時の通知

```python
def handle_band_edit_conversation(event, user_state):
    # ... 既存処理 ...

    elif step == 'add_member':
        # 追加するメンバー名を入力された
        band = Band.objects.get(id=user_state.get('band_id'))
        member_names = [name.strip() for name in text.split(',')]

        added = []
        added_members = []  # 通知用
        not_found = []
        already_member = []

        for name in member_names:
            m = Member.objects.filter(name=name).first()
            if not m:
                not_found.append(name)
            elif m in band.members.all():
                already_member.append(name)
            else:
                band.members.add(m)
                added.append(name)
                added_members.append(m)

        # 追加されたメンバーに通知（追加操作者を除く）
        if added_members:
            notify_band_members(band, added_members, exclude_user_id=line_user_id)

        clear_user_state(line_user_id)
        # ... 結果メッセージ ...
```

### 通知例

**バンド登録時（3人登録、1人が登録者の場合）:**

登録者（山田）の画面:
```
バンド登録が完了しました！

バンド名: RADWIMPS1
コピー元: RADWIMPS
メンバー: 山田、佐藤、鈴木
```

佐藤・鈴木への通知:
```
「RADWIMPS1」にメンバーとして登録されました。

コピー元: RADWIMPS
メンバー: 山田、佐藤、鈴木
```

**メンバー追加時:**

追加操作者（山田）の画面:
```
追加しました: 田中、高橋

現在のメンバー: 山田、佐藤、鈴木、田中、高橋
```

田中・高橋への通知:
```
「RADWIMPS1」にメンバーとして登録されました。

コピー元: RADWIMPS
メンバー: 山田、佐藤、鈴木、田中、高橋
```

---

## 注意事項

1. **後方互換性**
   - 既存のタイマーデータを壊さないよう移行
   - APIの変更は段階的に

2. **LINE通知の送信制限**
   - 対象者が増えるとAPI制限に注意
   - 一斉送信の場合はレート制限を考慮

3. **UIの複雑化**
   - 機能追加に伴いUIが複雑になりすぎないよう注意
   - フェーズごとにユーザビリティを確認

4. **担当者の人数**
   - 管理3人、渉外2人などの制約はシステムで強制するか？
   - 現時点では制約なし（運用で対応）が推奨

---

## 将来の拡張案

1. **一括登録機能**
   - CSVインポート
   - 過去のリハーサルからコピー

2. **担当者自動割り当て**
   - 部局メンバーからランダム/ローテーション

3. **出欠管理**
   - メンバーの出欠状態を記録
   - 欠席者への通知スキップ

4. **統計機能**
   - メンバーごとの担当回数
   - バンドごとのリハーサル履歴
