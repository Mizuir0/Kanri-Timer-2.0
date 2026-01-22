# ユーザー管理機能

## 概要

メンバー管理をDjango AdminからフロントエンドUIに移行し、LINE経由での簡単な登録機能を提供する。

---

## 要件まとめ

### LINE登録
- 未登録ユーザーがLINEでメッセージを送信 → 名前として登録
- 既に同じ名前が存在 → エラー「既に登録されています」
- 既にLINE IDが紐付いているユーザー → 「既に登録済みです」と返信
- 部局は「未設定」で登録、後からフロントエンドで設定

### フロントエンド管理
- メンバー一覧表示
- メンバー追加（手動）
- メンバー編集（名前、部局）
- メンバー削除
- LINE ID解除

### パスワード保護
- メンバー管理画面のみパスワード必要
- タイマー操作画面はパスワード不要
- アプリ全体で1つの共通パスワード
- パスワードは環境変数で管理

---

## LINE登録フロー

### フローチャート

```
ユーザーがLINE Botにメッセージ送信
           │
           ▼
    LINE IDは登録済み？
      ／        ＼
    YES          NO
     │            │
     ▼            ▼
 「既に登録      メッセージを
  済みです」     名前として処理
     │            │
     │            ▼
     │      同じ名前は存在する？
     │        ／        ＼
     │      YES          NO
     │       │            │
     │       ▼            ▼
     │   そのメンバーに    新規メンバー作成
     │   LINE IDはある？   LINE ID紐付け
     │    ／      ＼            │
     │  YES       NO            ▼
     │   │         │      「登録が完了しました！
     │   ▼         ▼       名前: ○○
     │ 「既に別の  LINE ID     部局: 未設定」
     │  アカウント  を紐付け
     │  と連携      │
     │  されて      ▼
     │  います」 「LINE連携が
     │           完了しました！」
     ▼       ▼            ▼
          処理終了
```

### LINE Botのメッセージ

**新規登録成功時:**
```
登録が完了しました！
名前: 山田太郎
部局: 未設定

部局の設定はメンバー管理画面から行えます。
```

**既存メンバーへのLINE連携成功時:**
```
LINE連携が完了しました！
名前: 山田太郎
部局: 管理
```

**既にLINE ID登録済みの場合:**
```
既に登録済みです。

登録情報:
名前: 山田太郎
部局: 管理
```

**名前が既に別のLINEと連携済みの場合:**
```
「山田太郎」は既に別のLINEアカウントと連携されています。
```

---

## データモデル

### Member（既存モデルの拡張）

```python
class Member(models.Model):
    DEPARTMENT_CHOICES = [
        ('', '未設定'),
        ('kanri', '管理'),
        ('shougai', '渉外'),
        ('gouhyou', '合評'),
        ('kaikei', '会計'),
        ('ckyou', 'C協'),
        ('shoki', '書記'),
    ]

    GRADE_CHOICES = [
        (1, '1年'),
        (2, '2年'),
        (3, '3年'),
    ]

    name = models.CharField(max_length=100, unique=True)  # ユニーク制約追加
    line_user_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    department = models.CharField(
        max_length=20,
        choices=DEPARTMENT_CHOICES,
        blank=True,
        default=''
    )
    grade = models.PositiveSmallIntegerField(
        choices=GRADE_CHOICES,
        null=True,
        blank=True
    )
    is_active = models.BooleanField(default=True)  # 4年生になると False
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['department', 'grade', 'name']

    @classmethod
    def active_members(cls):
        """有効なメンバーのみ取得"""
        return cls.objects.filter(is_active=True)
```

---

## パスワード認証

### 仕組み

1. 環境変数 `ADMIN_PASSWORD` にパスワードを設定
2. メンバー管理画面にアクセス時、パスワード入力を要求
3. 正しいパスワード入力 → セッションに認証状態を保存
4. 以降はセッションが有効な間、パスワード不要

### バックエンド実装

