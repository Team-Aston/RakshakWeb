import { useEffect, useState } from 'react';
import io from 'socket.io-client';

export default function LogList() {
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    const socket = io('http://192.168.0.116:3000', {
      reconnection: true,
    });

    socket.on('log', (data) => {
      setLogs((prev) => [
        ...prev,
        {
          message: data.message,
          timestamp: new Date(data.timestamp * 1000).toLocaleString(),
        },
      ].slice(-50)); // Keep last 50 logs
    });

    return () => {
      socket.disconnect();
    };
  }, []);

  return (
    <div className="log-container">
      <h2>Logs</h2>
      {logs.length === 0 ? (
        <p>No logs yet</p>
      ) : (
        <ul className="log-list">
          {logs.map((log, index) => (
            <li key={index} className="log-item">
              <span className="timestamp">{log.timestamp}</span>: {log.message}
            </li>
          ))}
        </ul>
      )}
      <style jsx>{`
        .log-container {
          flex: 1;
          background: #f0f0f0;
          padding: 10px;
          border-radius: 8px;
          max-height: 400px;
          overflow-y: auto;
        }
        h2 {
          margin: 0 0 10px;
          font-size: 1.2em;
        }
        .log-list {
          list-style: none;
          padding: 0;
          margin: 0;
        }
        .log-item {
          padding: 5px 0;
          border-bottom: 1px solid #ddd;
          font-size: 0.9em;
        }
        .timestamp {
          color: #555;
          margin-right: 10px;
        }
        p {
          text-align: center;
          color: #666;
        }
      `}</style>
    </div>
  );
}
