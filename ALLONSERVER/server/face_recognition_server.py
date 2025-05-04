import sys  # Add sys import
import cv2
import socketio
import numpy as np
from flask import Flask
import face_recognition  # Import face_recognition library
import os  # Added os import
import time  # Import time for potential delays

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
sio = socketio.Client(reconnection_delay=1, reconnection_delay_max=10)


# Paths for storing encoded faces - Adjust as needed
encoding_file = "face_encodings.npy"
names_file = "face_names.npy"
# IMPORTANT: Update this path to your actual image folder
people_images_folder = "/media/shoaib/STUDYLINUX/Prakalp/RakshakWeb/my_images"  # <--- Using path from workspace structure

# Variables to hold encodings
known_face_encodings = []
known_face_names = []

# --- State variables for logging ---
last_recognized_names_set = set()
last_unknown_detected = False
# --- End State variables ---


def save_encodings():
    """Saves face encodings and names."""
    try:
        np.save(encoding_file, np.array(known_face_encodings, dtype=object))
        np.save(names_file, np.array(known_face_names, dtype=object))
        print("Encodings saved!")
    except Exception as e:
        print(f"Error saving encodings: {e}")


def load_encodings():
    """Loads encodings if the file exists."""
    global known_face_encodings, known_face_names
    encoding_path = os.path.join(os.path.dirname(__file__), encoding_file)  # Look in script's directory
    names_path = os.path.join(os.path.dirname(__file__), names_file)  # Look in script's directory

    if os.path.exists(encoding_path) and os.path.exists(names_path):
        try:
            known_face_encodings = np.load(encoding_path, allow_pickle=True).tolist()
            known_face_names = np.load(names_path, allow_pickle=True).tolist()
            # Basic validation
            if isinstance(known_face_encodings, list) and isinstance(known_face_names, list) and len(known_face_encodings) == len(known_face_names):
                return True
            else:
                print("Encoding files seem corrupted. Regenerating...")
                return False
        except Exception as e:
            print(f"Error loading encodings: {e}. Regenerating...")
            return False
    return False


# --- Load or Generate Encodings ---
if load_encodings():
    print(f"Loaded {len(known_face_encodings)} known faces from cache.")
else:
    print("Loading known faces from images...")
    # Use absolute path based on workspace root provided
    absolute_people_images_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'my_images'))  # Go up one level from server/
    print(f"Looking for images in: {absolute_people_images_folder}")

    if not os.path.isdir(absolute_people_images_folder):
        print(f"Error: Image folder not found at {absolute_people_images_folder}. Please create it and add images relative to the project root.")
    else:
        for person_name in os.listdir(absolute_people_images_folder):
            person_folder = os.path.join(absolute_people_images_folder, person_name)
            if os.path.isdir(person_folder):
                for filename in os.listdir(person_folder):
                    if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                        img_path = os.path.join(person_folder, filename)
                        try:
                            print(f"Processing {img_path} for {person_name}...")
                            image = face_recognition.load_image_file(img_path)
                            # Use CNN model for encoding generation for better accuracy if possible, fallback to hog
                            encodings = face_recognition.face_encodings(image, model="cnn")
                            if not encodings:
                                print(f"Trying HOG model for {filename}...")
                                encodings = face_recognition.face_encodings(image, model="hog")

                            if encodings:
                                known_face_encodings.append(encodings[0])
                                known_face_names.append(person_name)
                                print(f"Encoded: {filename} for {person_name}")
                            else:
                                print(f"Warning: No face found in {filename} using either model, skipping...")
                        except Exception as e:
                            print(f"Error processing {filename}: {e}")

        if known_face_encodings:
            save_encodings()  # Save in script's directory
        else:
            print("Warning: No faces found or encoded. Face recognition will only detect 'Unknown'.")

print(f"Ready! Using {len(known_face_encodings)} known face(s).\n")

# --- Logging Function ---
def emit_log(message):
    """Emit a log message to the Node.js server."""
    log_data = {'message': message, 'timestamp': time.time()}
    if sio.connected and '/' in sio.namespaces:
        try:
            sio.emit('log', log_data)
            # Also print to Python console for debugging
            print(f"Log Emitted: {message}")
        except Exception as e:
            print(f"Error emitting log via Socket.IO: {e}")
    else:
        # Print to console even if not connected
        print(f"Log (Not Emitted - Socket Disconnected): {message}")

# --- Parameters ---
# Recognition tolerance (lower = stricter matching) - Adjusting for stability
recognition_tolerance = 0.5  # Increased from 0.4
# Face detection model ('hog' is faster, 'cnn' is slower but more accurate)
detection_model = "hog"
# Frame resize factor for processing (1.0 = original size)
resize_factor = 1.0  # Ensure this is 1.0 to avoid scaling issues

# --- Socket.IO Event Handlers ---
@sio.event
def connect():
    print("Connection established with server")


@sio.event
def connect_error(data):
    print(f"Connection failed: {data}")


