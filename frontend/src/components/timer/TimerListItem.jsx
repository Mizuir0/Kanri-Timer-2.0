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

  // 時間差の色を決定（完了時のみ表示）
  const getTimeDifferenceColor = () => {
    if (!timer.time_difference) return '';

    const diff = timer.time_difference;
    if (diff > 0) {
      return 'text-red-600'; // 押し
    } else if (diff < 0) {
      return 'text-green-600'; // 巻き
    } else {
      return 'text-gray-600'; // 定刻通り
    }
  };

  // 時間差を表示形式に変換
  const formatTimeDifference = () => {
    if (!timer.time_difference) return '';

    const absDiff = Math.abs(timer.time_difference);
    const minutes = Math.floor(absDiff / 60);
    const seconds = absDiff % 60;
    const timeStr = `${minutes}:${seconds.toString().padStart(2, '0')}`;

    if (timer.time_difference > 0) {
      return `+${timeStr} 押し`;
    } else if (timer.time_difference < 0) {
      return `-${timeStr} 巻き`;
    } else {
      return '定刻通り';
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
          <span className={`text-sm font-medium tabular-nums ${getTimeDifferenceColor()}`}>
            {formatTimeDifference()}
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
