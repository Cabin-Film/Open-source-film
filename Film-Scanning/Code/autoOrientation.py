import os
import cv2
import numpy as np
from PIL import Image
from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input, decode_predictions

model = MobileNetV2(weights='imagenet')

input_folder = 'jpeg_folder'
output_folder = 'corrected_folder'
os.makedirs(output_folder, exist_ok=True)

def predict_orientation(image):
    img_resized = cv2.resize(image, (224, 224))
    img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
    img_preprocessed = preprocess_input(img_rgb)
    img_preprocessed = np.expand_dims(img_preprocessed, axis=0)
    
    preds = model.predict(img_preprocessed)
    decoded = decode_predictions(preds, top=1)[0][0][1].lower()
    
    keywords_up = ['tree', 'person', 'building', 'airplane', 'dog', 'bird', 'mountain']
    
    if any(word in decoded for word in keywords_up):
        return 0
    else:
        return 180

def rotate_image(image_path, angle):
    img = Image.open(image_path)
    rotated = img.rotate(angle, expand=True)
    return rotated

for filename in os.listdir(input_folder):
    if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
        path = os.path.join(input_folder, filename)
        image = cv2.imread(path)

        rotation_angle = predict_orientation(image)
        rotated_img = rotate_image(path, rotation_angle)

        save_path = os.path.join(output_folder, filename)
        rotated_img.save(save_path)

        print(f"Processed {filename}: rotated {rotation_angle} degrees")
