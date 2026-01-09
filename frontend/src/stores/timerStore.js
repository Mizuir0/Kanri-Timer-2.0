import { create } from 'zustand';
import { getMembers } from '../services/api';

export const useTimerStore = create((set) => ({
  // タイマー状態
  currentTimer: null,
  remainingSeconds: 0,
  isRunning: false,
  isPaused: false,
  lineNotificationsEnabled: true,

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
    lineNotificationsEnabled: state.line_notifications_enabled ?? true,
    totalTimeDifference: state.total_time_difference || 0,
    totalTimeDifferenceDisplay: state.total_time_difference_display || '',
  }),

  // LINE通知設定
  setLineNotificationsEnabled: (enabled) => set({ lineNotificationsEnabled: enabled }),

  // タイマーリスト更新（MVP Step 2）
  // 注: totalTimeDifference は timer_state_updated イベント（updateTimerState）で更新される
  //     ここで再計算すると、実行中タイマーの一時停止時間が含まれないため不正確になる
  updateTimerList: (timers) => {
    set({ allTimers: timers });
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
