import { useTimerStore } from '../../stores/timerStore';
import SortableTimerItem from './SortableTimerItem';
import useDeviceDetect from '../../hooks/useDeviceDetect';
import { reorderTimers, deleteAllTimers } from '../../services/api';
import {
  DndContext,
  closestCenter,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import {
  SortableContext,
  verticalListSortingStrategy,
  arrayMove,
} from '@dnd-kit/sortable';

const TimerList = () => {
  const { allTimers, currentTimer, setAllTimers, openTimerForm } = useTimerStore();
  const { isMobile } = useDeviceDetect();

  // Drag & Drop センサー設定
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8, // 8pxドラッグで開始（誤操作防止）
      },
    })
  );

  // ドラッグ終了ハンドラ
  const handleDragEnd = async (event) => {
    const { active, over } = event;

    if (!over || active.id === over.id) {
      return; // 移動なし
    }

    // 楽観的UI更新
    const oldIndex = allTimers.findIndex((t) => t.id === active.id);
    const newIndex = allTimers.findIndex((t) => t.id === over.id);

    if (oldIndex === -1 || newIndex === -1) return;

    const newTimers = arrayMove(allTimers, oldIndex, newIndex);
    setAllTimers(newTimers);

    // API呼び出し（並び替え）
    try {
      const newTimerIds = newTimers.map((t) => t.id);
      await reorderTimers(newTimerIds);
      console.log('タイマーの順序を更新しました');
    } catch (error) {
      console.error('順序変更失敗:', error);
      // エラー時はWebSocketで元の順序が配信される（自動ロールバック）
      alert('順序の変更に失敗しました。');
    }
  };

  // 全タイマー削除ハンドラ
  const handleDeleteAll = async () => {
    const confirmMessage = `全てのタイマー（${allTimers.length}件）を削除してもよろしいですか？\n\nこの操作は取り消せません。`;
    if (!window.confirm(confirmMessage)) {
      return;
    }

    try {
      await deleteAllTimers();
      console.log('全タイマー削除成功');
    } catch (error) {
      console.error('全タイマー削除失敗:', error);
      const errorMessage = error.response?.data?.detail || '全タイマーの削除に失敗しました。';
      alert(errorMessage);
    }
  };

  // 全タイマーが完了しているかチェック
  const allTimersCompleted = allTimers.length > 0 && allTimers.every((t) => t.completed_at);

  if (!allTimers || allTimers.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        {/* ヘッダー */}
        <div className="bg-gray-50 px-4 py-3 border-b border-gray-200 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-700">タイマー一覧</h2>
            <p className="text-xs text-gray-500 mt-1">0 / 0 完了</p>
          </div>
          {!isMobile && (
            <button
              onClick={() => openTimerForm(null)}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm font-medium"
              title="タイマーを追加"
            >
              + 追加
            </button>
          )}
        </div>

        {/* 空状態 */}
        <div className="p-4 text-center text-gray-500">
          タイマーがありません
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      {/* ヘッダー */}
      <div className="bg-gray-50 px-4 py-3 border-b border-gray-200 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-700">タイマー一覧</h2>
          <p className="text-xs text-gray-500 mt-1">
            {allTimers.filter((t) => t.completed_at).length} / {allTimers.length} 完了
          </p>
        </div>
        {!isMobile && (
          <div className="flex gap-2">
            {/* 全タイマー削除ボタン（全完了時のみ表示） */}
            {allTimersCompleted && (
              <button
                onClick={handleDeleteAll}
                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors text-sm font-medium"
                title="全てのタイマーを削除"
              >
                全削除
              </button>
            )}
            {/* タイマー追加ボタン */}
            <button
              onClick={() => openTimerForm(null)}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm font-medium"
              title="タイマーを追加"
            >
              + 追加
            </button>
          </div>
        )}
      </div>

      {/* タイマーリスト */}
      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragEnd={handleDragEnd}
      >
        <SortableContext
          items={allTimers.map((t) => t.id)}
          strategy={verticalListSortingStrategy}
        >
          <div className="max-h-96 overflow-y-auto">
            {allTimers.map((timer) => (
              <SortableTimerItem
                key={timer.id}
                timer={timer}
                isCurrent={currentTimer?.id === timer.id}
                isMobile={isMobile}
              />
            ))}
          </div>
        </SortableContext>
      </DndContext>
    </div>
  );
};

export default TimerList;
