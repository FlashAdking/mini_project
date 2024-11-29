import cv2
import numpy as np
import onnxruntime as ort

# Load YOLO model
onnx_model_path = "yolov8n-face.onnx"  # Update the path if needed
session = ort.InferenceSession(onnx_model_path)

# Load Haar Cascade
haar_cascade_path = "haarcascade_frontalface_default.xml"  # Update the path if needed
classifier = cv2.CascadeClassifier(haar_cascade_path)

# Load the group photo
image_path = "test_img/test.jpg"
image = cv2.imread(image_path)

if image is None:
    print(f"Error: Unable to load image at {image_path}")
    exit()

# Get dimensions
img_height, img_width, _ = image.shape
input_size = 640

# Preprocess image for YOLO
def preprocess_image(image, input_size):
    resized_image = cv2.resize(image, (input_size, input_size))
    normalized_image = resized_image.astype(np.float32) / 255.0
    chw_image = normalized_image.transpose(2, 0, 1)
    return np.expand_dims(chw_image, axis=0)

blob = preprocess_image(image, input_size)

# Run YOLO inference
inputs = {session.get_inputs()[0].name: blob}
outputs = session.run(None, inputs)

# Decode YOLO output
def decode_yolo_output(output, img_width, img_height, confidence_threshold=0.4):
    detections = output[0].squeeze()
    boxes = []
    for detection in detections:
        x_center, y_center, width, height, confidence = detection[:5]
        if confidence > confidence_threshold:
            x_center = int(x_center * img_width / input_size)
            y_center = int(y_center * img_height / input_size)
            width = int(width * img_width / input_size)
            height = int(height * img_height / input_size)
            x1 = max(0, int(x_center - width / 2))
            y1 = max(0, int(y_center - height / 2))
            x2 = min(img_width, int(x_center + width / 2))
            y2 = min(img_height, int(y_center + height / 2))
            boxes.append((x1, y1, x2, y2))
    return boxes

yolo_boxes = decode_yolo_output(outputs, img_width, img_height)

# Use Haar Cascade as fallback if YOLO fails
if len(yolo_boxes) == 0:
    print("No faces detected with YOLO. Falling back to Haar Cascade...")
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    haar_boxes = classifier.detectMultiScale(
        gray_image,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(30, 30)
    )
    yolo_boxes = [(x, y, x + w, y + h) for (x, y, w, h) in haar_boxes]

# Draw all detected boxes on the image
for (x1, y1, x2, y2) in yolo_boxes:
    cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)  # Green for YOLO

# Display and save the output
cv2.imshow("Combined Detection", image)
cv2.waitKey(0)
cv2.destroyAllWindows()
cv2.imwrite("output_combined_detection.jpg", image)

print(f"Detected {len(yolo_boxes)} faces using combined methods.")
