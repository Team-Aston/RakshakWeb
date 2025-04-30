import { useEffect, useState } from 'react';
import io from 'socket.io-client';

export default function VideoStream() {
  const [frame, setFrame] = useState('');

  useEffect(() => {
    // Connect to Socket.IO server (replace <laptop-ip> with actual IP)
    const socket = io('http://localhost:3000', {
      reconnection: true,
    });

    socket.on('connect', () => {
      console.log('Connected to server');
    });

    // Listen for the processed frame event from the server
    socket.on('processed_frame', (data) => {
      const blob = new Blob([data], { type: 'image/jpeg' });
      const url = URL.createObjectURL(blob);
      // Store the previous URL to revoke it after the new one is set
      const previousUrl = frame;
      setFrame(url);

      // Clean up the previous blob URL after a short delay
      // to ensure the new image has rendered
      if (previousUrl) {
        setTimeout(() => URL.revokeObjectURL(previousUrl), 50); // Delay might need adjustment
      }
    });

    socket.on('disconnect', () => {
      console.log('Disconnected from server');
    });

    // Cleanup function
    return () => {
      // Revoke the last frame's URL when the component unmounts
      if (frame) {
        URL.revokeObjectURL(frame);
      }
      socket.disconnect();
    };
  }, [frame]); // Add frame as a dependency to manage URL revocation correctly

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