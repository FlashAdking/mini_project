
import cv2


pixels = cv2.imread('test_img/test.jpg')

temp = "haarcascade_frontalface_default.xml"

classifier = cv2.CascadeClassifier(temp)

boxes = classifier.detectMultiScale(pixels)

for box in boxes:
    x,y , width , height = box
    x2 , y2 = x + width , y + height
    cv2.rectangle(pixels, (x, y), (x2, y2), (0, 255, 0), 2)


cv2.imshow('face detected',pixels)
cv2.waitKey(0)
cv2.destroyAllWindows()