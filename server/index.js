const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const { spawn } = require('child_process');

const app = express();
const server = http.createServer(app);
const io = socketIo(server, {
  cors: {
    origin: 'http://localhost:3001',
    methods: ['GET', 'POST'],
  },
});

// Start the Python face recognition script
const pythonProcess = spawn('python', ['face_recognition_server.py']);
pythonProcess.stdout.on('data', (data) => {
  console.log(`Python: ${data}`);
});
pythonProcess.stderr.on('data', (data) => {
  console.error(`Python Error: ${data}`);
});

io.on('connection', (socket) => {
  console.log('Client connected:', socket.id);

  // Forward video frames from clients to the Python script
  socket.on('video_frame', (data) => {
    io.emit('video_frame', data); // Forward to Python script
  });

  // Forward processed frames from Python to clients
  socket.on('processed_frame', (data) => {
    socket.broadcast.emit('video_frame', data);
  });

  socket.on('disconnect', () => {
    console.log('Client disconnected:', socket.id);
  });
});

const PORT = 3000;
server.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});