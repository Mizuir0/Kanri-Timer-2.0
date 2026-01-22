# 仕事割自動作成機能

## 概要

バンドの出演順から、各部局の担当者を自動で割り当てる機能。制約を考慮しながら公平に配分し、Excelファイルとして出力する。

---

## 要件まとめ

### 各部局の担当者数（1タイマーあたり）

| 部局 | 人数 | 2年以上必須 |
|------|------|-------------|
| 管理 | 3人 | ✓（2人以上のため） |
| 渉外 | 2人 | ✓（2人以上のため） |
| 合評 | 2人 | ✓（2人以上のため） |
| 会計 | 1人 | - |
| C協 | 1人 | - |
| 書記 | 1人 | - |

**合計: 10人/タイマー**

### 制約条件

| # | 制約 | 説明 |
|---|------|------|
| 1 | 自分の出番NG | バンドメンバーは自分のバンドの出番で担当不可 |
| 2 | 前後の出番NG | バンドメンバーは自分のバンドの前後の出番で担当不可 |
| 3 | 均等配分 | 部局内で全員がなるべく同じ回数担当 |
| 4 | 上級生必須 | 2人以上の部局では少なくとも1人は2年か3年 |

### 制約を満たせない場合

- 警告を出しつつ、可能な範囲で割り当てる
- 制約違反箇所をExcelで色付け表示

---

## アクセス制御

メンバー管理画面と同様、パスワード保護を適用する。

- 仕事割作成ページへのアクセスにはパスワード入力が必要
- 認証済みセッションがあればパスワード不要（メンバー管理と共通）

---

## 入力

### 専用ページでの入力項目

1. **バンド順**（テキストエリア）
   - 1行に1バンド名
   - 登録済みバンドと照合

2. **参加メンバー**（部局ごとにチェックボックス）
   - 各部局のメンバー一覧を表示
   - 参加できないメンバーのチェックを外す

### 入力画面イメージ

```
┌─────────────────────────────────────────────────────────┐
│  仕事割自動作成                                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  【バンド順】                                            │
│  ┌─────────────────────────────────────┐               │
│  │ RADWIMPS                            │               │
│  │ Official髭男dism                     │               │
│  │ King Gnu                            │               │
│  │ YOASOBI                             │               │
│  │ ...                                 │               │
│  └─────────────────────────────────────┘               │
│                                                         │
│  【参加メンバー】                                        │
│                                                         │
│  管理 (3人必要)                         [全選択] [全解除] │
│  ☑ 山田太郎 (3年)    ☑ 佐藤花子 (2年)                    │
│  ☑ 鈴木一郎 (1年)    ☐ 田中次郎 (2年) ← 不参加          │
│  ☑ 高橋三郎 (1年)    ☑ 伊藤四郎 (3年)                    │
│                                                         │
│  渉外 (2人必要)                         [全選択] [全解除] │
│  ☑ 渡辺五郎 (2年)    ☑ 中村六郎 (1年)                    │
│  ...                                                    │
│                                                         │
│  [生成してダウンロード]                                  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 出力

### Excelファイル形式

**ファイル名**: `仕事割_YYYYMMDD_HHMMSS.xlsx`

**シート構成**:
1. 仕事割表（メイン）
2. 警告一覧
3. 統計情報

### シート1: 仕事割表

| # | バンド名 | 管理1 | 管理2 | 管理3 | 渉外1 | 渉外2 | 合評1 | 合評2 | 会計 | C協 | 書記 |
|---|----------|-------|-------|-------|-------|-------|-------|-------|------|-----|------|
| 1 | RADWIMPS | 山田 | 佐藤 | 鈴木 | 渡辺 | 中村 | 加藤 | 吉田 | 木村 | 林 | 清水 |
| 2 | 髭男 | 山田 | 高橋 | 伊藤 | 渡辺 | 小林 | 加藤 | 山本 | 木村 | 林 | 清水 |
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |

**色分け**:
- 🔴 赤背景: 制約違反（自分の出番/前後で担当）
- 🟡 黄背景: 上級生不在の警告
- 🟢 緑背景: 正常

### シート2: 警告一覧

| # | バンド名 | 部局 | 警告内容 |
|---|----------|------|----------|
| 3 | King Gnu | 管理 | 上級生が割り当てられませんでした |
| 5 | YOASOBI | 渉外 | 山田太郎が自身の出番に割り当てられています |

### シート3: 統計情報

| 部局 | メンバー | 担当回数 | 平均との差 |
|------|----------|----------|-----------|
| 管理 | 山田太郎 | 8回 | +1 |
| 管理 | 佐藤花子 | 7回 | 0 |
| 管理 | 鈴木一郎 | 7回 | 0 |
| ... | ... | ... | ... |

---

## アルゴリズム

### 概要

貪欲法（Greedy Algorithm）+ 均等化調整

### 処理フロー

```
入力: バンド順リスト, 参加メンバーリスト
       │
       ▼
  各バンドのメンバー情報を取得
       │
       ▼
  各メンバーのNG枠を計算
  （自分のバンドの出番 ± 1）
       │
       ▼
  タイマー1から順に割り当て
       │
       ├─→ 各部局について:
       │     │
       │     ▼
       │   割り当て可能なメンバーを抽出
       │   （NG枠でない & 参加メンバー）
       │     │
       │     ▼
       │   優先度でソート:
       │   1. 担当回数が少ない人
       │   2. 2年以上が必要な場合は上級生優先
       │     │
       │     ▼
       │   必要人数を割り当て
       │   （足りない場合は警告付きで制約緩和）
       │
       ▼
  結果をExcel出力
