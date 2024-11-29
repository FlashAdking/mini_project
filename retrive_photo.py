import os
import cv2
import psycopg2
import numpy as np

# Database connection
connection = psycopg2.connect(
    dbname="postgres",
    user="postgres",
    password="mysql123",
    host="localhost",
    port="5432"
)
cursor = connection.cursor()

# Create a new table for storing student details and photos
cursor.execute("""
    CREATE TABLE IF NOT EXISTS students_new (
        id SERIAL PRIMARY KEY,
        roll_no VARCHAR(10),
        prn VARCHAR(20) UNIQUE,
        name VARCHAR(100),
        photo BYTEA
    )
""")
connection.commit()

# Folder containing the images
image_folder = "img_known/"

# Iterate through all images in the folder
for file_name in os.listdir(image_folder):
    if file_name.lower().endswith(('.jpg', '.png')):  # Filter valid image files
        try:
            # Extract metadata from the file name
            base_name = os.path.splitext(file_name)[0]
            
            # Split into parts and handle the name properly
            roll_no, prn, *name_parts = base_name.split('_')
            name = " ".join(name_parts)  # Reconstruct name from remaining parts
            
            # Read the image
            file_path = os.path.join(image_folder, file_name)
            image = cv2.imread(file_path)
            if image is None:
                print(f"Error: Could not read {file_name}")
                continue
            
            # Encode the image to binary
            _, buffer = cv2.imencode('.jpg', image)
            photo_binary = buffer.tobytes()
            
            # Insert into the database
            cursor.execute("""
                INSERT INTO students_new (roll_no, prn, name, photo)
                VALUES (%s, %s, %s, %s)
            """, (roll_no, prn, name, photo_binary))
            connection.commit()
            
            print(f"Inserted {name} (PRN: {prn}) into the database.")
        
        except Exception as e:
            print(f"Error processing {file_name}: {e}")

# Close the database connection
cursor.close()
connection.close()
