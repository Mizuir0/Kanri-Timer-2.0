# タイマー一括登録機能

## 概要

Excelファイルからタイマー（出番）と担当者を一括登録する機能。既存のリハーサル仕事表を活用して効率的にタイマーをセットアップする。

---

## 前提条件

- **Feature_MemberManagement.md** の実装が完了していること
  - Bandモデルが存在すること
  - Memberモデルにdepartmentフィールドがあること
  - TimerStaffモデルが存在すること

---

## Excel形式

### 入力フォーマット

```
| バンド名 | 管理1 | 管理2 | 管理3 | 渉外1 | 渉外2 | 合評1 | 合評2 | 会計 | C協 | 書記 |
|----------|-------|-------|-------|-------|-------|-------|-------|------|-----|------|
| Band A   | 中尾  | 星野  | 山田  | 青木  | 半田  | 松本  | 鈴木  | 田中 | 佐藤| 高橋 |
| Band B   | 山田  | 中尾  | 星野  | 半田  | 青木  | 鈴木  | 松本  | 佐藤 | 田中| 高橋 |
| ...      | ...   | ...   | ...   | ...   | ...   | ...   | ...   | ...  | ... | ...  |
```

### 列の対応

| 列名 | 役割 | 必須 |
|------|------|------|
| バンド名 | バンド識別（Bandモデルと照合） | ○ |
| 管理1〜3 | 管理担当者 | - |
| 渉外1〜2 | 渉外担当者 | - |
| 合評1〜2 | 合評担当者 | - |
| 会計 | 会計担当者 | - |
| C協 | C協担当者 | - |
| 書記 | 書記担当者 | - |

---

## インポート仕様

### 基本動作

1. 既存のタイマーを**全削除**
2. Excelの上から順にタイマーを作成
3. 持ち時間はデフォルト**15分**
4. バンド情報（コピー元・メンバー）は既存Bandから自動取得

### バンドの処理

```
Excelのバンド名
    │
    ▼
データベースで検索
    │
    ├── 既存バンドあり
    │       │
    │       ▼
    │   タイマー作成
    │   ├── band: 既存バンドを紐付け
    │   ├── minutes: 15（デフォルト）
    │   └── order: Excel行順
    │
    └── 既存バンドなし
            │
            ▼
        この行をスキップ（警告に追加）
```

### 担当者の処理

```
Excelの担当者名（例: 「中尾」）
    │
    ▼
メンバーDBで検索
    │
    ├── メンバーあり
    │       │
    │       ▼
    │   TimerStaff作成
    │   ├── timer: 作成したタイマー
    │   ├── member: 見つかったメンバー
    │   └── role: 列から推測（管理1→kanri等）
    │
    └── メンバーなし
            │
            ▼
        この担当者をスキップ（警告に追加）
```

### 列名から役割への変換

```python
COLUMN_TO_ROLE = {
    '管理1': 'kanri',
    '管理2': 'kanri',
    '管理3': 'kanri',
    '渉外1': 'shougai',
    '渉外2': 'shougai',
    '合評1': 'gouhyou',
    '合評2': 'gouhyou',
    '会計': 'kaikei',
    'C協': 'ckyou',
    '書記': 'shoki',
}
```

---

## インポート結果

### 成功時

```
インポートが完了しました。

作成されたタイマー: 12件
登録された担当者: 108人

警告:
- バンド「Band X」が見つかりませんでした（2行目）
- メンバー「田中」が見つかりませんでした（3行目: 会計）
- メンバー「Unknown」が見つかりませんでした（5行目: 渉外1）
```

### エラー時

```
インポートに失敗しました。

エラー:
- ファイル形式が正しくありません（.xlsx形式のみ対応）
- 「バンド名」列が見つかりません
```

---

## UI設計

### インポートボタンの配置

タイマー一覧の上部に配置:

```
┌─────────────────────────────────────────────────┐
│ タイマー一覧                                    │
├─────────────────────────────────────────────────┤
│                                                 │
│ [+ 新規追加]  [Excelからインポート]             │
│                                                 │
│ ┌─────────────────────────────────────────────┐ │
│ │ 1. Band A (BUMP OF CHICKEN)      15:00     │ │
│ │ 2. Band B (Official髭男dism)     15:00     │ │
│ │ ...                                        │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
└─────────────────────────────────────────────────┘
```

### インポートモーダル

```
┌─────────────────────────────────────────────────┐
│ Excelからインポート                       [×]   │
├─────────────────────────────────────────────────┤
│                                                 │
│ ⚠️ 注意: 既存のタイマーは全て削除されます       │
│                                                 │
│ ┌─────────────────────────────────────────────┐ │
│ │                                             │ │
│ │     📁 ファイルをドラッグ＆ドロップ         │ │
│ │        または クリックして選択              │ │
│ │                                             │ │
│ │         対応形式: .xlsx                     │ │
│ │                                             │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ 📝 フォーマット:                                │
│ | バンド名 | 管理1 | 管理2 | 管理3 | 渉外1 | ...│
│                                                 │
│              [キャンセル]  [インポート]         │
│                                                 │
└─────────────────────────────────────────────────┘
```