```

### 擬似コード

```python
def generate_work_assignment(band_order, participating_members):
    # 各メンバーのNG枠を計算
    member_ng_slots = calculate_ng_slots(band_order)

    # 各メンバーの担当回数を初期化
    assignment_count = {member.id: 0 for member in participating_members}

    # 結果格納用
    assignments = []
    warnings = []

    for slot_index, band in enumerate(band_order):
        slot_assignment = {'band': band}

        for dept, required_count in DEPARTMENT_REQUIREMENTS.items():
            # この部局の参加メンバー
            dept_members = [m for m in participating_members if m.department == dept]

            # 割り当て可能なメンバー（NG枠でない）
            available = [
                m for m in dept_members
                if slot_index not in member_ng_slots.get(m.id, [])
            ]

            # 優先度でソート
            available.sort(key=lambda m: (
                assignment_count[m.id],  # 担当回数が少ない順
                0 if m.grade >= 2 else 1  # 上級生優先（必要な場合）
            ))

            # 割り当て
            assigned = []
            needs_senior = required_count >= 2
            has_senior = False

            for member in available:
                if len(assigned) >= required_count:
                    break
                assigned.append(member)
                assignment_count[member.id] += 1
                if member.grade >= 2:
                    has_senior = True

            # 人数不足の場合、制約を緩和して警告
            if len(assigned) < required_count:
                # NG枠のメンバーからも割り当て（警告付き）
                for member in dept_members:
                    if member not in assigned and len(assigned) < required_count:
                        assigned.append(member)
                        assignment_count[member.id] += 1
                        warnings.append({
                            'slot': slot_index + 1,
                            'band': band.name,
                            'dept': dept,
                            'message': f'{member.name}が制約違反で割り当てられました'
                        })

            # 上級生チェック
            if needs_senior and not has_senior:
                warnings.append({
                    'slot': slot_index + 1,
                    'band': band.name,
                    'dept': dept,
                    'message': '上級生が割り当てられませんでした'
                })

            slot_assignment[dept] = assigned

        assignments.append(slot_assignment)

    return assignments, warnings


