import psycopg2
import os

# Database connection
conn = psycopg2.connect(
    dbname="postgres",
    user="postgres",
    password="mysql123",
    host="localhost",
    port="5432"
)
cur = conn.cursor()

# Directory containing images
image_dir = 'img_known/'

# Insert student details with images
for img_filename in os.listdir(image_dir):
    if img_filename.endswith(('.jpg', '.jpeg', '.png')):  # Process only image files
        # Extract details from the filename
        parts = img_filename.split('_')
        if len(parts) == 3:
            roll_no = parts[0]  # First part is the roll number
            prn = parts[1]      # Second part is the PRN

            # Process the name part
            parts_ = parts[2].split(' ')
            name_part = parts_[0] + " " + parts_[1].split('.')[0]  # Combine first and last name
            name_parts = name_part.split(' ')  # Split first and last name
            if len(name_parts) == 2:
                name = name_parts[0].capitalize() + " " + name_parts[1].capitalize()  # Capitalize both parts
            else:
                print(f"Skipping file {img_filename}: Invalid name format")
                continue

            # Read the image data
            img_path = os.path.join(image_dir, img_filename)
            with open(img_path, 'rb') as file:
                photo_data = file.read()

            # Insert data into the database
            try:
                cur.execute("""
                    INSERT INTO students (name, roll_no, prn, photo)
                    VALUES (%s, %s, %s, %s)
                """, (name, roll_no, prn, photo_data))
            except psycopg2.IntegrityError as e:
                print(f"Error inserting {img_filename}: {e}")
                conn.rollback()
        else:
            print(f"Skipping file {img_filename}: Invalid this  format")

# Commit changes and close the connection
conn.commit()
cur.close()
conn.close()
