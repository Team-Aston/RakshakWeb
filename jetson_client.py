import cv2
import socketio
import time

# Initialize Socket.IO client
sio = socketio.Client()

# Connect to the laptop server
try:
    sio.connect('http://localhost:3000')
    print("Connected to server")
except Exception as e:
    print(f"Connection failed: {e}")
    exit(1)

# Initialize video capture (adjust device ID if needed)
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open camera")
    sio.disconnect()
    exit(1)

# Set frame size for consistency
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture frame")
            continue

        # Encode frame to JPEG
        _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])

        # Send frame as binary
        try:
            sio.emit('video_frame', buffer.tobytes())
        except Exception as e:
            print(f"Error sending video_frame: {e}")

        # Control frame rate (~10 FPS)
        time.sleep(0.1)
except KeyboardInterrupt:
    print("Stopping client")
except Exception as e:
    print(f"Error: {e}")
finally:
    cap.release()
    sio.disconnect()