def calculate_ng_slots(band_order):
    """各メンバーのNG枠（自分のバンドの前後含む）を計算"""
    member_ng_slots = {}

    for slot_index, band in enumerate(band_order):
        for member in band.members.all():
            if member.id not in member_ng_slots:
                member_ng_slots[member.id] = set()

            # 自分の出番
            member_ng_slots[member.id].add(slot_index)
            # 前の出番
            if slot_index > 0:
                member_ng_slots[member.id].add(slot_index - 1)
            # 後の出番
            if slot_index < len(band_order) - 1:
                member_ng_slots[member.id].add(slot_index + 1)

    return member_ng_slots
```

---

## API設計

### エンドポイント

| Method | Endpoint | 説明 |
|--------|----------|------|
| GET | `/api/work-assignment/members/` | 部局ごとのメンバー一覧取得 |
| POST | `/api/work-assignment/generate/` | 仕事割生成・Excelダウンロード |
| POST | `/api/work-assignment/validate-bands/` | バンド名の存在チェック |

### リクエスト例（生成）

```json
POST /api/work-assignment/generate/
{
  "band_names": [
    "RADWIMPS",
    "Official髭男dism",
    "King Gnu",
    "YOASOBI"
  ],
  "participating_members": {
    "kanri": [1, 2, 3, 5, 6],
    "shougai": [10, 11, 12],
    "gouhyou": [20, 21, 22, 23],
    "kaikei": [30, 31],
    "ckyou": [40, 41],
    "shoki": [50, 51]
  }
}
```

### レスポンス

Excelファイル（`application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`）

---

## フロントエンド設計

### ページ構成

```
/work-assignment
  └── WorkAssignmentPage.jsx
        ├── BandOrderInput.jsx      // バンド順入力
        ├── MemberSelector.jsx      // 参加メンバー選択
        └── GenerateButton.jsx      // 生成ボタン
```

### 状態管理

```javascript
const [bandOrder, setBandOrder] = useState('');  // テキストエリアの内容
const [participatingMembers, setParticipatingMembers] = useState({
  kanri: [],    // 選択されたメンバーIDの配列
  shougai: [],
  gouhyou: [],
  kaikei: [],
  ckyou: [],
  shoki: [],
});
const [validationErrors, setValidationErrors] = useState([]);  // バンド名エラー
const [isGenerating, setIsGenerating] = useState(false);
```

### バンド名バリデーション

入力されたバンド名が登録済みか確認し、未登録のバンドは警告表示。

```jsx
// バンド名入力時のバリデーション
const validateBandNames = async () => {
  const names = bandOrder.split('\n').filter(n => n.trim());
  const response = await fetch('/api/work-assignment/validate-bands/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ band_names: names }),
  });
  const data = await response.json();
  setValidationErrors(data.unknown_bands);  // 未登録バンド名の配列
};
```

---

## バックエンド実装

### ファイル構成

```
backend/apps/work_assignment/
├── __init__.py
├── urls.py
├── views.py
├── services/
│   ├── __init__.py
│   ├── assignment_generator.py  # 割り当てロジック
│   └── excel_exporter.py        # Excel出力
└── tests/
    └── test_assignment.py
```

### Excel出力（openpyxl）

```python
# backend/apps/work_assignment/services/excel_exporter.py

from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment
from io import BytesIO

# 色定義
RED_FILL = PatternFill(start_color='FFCCCC', end_color='FFCCCC', fill_type='solid')
YELLOW_FILL = PatternFill(start_color='FFFFCC', end_color='FFFFCC', fill_type='solid')
GREEN_FILL = PatternFill(start_color='CCFFCC', end_color='CCFFCC', fill_type='solid')
HEADER_FILL = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')


