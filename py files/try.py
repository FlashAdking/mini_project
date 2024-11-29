import face_recognition
import os
import pickle

# Load the saved encodings
encoding_file = "face_encodings.pkl"
try:
    with open(encoding_file, "rb") as f:
        data = pickle.load(f)
        known_face_encodings = data["encodings"]
        known_face_names = data["names"]
        print(f"Loaded {len(known_face_names)} known student encodings.")
except FileNotFoundError:
    print(f"Error: Encoding file '{encoding_file}' not found.")
    exit()

# Initialize attendance set
attendance_set = set()

# Path to group photos
group_photos_path = "test_img/"  # Replace with the folder containing group photos
group_photos = [os.path.join(group_photos_path, f) for f in os.listdir(group_photos_path)
                if f.endswith(('.jpg', '.png', '.jpeg'))]

for photo_path in group_photos:
    try:
        print(f"Processing group photo: {photo_path}")

        # Load the group photo
        group_image = face_recognition.load_image_file(photo_path)

        # Detect faces and generate encodings
        face_locations = face_recognition.face_locations(group_image)
        face_encodings = face_recognition.face_encodings(group_image, face_locations)

        print(f"Found {len(face_encodings)} faces in {photo_path}.")

        # Compare each detected face
        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.6)
            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)

            # Find the best match
            best_match_index = None
            if len(face_distances) > 0:
                best_match_index = face_distances.argmin()

            if best_match_index is not None and matches[best_match_index]:
                name = known_face_names[best_match_index]
                attendance_set.add(name)
                print(f"Recognized: {name}")
            else:
                print("Unknown face detected.")

    except Exception as e:
        print(f"Error processing {photo_path}: {e}")

# Display the attendance
print("\nMarked Attendance:")
for student in attendance_set:
    print(f"- {student}")

# Optionally: Save attendance to a file or database
attendance_file = "attendance.txt"
try:
    with open(attendance_file, "w") as f:
        for student in sorted(attendance_set):
            f.write(student + "\n")
    print(f"Attendance saved to '{attendance_file}'.")
except Exception as e:
    print(f"Error saving attendance: {e}")
