import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { useTimerStore } from '../../stores/timerStore';
import { deleteTimer } from '../../services/api';
import { useState } from 'react';

const SortableTimerItem = ({ timer, isCurrent, isMobile }) => {
  const { openTimerForm, isRunning } = useTimerStore();
  const [isHovered, setIsHovered] = useState(false);

  // Sortable hooks
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: timer.id,
    disabled: timer.is_completed || isMobile || (isCurrent && isRunning), // 完了済み、モバイル、または実行中ではドラッグ無効
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  // 編集不可判定
  const isEditable = !timer.is_completed && !(isCurrent && isRunning);

  // 削除ハンドラ
  const handleDelete = async () => {
    if (!window.confirm(`「${timer.band_name}」を削除しますか？`)) {
      return;
    }

    try {
      await deleteTimer(timer.id);
      console.log('タイマー削除成功');
    } catch (error) {
      console.error('タイマー削除失敗:', error);
      const errorMessage = error.response?.data?.detail || 'タイマーの削除に失敗しました。';
      alert(errorMessage);
    }
  };

  // 編集ハンドラ
  const handleEdit = () => {
    openTimerForm(timer);
  };

  // 完了インジケータ
  const getStatusIcon = () => {
    if (timer.completed_at) return '✅';
    if (isCurrent) return '▶️';
    return '⚪';
  };

  // 時間差の色
  const getTimeDifferenceColor = () => {
    if (!timer.time_difference) return '';
    const diff = timer.time_difference;
    if (diff > 0) return 'text-red-600'; // 押し
    if (diff < 0) return 'text-green-600'; // 巻き
    return 'text-gray-600'; // 定刻通り
  };

  // 時間差フォーマット
  const formatTimeDifference = () => {
    if (!timer.time_difference) return '';
    const absDiff = Math.abs(timer.time_difference);
    const minutes = Math.floor(absDiff / 60);
    const seconds = absDiff % 60;
    const timeStr = `${minutes}:${seconds.toString().padStart(2, '0')}`;

    if (timer.time_difference > 0) return `+${timeStr} 押し`;
    if (timer.time_difference < 0) return `-${timeStr} 巻き`;
    return '定刻通り';
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`
        p-3 border-b border-gray-200 transition-colors relative
        ${isCurrent ? 'bg-blue-50 border-l-4 border-l-blue-500' : 'hover:bg-gray-50'}
        ${timer.completed_at ? 'opacity-75' : ''}
        ${isDragging ? 'cursor-grabbing' : ''}
      `}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className="flex items-center gap-2">
        {/* ドラッグハンドル（PC版のみ、未完了タイマーのみ、実行中でない） */}
        {!isMobile && !timer.is_completed && !(isCurrent && isRunning) && (
          <div {...attributes} {...listeners} className="cursor-grab text-gray-400 hover:text-gray-600">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path d="M7 2a2 2 0 1 0 0 4 2 2 0 0 0 0-4zM7 7a2 2 0 1 0 0 4 2 2 0 0 0 0-4zM7 12a2 2 0 1 0 0 4 2 2 0 0 0 0-4zM13 2a2 2 0 1 0 0 4 2 2 0 0 0 0-4zM13 7a2 2 0 1 0 0 4 2 2 0 0 0 0-4zM13 12a2 2 0 1 0 0 4 2 2 0 0 0 0-4z" />
            </svg>
          </div>
        )}

        {/* ステータスアイコン */}
        <span className="text-lg">{getStatusIcon()}</span>

        {/* バンド名とメンバー */}
        <div className="flex-1">
          <div
            className={`
              font-medium
              ${timer.completed_at ? 'line-through text-gray-500' : 'text-gray-900'}
              ${isCurrent ? 'font-bold text-blue-700' : ''}
            `}
          >
            {timer.band_name}
          </div>
          <div className="text-xs text-gray-500 mt-0.5">
            {timer.members && timer.members.join('・')}
          </div>
        </div>

        {/* 時間差（完了時のみ） */}
        {timer.completed_at && timer.time_difference !== null && (
          <span className={`text-sm font-medium tabular-nums ${getTimeDifferenceColor()}`}>
            {formatTimeDifference()}
          </span>
        )}

        {/* 編集・削除ボタン（PC版のみ、ホバー時、編集可能な場合のみ） */}
        {!isMobile && isHovered && isEditable && (
          <div className="flex gap-1">
            <button
              onClick={handleEdit}
              className="p-1 text-blue-600 hover:bg-blue-100 rounded transition-colors"
              title="編集"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                />
              </svg>
            </button>
            <button
              onClick={handleDelete}
              className="p-1 text-red-600 hover:bg-red-100 rounded transition-colors"
              title="削除"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                />
              </svg>
            </button>
          </div>
        )}

        {/* 編集不可アイコン（実行中・完了済み） */}
        {!isMobile && !isEditable && (
          <div className="text-gray-400" title="編集・削除不可">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z"
                clipRule="evenodd"
              />
            </svg>
          </div>
        )}
      </div>

      {/* 現在のタイマーの場合は補足情報 */}
      {isCurrent && !timer.completed_at && (
        <div className="mt-1 text-xs text-blue-600 ml-7">実行中</div>
      )}
    </div>
  );
};

export default SortableTimerItem;
