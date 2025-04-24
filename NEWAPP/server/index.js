const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const bodyParser = require('body-parser');
const multer = require('multer');

const app = express();
const server = http.createServer(app);
const io = socketIo(server, {
  cors: {
    origin: 'http://localhost:3001', // Allow Next.js app
    methods: ['GET', 'POST'],
  },
});

app.use(bodyParser.json());
const upload = multer();

// Serve a basic endpoint for testing
app.get('/', (req, res) => {
  res.send('Socket.IO server running');
});

// MJPEG stream endpoint
let latestFrame = null;

app.post('/video_feed', upload.single('frame'), (req, res) => {
  latestFrame = req.file.buffer; // Store the latest frame
  res.sendStatus(200);
});

app.get('/video_feed', (req, res) => {
  res.writeHead(200, {
    'Content-Type': 'multipart/x-mixed-replace; boundary=frame',
  });

  const interval = setInterval(() => {
    if (latestFrame) {
      res.write(`--frame\r\n`);
      res.write(`Content-Type: image/jpeg\r\n\r\n`);
      res.write(latestFrame);
      res.write(`\r\n`);
    }
  }, 1000 / 20); // Adjust frame rate as needed

  req.on('close', () => {
    clearInterval(interval);
  });
});

// Start server
const PORT = 3000;
server.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});