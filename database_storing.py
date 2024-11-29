import os
import cv2
import psycopg2
import numpy as np
from facenet_pytorch import MTCNN, InceptionResnetV1
import torch
import logging

# Initialize MTCNN and FaceNet (InceptionResnetV1)
mtcnn = MTCNN()
model = InceptionResnetV1(pretrained='vggface2').eval()

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
logging.basicConfig(filename='setup_database.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_students_table():
    """Creates the 'students_new' table if it doesn't already exist."""
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students_new (
                prn VARCHAR PRIMARY KEY,
                roll_no VARCHAR,
                name VARCHAR,
                photo BYTEA,
                encodings BYTEA
            );
        """)
        connection.commit()
        logging.info("Table 'students_new' ensured to exist.")
        print("Table 'students_new' created or already exists.")
    except Exception as e:
        logging.error(f"Error creating table: {e}")
        print(f"Error creating table: {e}")

def parse_filename(filename):
    """
    Extracts roll number, PRN, and name from the filename.
    Example format: A27_2324000295_fname lname.jpg
    """
    filename_without_extension = os.path.splitext(filename)[0]
    parts = filename_without_extension.split('_')
    if len(parts) < 3:
        logging.error(f"Invalid file name format: {filename}")
        print(f"Invalid file name format: {filename}")
        return None, None, None
    roll_no = parts[0]
    prn = parts[1]
    name = ' '.join(parts[2:])
    return roll_no, prn, name

def image_to_binary(image_path):
    """Converts an image to binary format."""
    try:
        with open(image_path, 'rb') as file:
            return file.read()
    except Exception as e:
        logging.error(f"Error converting image to binary: {e}")
        return None

def generate_encoding(image_path):
    """Generates a face encoding using MTCNN and FaceNet."""
    try:
        # Load the image
        image = cv2.imread(image_path)
        if image is None:
            logging.error(f"Failed to read image: {image_path}")
            return None
        
        # Convert to RGB format
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Detect face
        face, _ = mtcnn.detect(rgb_image)
        if face is None or len(face) == 0:
            logging.warning(f"No face detected in image: {image_path}")
            return None
        
        # Process the first detected face
        x1, y1, x2, y2 = map(int, face[0])  # Get the first face
        face_region = rgb_image[y1:y2, x1:x2]
        
        # Resize to 160x160 for FaceNet model
        face_resized = cv2.resize(face_region, (160, 160))
        face_tensor = torch.tensor(face_resized).permute(2, 0, 1).unsqueeze(0).float()
        
        # Generate the encoding
        with torch.no_grad():
            encoding = model(face_tensor).squeeze().numpy()
        return encoding
    except Exception as e:
        logging.error(f"Error generating encoding for {image_path}: {e}")
        return None

def process_and_store_images(image_directory):
    """Processes all images in the given directory and stores them in the database."""
    if not os.path.isdir(image_directory):
        logging.error(f"Directory not found: {image_directory}")
        print(f"Directory not found: {image_directory}")
        return
    
    print(f"Processing images in directory: {image_directory}")
    logging.info(f"Processing images in directory: {image_directory}")
    
    for filename in os.listdir(image_directory):
        if filename.lower().endswith(('.jpg', '.png', '.webp', '.avif')):
            image_path = os.path.join(image_directory, filename)
            
            # Parse the filename for details
            roll_no, prn, name = parse_filename(filename)
            if not roll_no or not prn or not name:
                continue  # Skip invalid files
            
            # Convert image to binary
            photo_binary = image_to_binary(image_path)
            if photo_binary is None:
                logging.warning(f"Skipping file {filename} due to binary conversion issues.")
                continue
            
            # Generate encoding
            encoding = generate_encoding(image_path)
            if encoding is None:
                logging.warning(f"Skipping file {filename} due to encoding issues.")
                continue
            
            # Check if the student already exists
            cursor.execute("SELECT prn FROM students_new WHERE prn = %s", (prn,))
            if cursor.fetchone():
                logging.info(f"Student with PRN {prn} already exists. Skipping.")
                print(f"Student with PRN {prn} already exists. Skipping.")
                continue
            
            # Insert data into the database
            try:
                cursor.execute(
                    "INSERT INTO students_new (prn, roll_no, name, photo, encodings) VALUES (%s, %s, %s, %s, %s)",
                    (prn, roll_no, name, photo_binary, encoding.tobytes())
                )
                logging.info(f"Inserted student: PRN={prn}, Roll No={roll_no}, Name={name}")
                print(f"Inserted student: PRN={prn}, Roll No={roll_no}, Name={name}")
                connection.commit()
            except Exception as e:
                logging.error(f"Error inserting student {prn}: {e}")
                print(f"Error inserting student {prn}: {e}")

if __name__ == "__main__":
    # Ensure the table exists
    create_students_table()

    # Directory containing the images
    image_directory = os.path.abspath("img_known/")  # Adjust this to your folder path

    # Process and store images
    process_and_store_images(image_directory)

    # Close database connection
    cursor.close()
    connection.close()
    logging.info("Database setup and image processing complete.")
    print("Database setup and image processing complete.")
