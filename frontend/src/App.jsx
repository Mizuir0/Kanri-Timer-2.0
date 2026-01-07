import { useEffect } from 'react';
import { useTimerStore } from './stores/timerStore';
import websocketService from './services/websocket';
import useKeyboard from './hooks/useKeyboard';
import { getTimerState, getTimers } from './services/api';
import CurrentTimer from './components/timer/CurrentTimer';
import TimerControls from './components/timer/TimerControls';
import TimeDifferenceDisplay from './components/timer/TimeDifferenceDisplay';
import TimerList from './components/timer/TimerList';
import TimerFormModal from './components/admin/TimerFormModal';

function App() {
  const {
    updateTimerState,
    updateTimerList,
    remainingSeconds,
    setRemainingSeconds,
    isRunning,
    isPaused,
    isTimerFormOpen,
    editingTimer,
    closeTimerForm,
    fetchMembers,
  } = useTimerStore();

  // キーボードショートカットを有効化（MVP Step 2）
  useKeyboard();

  // 初期データ取得
  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        const [stateData, timersData] = await Promise.all([
          getTimerState(),
          getTimers(),
        ]);

        // タイマー一覧を先に更新
        updateTimerList(timersData);

        // current_timerがnullで、未完了タイマーがある場合は最初のタイマーを自動セット
        if (!stateData.current_timer && timersData.length > 0) {
          const firstIncompleteTimer = timersData.find(t => !t.is_completed);
          if (firstIncompleteTimer) {
            stateData.current_timer = firstIncompleteTimer;
            stateData.remaining_seconds = firstIncompleteTimer.minutes * 60;
            console.log('[App] 最初のタイマーを自動セット:', firstIncompleteTimer.band_name);
          }
        }

        updateTimerState(stateData);

        // メンバー情報も取得（モーダル用）
        await fetchMembers();
        console.log('[App] 初期データ取得完了');
      } catch (error) {
        console.error('[App] 初期データ取得失敗:', error);
      }
    };

    fetchInitialData();
  }, [updateTimerState, updateTimerList, fetchMembers]);

  // WebSocket接続とイベントリスナー設定（MVP Step 4）
  useEffect(() => {
    // WebSocket接続
    websocketService.connect();

    // タイマー状態更新イベント
    const handleTimerStateUpdate = (data) => {
      console.log('[App] タイマー状態更新:', data);
      updateTimerState(data);
    };

    // タイマーリスト更新イベント
    const handleTimerListUpdate = (data) => {
      console.log('[App] タイマーリスト更新:', data);
      updateTimerList(data);
    };

    // 接続確立イベント
    const handleConnectionEstablished = () => {
      console.log('[App] WebSocket接続確立');
    };

    // 接続切断イベント
    const handleConnectionLost = () => {
      console.warn('[App] WebSocket接続切断 - 再接続を試みます');
    };

    // リスナー登録
    websocketService.on('timer_state_updated', handleTimerStateUpdate);
    websocketService.on('timer_list_updated', handleTimerListUpdate);
    websocketService.on('connection_established', handleConnectionEstablished);
    websocketService.on('connection_lost', handleConnectionLost);

    // クリーンアップ
    return () => {
      websocketService.off('timer_state_updated', handleTimerStateUpdate);
      websocketService.off('timer_list_updated', handleTimerListUpdate);
      websocketService.off('connection_established', handleConnectionEstablished);
      websocketService.off('connection_lost', handleConnectionLost);
      websocketService.disconnect();
    };
  }, [updateTimerState, updateTimerList]);

  // クライアント側でカウントダウン（表示のスムーズさのため）
  useEffect(() => {
    // isRunningがtrueで、isPausedがfalseの時のみカウントダウン
    if (!isRunning || isPaused) {
      return;
    }

    const intervalId = setInterval(() => {
      setRemainingSeconds(Math.max(0, remainingSeconds - 1));
    }, 1000);

    return () => clearInterval(intervalId);
  }, [remainingSeconds, setRemainingSeconds, isRunning, isPaused]);

  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-blue-600 text-white p-4 shadow-md">
        <h1 className="text-3xl font-bold text-center">KanriTimer 2.0</h1>
      </header>

      <main className="container mx-auto p-6 max-w-7xl">
        {/* 全体の進行状況（押し巻き表示） */}
        <div className="mb-6">
          <TimeDifferenceDisplay />
        </div>

        {/* メインコンテンツ: PC版は2カラム、モバイル版は縦積み */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 左カラム: 現在のタイマーとコントロール */}
          <div className="space-y-6">
            <CurrentTimer />
            <TimerControls />
          </div>

          {/* 右カラム: タイマー一覧 */}
          <div>
            <TimerList />
          </div>
        </div>

        {/* 開発情報 */}
        <div className="bg-green-50 border-l-4 border-green-500 p-4 mt-6">
          <p className="text-sm text-green-700">
            <strong>MVP Step 3:</strong> CRUD機能（作成・編集・削除・並び替え）
          </p>
          <p className="text-xs text-green-600 mt-1">
            ✅ タイマー作成 | ✅ タイマー編集 | ✅ タイマー削除 | ✅ ドラッグ&ドロップ並び替え
          </p>
        </div>
      </main>

      {/* タイマー追加・編集モーダル */}
      <TimerFormModal
        isOpen={isTimerFormOpen}
        onClose={closeTimerForm}
        timer={editingTimer}
      />
    </div>
  );
}

export default App;
