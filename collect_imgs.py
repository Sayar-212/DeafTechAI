import os
import cv2

DATA_DIR = './data'
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Update the number of classes to include 0-9 and A-Z
classes = [str(i) for i in range(10)] + [chr(i) for i in range(65, 91)]  # 0-9 and A-Z
dataset_size = 100

cap = cv2.VideoCapture(0)  # Change this if needed

for label in classes:
    class_dir = os.path.join(DATA_DIR, label)
    if not os.path.exists(class_dir):
        os.makedirs(class_dir)

    print(f'Collecting data for class {label}')
    counter = 0

    while counter < dataset_size:
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture image")
            break
        
        # Show the current frame with instructions
        cv2.putText(frame, f'Class {label}: Press "Q" to start', (10, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 255, 0), 3, cv2.LINE_AA)
        cv2.imshow('frame', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("Starting capture...")
            break

    while counter < dataset_size:
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture image")
            break
        
        # Save the captured image
        cv2.imwrite(os.path.join(class_dir, f'{counter}.jpg'), frame)
        counter += 1
        
        cv2.imshow('frame', frame)
        cv2.waitKey(1)
    
cap.release()
cv2.destroyAllWindows()