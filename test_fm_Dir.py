import os
import cv2
import psycopg2
import numpy as np
from facenet_pytorch import MTCNN, InceptionResnetV1
import torch
import tensorflow as tf
import logging
from datetime import datetime

# Initialize MTCNN detector and InceptionResnetV1 model (FaceNet)
mtcnn = MTCNN()
model = InceptionResnetV1(pretrained='vggface2').eval()

# TensorFlow face recognition model for comparison
def compare_encodings(extracted_encoding, db_encoding):
    """
    Compares the extracted face encoding with the stored face encoding from the database.
    Uses TensorFlow to compare the two encodings.
    """
    # Reshaping encodings to match the input format for TensorFlow
    extracted_encoding = tf.convert_to_tensor(extracted_encoding, dtype=tf.float32)
    db_encoding = tf.convert_to_tensor(db_encoding, dtype=tf.float32)
    
    # Calculate cosine similarity between the two encodings
    similarity = tf.reduce_sum(tf.multiply(extracted_encoding, db_encoding))
    threshold = 0.85  # Set a threshold for similarity

    if similarity.numpy() > threshold:
        return True
    return False

# Database connection
connection = psycopg2.connect(
    dbname="postgres",
    user="postgres",
    password="mysql123",
    host="localhost",
    port="5432"
)
cursor = connection.cursor()

# Set up logging
logging.basicConfig(filename='face_encoding_process.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Check if the required tables exist, create them if not
def create_tables_if_not_exists():
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students_new (
            prn VARCHAR PRIMARY KEY,
            encodings BYTEA,
            photo BYTEA
        );
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            prn VARCHAR,
            date DATE,
            status VARCHAR,
            FOREIGN KEY (prn) REFERENCES students_new (prn)
        );
    """)
    connection.commit()

# Call the function to ensure tables exist
create_tables_if_not_exists()

# Path to group photo
group_photo_path = "test_img/g20-photo.webp"
TOLERANCE = 0.6  # Face recognition tolerance

# Load the group photo
group_image = cv2.imread(group_photo_path)
if group_image is None:
    logging.error("Error: Could not read the group photo.")
    exit()

# Convert the image to RGB (MTCNN and FaceNet require RGB format)
rgb_group_image = cv2.cvtColor(group_image, cv2.COLOR_BGR2RGB)

# Detect faces in the group photo using MTCNN
faces, _ = mtcnn.detect(rgb_group_image)
if faces is None or len(faces) == 0:
    logging.warning("No faces detected in the group photo.")
    exit()

# Extract face encodings from the group photo
group_face_encodings = []
for face in faces:
    x1, y1, x2, y2 = face
    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)  # Convert to int for slicing
    
    # Ensure the face region is valid before resizing
    if x1 < 0 or y1 < 0 or x2 <= x1 or y2 <= y1:
        logging.warning(f"Invalid face region: ({x1}, {y1}), ({x2}, {y2})")
        continue
    
    face_region = rgb_group_image[y1:y2, x1:x2]  # Extract the face region

    # Ensure the face region is non-empty before attempting resize
    if face_region.size == 0:
        logging.warning(f"Empty face region for coordinates: ({x1}, {y1}), ({x2}, {y2})")
        continue

    # Resize face to the required size (160x160)
    face_resized = cv2.resize(face_region, (160, 160))

    # Convert face to tensor and normalize
    face_tensor = np.transpose(face_resized, (2, 0, 1))  # Convert to CxHxW format
    face_tensor = np.expand_dims(face_tensor, axis=0)  # Add batch dimension (1, C, H, W)

    # Get the face embedding
    face_embedding = model(torch.tensor(face_tensor, dtype=torch.float32))

    # Flatten to 1D array
    encoding = face_embedding.detach().numpy().flatten()

    # Append to the list of face encodings
    group_face_encodings.append(encoding)

# Fetch stored encodings and photos from the database
cursor.execute("SELECT prn, encodings, photo FROM students_new")
stored_encodings = cursor.fetchall()

# Compare the extracted group face encodings with the stored encodings
matched_students = set()
for idx, extracted_encoding in enumerate(group_face_encodings):
    for prn, db_encoding_binary, db_photo_binary in stored_encodings:
        # Convert binary encoding back to numpy array
        db_encoding = np.frombuffer(db_encoding_binary, dtype=np.float32)

        # Compare the extracted encoding with the stored encoding
        if compare_encodings(extracted_encoding, db_encoding):
            matched_students.add(prn)
            logging.info(f"Group face {idx + 1} matched with student PRN: {prn}")

            # Convert binary photo to image
            student_photo = np.frombuffer(db_photo_binary, dtype=np.uint8)
            student_photo_image = cv2.imdecode(student_photo, cv2.IMREAD_COLOR)

            # Only display the student's photo once for the first match
            if prn not in matched_students:
                cv2.imshow(f"Matched Student: {prn}", student_photo_image)
                cv2.waitKey(0)

# Log the matched students and mark attendance
current_date = datetime.now().strftime('%Y-%m-%d')
for prn in matched_students:
    # Check if attendance for the current date already exists
    cursor.execute("SELECT * FROM attendance WHERE prn = %s AND date = %s", (prn, current_date))
    existing_attendance = cursor.fetchone()

    # If no attendance record exists for the current date, insert it
    if not existing_attendance:
        cursor.execute(
            "INSERT INTO attendance (prn, date, status) VALUES (%s, %s, %s)",
            (prn, current_date, 'present')
        )
        logging.info(f"Attendance marked for PRN: {prn}")
    else:
        logging.info(f"Attendance already marked for PRN: {prn} on {current_date}")

# Commit the attendance entries
connection.commit()

# Draw bounding boxes around detected faces in the group photo
for face in faces:
    x1, y1, x2, y2 = int(face[0]), int(face[1]), int(face[2]), int(face[3])
    cv2.rectangle(group_image, (x1, y1), (x2, y2), (0, 255, 0), 2)

# Save the image with bounding boxes drawn around faces
output_image_path = "output/group_photo_with_faces.jpg"
cv2.imwrite(output_image_path, group_image)
logging.info(f"Processed image with bounding boxes saved to: {output_image_path}")

# Display the image with OpenCV after processing all matched faces
cv2.imshow("Group Photo with Matched Faces", group_image)
cv2.waitKey(0)
cv2.destroyAllWindows()

# Close the database connection
cursor.close()
connection.close()
