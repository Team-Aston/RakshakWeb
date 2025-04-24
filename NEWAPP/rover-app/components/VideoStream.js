export default function VideoStream() {
  return (
    <div className="video-container">
      <img src="http://192.168.0.116:3000/video_feed" alt="Rover Feed" className="video-feed" />
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
      `}</style>
    </div>
  );
}