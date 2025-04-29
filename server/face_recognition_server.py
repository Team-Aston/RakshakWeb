import sys # Add sys import
import cv2
import socketio
import numpy as np
from flask import Flask
import face_recognition # Import face_recognition library
import os # Added os import

# Print Python path and library location for debugging
print("--- Debug Info ---")
print(f"Python executable: {sys.executable}")
print("sys.path:")
for p in sys.path:
    print(f"  - {p}")
print(f"face_recognition location: {face_recognition.__file__}")
print("------------------")


# Initialize Flask and Socket.IO
app = Flask(__name__)
sio = socketio.Client()

# Paths for storing encoded faces - Adjust as needed
encoding_file = "face_encodings.npy"
names_file = "face_names.npy"
# IMPORTANT: Update this path to your actual image folder
people_images_folder = "/home/tanishq/Desktop/my_images" # <--- UPDATE THIS PATH

# Variables to hold encodings
known_face_encodings = []
known_face_names = []

def save_encodings():
    """Saves face encodings and names."""
    try:
        np.save(encoding_file, np.array(known_face_encodings, dtype=object))
        np.save(names_file, np.array(known_face_names, dtype=object))
        print("💾 Encodings saved!")
    except Exception as e:
        print(f"Error saving encodings: {e}")

def load_encodings():
    """Loads encodings if the file exists."""
    global known_face_encodings, known_face_names
    if os.path.exists(encoding_file) and os.path.exists(names_file):
        try:
            known_face_encodings = np.load(encoding_file, allow_pickle=True).tolist()
            known_face_names = np.load(names_file, allow_pickle=True).tolist()
            # Basic validation
            if isinstance(known_face_encodings, list) and isinstance(known_face_names, list) and len(known_face_encodings) == len(known_face_names):
                 return True
            else:
                print("⚠️ Encoding files seem corrupted. Regenerating...")
                return False
        except Exception as e:
            print(f"Error loading encodings: {e}. Regenerating...")
            return False
    return False

# --- Load or Generate Encodings ---
if load_encodings():
    print(f"✅ Loaded {len(known_face_encodings)} known faces from cache.")
else:
    print("🔍 Loading known faces from images...")
    if not os.path.isdir(people_images_folder):
         print(f"❌ Error: Image folder not found at {people_images_folder}. Please create it and add images.")
         # Optionally exit or handle this case differently
         # exit(1) # Or raise an error
    else:
        for person_name in os.listdir(people_images_folder):
            person_folder = os.path.join(people_images_folder, person_name)
            if os.path.isdir(person_folder):
                for filename in os.listdir(person_folder):
                    if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                        img_path = os.path.join(person_folder, filename)
                        try:
                            print(f"Processing {img_path} for {person_name}...")
                            image = face_recognition.load_image_file(img_path)
                            encodings = face_recognition.face_encodings(image)
                            if encodings:
                                known_face_encodings.append(encodings[0])
                                known_face_names.append(person_name)
                                print(f"✅ Encoded: {filename} for {person_name}")
                            else:
                                print(f"⚠️ Warning: No face found in {filename}, skipping...")
                        except Exception as e:
                            print(f"❌ Error processing {filename}: {e}")

        if known_face_encodings:
            save_encodings()
        else:
            print("❌ Warning: No faces found or encoded. Face recognition will only detect 'Unknown'.")
            # Consider if the server should run without known faces
            # raise ValueError("No faces found. Ensure images contain clear faces.")

print(f"🎉 Ready! Using {len(known_face_encodings)} known face(s).")

# Add dictionaries for smoothing
smoothed_boxes = {}
frame_history = {}
max_history = 5  # Number of frames to average over
smoothing_factor = 0.8 # Smoothing factor (higher = smoother, but more lag)

# Connect to the Node.js server
try:
    sio.connect('http://localhost:3000')  # Replace with your Node.js server address
    print("Connected to Node.js server")
except Exception as e:
    print(f"Connection to Node.js server failed: {e}")
    exit(1)

