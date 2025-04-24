import cv2
import time
import requests
import face_recognition
import numpy as np
import os

# Paths for storing encoded faces
encoding_file = "face_encodings.npy"
names_file = "face_names.npy"
faces_folder = "faces"  # Folder containing subfolders with person names

# Variables to hold encodings
known_face_encodings = []
known_face_names = []

def save_encodings():
    """Saves face encodings and names."""
    np.save(encoding_file, np.array(known_face_encodings, dtype=object))
    np.save(names_file, np.array(known_face_names, dtype=object))
    print("💾 Encodings saved!")

def load_encodings():
    """Loads encodings if the file exists."""
    global known_face_encodings, known_face_names
    if os.path.exists(encoding_file) and os.path.exists(names_file):
        known_face_encodings = np.load(encoding_file, allow_pickle=True).tolist()
        known_face_names = np.load(names_file, allow_pickle=True).tolist()
        return True
    return False

# Load from file if available
if load_encodings():
    print(f"✅ Loaded {len(known_face_encodings)} known faces from cache.")
else:
    print("🔍 Loading known faces...")
    for person_name in os.listdir(faces_folder):
        person_folder = os.path.join(faces_folder, person_name)
        if os.path.isdir(person_folder):
            for filename in os.listdir(person_folder):
                if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    img_path = os.path.join(person_folder, filename)
                    image = face_recognition.load_image_file(img_path)

                    encodings = face_recognition.face_encodings(image)
                    if encodings:
                        known_face_encodings.append(encodings[0])
                        known_face_names.append(person_name)
                        print(f"✅ Loaded: {filename} for {person_name}")
                    else:
                        print(f"❌ Warning: No face found in {filename}, skipping...")

    if known_face_encodings:
        save_encodings()
    else:
        raise ValueError("❌ No faces found. Ensure images contain clear faces.")

print(f"🎉 Ready! Found {len(known_face_encodings)} known face(s).")

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

        # Resize frame for faster processing
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = small_frame[:, :, ::-1]  # Convert BGR to RGB

        # Perform face recognition
        face_locations = face_recognition.face_locations(rgb_small_frame, model="hog")
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            # Scale back up face locations since the frame was resized
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            # Check if the face is a match for known faces
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.4)
            name = "Intruder"

            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)

            if matches[best_match_index] and face_distances[best_match_index] < 0.4:
                name = known_face_names[best_match_index]

                # Draw a green rectangle for known faces
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            else:
                # Draw a red rectangle for unknown faces
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                cv2.putText(frame, "Intruder Detected", (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

                # Send a log for unknown faces
                log_data = {
                    "message": "Intruder detected",
                    "timestamp": int(time.time())
                }
                try:
                    requests.post(f"{server_url}/log", json=log_data)
                except Exception as e:
                    print("Failed to send log:", e)

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