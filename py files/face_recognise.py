from cv2 import imread, imshow, waitKey, destroyAllWindows, CascadeClassifier, rectangle, imwrite

# Load the image
pixels = imread('test.jpg')

# Path to Haar Cascade XML file
temp = "haarcascade_frontalface_default.xml"

# Create the Haar Cascade Classifier
classifier = CascadeClassifier(temp)

# Perform face detection
boxes = classifier.detectMultiScale(pixels)

# Draw rectangles around detected faces
for box in boxes:
    x, y, width, height = box
    x2, y2 = x + width, y + height
    rectangle(pixels, (x, y), (x2, y2), (0, 255, 0), 2)  # Green color with thickness 2

imwrite('output_image.jpg', pixels)

# Display the result
imshow('Face Detection', pixels)
waitKey(0)
destroyAllWindows()
