import Head from 'next/head';
import VideoStream from '../components/VideoStream';
import LogList from '../components/LogList';

export default function Home() {
  return (
    <div className="container">
      <Head>
        <title>Rover Monitoring</title>
        <meta name="description" content="Rover video stream and logs" />
      </Head>
      <h1>Rover Monitoring</h1>
      <div className="content">
        <VideoStream />
        <LogList />
      </div>
      <style jsx>{`
        .container {
          max-width: 1200px;
          margin: 0 auto;
          padding: 20px;
        }
        h1 {
          text-align: center;
          margin-bottom: 20px;
        }
        .content {
          display: flex;
          gap: 20px;
        }
        @media (max-width: 768px) {
          .content {
            flex-direction: column;
          }
        }
      `}</style>
    </div>
  );
}