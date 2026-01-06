import { useEffect } from 'react';
import { useTimerStore } from '../stores/timerStore';
import { startTimer, pauseTimer, resumeTimer, skipTimer } from '../services/api';

/**
 * キーボードショートカットフック
 * - スペースキー: タイマー開始/一時停止/再開
 * - 右矢印キー: スキップ
 * - PC版のみ有効（モバイルでは無効）
 */
const useKeyboard = () => {
  const { isRunning, isPaused, currentTimer } = useTimerStore();

  useEffect(() => {
    // モバイルデバイスではキーボードショートカットを無効化
    const isMobile = window.matchMedia('(max-width: 768px)').matches;
    if (isMobile) {
      return;
    }

    const handleKeyDown = async (event) => {
      // 入力フィールドにフォーカスがある場合はショートカットを無効化
      const activeElement = document.activeElement;
      if (
        activeElement.tagName === 'INPUT' ||
        activeElement.tagName === 'TEXTAREA' ||
        activeElement.isContentEditable
      ) {
        return;
      }

      try {
        // スペースキー: 開始/一時停止/再開
        if (event.code === 'Space' || event.key === ' ') {
          event.preventDefault(); // ページスクロールを防ぐ

          if (!isRunning && currentTimer) {
            // タイマー未実行 → 開始
            await startTimer();
          } else if (isRunning && !isPaused) {
            // 実行中 → 一時停止
            await pauseTimer();
          } else if (isPaused) {
            // 一時停止中 → 再開
            await resumeTimer();
          }
        }

        // 右矢印キー: スキップ
        if ((event.code === 'ArrowRight' || event.key === 'ArrowRight') && isRunning) {
          event.preventDefault();

          if (confirm('このタイマーをスキップして次に進みますか？')) {
            await skipTimer();
          }
        }
      } catch (error) {
        console.error('キーボードショートカットエラー:', error);
      }
    };

    window.addEventListener('keydown', handleKeyDown);

    // クリーンアップ
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isRunning, isPaused, currentTimer]);
};

export default useKeyboard;
