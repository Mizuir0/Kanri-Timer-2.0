# オフライン対応機能

## 概要

テザリング環境でのタイマー操作を想定し、接続切断時の挙動を改善する機能。

---

## 背景・課題

### 利用環境
- WiFi環境なし
- スマホのモバイル通信でテザリングしてPCを接続
- タイマー操作はPC、確認はスマホでも可能

### 発生する問題
1. テザリング元のスマホ所有者が離席 → PCの接続が切れる
2. 現状の挙動:
   - タイマー表示がフリーズ
   - オフラインかどうか判別できない
   - 復帰時の再接続に時間がかかる場合がある

### 要件
- **最低限**: テザリング復帰時に即座に状態回復
- **理想**: オフライン中もタイマー表示が動き続け、オフライン状態が視覚的にわかる

---

## 実装計画

### Phase 1: オフライン検知と可視化

#### 機能一覧

| 機能 | 説明 |
|------|------|
| 接続状態監視 | ブラウザのオンライン/オフライン状態を監視 |
| WebSocket状態監視 | WebSocket接続の状態を監視 |
| オフライン警告バナー | オフライン時に画面上部に警告を表示 |
| 自動再接続強化 | 復帰検知で即座にWebSocket再接続＋状態取得 |

#### 技術詳細

##### 1. 接続状態監視フック (`useConnectionStatus.js`)

```javascript
// frontend/src/hooks/useConnectionStatus.js

import { useState, useEffect } from 'react';
import websocketService from '../services/websocket';

export const useConnectionStatus = () => {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [isWebSocketConnected, setIsWebSocketConnected] = useState(false);

  useEffect(() => {
    // ブラウザのオンライン/オフライン検知
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // WebSocket接続状態の監視
    const handleWsConnected = () => setIsWebSocketConnected(true);
    const handleWsDisconnected = () => setIsWebSocketConnected(false);

    websocketService.on('connection_established', handleWsConnected);
    websocketService.on('connection_lost', handleWsDisconnected);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      websocketService.off('connection_established', handleWsConnected);
      websocketService.off('connection_lost', handleWsDisconnected);
    };
  }, []);

  // 両方がtrueの場合のみ「接続中」
  const isConnected = isOnline && isWebSocketConnected;

  return { isOnline, isWebSocketConnected, isConnected };
};
```

##### 2. オフライン警告バナー (`OfflineBanner.jsx`)

```jsx
// frontend/src/components/common/OfflineBanner.jsx

const OfflineBanner = ({ isConnected }) => {
  if (isConnected) return null;

  return (
    <div className="fixed top-0 left-0 right-0 bg-red-600 text-white text-center py-2 z-50">
      <span className="font-bold">オフライン</span>
      <span className="ml-2 text-sm">接続が切断されています。テザリングを確認してください。</span>
    </div>
  );
};

export default OfflineBanner;
```

##### 3. WebSocket再接続強化 (`websocket.js` 修正)

```javascript
// frontend/src/services/websocket.js に追加

// オンライン復帰時に即座に再接続を試みる
window.addEventListener('online', () => {
  console.log('[WebSocket] オンライン復帰検知 - 再接続開始');
  this.reconnect();
});

// 再接続成功時に最新状態を取得
onReconnected() {
  // APIから最新状態を取得してストアを更新
  getTimerState().then(state => {
    useTimerStore.getState().updateTimerState(state);
  });
  getTimers().then(timers => {
    useTimerStore.getState().updateTimerList(timers);
  });
}
```

##### 4. App.jsx への組み込み

```jsx
// frontend/src/App.jsx に追加

import { useConnectionStatus } from './hooks/useConnectionStatus';
import OfflineBanner from './components/common/OfflineBanner';

function App() {
  const { isConnected } = useConnectionStatus();

  return (
    <div className="min-h-screen bg-gray-100">
      <OfflineBanner isConnected={isConnected} />
      {/* 既存のコンテンツ（オフライン時は上に余白追加） */}
      <div className={!isConnected ? 'pt-10' : ''}>
        {/* ... */}
      </div>
    </div>
  );
}
```