def export_to_excel(assignments, warnings, statistics):
    wb = Workbook()

    # シート1: 仕事割表
    ws1 = wb.active
    ws1.title = '仕事割表'
    create_assignment_sheet(ws1, assignments, warnings)

    # シート2: 警告一覧
    ws2 = wb.create_sheet('警告一覧')
    create_warnings_sheet(ws2, warnings)

    # シート3: 統計情報
    ws3 = wb.create_sheet('統計情報')
    create_statistics_sheet(ws3, statistics)

    # バイトストリームに出力
    output = BytesIO()
    wb.save(output)
    output.seek(0)

    return output


def create_assignment_sheet(ws, assignments, warnings):
    # ヘッダー
    headers = ['#', 'バンド名', '管理1', '管理2', '管理3',
               '渉外1', '渉外2', '合評1', '合評2', '会計', 'C協', '書記']

    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.fill = HEADER_FILL
        cell.font = Font(color='FFFFFF', bold=True)
        cell.alignment = Alignment(horizontal='center')

    # データ行
    warning_cells = {(w['slot'], w['dept']): w for w in warnings}

    for row_idx, assignment in enumerate(assignments, 2):
        ws.cell(row=row_idx, column=1, value=row_idx - 1)
        ws.cell(row=row_idx, column=2, value=assignment['band'].name)

        col = 3
        for dept in ['kanri', 'shougai', 'gouhyou', 'kaikei', 'ckyou', 'shoki']:
            members = assignment.get(dept, [])
            for member in members:
                cell = ws.cell(row=row_idx, column=col, value=member.name)

                # 警告チェック
                warning_key = (row_idx - 1, dept)
                if warning_key in warning_cells:
                    if '制約違反' in warning_cells[warning_key]['message']:
                        cell.fill = RED_FILL
                    elif '上級生' in warning_cells[warning_key]['message']:
                        cell.fill = YELLOW_FILL

                col += 1

            # 人数分のカラムを確保
            required = DEPARTMENT_REQUIREMENTS[dept]
            col += max(0, required - len(members))
```

---

## 実装フェーズ

### Phase 1: バックエンド基盤

1. `work_assignment` アプリ作成
2. 割り当てアルゴリズム実装
3. Excel出力機能実装
4. APIエンドポイント作成

**変更ファイル:**
- `backend/apps/work_assignment/` (新規ディレクトリ)
- `backend/backend/settings/base.py` (INSTALLED_APPS追加)
- `backend/backend/urls.py` (URL追加)

### Phase 2: フロントエンド

1. 仕事割作成ページ作成
2. バンド順入力コンポーネント
3. 参加メンバー選択コンポーネント
4. ファイルダウンロード処理

**変更ファイル:**
- `frontend/src/pages/WorkAssignment.jsx` (新規)
- `frontend/src/components/work-assignment/` (新規ディレクトリ)
- `frontend/src/main.jsx` (ルーティング追加)

### Phase 3: テスト・調整

1. 各種制約のテストケース作成
2. エッジケース対応（メンバー不足など）
3. Excel出力の確認・調整

---

## 依存ライブラリ

### バックエンド
- `openpyxl` (既存 - 一括登録で使用)

### フロントエンド
- 追加なし

---

## 注意事項

1. **バンドメンバー情報の前提**
   - バンドにメンバーが紐付いている必要がある
   - Feature_MemberManagement.md のバンド管理機能が前提

2. **参加メンバーの初期値**
   - デフォルトは全員参加（全員チェック済み）
   - 不参加者のみチェックを外す運用

3. **未登録バンドの扱い**
   - 入力されたバンド名が未登録の場合、警告表示
   - 未登録バンドは割り当て処理をスキップ（出力Excelには含まれない）

4. **パフォーマンス**
   - 通常のライブ規模（20〜30バンド）では問題なし
   - 大規模イベントでも線形時間で処理可能

---

## 関連機能

- [メンバー管理](./Feature_MemberManagement.md) - バンドメンバー情報
- [ユーザー管理](./Feature_UserManagement.md) - メンバーの学年情報
- [タイマー一括登録](./Feature_BulkTimerImport.md) - タイマー登録との連携
