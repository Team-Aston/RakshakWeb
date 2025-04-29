import cv2
import socketio
import numpy as np
from flask import Flask

# Initialize Flask and Socket.IO
app = Flask(__name__)
sio = socketio.Client()

# Connect to the Node.js server
try:
    sio.connect('http://localhost:3000')  # Replace with your Node.js server address
    print("Connected to Node.js server")
except Exception as e:
    print(f"Connection to Node.js server failed: {e}")
    exit(1)

# Load Haar cascade for face detection
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

@sio.on('video_frame')
def process_frame(data):
    try:
        # Decode the received frame
        nparr = np.frombuffer(data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Convert to grayscale for face detection
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect faces
        faces = face_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        # Draw rectangles around detected faces
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # Encode the processed frame to JPEG
        _, buffer = cv2.imencode('.jpg', frame)

        # Send the processed frame back to the Node.js server
        sio.emit('processed_frame', buffer.tobytes())
    except Exception as e:
        print(f"Error processing frame: {e}")

if __name__ == '__main__':
    print("Python face recognition server is running...")
    sio.wait()