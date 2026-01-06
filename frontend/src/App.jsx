import { useEffect, useRef } from 'react';
import { useTimerStore } from './stores/timerStore';
import { getTimerState, getTimers } from './services/api';
import useKeyboard from './hooks/useKeyboard';
import CurrentTimer from './components/timer/CurrentTimer';
import TimerControls from './components/timer/TimerControls';
import TimeDifferenceDisplay from './components/timer/TimeDifferenceDisplay';
import TimerList from './components/timer/TimerList';

function App() {
  const { updateTimerState, updateTimerList, remainingSeconds, setRemainingSeconds } = useTimerStore();
  const pollingIntervalRef = useRef(null);
  const timerListPollingRef = useRef(null);

  // キーボードショートカットを有効化（MVP Step 2）
  useKeyboard();

  // 初回読み込み時にタイマー状態を取得
  useEffect(() => {
    const fetchTimerState = async () => {
      try {
        const data = await getTimerState();
        updateTimerState(data);
      } catch (error) {
        console.error('タイマー状態の取得に失敗しました:', error);
      }
    };

    fetchTimerState();

    // 1秒ごとにポーリング（MVP Step 1ではWebSocket未実装）
    pollingIntervalRef.current = setInterval(fetchTimerState, 1000);

    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, [updateTimerState]);

  // タイマーリストのポーリング（MVP Step 2）
  useEffect(() => {
    const fetchTimerList = async () => {
      try {
        const timers = await getTimers();
        updateTimerList(timers);
      } catch (error) {
        console.error('タイマーリストの取得に失敗しました:', error);
      }
    };

    fetchTimerList();

    // 1秒ごとにポーリング
    timerListPollingRef.current = setInterval(fetchTimerList, 1000);

    return () => {
      if (timerListPollingRef.current) {
        clearInterval(timerListPollingRef.current);
      }
    };
  }, [updateTimerList]);

  // クライアント側でカウントダウン（表示のスムーズさのため）
  useEffect(() => {
    const intervalId = setInterval(() => {
      setRemainingSeconds(Math.max(0, remainingSeconds - 1));
    }, 1000);

    return () => clearInterval(intervalId);
  }, [remainingSeconds, setRemainingSeconds]);

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
            <strong>MVP Step 2:</strong> タイマー一覧と押し巻き表示
          </p>
          <p className="text-xs text-green-600 mt-1">
            ✅ タイマーリスト表示 | ✅ 全体の押し巻き表示 | ✅ 一時停止・スキップ | ✅ キーボードショートカット (Space: 一時停止/再開, →: スキップ)
          </p>
        </div>
      </main>
    </div>
  );
}

export default App;