#### 変更ファイル一覧 (Phase 1)

| ファイル | 変更内容 |
|----------|----------|
| `frontend/src/hooks/useConnectionStatus.js` | 新規作成 |
| `frontend/src/components/common/OfflineBanner.jsx` | 新規作成 |
| `frontend/src/services/websocket.js` | 再接続ロジック強化 |
| `frontend/src/App.jsx` | バナー組み込み |

---

### Phase 2: ローカルカウントダウン

#### 機能一覧

| 機能 | 説明 |
|------|------|
| ローカルタイマー | オフライン中もクライアント側でカウントダウン継続 |
| 操作ボタン無効化 | オフライン中はボタンをグレーアウト |
| 最終同期時刻表示 | 「最終同期: XX秒前」を表示 |
| 復帰時同期 | サーバーの状態でローカル表示を上書き |

#### 技術詳細

##### 1. ローカルカウントダウンフック (`useLocalCountdown.js`)

```javascript
// frontend/src/hooks/useLocalCountdown.js

import { useEffect, useRef } from 'react';
import { useTimerStore } from '../stores/timerStore';

export const useLocalCountdown = (isConnected) => {
  const intervalRef = useRef(null);
  const { isRunning, isPaused, remainingSeconds, setRemainingSeconds } = useTimerStore();

  useEffect(() => {
    // オフライン中かつタイマー実行中の場合、ローカルでカウントダウン
    if (!isConnected && isRunning && !isPaused) {
      intervalRef.current = setInterval(() => {
        setRemainingSeconds(prev => Math.max(0, prev - 1));
      }, 1000);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isConnected, isRunning, isPaused]);
};
```

##### 2. 最終同期時刻の追跡 (`timerStore.js` 修正)

```javascript
// frontend/src/stores/timerStore.js に追加

// ストアに追加
lastSyncTime: null,

// アクション追加
setLastSyncTime: (time) => set({ lastSyncTime: time }),

// updateTimerState を修正
updateTimerState: (state) => set({
  currentTimer: state.current_timer,
  remainingSeconds: state.remaining_seconds || 0,
  isRunning: state.is_running,
  isPaused: state.is_paused,
  lineNotificationsEnabled: state.line_notifications_enabled ?? true,
  totalTimeDifference: state.total_time_difference || 0,
  totalTimeDifferenceDisplay: state.total_time_difference_display || '',
  lastSyncTime: Date.now(), // 同期時刻を記録
}),
```

##### 3. 最終同期表示コンポーネント (`SyncStatus.jsx`)

```jsx
// frontend/src/components/common/SyncStatus.jsx

import { useState, useEffect } from 'react';
import { useTimerStore } from '../../stores/timerStore';

const SyncStatus = ({ isConnected }) => {
  const { lastSyncTime } = useTimerStore();
  const [secondsAgo, setSecondsAgo] = useState(0);

  useEffect(() => {
    if (!isConnected && lastSyncTime) {
      const interval = setInterval(() => {
        setSecondsAgo(Math.floor((Date.now() - lastSyncTime) / 1000));
      }, 1000);
      return () => clearInterval(interval);
    } else {
      setSecondsAgo(0);
    }
  }, [isConnected, lastSyncTime]);

  if (isConnected) return null;

  return (
    <div className="text-sm text-gray-500 text-center">
      最終同期: {secondsAgo}秒前
    </div>
  );
};

export default SyncStatus;
```

##### 4. 操作ボタン無効化 (`TimerControls.jsx` 修正)

```jsx
// frontend/src/components/timer/TimerControls.jsx

// propsまたはhookでisConnectedを受け取る
const { isConnected } = useConnectionStatus();

// ボタンに disabled 属性を追加
<button
  onClick={handleStart}
  disabled={!isConnected}
  className={`... ${!isConnected ? 'opacity-50 cursor-not-allowed' : ''}`}
>
  開始
</button>
```

#### 変更ファイル一覧 (Phase 2)

