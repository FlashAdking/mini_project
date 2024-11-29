from PIL import Image
import numpy as np
import cv2
import face_recognition
from mtcnn import MTCNN
import psycopg2

def preprocess_face(face_image, target_size=(150, 150)):
    """
    Preprocess the face image: crop, resize, and align.
    
    Args:
        face_image (numpy array): The cropped face image.
        target_size (tuple): The target size for resizing (width, height).
    
    Returns:
        numpy array: Preprocessed face image.
    """
    try:
        # Convert to PIL for resizing
        pil_image = Image.fromarray(face_image)
        
        # Resize to target dimensions
        pil_image = pil_image.resize(target_size, Image.ANTIALIAS)
        
        # Convert back to numpy array
        preprocessed_image = np.array(pil_image)
        return preprocessed_image
    except Exception as e:
        print(f"Error during face preprocessing: {e}")
        return None

# Connect to the database
try:
    connection = psycopg2.connect(
        dbname="postgres", 
        user="postgres", 
        password="mysql123", 
        host="localhost", 
        port="5432"
    )
    cursor = connection.cursor()
    print("Database connection established.")
except psycopg2.OperationalError as e:
    print(f"Database connection error: {e}")
    exit()

# Query to fetch student data (ID, name, and photo in binary)
try:
    cursor.execute("SELECT id, name, photo FROM students")
    students = cursor.fetchall()  # Fetch all students from the database
    print(f"Fetched {len(students)} student records.")
except psycopg2.Error as e:
    print(f"Database query error: {e}")
    connection.close()
    exit()

# Initialize MTCNN detector for face detection
detector = MTCNN()

# Process and update encodings for students in the database
for student_id, name, photo_binary in students:
    # Decode the stored photo from binary
    try:
        nparr = np.frombuffer(photo_binary, np.uint8)
        student_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if student_image is None:
            raise ValueError("Invalid image data or unsupported format.")
    except Exception as e:
        print(f"Error: Could not decode photo for Student ID {student_id}, Name: {name}. Error: {e}")
        continue

    # Convert to RGB
    rgb_image = cv2.cvtColor(student_image, cv2.COLOR_BGR2RGB)

    # Detect faces in the student photo using MTCNN
    detections = detector.detect_faces(rgb_image)
    
    if not detections:
        print(f"No faces detected in photo for Student ID {student_id}, Name: {name}")
        continue

    # Use the first detected face
    x, y, width, height = detections[0]['box']
    x1, y1 = max(0, x), max(0, y)
    x2, y2 = x1 + width, y1 + height

    # Crop the face from the image
    cropped_face = student_image[y1:y2, x1:x2]

    # Preprocess the detected face
    preprocessed_face = preprocess_face(cropped_face)

    if preprocessed_face is None:
        print(f"Error: Preprocessing failed for Student ID {student_id}, Name: {name}")
        continue

    # Generate face encodings
    rgb_face = cv2.cvtColor(preprocessed_face, cv2.COLOR_BGR2RGB)
    encodings = face_recognition.face_encodings(rgb_face)

    if encodings:
        face_encoding = encodings[0]
        encoding_binary = np.array(face_encoding).tobytes()

        # Update encoding in the database
        try:
            cursor.execute(
                "UPDATE students SET face_encoding = %s WHERE id = %s",
                (encoding_binary, student_id)
            )
            print(f"Face encoding updated for Student ID {student_id}, Name: {name}")
        except psycopg2.Error as e:
            print(f"Database update error for Student ID {student_id}: {e}")
    else:
        print(f"No face encodings found for Student ID {student_id}, Name: {name}")

# Commit changes and close the database connection
try:
    connection.commit()
    cursor.close()
    connection.close()
    print("Database connection closed.")
except psycopg2.Error as e:
    print(f"Error while closing the database: {e}")
