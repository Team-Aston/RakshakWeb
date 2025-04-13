import { useEffect, useState } from 'react';
import io from 'socket.io-client';

export default function VideoStream() {
  const [frame, setFrame] = useState('');

  useEffect(() => {
    // Connect to Socket.IO server (replace <laptop-ip> with actual IP)
    const socket = io('192.168.46.1:3000', {
      reconnection: true,
    });

    socket.on('connect', () => {
      console.log('Connected to server');
    });

    socket.on('video_frame', (data) => {
      const blob = new Blob([data], { type: 'image/jpeg' });
      const url = URL.createObjectURL(blob);
      setFrame(url);
      return () => URL.revokeObjectURL(url);
    });

    socket.on('disconnect', () => {
      console.log('Disconnected from server');
    });

    return () => {
      socket.disconnect();
    };
  }, []);

  return (
    <div className="video-container">
      {frame ? (
        <img src={frame} alt="Rover Feed" className="video-feed" />
      ) : (
        <p>Loading video feed...</p>
      )}
      <style jsx>{`
        .video-container {
          flex: 2;
          background: #f0f0f0;
          padding: 10px;
          border-radius: 8px;
        }
        .video-feed {
          width: 100%;
          max-width: 640px;
          height: auto;
          border-radius: 4px;
        }
        p {
          text-align: center;
          color: #666;
        }
      `}</style>
    </div>
  );
}