```python
# backend/apps/members/views.py

from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

# 環境変数からパスワードを取得
ADMIN_PASSWORD = config('ADMIN_PASSWORD', default='')

@api_view(['POST'])
def verify_password(request):
    """
    パスワード認証
    POST /api/members/auth/
    """
    password = request.data.get('password', '')

    if not ADMIN_PASSWORD:
        # パスワード未設定の場合は常に許可
        return Response({'authenticated': True})

    if password == ADMIN_PASSWORD:
        request.session['member_admin_authenticated'] = True
        return Response({'authenticated': True})

    return Response(
        {'authenticated': False, 'error': 'パスワードが正しくありません'},
        status=status.HTTP_401_UNAUTHORIZED
    )

@api_view(['GET'])
def check_auth(request):
    """
    認証状態確認
    GET /api/members/auth/
    """
    is_authenticated = request.session.get('member_admin_authenticated', False)
    return Response({'authenticated': is_authenticated})

@api_view(['POST'])
def logout(request):
    """
    ログアウト
    POST /api/members/logout/
    """
    request.session['member_admin_authenticated'] = False
    return Response({'success': True})
```

### フロントエンド実装

```jsx
// frontend/src/components/members/PasswordModal.jsx

import { useState } from 'react';

const PasswordModal = ({ isOpen, onAuthenticated }) => {
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('/api/members/auth/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password }),
        credentials: 'include',
      });

      const data = await response.json();

      if (data.authenticated) {
        onAuthenticated();
      } else {
        setError('パスワードが正しくありません');
      }
    } catch (err) {
      setError('認証に失敗しました');
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-80">
        <h2 className="text-xl font-bold mb-4">パスワード入力</h2>
        <form onSubmit={handleSubmit}>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="パスワード"
            className="w-full border rounded px-3 py-2 mb-2"
            autoFocus
          />
          {error && <p className="text-red-500 text-sm mb-2">{error}</p>}
          <button
            type="submit"
            className="w-full bg-blue-600 text-white rounded py-2"
          >
            認証
          </button>
        </form>
      </div>
    </div>
  );
};

export default PasswordModal;
```

---

## LINE Webhook処理

### 既存処理の拡張

```python
# backend/apps/line_integration/views.py

from apps.members.models import Member

@csrf_exempt
def line_webhook(request):
    """LINE Webhookエンドポイント"""
    # ... 署名検証など既存処理 ...

    for event in events:
        if event.type == 'message' and event.message.type == 'text':
            handle_text_message(event)
        elif event.type == 'follow':
            handle_follow(event)

    return HttpResponse('OK')


def handle_text_message(event):
    """テキストメッセージの処理"""
    line_user_id = event.source.user_id
    text = event.message.text.strip()

    # 既にLINE IDが登録されているか確認
    existing_member = Member.objects.filter(line_user_id=line_user_id).first()

    if existing_member:
        # 既に登録済み
        reply_message = (
            f"既に登録済みです。\n\n"
            f"登録情報:\n"
            f"名前: {existing_member.name}\n"
            f"部局: {existing_member.get_department_display() or '未設定'}"
        )
    else:
        # 未登録 → 名前として登録を試みる
        reply_message = register_member_by_line(text, line_user_id)

    # 返信
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_message)
    )


def register_member_by_line(name, line_user_id):
    """LINEからのメンバー登録"""
    existing_member = Member.objects.filter(name=name).first()

    if existing_member:
        if existing_member.line_user_id:
            # 既にLINE ID紐付け済み → エラー
            return f"「{name}」は既に別のLINEアカウントと連携されています。"
        else:
            # LINE ID未登録 → 紐付け
            existing_member.line_user_id = line_user_id
            existing_member.save()
            return (
                f"LINE連携が完了しました！\n"
                f"名前: {existing_member.name}\n"
                f"部局: {existing_member.get_department_display() or '未設定'}"
            )
    else:
        # 新規登録
        member = Member.objects.create(
            name=name,
            line_user_id=line_user_id,
            department=''  # 未設定
        )
        return (
            f"登録が完了しました！\n"
            f"名前: {member.name}\n"
            f"部局: 未設定\n\n"
            f"部局の設定はメンバー管理画面から行えます。"
        )


def handle_follow(event):
    """フォロー時の処理"""
    line_user_id = event.source.user_id

    # 既に登録されているか確認
    existing_member = Member.objects.filter(line_user_id=line_user_id).first()

    if existing_member:
        message = (
            f"おかえりなさい！\n\n"
            f"登録情報:\n"
            f"名前: {existing_member.name}\n"
            f"部局: {existing_member.get_department_display() or '未設定'}"
        )
    else:
        message = (
            f"KanriTimer へようこそ！\n\n"
            f"登録するには、あなたの名前を送信してください。\n"
            f"例: 山田太郎"
        )

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=message)
    )


def handle_department_registration(event):
    """部局登録コマンドの処理"""
    line_user_id = event.source.user_id

    # 登録済みか確認
    member = Member.objects.filter(line_user_id=line_user_id).first()

    if not member:
        # 未登録ユーザー
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="先に名前を登録してください。\n\n名前を送信すると登録できます。")
        )
        return

    # 部局選択ボタンを表示
    buttons_template = ButtonsTemplate(
        title='部局登録',
        text=f'現在の部局: {member.get_department_display() or "未設定"}\n\n登録する部局を選んでください',
        actions=[
            PostbackAction(label='管理', data='dept:kanri'),
            PostbackAction(label='渉外', data='dept:shougai'),
            PostbackAction(label='合評', data='dept:gouhyou'),
        ]
    )

    # 6つの部局があるので、2つのメッセージに分ける
    quick_reply = QuickReply(items=[
        QuickReplyButton(action=PostbackAction(label='管理', data='dept:kanri')),
        QuickReplyButton(action=PostbackAction(label='渉外', data='dept:shougai')),
        QuickReplyButton(action=PostbackAction(label='合評', data='dept:gouhyou')),
        QuickReplyButton(action=PostbackAction(label='会計', data='dept:kaikei')),
        QuickReplyButton(action=PostbackAction(label='C協', data='dept:ckyou')),
        QuickReplyButton(action=PostbackAction(label='書記', data='dept:shoki')),
    ])

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text=f'現在の部局: {member.get_department_display() or "未設定"}\n\n登録する部局を選んでください',
            quick_reply=quick_reply
        )
    )


def handle_postback(event):
    """Postbackイベントの処理（部局選択）"""
    line_user_id = event.source.user_id
    data = event.postback.data

    if data.startswith('dept:'):
        department = data.replace('dept:', '')

        member = Member.objects.filter(line_user_id=line_user_id).first()
        if not member:
            return

        # 部局を更新
        member.department = department
        member.save()

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=f"部局を更新しました！\n\n"
                     f"名前: {member.name}\n"
                     f"部局: {member.get_department_display()}"
            )
        )
```

