import { create } from 'zustand';

export const useTimerStore = create((set) => ({
  // タイマー状態
  currentTimer: null,
  remainingSeconds: 0,
  isRunning: false,
  isPaused: false,

  // アクション
  setCurrentTimer: (timer) => set({ currentTimer: timer }),
  setRemainingSeconds: (seconds) => set({ remainingSeconds: seconds }),
  setIsRunning: (isRunning) => set({ isRunning }),
  setIsPaused: (isPaused) => set({ isPaused }),

  // タイマー状態を一括更新
  updateTimerState: (state) => set({
    currentTimer: state.current_timer,
    remainingSeconds: state.remaining_seconds || 0,
    isRunning: state.is_running,
    isPaused: state.is_paused,
  }),
}));
