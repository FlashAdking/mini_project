import psycopg2
import cv2
import numpy as np

# Connect to the database
connection = psycopg2.connect(
    dbname="postgres",
    user="postgres",
    password="mysql123",
    host="localhost",
    port="5432"
)
cursor = connection.cursor()

# Fetch all records from the students_new table
cursor.execute("SELECT prn, photo FROM students_new")
rows = cursor.fetchall()

for prn, photo_binary in rows:
    try:
        # Decode the binary photo data
        nparr = np.frombuffer(photo_binary, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            print(f"Error: Could not decode the photo for PRN {prn}.")
            continue

        # Display the photo
        cv2.imshow(f"Photo for PRN {prn}", image)
        cv2.waitKey(0)  # Wait until a key is pressed
        cv2.destroyAllWindows()

    except Exception as e:
        print(f"Error processing PRN {prn}: {e}")

# Close the connection
cursor.close()
connection.close()
