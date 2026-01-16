import { useEffect, useRef, useState, useCallback } from 'react';

interface WebSocketMessage {
  type: string;
  data?: any;
  [key: string]: any;
}

export const useWebSocket = (url: string) => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [messageQueue, setMessageQueue] = useState<WebSocketMessage[]>([]);
  const ws = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;
  const reconnectDelay = useRef(1000);

  const connect = useCallback(() => {
    try {
      ws.current = new WebSocket(url);

      ws.current.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        reconnectAttempts.current = 0;
        reconnectDelay.current = 1000;
      };

      ws.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          setLastMessage(message);
          setMessageQueue((prev) => [...prev, message].slice(-100)); // Keep last 100 messages
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e);
        }
      };

      ws.current.onerror = (event) => {
        console.error('WebSocket error:', event);
        setIsConnected(false);
      };

      ws.current.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);

        // Attempt to reconnect with persistent retry
        if (reconnectAttempts.current < maxReconnectAttempts) {
          reconnectAttempts.current += 1;
          console.log(`Reconnecting... Attempt ${reconnectAttempts.current}/${maxReconnectAttempts}`);
          setTimeout(() => {
            connect();
          }, reconnectDelay.current);
          reconnectDelay.current = Math.min(reconnectDelay.current * 2, 10000);
        } else {
          // After max attempts, retry periodically every 30 seconds
          console.log('Max reconnection attempts reached. Retrying in 30 seconds...');
          setTimeout(() => {
            reconnectAttempts.current = 0;
            reconnectDelay.current = 1000;
            connect();
          }, 30000);
        }
      };
    } catch (e) {
      console.error('Failed to create WebSocket:', e);
    }
  }, [url]);

  const send = useCallback((message: WebSocketMessage) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected');
    }
  }, []);

  const disconnect = useCallback(() => {
    if (ws.current) {
      ws.current.close();
    }
  }, []);

  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    lastMessage,
    messageQueue,
    send,
    disconnect,
  };
};

export default useWebSocket;