@sio.on('video_frame')
def process_frame(data):
    global known_face_encodings, known_face_names, smoothed_boxes, frame_history # Ensure access to global lists and smoothing dicts

    try:
        # Decode the received frame
        nparr = np.frombuffer(data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if frame is None:
            print("Warning: Failed to decode frame.")
            return

        # Resize frame for faster processing (adjust fx/fy as needed)
        # Using 0.5 for a balance, CNN might handle smaller sizes better if GPU is available
        small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        # Find all the faces and face encodings in the current frame of video
        # Switch to CNN model if GPU is available and dlib is compiled with CUDA
        face_locations = face_recognition.face_locations(rgb_frame, model="cnn") # Using cnn model
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        recognized_names = [] # Store names found in this frame

        # Draw rectangles and names around detected faces
        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            name = "Unknown" # Default name

            # Check if there are known faces to compare against
            if known_face_encodings:
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.5)
                face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)

                if len(face_distances) > 0: # Ensure distances were calculated
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index] and face_distances[best_match_index] < 0.5: # Check distance threshold
                        name = known_face_names[best_match_index]

            recognized_names.append(name)

            # --- Bounding Box Smoothing Logic --- 
            # Add current bounding box to frame history
            if name not in frame_history:
                frame_history[name] = []
            frame_history[name].append([top, right, bottom, left])
            if len(frame_history[name]) > max_history:
                frame_history[name].pop(0)

            # Calculate the average bounding box over the last few frames
            avg_top = int(sum(box[0] for box in frame_history[name]) / len(frame_history[name]))
            avg_right = int(sum(box[1] for box in frame_history[name]) / len(frame_history[name]))
            avg_bottom = int(sum(box[2] for box in frame_history[name]) / len(frame_history[name]))
            avg_left = int(sum(box[3] for box in frame_history[name]) / len(frame_history[name]))

            # Apply exponential moving average smoothing
            if name not in smoothed_boxes:
                smoothed_boxes[name] = [avg_top, avg_right, avg_bottom, avg_left]
            else:
                smoothed_boxes[name][0] = int(smoothing_factor * smoothed_boxes[name][0] + (1 - smoothing_factor) * avg_top)
                smoothed_boxes[name][1] = int(smoothing_factor * smoothed_boxes[name][1] + (1 - smoothing_factor) * avg_right)
                smoothed_boxes[name][2] = int(smoothing_factor * smoothed_boxes[name][2] + (1 - smoothing_factor) * avg_bottom)
                smoothed_boxes[name][3] = int(smoothing_factor * smoothed_boxes[name][3] + (1 - smoothing_factor) * avg_left)

            smoothed_top, smoothed_right, smoothed_bottom, smoothed_left = smoothed_boxes[name]
            # --- End Smoothing Logic ---

            # Scale back up face locations since frame was scaled down (adjust factor based on fx/fy)
            scale_factor = 2 # Since fx=0.5, fy=0.5
            draw_top = smoothed_top * scale_factor
            draw_right = smoothed_right * scale_factor
            draw_bottom = smoothed_bottom * scale_factor
            draw_left = smoothed_left * scale_factor

            # Draw a box around the face using smoothed coordinates
            color = (0, 255, 0) if name != "Unknown" else (0, 0, 255) # Green if known, Red if unknown
            cv2.rectangle(frame, (draw_left, draw_top), (draw_right, draw_bottom), color, 2)

            # Draw a label with a name below the face
            cv2.rectangle(frame, (draw_left, draw_bottom - 25), (draw_right, draw_bottom), color, cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame, name, (draw_left + 6, draw_bottom - 6), font, 0.8, (255, 255, 255), 1)

        # Emit recognized names (only if any faces were detected)
        if recognized_names:
            # You might want to emit only unique names or handle multiple detections differently
            # For now, emitting all detected names (including "Unknown")
            sio.emit('face_recognized', {'names': recognized_names})
            print(f"Recognized: {recognized_names}") # Log recognized names


        # Encode the processed frame to JPEG
        _, buffer = cv2.imencode('.jpg', frame)

        # Send the processed frame back to the Node.js server
        sio.emit('processed_frame', buffer.tobytes())
    except Exception as e:
        print(f"Error processing frame: {e}")

if __name__ == '__main__':
    print("Python face recognition server is running...")
    sio.wait()