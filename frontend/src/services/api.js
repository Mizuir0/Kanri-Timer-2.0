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

// Step 2以降で追加
// export const pauseTimer = async () => { ... };
// export const resumeTimer = async () => { ... };
// export const skipTimer = async () => { ... };

export default api;
