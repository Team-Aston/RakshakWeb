import cv2
import os
import numpy as np
import json

# Path to training images
data_path = 'training_images'
if not os.path.exists(data_path):
    print(f"Error: Training data folder '{data_path}' does not exist.")
    exit(1)

labels = []
faces = []
label_map = {}

# Load images and labels
for label, person in enumerate(os.listdir(data_path)):
    person_path = os.path.join(data_path, person)
    if not os.path.isdir(person_path):
        continue  # Skip if not a directory

    label_map[label] = person
    for img_name in os.listdir(person_path):
        img_path = os.path.join(person_path, img_name)
        try:
            img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                print(f"Warning: Could not read image '{img_path}'. Skipping.")
                continue

            # Resize image to a consistent size (e.g., 200x200)
            img = cv2.resize(img, (200, 200))

            faces.append(img)
            labels.append(label)
        except Exception as e:
            print(f"Error processing image '{img_path}': {e}")

# Train the recognizer
if len(faces) == 0 or len(labels) == 0:
    print("Error: No valid training data found.")
    exit(1)

recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.train(faces, np.array(labels))
recognizer.save('face_model.yml')

# Save the label map
with open('labels.json', 'w') as f:
    json.dump(label_map, f)

print("Training complete. Model saved as 'face_model.yml'. Label map saved as 'labels.json'.")