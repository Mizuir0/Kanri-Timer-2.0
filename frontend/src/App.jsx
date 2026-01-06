import { useEffect, useRef } from 'react';
import { useTimerStore } from './stores/timerStore';
import { getTimerState } from './services/api';
import CurrentTimer from './components/timer/CurrentTimer';
import TimerControls from './components/timer/TimerControls';

function App() {
  const { updateTimerState, remainingSeconds, setRemainingSeconds } = useTimerStore();
  const pollingIntervalRef = useRef(null);

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

      <main className="container mx-auto p-6 max-w-4xl">
        <div className="space-y-6">
          <CurrentTimer />
          <TimerControls />

          <div className="bg-blue-50 border-l-4 border-blue-500 p-4 mt-6">
            <p className="text-sm text-blue-700">
              <strong>MVP Step 1:</strong> 最小構成（タイマー表示+開始ボタン）
            </p>
            <p className="text-xs text-blue-600 mt-1">
              ※ 一時停止・スキップ・タイマー一覧はStep 2以降で実装します
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
