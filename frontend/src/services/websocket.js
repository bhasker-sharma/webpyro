/**
 * WebSocket Service
 * Manages WebSocket connection for real-time temperature updates
 */

class WebSocketService {
    constructor() {
        this.ws = null;
        this.reconnectInterval = 3000;
        this.reconnectTimeout = null;
        this.listeners = new Map();
        this.isIntentionallyClosed = false;
    }

    connect(url = 'ws://localhost:8000/api/ws') {
        if (this.ws?.readyState === WebSocket.OPEN) {
            console.log('WebSocket already connected');
            return;
        }

        this.isIntentionallyClosed = false;
        console.log('Connecting to WebSocket:', url);

        try {
            this.ws = new WebSocket(url);

            this.ws.onopen = () => {
                console.log('✅ WebSocket connected');
                this.notifyListeners('connection', { connected: true });
            };

            this.ws.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    console.log('📩 WebSocket message:', message);
                    this.notifyListeners(message.type, message.data);
                } catch (err) {
                    console.error('Error parsing WebSocket message:', err);
                }
            };

            this.ws.onerror = (error) => {
                console.error('❌ WebSocket error:', error);
            };

            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                this.notifyListeners('connection', { connected: false });

                // Auto-reconnect if not intentionally closed
                if (!this.isIntentionallyClosed) {
                    console.log(`Reconnecting in ${this.reconnectInterval}ms...`);
                    this.reconnectTimeout = setTimeout(() => {
                        this.connect(url);
                    }, this.reconnectInterval);
                }
            };
        } catch (err) {
            console.error('Error creating WebSocket:', err);
        }
    }

    disconnect() {
        this.isIntentionallyClosed = true;
        if (this.reconnectTimeout) {
            clearTimeout(this.reconnectTimeout);
        }
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        console.log('WebSocket disconnected intentionally');
    }

    on(eventType, callback) {
        if (!this.listeners.has(eventType)) {
            this.listeners.set(eventType, []);
        }
        this.listeners.get(eventType).push(callback);
    }

    off(eventType, callback) {
        if (!this.listeners.has(eventType)) return;
        const callbacks = this.listeners.get(eventType);
        const index = callbacks.indexOf(callback);
        if (index > -1) {
            callbacks.splice(index, 1);
        }
    }

    notifyListeners(eventType, data) {
        if (!this.listeners.has(eventType)) return;
        this.listeners.get(eventType).forEach(callback => {
            callback(data);
        });
    }
}

// Create singleton instance
export const websocketService = new WebSocketService();
