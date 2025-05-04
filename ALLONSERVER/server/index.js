// filepath: e:\KMIT\Projects\Prakalp\WebApp\ALLONSERVER\server\index.js
const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const { spawn } = require('child_process');

const app = express();
const server = http.createServer(app);
const io = socketIo(server, {
  cors: {
    origin: 'http://localhost:3001', // Ensure this matches your React app's URL
    methods: ['GET', 'POST'],
  },
});

// Start the Python face recognition script
// Make sure the python command activates conda env if needed
// Example: const pythonCommand = 'conda activate dlib && python face_recognition_server.py';
// const pythonProcess = spawn('cmd.exe', ['/c', pythonCommand], { shell: true });
const pythonProcess = spawn('python', ['face_recognition_server.py']); // Use this if conda activation isn't needed or handled elsewhere

pythonProcess.stdout.on('data', (data) => {
  console.log(`Python stdout: ${data}`); // Log stdout for debugging
});
pythonProcess.stderr.on('data', (data) => {
  console.error(`Python stderr: ${data}`); // Log stderr for debugging
});
pythonProcess.on('close', (code) => {
  console.log(`Python process exited with code ${code}`);
});


io.on('connection', (socket) => {
  console.log('Client connected:', socket.id);

  // Listen for 'log' events from ANY client (including the Python script)
  socket.on('log', (logData) => {
    console.log(`Received log: ${logData.message}`);
    // Broadcast the log to ALL OTHER connected clients (the web UIs)
    socket.broadcast.emit('log', logData);
  });

  // Forward video frames (assuming Python listens for this)
  socket.on('video_frame', (data) => {
    io.emit('video_frame', data); // Broadcast to all clients
  });

  // Forward processed frames from Python script back to the web clients
  socket.on('processed_frame', (data) => {
    socket.broadcast.emit('processed_frame', data);
  });

  // Forward recognized names from Python script back to the web clients
  socket.on('face_recognized', (data) => {
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