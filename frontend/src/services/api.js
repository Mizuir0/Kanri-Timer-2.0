import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// タイマー状態取得
export const getTimerState = async () => {
  const response = await api.get('/api/timers/timer-state/');
  return response.data;
};

// タイマー開始
export const startTimer = async (timerId = null) => {
  const response = await api.post('/api/timers/timer-state/start/', {
    timer_id: timerId,
  });
  return response.data;
};

// タイマー一覧取得
export const getTimers = async () => {
  const response = await api.get('/api/timers/');
  return response.data;
};

// タイマー一時停止
export const pauseTimer = async () => {
  const response = await api.post('/api/timers/timer-state/pause/');
  return response.data;
};

// タイマー再開
export const resumeTimer = async () => {
  const response = await api.post('/api/timers/timer-state/resume/');
  return response.data;
};

// タイマースキップ
export const skipTimer = async () => {
  const response = await api.post('/api/timers/timer-state/skip/');
  return response.data;
};

// ============================================================================
// CRUD Operations (MVP Step 3)
// ============================================================================

// メンバー一覧取得
export const getMembers = async () => {
  const response = await api.get('/api/members/');
  return response.data;
};

// タイマー作成
export const createTimer = async (timerData) => {
  const response = await api.post('/api/timers/create/', timerData);
  return response.data;
};

// タイマー更新
export const updateTimer = async (timerId, timerData) => {
  const response = await api.put(`/api/timers/${timerId}/`, timerData);
  return response.data;
};

// タイマー削除
export const deleteTimer = async (timerId) => {
  const response = await api.delete(`/api/timers/${timerId}/delete/`);
  return response.data;
};

// タイマー順序変更
export const reorderTimers = async (timerIds) => {
  const response = await api.post('/api/timers/reorder/', { timer_ids: timerIds });
  return response.data;
};

// 全タイマー削除（全完了時のみ）
export const deleteAllTimers = async () => {
  const response = await api.post('/api/timers/delete-all/');
  return response.data;
};

export default api;
