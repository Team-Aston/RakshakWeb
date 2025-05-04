import { useEffect, useState } from 'react';
import io from 'socket.io-client';

export default function LogList() {
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    // Connect to the CORRECT Socket.IO server URL
    const socket = io('http://localhost:3000', { // Changed from 30000 to 3000
      reconnection: true,
    });

    socket.on('connect', () => {
      console.log('LogList connected to Socket.IO server');
    });

    socket.on('log', (data) => {
      console.log('Received log in frontend:', data); // Add console log for debugging
      setLogs((prev) => [
        ...prev,
        {
          message: data.message,
          timestamp: new Date(data.timestamp * 1000).toLocaleString(),
        },
      ].slice(-50)); // Keep only the last 50 logs
    });

    socket.on('disconnect', () => {
      console.log('LogList disconnected from Socket.IO server');
    });

    // Error handling
    socket.on('connect_error', (err) => {
      console.error('LogList connection error:', err);
    });

    return () => {
      socket.disconnect();
    };
  }, []); // Empty dependency array ensures this runs only once on mount

  return (
    <div className="log-container">
      <h2>Logs</h2>
      {logs.length === 0 ? (
        <p>No logs yet</p>
      ) : (
        <ul className="log-list">
          {/* Reverse the logs array for display if you want newest first */}
          {logs.slice().reverse().map((log, index) => (
            <li key={index} className="log-item">
              <span className="timestamp">{log.timestamp}</span>: {log.message}
            </li>
          ))}
        </ul>
      )}
      {/* ... existing styles ... */}
       <style jsx>{`
        .log-container {
          flex: 1;
          background: #f0f0f0;
          padding: 10px;
          border-radius: 8px;
          max-height: 400px; /* Or adjust as needed */
          overflow-y: auto; /* Enable scrolling */
          display: flex; /* Use flexbox for layout */
          flex-direction: column; /* Stack items vertically */
        }
        h2 {
          margin: 0 0 10px;
          font-size: 1.2em;
          flex-shrink: 0; /* Prevent header from shrinking */
        }
        .log-list {
          list-style: none;
          padding: 0;
          margin: 0;
          flex-grow: 1; /* Allow list to take remaining space */
          overflow-y: auto; /* Enable scrolling specifically for the list */
        }
        .log-item {
          padding: 5px 0;
          border-bottom: 1px solid #ddd;
          font-size: 0.9em;
        }
        .log-item:last-child {
          border-bottom: none; /* Remove border from last item */
        }
        .timestamp {
          color: #555;
          margin-right: 10px;
        }
        p {
          text-align: center;
          color: #666;
          margin-top: 20px; /* Add some space if list is empty */
        }
      `}</style>
    </div>
  );
}