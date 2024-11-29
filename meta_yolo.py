import os
import cv2
import psycopg2
import numpy as np
from retinaface import RetinaFace  # RetinaFace for face detection
import torch
import tensorflow as tf
import logging
from datetime import datetime
from insightface.app import FaceAnalysis  # ArcFace for face encoding

# Initialize RetinaFace detector
detector = RetinaFace()

# Initialize InsightFace ArcFace model
app = FaceAnalysis()
app.prepare(ctx_id=0, nms=0.4)  # Use 0 for CPU or change to 1 for GPU

# TensorFlow face recognition model for comparison
def compare_encodings(extracted_encoding, db_encoding):
    """
    Compares the extracted face encoding with the stored face encoding from the database.
    Uses TensorFlow to compare the two encodings.
    """
    extracted_encoding = tf.convert_to_tensor(extracted_encoding, dtype=tf.float32)
    db_encoding = tf.convert_to_tensor(db_encoding, dtype=tf.float32)
    
    similarity = tf.reduce_sum(tf.multiply(extracted_encoding, db_encoding))
    threshold = 0.90  # Increased threshold for stricter matching

    return similarity.numpy() > threshold

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

# Ensure tables exist
def create_tables_if_not_exists():
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students_new (
            prn VARCHAR PRIMARY KEY,
            roll_no VARCHAR,
            name VARCHAR,
            photo BYTEA,
            encodings BYTEA
        );
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            prn VARCHAR,
            date DATE,
            status VARCHAR,
            FOREIGN KEY (prn) REFERENCES students_new (prn),
            PRIMARY KEY (prn, date)
        );
    """)
    connection.commit()

create_tables_if_not_exists()

# Path to group photo
group_photo_path = "test_img/g20-photo.webp"
TOLERANCE = 0.6  # Face recognition tolerance

# Load the group photo
group_image = cv2.imread(group_photo_path)
if group_image is None:
    logging.error("Error: Could not read the group photo.")
    exit()

# Convert the image to RGB for RetinaFace
rgb_group_image = cv2.cvtColor(group_image, cv2.COLOR_BGR2RGB)

# Detect faces using RetinaFace
faces = detector.detect_faces(rgb_group_image)

if not faces:
    logging.warning("No faces detected in the group photo.")
    exit()

# Extract face encodings using ArcFace
group_face_encodings = []
for face in faces:
    x1, y1, x2, y2 = face['box']
    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)  # Convert to int for slicing

    if x1 < 0 or y1 < 0 or x2 <= x1 or y2 <= y1:
        logging.warning(f"Invalid face region: ({x1}, {y1}), ({x2}, {y2})")
        continue

    face_region = rgb_group_image[y1:y2, x1:x2]  # Extract the face region

    if face_region.size == 0:
        logging.warning(f"Empty face region for coordinates: ({x1}, {y1}), ({x2}, {y2})")
        continue

    # Perform face embedding using ArcFace
    face_info = app.get(face_region)
    if not face_info:
        continue  # Skip if no face is detected

    face_embedding = face_info[0].embedding  # Get the face embedding
    group_face_encodings.append(face_embedding)

# Fetch stored encodings from the database
cursor.execute("SELECT prn, encodings, name FROM students_new")
stored_encodings = cursor.fetchall()

# Compare the extracted group face encodings with the stored encodings
matched_students = set()
for extracted_encoding in group_face_encodings:
    for prn, db_encoding_binary, name in stored_encodings:
        db_encoding = np.frombuffer(db_encoding_binary, dtype=np.float32)

        if compare_encodings(extracted_encoding, db_encoding):
            matched_students.add(prn)
            logging.info(f"Matched with student PRN: {prn}")

# Log the matched students and mark attendance
if matched_students:
    logging.info(f"Attendance marked for: {', '.join(matched_students)}")
    current_date = datetime.now().strftime('%Y-%m-%d')
    for prn in matched_students:
        cursor.execute(
            "INSERT INTO attendance (prn, date, status) VALUES (%s, %s, %s) ON CONFLICT (prn, date) DO UPDATE SET status = EXCLUDED.status",
            (prn, current_date, 'present')
        )
    connection.commit()

    # Fetch and print the names of the students who are present
    cursor.execute("""
        SELECT s.name FROM students_new s
        JOIN attendance a ON s.prn = a.prn
        WHERE a.status = 'present' AND a.date = %s
    """, (current_date,))
    present_students = cursor.fetchall()

    print("Students Present Today:")
    for student in present_students:
        print(student[0])  # Assuming the student name is in the first column
else:
    logging.info("No matches found in the group photo.")

# Draw bounding boxes for faces in the group photo
for face in faces:
    x1, y1, x2, y2 = face['box']
    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
    cv2.rectangle(group_image, (x1, y1), (x2, y2), (0, 255, 0), 2)  # Green box for faces

# Save the image with bounding boxes, without labels
output_image_path = "output/group_photo_with_faces.jpg"
cv2.imwrite(output_image_path, group_image)
logging.info(f"Processed image with bounding boxes saved to: {output_image_path}")

# Display the image
cv2.imshow("Matched Faces", group_image)
cv2.waitKey(0)
cv2.destroyAllWindows()

# Close the database connection
cursor.close()
connection.close()
