import { useTimerStore } from '../../stores/timerStore';
import { startTimer } from '../../services/api';
import Button from '../common/Button';

const TimerControls = () => {
  const { currentTimer, isRunning, isPaused } = useTimerStore();

  const handleStart = async () => {
    try {
      await startTimer();
      // タイマー状態は別途ポーリングで更新される
    } catch (error) {
      console.error('タイマーの開始に失敗しました:', error);
      alert('タイマーの開始に失敗しました');
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex gap-4 justify-center">
        {!isRunning && (
          <Button
            onClick={handleStart}
            variant="primary"
            disabled={!currentTimer}
            className="text-xl px-8 py-4"
          >
            開始 (スペース)
          </Button>
        )}

        {/* Step 2で追加
        {isRunning && !isPaused && (
          <>
            <Button onClick={handlePause} variant="warning">
              一時停止 (スペース)
            </Button>
            <Button onClick={handleSkip} variant="secondary">
              スキップ (→)
            </Button>
          </>
        )}

        {isPaused && (
          <>
            <Button onClick={handleResume} variant="success">
              再開 (スペース)
            </Button>
            <Button onClick={handleSkip} variant="secondary">
              スキップ (→)
            </Button>
          </>
        )}
        */}
      </div>
    </div>
  );
};

export default TimerControls;
