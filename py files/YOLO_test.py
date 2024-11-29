import cv2
import numpy as np
import onnxruntime as ort

# Load YOLOv11 model
onnx_model_path = "yolov11n-face.onnx"  # Update with the yolov11n-face.onnx file path
session = ort.InferenceSession(onnx_model_path)

# Load group photo
group_photo_path = "test_img/test.jpg"  # Update with the correct file path
group_image = cv2.imread(group_photo_path)

if group_image is None:
    print(f"Error: Unable to load image at {group_photo_path}")
    exit()

# Get original image dimensions
original_height, original_width, _ = group_image.shape
input_size = 640  # Model input size (could be different for yolov11n, check the model input size)

# Preprocess the image for YOLO
def preprocess_image(image, input_size):
    resized_image = cv2.resize(image, (input_size, input_size))
    normalized_image = resized_image.astype(np.float32) / 255.0
    chw_image = normalized_image.transpose(2, 0, 1)
    return np.expand_dims(chw_image, axis=0)

blob = preprocess_image(group_image, input_size)

# Run inference with YOLOv11 model
inputs = {session.get_inputs()[0].name: blob}
outputs = session.run(None, inputs)

# Decode YOLO output with NMS and other post-processing
# Add debugging print statements to check coordinates
def decode_yolo_output(output, img_width, img_height, confidence_threshold=0.6, nms_threshold=0.4):
    detections = output[0].squeeze()  # Remove batch dimension
    boxes = []
    confidences = []
    class_ids = []

    # Iterate through detections
    for detection in detections:
        x_center, y_center, width, height, confidence = detection[:5]
        if confidence > confidence_threshold:
            # Calculate bounding box coordinates
            x_center = int(x_center * img_width / input_size)
            y_center = int(y_center * img_height / input_size)
            width = int(width * img_width / input_size)
            height = int(height * img_height / input_size)
            
            # Calculate bounding box corners (top-left and bottom-right)
            x1 = int(x_center - width / 2)
            y1 = int(y_center - height / 2)
            x2 = int(x_center + width / 2)
            y2 = int(y_center + height / 2)

            # Ensure bounding box is within image bounds
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(img_width, x2), min(img_height, y2)

            print(f"Bounding box: ({x1}, {y1}) -> ({x2}, {y2})")  # Debug print for box coordinates

            boxes.append([x1, y1, x2, y2])
            confidences.append(confidence)
            class_ids.append(0)  # Assuming 0 is the face class

    # Apply NMS (Non-Maximum Suppression) to filter out overlapping boxes
    indices = cv2.dnn.NMSBoxes(boxes, confidences, confidence_threshold, nms_threshold)

    # Convert NMS indices to a list of boxes
    nms_boxes = []
    if len(indices) > 0:
        for i in indices.flatten():
            nms_boxes.append(boxes[i])

    return nms_boxes

# Draw bounding boxes around detected faces for debugging
for (x1, y1, x2, y2) in boxes:
    print(f"Drawing box: ({x1}, {y1}) -> ({x2}, {y2})")  # Debug print before drawing
    cv2.rectangle(group_image, (x1, y1), (x2, y2), (0, 255, 0), 2)  # Draw green rectangles on faces

# Show the image with bounding boxes for debugging
cv2.imshow("Group Image with Bounding Boxes", group_image)
cv2.waitKey(0)
cv2.destroyAllWindows()
