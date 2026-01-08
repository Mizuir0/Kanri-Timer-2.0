import { useTimerStore } from '../../stores/timerStore';
import { startTimer, pauseTimer, resumeTimer, skipTimer } from '../../services/api';
import Button from '../common/Button';
import useDeviceDetect from '../../hooks/useDeviceDetect';

const TimerControls = () => {
  const { currentTimer, isRunning, isPaused } = useTimerStore();
  const { isMobile } = useDeviceDetect();

  const handleStart = async () => {
    try {
      await startTimer();
      // タイマー状態は別途ポーリングで更新される
    } catch (error) {
      console.error('タイマーの開始に失敗しました:', error);
      alert('タイマーの開始に失敗しました');
    }
  };

  const handlePause = async () => {
    try {
      await pauseTimer();
    } catch (error) {
      console.error('タイマーの一時停止に失敗しました:', error);
      alert('タイマーの一時停止に失敗しました');
    }
  };

  const handleResume = async () => {
    try {
      await resumeTimer();
    } catch (error) {
      console.error('タイマーの再開に失敗しました:', error);
      alert('タイマーの再開に失敗しました');
    }
  };

  const handleSkip = async () => {
    if (!confirm('このタイマーをスキップして次に進みますか？')) {
      return;
    }
    try {
      await skipTimer();
    } catch (error) {
      console.error('タイマーのスキップに失敗しました:', error);
      alert('タイマーのスキップに失敗しました');
    }
  };

  // モバイルでは操作ボタンを非表示（閲覧専用）
  if (isMobile) {
    return null;
  }

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
      </div>
    </div>
  );
};

export default TimerControls;
