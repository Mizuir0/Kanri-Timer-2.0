import { create } from 'zustand';
import { getMembers } from '../services/api';

export const useTimerStore = create((set) => ({
  // タイマー状態
  currentTimer: null,
  remainingSeconds: 0,
  isRunning: false,
  isPaused: false,

  // タイマーリスト（MVP Step 2）
  allTimers: [],
  totalTimeDifference: 0,
  totalTimeDifferenceDisplay: '',

  // CRUD状態（MVP Step 3）
  isTimerFormOpen: false,
  editingTimer: null,
  members: [],

  // アクション
  setCurrentTimer: (timer) => set({ currentTimer: timer }),
  setRemainingSeconds: (seconds) => set({ remainingSeconds: seconds }),
  setIsRunning: (isRunning) => set({ isRunning }),
  setIsPaused: (isPaused) => set({ isPaused }),

  // タイマーリスト更新（MVP Step 2）
  setAllTimers: (timers) => set({ allTimers: timers }),
  setTotalTimeDifference: (diff) => set({ totalTimeDifference: diff }),
  setTotalTimeDifferenceDisplay: (display) => set({ totalTimeDifferenceDisplay: display }),

  // タイマー状態を一括更新
  updateTimerState: (state) => set({
    currentTimer: state.current_timer,
    remainingSeconds: state.remaining_seconds || 0,
    isRunning: state.is_running,
    isPaused: state.is_paused,
  }),

  // タイマーリストと押し巻き計算を一括更新（MVP Step 2）
  updateTimerList: (timers) => {
    // 全体の時間差を計算
    const totalDiff = timers.reduce((sum, timer) => {
      return sum + (timer.time_difference || 0);
    }, 0);

    // 表示用文字列を生成
    let displayText = '';
    if (totalDiff === 0) {
      displayText = '定刻通り';
    } else {
      const absDiff = Math.abs(totalDiff);
      const minutes = Math.floor(absDiff / 60);
      const seconds = absDiff % 60;
      const timeStr = `${minutes}:${seconds.toString().padStart(2, '0')}`;

      if (totalDiff > 0) {
        displayText = `+${timeStr} 押し`;
      } else {
        displayText = `-${timeStr} 巻き`;
      }
    }

    set({
      allTimers: timers,
      totalTimeDifference: totalDiff,
      totalTimeDifferenceDisplay: displayText,
    });
  },

  // CRUD アクション（MVP Step 3）
  openTimerForm: (timer = null) => set({ isTimerFormOpen: true, editingTimer: timer }),
  closeTimerForm: () => set({ isTimerFormOpen: false, editingTimer: null }),
  setMembers: (members) => set({ members }),

  fetchMembers: async () => {
    try {
      const members = await getMembers();
      set({ members });
    } catch (error) {
      console.error('Failed to fetch members:', error);
    }
  },
}));