### handle_text_message の修正

```python
def handle_text_message(event):
    """テキストメッセージの処理"""
    line_user_id = event.source.user_id
    text = event.message.text.strip()

    # 「部局登録」コマンドの処理
    if text == '部局登録':
        handle_department_registration(event)
        return

    # 既にLINE IDが登録されているか確認
    existing_member = Member.objects.filter(line_user_id=line_user_id).first()

    if existing_member:
        # 既に登録済み
        reply_message = (
            f"既に登録済みです。\n\n"
            f"登録情報:\n"
            f"名前: {existing_member.name}\n"
            f"部局: {existing_member.get_department_display() or '未設定'}\n\n"
            f"部局を変更するには「部局登録」と送信してください。"
        )
    else:
        # 未登録 → 名前として登録を試みる
        reply_message = register_member_by_line(text, line_user_id)

    # 返信
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_message)
    )
```

### Webhookにpostbackイベントを追加

```python
@csrf_exempt
def line_webhook(request):
    """LINE Webhookエンドポイント"""
    # ... 署名検証など既存処理 ...

    for event in events:
        if event.type == 'message' and event.message.type == 'text':
            handle_text_message(event)
        elif event.type == 'follow':
            handle_follow(event)
        elif event.type == 'postback':
            handle_postback(event)

    return HttpResponse('OK')
```

---

## LINE部局登録フロー

### フローチャート

```
登録済みユーザー → 「部局登録」と送信
                     │
                     ▼
              Quick Replyで部局選択肢を表示
              [管理] [渉外] [合評] [会計] [C協] [書記]
                     │
                     ▼
              ユーザーがボタンをタップ
                     │
                     ▼
              Postbackイベント受信
                     │
                     ▼
              部局を更新
                     │
                     ▼
              「部局を更新しました！」
```

### メッセージ例

**部局選択画面:**
```
現在の部局: 未設定

登録する部局を選んでください

[管理] [渉外] [合評] [会計] [C協] [書記]  ← Quick Reply
```

**更新完了:**
```
部局を更新しました！

名前: 山田太郎
部局: 管理
```

**未登録ユーザーの場合:**
```
先に名前を登録してください。

名前を送信すると登録できます。
```

---

## フロントエンドUI

### メンバー管理画面へのアクセス

