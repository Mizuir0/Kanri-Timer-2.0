import { useTimerStore } from '../../stores/timerStore';
import { formatTime } from '../../utils/timeFormat';

const CurrentTimer = () => {
  const { currentTimer, remainingSeconds, isRunning, isPaused } = useTimerStore();

  if (!currentTimer) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-8 text-center">
        <p className="text-gray-500 text-lg">タイマーがありません</p>
        <p className="text-sm text-gray-400 mt-2">
          タイマーを作成して開始してください
        </p>
      </div>
    );
  }

  const getStatusBadge = () => {
    if (isPaused) {
      return <span className="text-yellow-500 text-xl">一時停止⏸️</span>;
    }
    if (isRunning) {
      return <span className="text-red-500 text-xl">実行中🔴</span>;
    }
    return <span className="text-gray-500 text-xl">待機中</span>;
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-8">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold text-gray-600">現在のタイマー</h2>
        {getStatusBadge()}
      </div>

      <div className="text-center">
        <h3 className="text-4xl font-bold mb-6">{currentTimer.band_name}</h3>

        <div className="text-8xl font-bold text-gray-800 mb-6">
          {formatTime(remainingSeconds)}
        </div>

        <div className="mt-6 text-gray-600">
          <p className="text-xl">
            {currentTimer.members && currentTimer.members.join('、')}
          </p>
        </div>
      </div>
    </div>
  );
};

export default CurrentTimer;
