import { useTimerStore } from '../../stores/timerStore';
import TimerListItem from './TimerListItem';

const TimerList = () => {
  const { allTimers, currentTimer } = useTimerStore();

  if (!allTimers || allTimers.length === 0) {
    return (
      <div className="p-4 text-center text-gray-500">
        タイマーがありません
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      {/* ヘッダー */}
      <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-700">タイマー一覧</h2>
        <p className="text-xs text-gray-500 mt-1">
          {allTimers.filter(t => t.completed_at).length} / {allTimers.length} 完了
        </p>
      </div>

      {/* タイマーリスト */}
      <div className="max-h-96 overflow-y-auto">
        {allTimers.map((timer) => (
          <TimerListItem
            key={timer.id}
            timer={timer}
            isCurrent={currentTimer?.id === timer.id}
          />
        ))}
      </div>
    </div>
  );
};

export default TimerList;
