import { formatTimeDifference, getTimeDifferenceColor } from '../../utils/timeFormat';

const TimerListItem = ({ timer, isCurrent }) => {
  // 完了インジケータを決定
  const getStatusIcon = () => {
    if (timer.completed_at) {
      return '✅';
    } else if (isCurrent) {
      return '▶️';
    } else {
      return '⚪';
    }
  };

  return (
    <div
      className={`
        p-3 border-b border-gray-200 transition-colors
        ${isCurrent ? 'bg-blue-50 border-l-4 border-l-blue-500' : 'hover:bg-gray-50'}
        ${timer.completed_at ? 'opacity-75' : ''}
      `}
    >
      <div className="flex items-center gap-2">
        {/* ステータスアイコン */}
        <span className="text-lg">{getStatusIcon()}</span>

        {/* バンド名 */}
        <span
          className={`
            flex-1 font-medium
            ${timer.completed_at ? 'line-through text-gray-500' : 'text-gray-900'}
            ${isCurrent ? 'font-bold text-blue-700' : ''}
          `}
        >
          {timer.band_name}
        </span>

        {/* 時間差（完了時のみ） */}
        {timer.completed_at && timer.time_difference !== null && (
          <span className={`text-sm font-medium tabular-nums ${getTimeDifferenceColor(timer.time_difference)}`}>
            {formatTimeDifference(timer.time_difference)}
          </span>
        )}
      </div>

      {/* 現在のタイマーの場合は補足情報 */}
      {isCurrent && !timer.completed_at && (
        <div className="mt-1 text-xs text-blue-600 ml-7">
          実行中
        </div>
      )}
    </div>
  );
};

export default TimerListItem;