```jsx
// frontend/src/App.jsx に追加

// ヘッダーまたはフッターにリンク追加
<a href="/members" className="text-blue-600 underline">
  メンバー管理
</a>
```

### ルーティング追加

```jsx
// frontend/src/main.jsx または App.jsx

import { BrowserRouter, Routes, Route } from 'react-router-dom';
import MemberManagement from './pages/MemberManagement';

<BrowserRouter>
  <Routes>
    <Route path="/" element={<App />} />
    <Route path="/members" element={<MemberManagement />} />
  </Routes>
</BrowserRouter>
```

### メンバー管理ページ

```jsx
// frontend/src/pages/MemberManagement.jsx

import { useState, useEffect } from 'react';
import PasswordModal from '../components/members/PasswordModal';
import MemberList from '../components/members/MemberList';
import MemberFormModal from '../components/members/MemberFormModal';

const MemberManagement = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [members, setMembers] = useState([]);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingMember, setEditingMember] = useState(null);

  // 認証状態確認
  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const response = await fetch('/api/members/auth/', {
        credentials: 'include',
      });
      const data = await response.json();
      setIsAuthenticated(data.authenticated);
    } catch (err) {
      setIsAuthenticated(false);
    } finally {
      setIsLoading(false);
    }
  };

  // メンバー一覧取得
  useEffect(() => {
    if (isAuthenticated) {
      fetchMembers();
    }
  }, [isAuthenticated]);

  const fetchMembers = async () => {
    const response = await fetch('/api/members/');
    const data = await response.json();
    setMembers(data);
  };

  if (isLoading) {
    return <div className="p-4">読み込み中...</div>;
  }

  if (!isAuthenticated) {
    return (
      <PasswordModal
        isOpen={true}
        onAuthenticated={() => setIsAuthenticated(true)}
      />
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-blue-600 text-white p-4 shadow-md">
        <div className="container mx-auto flex justify-between items-center">
          <h1 className="text-2xl font-bold">メンバー管理</h1>
          <a href="/" className="text-white underline">タイマーに戻る</a>
        </div>
      </header>

      <main className="container mx-auto p-6 max-w-4xl">
        <div className="mb-4 flex justify-between items-center">
          <h2 className="text-xl font-bold">メンバー一覧</h2>
          <button
            onClick={() => {
              setEditingMember(null);
              setIsFormOpen(true);
            }}
            className="bg-green-600 text-white px-4 py-2 rounded"
          >
            + 新規追加
          </button>
        </div>

        <MemberList
          members={members}
          onEdit={(member) => {
            setEditingMember(member);
            setIsFormOpen(true);
          }}
          onDelete={async (memberId) => {
            if (confirm('削除しますか？')) {
              await fetch(`/api/members/${memberId}/delete/`, {
                method: 'DELETE',
              });
              fetchMembers();
            }
          }}
          onUnlinkLine={async (memberId) => {
            if (confirm('LINE連携を解除しますか？')) {
              await fetch(`/api/members/${memberId}/unlink-line/`, {
                method: 'POST',
              });
              fetchMembers();
            }
          }}
        />

        <MemberFormModal
          isOpen={isFormOpen}
          member={editingMember}
          onClose={() => setIsFormOpen(false)}
          onSaved={() => {
            setIsFormOpen(false);
            fetchMembers();
          }}
        />
      </main>
    </div>
  );
};

export default MemberManagement;
```

### メンバー一覧コンポーネント

```jsx
// frontend/src/components/members/MemberList.jsx

const DEPARTMENT_LABELS = {
  '': '未設定',
  'kanri': '管理',
  'shougai': '渉外',
  'gouhyou': '合評',
  'kaikei': '会計',
  'ckyou': 'C協',
  'shoki': '書記',
};

const MemberList = ({ members, onEdit, onDelete, onUnlinkLine }) => {
  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <table className="w-full">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left">名前</th>
            <th className="px-4 py-3 text-left">部局</th>
            <th className="px-4 py-3 text-center">LINE</th>
            <th className="px-4 py-3 text-center">操作</th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {members.map((member) => (
            <tr key={member.id} className="hover:bg-gray-50">
              <td className="px-4 py-3">{member.name}</td>
              <td className="px-4 py-3">
                {DEPARTMENT_LABELS[member.department] || '未設定'}
              </td>
              <td className="px-4 py-3 text-center">
                {member.line_user_id ? (
                  <span className="text-green-600">✓ 連携済</span>
                ) : (
                  <span className="text-gray-400">未連携</span>
                )}
              </td>
              <td className="px-4 py-3 text-center space-x-2">
                <button
                  onClick={() => onEdit(member)}
                  className="text-blue-600 hover:underline"
                >
                  編集
                </button>
                {member.line_user_id && (
                  <button
                    onClick={() => onUnlinkLine(member.id)}
                    className="text-orange-600 hover:underline"
                  >
                    LINE解除
                  </button>
                )}
                <button
                  onClick={() => onDelete(member.id)}
                  className="text-red-600 hover:underline"
                >
                  削除
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {members.length === 0 && (
        <div className="p-8 text-center text-gray-500">
          メンバーが登録されていません
        </div>
      )}
    </div>
  );
};

export default MemberList;
```