@sio.event
def disconnect():
    print("Disconnected from server")


# --- Connect to the Node.js server ---
NODE_SERVER_URL = 'http://localhost:3000'  # Make sure this matches your Node.js server
print(f"Attempting to connect to Node.js server at {NODE_SERVER_URL}...")
try:
    sio.connect(NODE_SERVER_URL, wait_timeout=10)
except socketio.exceptions.ConnectionError as e:
    print(f"Connection to Node.js server failed: {e}")
    exit(1)


@sio.on('video_frame')
def process_frame(data):
    global known_face_encodings, known_face_names
    # --- Add global state variables ---
    global last_recognized_names_set, last_unknown_detected
    # --- End Add global state variables ---

    if not sio.connected or '/' not in sio.namespaces:
        print("Warning: process_frame called but not connected to namespace '/'. Skipping.")
        return

    try:
        nparr = np.frombuffer(data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if frame is None:
            print("Warning: Failed to decode frame.")
            return

        # --- Face Detection and Recognition ---

        # Resize frame if needed for performance (optional)
        if resize_factor != 1.0:
            small_frame = cv2.resize(frame, (0, 0), fx=resize_factor, fy=resize_factor)
            rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)  # Convert BGR to RGB
        else:
            # Process original frame directly
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Convert BGR to RGB

        # Find face locations and encodings
        face_locations = face_recognition.face_locations(rgb_frame, model=detection_model)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        # --- Track current frame's detections ---
        current_recognized_names = []
        unknown_detected_current = False
        # --- End Track current frame's detections ---

        # Loop through each face found in the frame
        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            name = "Unknown Person"  # Default name

            # Compare against known faces
            if known_face_encodings:
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=recognition_tolerance)
                face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)

                if len(face_distances) > 0:
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index] and face_distances[best_match_index] < recognition_tolerance:
                        name = known_face_names[best_match_index]

            # --- Store name or mark unknown ---
            if name != "Unknown Person":
                current_recognized_names.append(name)
            else:
                unknown_detected_current = True
            # --- End Store name or mark unknown ---

            # Scale coordinates back up if frame was resized
            if resize_factor != 1.0:
                scale_factor = 1 / resize_factor
                draw_top = int(top * scale_factor)
                draw_right = int(right * scale_factor)
                draw_bottom = int(bottom * scale_factor)
                draw_left = int(left * scale_factor)
            else:
                # Use coordinates directly if no resize
                draw_top, draw_right, draw_bottom, draw_left = top, right, bottom, left

            # Draw rectangle
            color = (0, 255, 0) if name != "Unknown Person" else (0, 0, 255)
            cv2.rectangle(frame, (draw_left, draw_top), (draw_right, draw_bottom), color, 2)

            # Draw text label
            cv2.putText(frame, name, (draw_left, draw_bottom + 25), cv2.FONT_HERSHEY_DUPLEX, 0.6, color, 1)

        # --- Process Logs Based on State Change ---
        current_recognized_names_set = set(current_recognized_names)

        # Newly recognized faces
        newly_recognized = current_recognized_names_set - last_recognized_names_set
        for name in newly_recognized:
            emit_log(f"Recognized {name}")

        # Faces no longer recognized
        lost_recognition = last_recognized_names_set - current_recognized_names_set
        for name in lost_recognition:
            emit_log(f"Lost sight of {name}")

        # Unknown face status change
        if unknown_detected_current and not last_unknown_detected:
            emit_log("Unrecognized face detected")
        elif not unknown_detected_current and last_unknown_detected:
            emit_log("Unrecognized face(s) no longer detected")

        # Update state for the next frame
        last_recognized_names_set = current_recognized_names_set
        last_unknown_detected = unknown_detected_current
        # --- End Process Logs Based on State Change ---

        # --- Emit results ---
        try:
            # Emit recognized names if any were found (this can still be useful for UI)
            if current_recognized_names:  # Send only recognized, not 'Unknown'
                unique_names = list(current_recognized_names_set)  # Use the set for unique names
                if sio.connected and '/' in sio.namespaces:
                    sio.emit('face_recognized', {'names': unique_names})

            # Encode the frame with drawings
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
            _, buffer = cv2.imencode('.jpg', frame, encode_param)

            # Emit the processed frame
            if sio.connected and '/' in sio.namespaces:
                sio.emit('processed_frame', buffer.tobytes())

        except socketio.exceptions.BadNamespaceError as bne:
            print(f"SocketIO Error during emit: {bne}. Namespace likely disconnected.")
        except Exception as emit_err:
            print(f"Error during emit: {emit_err}")

    except Exception as e:
        print(f"Error processing frame: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    print("Python face recognition server starting...")
    try:
        sio.wait()
    except KeyboardInterrupt:
        print("Interrupted by user. Disconnecting...")
    finally:
        if sio.connected:
            sio.disconnect()
        print("Server shut down.")