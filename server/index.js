const express = require('express');
const http = require('http');
const socketIo = require('socket.io');

const app = express();
const server = http.createServer(app);
const io = socketIo(server, {
  cors: {
    origin: 'http://localhost:3001', // Allow Next.js app
    methods: ['GET', 'POST'],
  },
});

// Serve a basic endpoint for testing
app.get('/', (req, res) => {
  res.send('Socket.IO server running');
});

// Handle Socket.IO connections
io.on('connection', (socket) => {
  console.log('Client connected:', socket.id);

  // Receive and broadcast video frames
  socket.on('video_frame', (data) => {
    socket.broadcast.emit('video_frame', data);
  });

  // Receive and broadcast logs
  socket.on('log', (data) => {
    socket.broadcast.emit('log', data);
  });

  socket.on('disconnect', () => {
    console.log('Client disconnected:', socket.id);
  });
});

// Start server
const PORT = 3000;
server.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});