### メンバー編集モーダル

```jsx
// frontend/src/components/members/MemberFormModal.jsx

import { useState, useEffect } from 'react';

const DEPARTMENTS = [
  { value: '', label: '未設定' },
  { value: 'kanri', label: '管理' },
  { value: 'shougai', label: '渉外' },
  { value: 'gouhyou', label: '合評' },
  { value: 'kaikei', label: '会計' },
  { value: 'ckyou', label: 'C協' },
  { value: 'shoki', label: '書記' },
];

const MemberFormModal = ({ isOpen, member, onClose, onSaved }) => {
  const [name, setName] = useState('');
  const [department, setDepartment] = useState('');
  const [error, setError] = useState('');

  const isEditing = !!member;

  useEffect(() => {
    if (member) {
      setName(member.name);
      setDepartment(member.department || '');
    } else {
      setName('');
      setDepartment('');
    }
    setError('');
  }, [member, isOpen]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    const url = isEditing
      ? `/api/members/${member.id}/`
      : '/api/members/create/';
    const method = isEditing ? 'PUT' : 'POST';

    try {
      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, department }),
      });

      if (response.ok) {
        onSaved();
      } else {
        const data = await response.json();
        setError(data.error || '保存に失敗しました');
      }
    } catch (err) {
      setError('保存に失敗しました');
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-96">
        <h2 className="text-xl font-bold mb-4">
          {isEditing ? 'メンバー編集' : 'メンバー追加'}
        </h2>

        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-sm font-medium mb-1">名前</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full border rounded px-3 py-2"
              required
            />
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium mb-1">部局</label>
            <select
              value={department}
              onChange={(e) => setDepartment(e.target.value)}
              className="w-full border rounded px-3 py-2"
            >
              {DEPARTMENTS.map((dept) => (
                <option key={dept.value} value={dept.value}>
                  {dept.label}
                </option>
              ))}
            </select>
          </div>

          {error && <p className="text-red-500 text-sm mb-4">{error}</p>}

          <div className="flex justify-end space-x-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border rounded"
            >
              キャンセル
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded"
            >
              {isEditing ? '更新' : '追加'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default MemberFormModal;
```

---

## API設計

### メンバー管理API

| Method | Endpoint | 説明 | 認証 |
|--------|----------|------|------|
| GET | `/api/members/` | メンバー一覧 | 不要 |
| POST | `/api/members/create/` | メンバー作成 | 必要 |
| PUT | `/api/members/<id>/` | メンバー更新 | 必要 |
| DELETE | `/api/members/<id>/delete/` | メンバー削除 | 必要 |
| POST | `/api/members/<id>/unlink-line/` | LINE連携解除 | 必要 |

### 認証API

| Method | Endpoint | 説明 |
|--------|----------|------|
| GET | `/api/members/auth/` | 認証状態確認 |
| POST | `/api/members/auth/` | パスワード認証 |
| POST | `/api/members/logout/` | ログアウト |

---

## 環境変数

```
# 本番環境 (Railway)
ADMIN_PASSWORD=your-secure-password-here
```

---

## 実装フェーズ

### Phase 1: パスワード認証

**優先度: 高**

1. 認証APIエンドポイント作成
2. セッション管理の実装
3. パスワードモーダルコンポーネント
4. 環境変数設定

**変更ファイル:**
- `backend/apps/members/views.py`
- `backend/apps/members/urls.py`
- `frontend/src/components/members/PasswordModal.jsx`（新規）

### Phase 2: フロントエンドUI

**優先度: 高**

1. ルーティング設定（react-router-dom追加）
2. メンバー管理ページ作成
3. メンバー一覧コンポーネント
4. メンバー追加/編集モーダル
5. 削除・LINE解除機能