### インポート結果モーダル

```
┌─────────────────────────────────────────────────┐
│ インポート結果                            [×]   │
├─────────────────────────────────────────────────┤
│                                                 │
│ ✅ インポートが完了しました                     │
│                                                 │
│ 作成されたタイマー: 12件                        │
│ 登録された担当者: 108人                         │
│                                                 │
│ ⚠️ 警告 (3件)                                   │
│ ┌─────────────────────────────────────────────┐ │
│ │ • バンド「Band X」が見つかりません（2行目） │ │
│ │ • メンバー「田中」が見つかりません          │ │
│ │   （3行目: 会計）                           │ │
│ │ • メンバー「Unknown」が見つかりません       │ │
│ │   （5行目: 渉外1）                          │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│                              [閉じる]           │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## バックエンド実装

### APIエンドポイント

```
POST /api/timers/import/
Content-Type: multipart/form-data

Body: file (Excel file)
```

### 処理フロー

```python
# backend/apps/timers/views.py

import openpyxl
from django.db import transaction
from apps.members.models import Member
from apps.bands.models import Band
from .models import Timer, TimerStaff

COLUMN_TO_ROLE = {
    '管理1': 'kanri', '管理2': 'kanri', '管理3': 'kanri',
    '渉外1': 'shougai', '渉外2': 'shougai',
    '合評1': 'gouhyou', '合評2': 'gouhyou',
    '会計': 'kaikei',
    'C協': 'ckyou',
    '書記': 'shoki',
}

