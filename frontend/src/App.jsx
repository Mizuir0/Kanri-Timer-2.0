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
    setCurrentTimer,
    setRemainingSeconds,
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
            // remaining_secondsはバックエンドで計算されるので設定不要
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

      // タイマーが開始されていない場合、最初の未完了タイマーを自動セット
      // 最新の状態を取得するため、useTimerStore.getState() を使用
      const { isRunning: currentIsRunning, currentTimer: currentCurrentTimer } = useTimerStore.getState();

      if (!currentIsRunning && data.length > 0) {
        const firstIncompleteTimer = data.find(t => !t.is_completed);
        if (firstIncompleteTimer) {
          // 現在のタイマーと異なる場合のみ更新
          if (!currentCurrentTimer || currentCurrentTimer.id !== firstIncompleteTimer.id) {
            setCurrentTimer(firstIncompleteTimer);
            setRemainingSeconds(firstIncompleteTimer.minutes * 60);
            console.log('[App] 並び替え検知: 新しい最初のタイマーを自動セット:', firstIncompleteTimer.band_name);
          }
        }
      }
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
  }, [updateTimerState, updateTimerList, setCurrentTimer, setRemainingSeconds]);

  // クライアント側のカウントダウンは削除
  // WebSocketからの更新を信頼することで、表示のズレを防ぐ

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

        {/* メインコンテンツ: PC版は2:1比率、モバイル版は縦積み */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* 左カラム: 現在のタイマーとコントロール (2/3幅) */}
          <div className="lg:col-span-2 space-y-6">
            <CurrentTimer />
            <TimerControls />
          </div>

          {/* 右カラム: タイマー一覧 (1/3幅) */}
          <div className="lg:col-span-1">
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
