class WebSocketService {
  constructor() {
    this.ws = null;
    this.url = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/timer/';
    this.reconnectInterval = 3000; // 3秒
    this.reconnectTimer = null;
    this.listeners = {
      timer_state_updated: [],
      timer_list_updated: [],
      connection_established: [],
      connection_lost: [],
    };
    this.isIntentionallyClosed = false;
  }

  connect() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      console.log('[WebSocket] 既に接続されています');
      return;
    }

    console.log('[WebSocket] 接続開始:', this.url);
    this.isIntentionallyClosed = false;
    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => {
      console.log('[WebSocket] 接続成功');
      this.clearReconnectTimer();
    };

    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        console.log('[WebSocket] メッセージ受信:', message.type);
        this.handleMessage(message);
      } catch (error) {
        console.error('[WebSocket] メッセージ解析エラー:', error);
      }
    };

    this.ws.onerror = (error) => {
      console.error('[WebSocket] エラー:', error);
    };

    this.ws.onclose = (event) => {
      console.log('[WebSocket] 接続終了:', event.code, event.reason);
      this.notifyListeners('connection_lost', null);

      // 意図的な切断でなければ再接続
      if (!this.isIntentionallyClosed) {
        this.scheduleReconnect();
      }
    };
  }

  disconnect() {
    console.log('[WebSocket] 切断処理開始');
    this.isIntentionallyClosed = true;
    this.clearReconnectTimer();

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  scheduleReconnect() {
    this.clearReconnectTimer();
    console.log(`[WebSocket] ${this.reconnectInterval}ms後に再接続を試みます`);
    this.reconnectTimer = setTimeout(() => {
      console.log('[WebSocket] 再接続を試みます...');
      this.connect();
    }, this.reconnectInterval);
  }

  clearReconnectTimer() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  handleMessage(message) {
    const { type, data } = message;
    this.notifyListeners(type, data);
  }

  on(eventType, callback) {
    if (this.listeners[eventType]) {
      this.listeners[eventType].push(callback);
    }
  }

  off(eventType, callback) {
    if (this.listeners[eventType]) {
      this.listeners[eventType] = this.listeners[eventType].filter(
        (cb) => cb !== callback
      );
    }
  }

  notifyListeners(eventType, data) {
    if (this.listeners[eventType]) {
      this.listeners[eventType].forEach((callback) => {
        callback(data);
      });
    }
  }
}

// Singleton instance
const websocketService = new WebSocketService();

export default websocketService;