**変更ファイル:**
- `frontend/src/main.jsx`
- `frontend/src/pages/MemberManagement.jsx`（新規）
- `frontend/src/components/members/MemberList.jsx`（新規）
- `frontend/src/components/members/MemberFormModal.jsx`（新規）

### Phase 3: LINE登録機能

**優先度: 中**

1. 既存Webhook処理の拡張
2. 登録/重複チェックロジック
3. 返信メッセージの実装
4. フォロー時の案内メッセージ

**変更ファイル:**
- `backend/apps/line_integration/views.py`

### Phase 4: メンバーモデル拡張

**優先度: 中**

1. departmentフィールド追加
2. nameのユニーク制約追加
3. マイグレーション作成・実行
4. 既存データの移行

**変更ファイル:**
- `backend/apps/members/models.py`
- 新規マイグレーションファイル

---

## セキュリティ考慮事項

1. **パスワードの強度**
   - 環境変数で設定するため、十分な長さと複雑さを推奨
   - 例: 12文字以上、英数字混合

2. **セッション管理**
   - セッションはサーバー側で管理
   - HTTPS環境での運用を推奨

3. **CORS設定**
   - 認証APIはCORS設定を適切に

4. **レート制限**
   - パスワード試行回数の制限（将来的な改善）

---

## 注意事項

1. **既存メンバーの移行**
   - department フィールド追加時、既存データは `kanri`（管理）に設定

2. **LINE登録の注意**
   - 名前が重複する場合は登録不可
   - 本名でなくニックネームでも可

3. **UI/UXの改善点**
   - 部局での絞り込み機能（将来追加）
   - ソート機能（将来追加）
   - 検索機能（将来追加）

---

## 学年管理

### 概要

サークルは3年生で卒業のため、4年生になるタイミングでメンバーを自動的に無効化する。

### 仕様

| 項目 | 内容 |
|------|------|
| 学年の選択肢 | 1年、2年、3年 |
| 4年生の扱い | `is_active = False` に自動更新 |
| 無効メンバー | メンバー一覧に表示しない |
| 更新タイミング | 毎年4月1日 0:00 に自動実行 |
| 手動変更 | 不可（自動更新のみ） |

### LINE登録時の学年選択

名前登録後、学年を選択させる。

```
ユーザー → 名前を送信
              │
              ▼
        名前を登録
              │
              ▼
        学年選択を表示
        [1年] [2年] [3年]  ← Quick Reply
              │
              ▼
        学年を登録
              │
              ▼
        登録完了メッセージ
```

### LINE登録フローの修正

```python
def register_member_by_line(name, line_user_id):
    """LINEからのメンバー登録（学年選択を追加）"""
    existing_member = Member.objects.filter(name=name).first()

    if existing_member:
        if existing_member.line_user_id:
            return (
                f"「{name}」は既に別のLINEアカウントと連携されています。",
                None  # Quick Reply なし
            )
        else:
            # LINE ID未登録 → 紐付け、学年選択へ
            existing_member.line_user_id = line_user_id
            existing_member.save()

            # 学年が未設定の場合は選択を促す
            if existing_member.grade is None:
                set_user_state(line_user_id, {
                    'mode': 'grade_registration',
                    'member_id': existing_member.id
                })
                return (
                    f"LINE連携が完了しました！\n"
                    f"名前: {existing_member.name}\n\n"
                    f"学年を選んでください。",
                    get_grade_quick_reply()
                )
            else:
                return (
                    f"LINE連携が完了しました！\n"
                    f"名前: {existing_member.name}\n"
                    f"学年: {existing_member.get_grade_display()}\n"
                    f"部局: {existing_member.get_department_display() or '未設定'}",
                    None
                )
    else:
        # 新規登録
        member = Member.objects.create(
            name=name,
            line_user_id=line_user_id,
            department='',
            grade=None,
            is_active=True
        )

        # 学年選択へ
        set_user_state(line_user_id, {
            'mode': 'grade_registration',
            'member_id': member.id
        })

        return (
            f"登録が完了しました！\n"
            f"名前: {member.name}\n\n"
            f"学年を選んでください。",
            get_grade_quick_reply()
        )


def get_grade_quick_reply():
    """学年選択用のQuick Reply"""
    return QuickReply(items=[
        QuickReplyButton(action=PostbackAction(label='1年', data='grade:1')),
        QuickReplyButton(action=PostbackAction(label='2年', data='grade:2')),
        QuickReplyButton(action=PostbackAction(label='3年', data='grade:3')),
    ])


def handle_postback(event):
    """Postbackイベントの処理"""
    line_user_id = event.source.user_id
    data = event.postback.data

    # 学年選択
    if data.startswith('grade:'):
        grade = int(data.replace('grade:', ''))
        user_state = get_user_state(line_user_id)

        if user_state and user_state.get('mode') == 'grade_registration':
            member = Member.objects.get(id=user_state.get('member_id'))
            member.grade = grade
            member.save()

            clear_user_state(line_user_id)

            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=f"学年を登録しました！\n\n"
                         f"名前: {member.name}\n"
                         f"学年: {member.get_grade_display()}\n"
                         f"部局: {member.get_department_display() or '未設定'}\n\n"
                         f"部局を変更するには「部局登録」と送信してください。"
                )
            )

    # 部局選択
    if data.startswith('dept:'):
        # ... 既存処理 ...
        pass
```