| ファイル | 変更内容 |
|----------|----------|
| `frontend/src/hooks/useLocalCountdown.js` | 新規作成 |
| `frontend/src/components/common/SyncStatus.jsx` | 新規作成 |
| `frontend/src/stores/timerStore.js` | lastSyncTime追加 |
| `frontend/src/components/timer/TimerControls.jsx` | ボタン無効化 |
| `frontend/src/components/timer/CurrentTimer.jsx` | SyncStatus表示 |
| `frontend/src/App.jsx` | useLocalCountdown組み込み |

---

## UI/UX設計

### オフライン時の画面イメージ

```
┌─────────────────────────────────────────────────┐
│ ⚠️ オフライン - 接続が切断されています          │ ← 赤いバナー
├─────────────────────────────────────────────────┤
│                                                 │
│              KanriTimer 2.0                     │
│                                                 │
│         ┌─────────────────────┐                 │
│         │      04:32          │ ← ローカルで   │
│         │   バンド名          │   カウントダウン│
│         │  最終同期: 15秒前   │                 │
│         └─────────────────────┘                 │
│                                                 │
│    [開始] [一時停止] [スキップ]  ← グレーアウト  │
│                                                 │
└─────────────────────────────────────────────────┘
```

### 状態遷移

```
オンライン
    │
    ├── テザリング切断 ──→ オフライン
    │                         │
    │                         ├── 警告バナー表示
    │                         ├── ローカルカウントダウン開始
    │                         └── 操作ボタン無効化
    │
    └── テザリング復帰 ←──────┘
              │
              ├── WebSocket再接続
              ├── サーバーから状態取得
              ├── ローカル表示を同期
              └── 警告バナー非表示
```

---

## テスト計画

### Phase 1 テスト項目

| # | テスト内容 | 確認方法 |
|---|-----------|----------|
| 1 | WiFi切断でバナー表示 | PCのWiFiをオフ |
| 2 | WiFi復帰でバナー消去 | PCのWiFiをオン |
| 3 | 復帰時に最新状態を取得 | 別端末でタイマー操作後に復帰 |
| 4 | WebSocket切断を検知 | サーバーを停止 |

### Phase 2 テスト項目

| # | テスト内容 | 確認方法 |
|---|-----------|----------|
| 1 | オフラインでカウントダウン継続 | WiFi切断後もタイマー表示が減る |
| 2 | 操作ボタンが無効化 | オフライン時にボタンが押せない |
| 3 | 最終同期時刻が更新される | オフライン中に秒数が増える |
| 4 | 復帰時にサーバー状態で同期 | 別端末で操作 → 復帰で反映 |

### テザリング環境での実地テスト

1. スマホでテザリング開始
2. PCでタイマー開始
3. スマホを持って離席（テザリング切断）
4. バナー表示・ローカルカウントダウンを確認
5. スマホを戻す（テザリング復帰）
6. 状態が正しく同期されることを確認

---

## 実装優先度

| 優先度 | 機能 | Phase |
|--------|------|-------|
| 高 | オフライン警告バナー | 1 |
| 高 | 再接続時の状態取得 | 1 |
| 中 | ローカルカウントダウン | 2 |
| 中 | 操作ボタン無効化 | 2 |
| 低 | 最終同期時刻表示 | 2 |

---

## 注意事項

1. **タイマーの正確性**
   - ローカルカウントダウンはあくまで「表示用」
   - サーバー側のタイマーが正（押し巻き計算等）
   - 復帰時は必ずサーバー状態で上書き

2. **長時間オフライン**
   - 数分程度のオフラインを想定
   - 長時間（数十分以上）は想定外

3. **複数端末**
   - オフライン中の端末は他端末の操作を受信できない
   - 復帰時にまとめて同期

---

## 関連ファイル

- `frontend/src/services/websocket.js` - WebSocket接続管理
- `frontend/src/stores/timerStore.js` - タイマー状態管理
- `frontend/src/App.jsx` - メインコンポーネント
- `frontend/src/components/timer/` - タイマー関連コンポーネント
