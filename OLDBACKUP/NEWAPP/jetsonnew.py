import cv2
import time
import requests

# Load face detection model (Haar Cascade Classifier)
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Initialize camera
cap = cv2.VideoCapture(0)  # Using the first camera (you can adjust if needed)
frame_rate = 20  # Desired frame rate
server_url = 'http://192.168.0.116:3000/video_feed'  # Replace with your server's IP and endpoint

try:
    while True:
        # Capture video frame
        ret, frame = cap.read()
        if not ret:
            break

        # Perform face detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)

        # Draw rectangle around faces and add label
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(frame, 'Face Detected', (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

        # Convert frame to JPEG
        ret, jpeg = cv2.imencode('.jpg', frame)
        if not ret:
            break

        # Send frame to the server
        response = requests.post(server_url, files={'frame': ('frame.jpg', jpeg.tobytes(), 'image/jpeg')})
        if response.status_code != 200:
            print("Failed to send frame:", response.status_code)

        # Wait before next frame
        time.sleep(1 / frame_rate)

except KeyboardInterrupt:
    print("Stopping video stream...")

finally:
    cap.release()
    print("Camera released")