### 学年自動更新（Celery Beat）

毎年4月1日 0:00 に実行するタスク。

```python
# backend/apps/members/tasks.py

from celery import shared_task
from django.utils import timezone
from .models import Member
import logging

logger = logging.getLogger(__name__)


@shared_task
def update_member_grades():
    """
    メンバーの学年を1つ上げる
    4年生（3年→4年）になるメンバーは無効化する
    """
    updated_count = 0
    deactivated_count = 0

    # 有効なメンバーのみ対象
    for member in Member.objects.filter(is_active=True, grade__isnull=False):
        if member.grade >= 3:
            # 3年生 → 4年生（卒業）→ 無効化
            member.is_active = False
            member.save()
            deactivated_count += 1
            logger.info(f"Member {member.name} deactivated (graduated)")
        else:
            # 1年→2年、2年→3年
            member.grade += 1
            member.save()
            updated_count += 1
            logger.info(f"Member {member.name} grade updated to {member.grade}")

    logger.info(
        f"Grade update completed: "
        f"{updated_count} updated, {deactivated_count} deactivated"
    )

    return {
        'updated': updated_count,
        'deactivated': deactivated_count
    }
```

### Celery Beat スケジュール設定

```python
# backend/backend/settings/base.py

from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    # ... 既存のスケジュール ...

    'update-member-grades': {
        'task': 'apps.members.tasks.update_member_grades',
        'schedule': crontab(month_of_year=4, day_of_month=1, hour=0, minute=0),
        # 毎年4月1日 0:00 に実行
    },
}
```

### メッセージ例

**学年選択:**
```
登録が完了しました！
名前: 山田太郎

学年を選んでください。

[1年] [2年] [3年]  ← Quick Reply
```

**学年登録完了:**
```
学年を登録しました！

名前: 山田太郎
学年: 1年
部局: 未設定

部局を変更するには「部局登録」と送信してください。
```

### メンバー一覧の表示

有効なメンバーのみ表示するようAPIを修正。

```python
# backend/apps/members/views.py

@api_view(['GET'])
def get_members(request):
    """メンバー一覧取得（有効なメンバーのみ）"""
    members = Member.objects.filter(is_active=True)
    serializer = MemberSerializer(members, many=True)
    return Response(serializer.data)
```

### 通知への影響

無効化されたメンバー（`is_active=False`）は通知対象から除外。

```python
def get_notification_targets(timer):
    """通知対象を取得（有効なメンバーのみ）"""
    targets = []

    # バンドメンバー（有効なメンバーのみ）
    if settings.notify_band_members:
        targets.extend(
            timer.band.members.filter(is_active=True).exclude(line_user_id='')
        )

    # 担当者（有効なメンバーのみ）
    for staff in timer.staff.filter(member__is_active=True):
        # ... 既存処理 ...

    return list(set(targets))
```

### 実装フェーズに追加

**Phase 5: 学年管理**

1. Memberモデルにgrade, is_activeフィールド追加
2. LINE登録フローに学年選択追加
3. 学年自動更新タスク作成
4. Celery Beatスケジュール設定
5. メンバー一覧・通知の有効メンバーフィルタリング

**変更ファイル:**
- `backend/apps/members/models.py`
- `backend/apps/members/tasks.py`（新規）
- `backend/apps/line_integration/views.py`
- `backend/backend/settings/base.py`