@api_view(['POST'])
def import_timers(request):
    """Excelからタイマーを一括インポート"""
    file = request.FILES.get('file')

    if not file:
        return Response(
            {'error': 'ファイルが選択されていません'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not file.name.endswith('.xlsx'):
        return Response(
            {'error': 'ファイル形式が正しくありません（.xlsx形式のみ対応）'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        result = process_excel_import(file)
        return Response(result)
    except Exception as e:
        return Response(
            {'error': f'インポートに失敗しました: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def process_excel_import(file):
    """Excelファイルを処理してタイマーを作成"""
    workbook = openpyxl.load_workbook(file)
    sheet = workbook.active

    # ヘッダー行を取得
    headers = [cell.value for cell in sheet[1]]

    if 'バンド名' not in headers:
        raise ValueError('「バンド名」列が見つかりません')

    band_col_idx = headers.index('バンド名')

    warnings = []
    created_timers = 0
    created_staff = 0

    with transaction.atomic():
        # 既存タイマーを全削除
        Timer.objects.all().delete()

        # 2行目以降を処理
        for row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
            band_name = row[band_col_idx]

            if not band_name:
                continue

            # バンドを検索
            band = Band.objects.filter(name=band_name).first()

            if not band:
                warnings.append(f'バンド「{band_name}」が見つかりませんでした（{row_idx}行目）')
                continue

            # タイマー作成
            timer = Timer.objects.create(
                band=band,
                minutes=15,  # デフォルト15分
                order=created_timers
            )
            created_timers += 1

            # 担当者を処理
            for col_idx, col_name in enumerate(headers):
                if col_name in COLUMN_TO_ROLE:
                    member_name = row[col_idx]

                    if not member_name:
                        continue

                    # メンバーを検索
                    member = Member.objects.filter(name=member_name).first()

                    if not member:
                        warnings.append(
                            f'メンバー「{member_name}」が見つかりませんでした'
                            f'（{row_idx}行目: {col_name}）'
                        )
                        continue

                    # TimerStaff作成
                    TimerStaff.objects.create(
                        timer=timer,
                        member=member,
                        role=COLUMN_TO_ROLE[col_name]
                    )
                    created_staff += 1

    return {
        'success': True,
        'created_timers': created_timers,
        'created_staff': created_staff,
        'warnings': warnings
    }
```

### 依存ライブラリ

```
# backend/requirements.txt に追加
openpyxl==3.1.2
```

---

## フロントエンド実装

### インポートモーダルコンポーネント

```jsx
// frontend/src/components/timer/ImportModal.jsx

import { useState, useRef } from 'react';

const ImportModal = ({ isOpen, onClose, onImported }) => {
  const [file, setFile] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && droppedFile.name.endsWith('.xlsx')) {
      setFile(droppedFile);
    }
  };

  const handleImport = async () => {
    if (!file) return;

    setIsLoading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/api/timers/import/', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        setResult(data);
        onImported();
      } else {
        setResult({ error: data.error });
      }
    } catch (err) {
      setResult({ error: 'インポートに失敗しました' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    setFile(null);
    setResult(null);
    onClose();
  };

  if (!isOpen) return null;

  // 結果表示
  if (result) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 w-[500px] max-h-[80vh] overflow-y-auto">
          <h2 className="text-xl font-bold mb-4">インポート結果</h2>

          {result.error ? (
            <div className="text-red-600 mb-4">
              <p className="font-bold">エラー</p>
              <p>{result.error}</p>
            </div>
          ) : (
            <>
              <div className="text-green-600 mb-4">
                <p className="font-bold">インポートが完了しました</p>
              </div>

              <div className="mb-4">
                <p>作成されたタイマー: {result.created_timers}件</p>
                <p>登録された担当者: {result.created_staff}人</p>
              </div>

              {result.warnings.length > 0 && (
                <div className="mb-4">
                  <p className="font-bold text-yellow-600">
                    警告 ({result.warnings.length}件)
                  </p>
                  <ul className="list-disc list-inside text-sm text-gray-600 max-h-40 overflow-y-auto">
                    {result.warnings.map((warning, idx) => (
                      <li key={idx}>{warning}</li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          )}

          <div className="flex justify-end">
            <button
              onClick={handleClose}
              className="px-4 py-2 bg-blue-600 text-white rounded"
            >
              閉じる
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ファイル選択画面
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-[500px]">
        <h2 className="text-xl font-bold mb-4">Excelからインポート</h2>

        <div className="bg-yellow-50 border border-yellow-200 rounded p-3 mb-4">
          <p className="text-yellow-800 text-sm">
            ⚠️ 注意: 既存のタイマーは全て削除されます
          </p>
        </div>

        <div
          className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer hover:border-blue-500"
          onClick={() => fileInputRef.current?.click()}
          onDrop={handleDrop}
          onDragOver={(e) => e.preventDefault()}
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept=".xlsx"
            className="hidden"
          />

          {file ? (
            <p className="text-green-600">{file.name}</p>
          ) : (
            <>
              <p className="text-gray-500 mb-2">
                ファイルをドラッグ＆ドロップ
              </p>
              <p className="text-gray-400 text-sm">
                または クリックして選択
              </p>
              <p className="text-gray-400 text-xs mt-2">
                対応形式: .xlsx
              </p>
            </>
          )}
        </div>

        <div className="mt-4 text-sm text-gray-500">
          <p className="font-medium">フォーマット:</p>
          <p className="text-xs">| バンド名 | 管理1 | 管理2 | 管理3 | 渉外1 | ...</p>
        </div>

        <div className="flex justify-end space-x-2 mt-6">
          <button
            onClick={handleClose}
            className="px-4 py-2 border rounded"
          >
            キャンセル
          </button>
          <button
            onClick={handleImport}
            disabled={!file || isLoading}
            className={`px-4 py-2 rounded text-white ${
              file && !isLoading
                ? 'bg-blue-600 hover:bg-blue-700'
                : 'bg-gray-400 cursor-not-allowed'
            }`}
          >
            {isLoading ? 'インポート中...' : 'インポート'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ImportModal;
```

---

## API設計

| Method | Endpoint | 説明 |
|--------|----------|------|
| POST | `/api/timers/import/` | Excelファイルからタイマーを一括インポート |

### リクエスト

```
POST /api/timers/import/
Content-Type: multipart/form-data

file: (Excel file)
```

### レスポンス（成功時）

```json
{
  "success": true,
  "created_timers": 12,
  "created_staff": 108,
  "warnings": [
    "バンド「Band X」が見つかりませんでした（2行目）",
    "メンバー「田中」が見つかりませんでした（3行目: 会計）"
  ]
}
```

### レスポンス（エラー時）

```json
{
  "error": "ファイル形式が正しくありません（.xlsx形式のみ対応）"
}
```

---

## 実装フェーズ

### Phase 1: バックエンド

**優先度: 高**

1. openpyxlライブラリ追加
2. インポートAPIエンドポイント作成
3. Excel解析ロジック実装
4. エラーハンドリング

**変更ファイル:**
- `backend/requirements.txt`
- `backend/apps/timers/views.py`
- `backend/apps/timers/urls.py`

### Phase 2: フロントエンド

**優先度: 高**

1. インポートモーダルコンポーネント
2. ファイルアップロード機能
3. 結果表示UI
4. タイマー一覧への組み込み

**変更ファイル:**
- `frontend/src/components/timer/ImportModal.jsx`（新規）
- `frontend/src/components/timer/TimerList.jsx`

---

## 注意事項

1. **前提条件**
   - Feature_MemberManagement.mdの実装が必要
   - バンドとメンバーが事前に登録されていること

2. **データの整合性**
   - バンド名は完全一致で検索
   - メンバー名も完全一致で検索
   - 表記揺れに注意（全角/半角、スペースなど）

3. **ファイルサイズ**
   - 大きなファイルの場合、処理に時間がかかる可能性
   - 必要に応じてタイムアウト設定を調整

4. **既存データの削除**
   - インポート時に既存タイマーは全削除される
   - 必要に応じてバックアップ機能を検討

---

## 将来の拡張案

1. **プレビュー機能**
   - インポート前にデータをプレビュー表示
   - 問題がある行をハイライト

2. **持ち時間の列対応**
   - Excelに持ち時間列があれば読み込む

3. **追加モード**
   - 既存タイマーを削除せず追加のみ

4. **テンプレートダウンロード**
   - 正しい形式のExcelテンプレートをダウンロード可能に
