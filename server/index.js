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

  // Forward video frames from web clients to the Python script
  socket.on('video_frame', (data) => {
    // Emit specifically to the Python script if possible, or broadcast if simpler
    // Broadcasting is okay if only Python listens for this raw frame event
    io.emit('video_frame', data); // Forward to Python script
  });

  // Forward processed frames from Python script back to the web clients
  socket.on('processed_frame', (data) => {
    // Broadcast the processed frame to all *other* clients (the web UIs)
    // Use the correct event name that the frontend expects (e.g., 'processed_frame')
    socket.broadcast.emit('processed_frame', data);
  });

  // Forward recognized names from Python script back to the web clients
  socket.on('face_recognized', (data) => {
    // Broadcast the names to all *other* clients (the web UIs)
    socket.broadcast.emit('face_recognized', data);
  });


  socket.on('disconnect', () => {
    console.log('Client disconnected:', socket.id);
  });
});

const PORT = 3000;
server.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});