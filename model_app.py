import pickle
import cv2
import mediapipe as mp
import numpy as np
import pyttsx3
import tkinter as tk
from tkinter import simpledialog
from PIL import Image, ImageTk
from googletrans import Translator  # Import the Translator class

# Load the trained model
with open('model.p', 'rb') as f:
    model_dict = pickle.load(f)
model = model_dict['model']

# Initialize text-to-speech engine
engine = pyttsx3.init()

# Initialize webcam
cap = cv2.VideoCapture(0)

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

hands = mp_hands.Hands(static_image_mode=False, min_detection_confidence=0.5, min_tracking_confidence=0.5)

# Update the labels dictionary as per your classes
labels_dict = {str(i): str(i) for i in range(10)}  # 0-9
labels_dict.update({chr(i): chr(i) for i in range(65, 91)})  # A-Z

recognized_text = ""
gesture_detected = False
last_character = ""
current_character = ""

# Initialize translator
translator = Translator()
translated_text = ""  # Store translated text

# Function to speak recognized text or translated text
def speak_text():
    text_to_speak = translated_text if translated_text else recognized_text
    if text_to_speak:
        engine.say(text_to_speak)
        engine.runAndWait()

# Function to translate recognized text
def translate_text():
    global translated_text
    # List of supported Indian languages
    languages = {
        'Hindi': 'hi',
        'Bengali': 'bn',
        'Telugu': 'te',
        'Marathi': 'mr',
        'Tamil': 'ta',
        'Gujarati': 'gu',
        'Malayalam': 'ml',
        'Kannada': 'kn',
        'Odia': 'or'
    }

    def on_language_select(lang_code):
        global translated_text
        try:
            translated = translator.translate(recognized_text, dest=lang_code)
            translated_text = translated.text
            translator_label.config(text=f"Translated: {translated_text}")
            speak_text()
            lang_window.destroy()
        except Exception as e:
            print(f"Translation Error: {e}")
            translated_text = ""

    # Create a new window for language selection
    lang_window = tk.Toplevel(root)
    lang_window.title("Select Language")
    lang_window.geometry("350x450")

    tk.Label(lang_window, text="Select a language:", font=('Helvetica', 14)).pack(pady=10)

    for lang_name, lang_code in languages.items():
        tk.Button(lang_window, text=lang_name, command=lambda code=lang_code: on_language_select(code), font=('Helvetica', 12)).pack(pady=5)

# Create the main window
root = tk.Tk()
root.title("Sign Language Recognition")
root.configure(bg='white')
root.attributes('-fullscreen', True)

# Create and place the widgets
text_display = tk.Label(root, text="Sentence: ", bg='white', font=('Helvetica', 24))
text_display.pack(pady=20, anchor='w', padx=20)  # Place below gesture box

# Translator label
translator_label = tk.Label(root, text="", bg='white', font=('Helvetica', 20))
translator_label.pack(pady=10, anchor='w', padx=20)

# Button functions
def on_next():
    global recognized_text, current_character
    if current_character:
        recognized_text += current_character
        current_character = ""
    display_text = f"Sentence: {recognized_text}"
    text_display.config(text=display_text)

def on_space():
    global recognized_text
    recognized_text += ' '
    display_text = f"Sentence: {recognized_text}"
    text_display.config(text=display_text)

def on_quit():
    root.quit()

def on_speak():
    speak_text()

def on_clear():
    global recognized_text, translated_text
    recognized_text = ""
    translated_text = ""
    display_text = "Sentence: "
    text_display.config(text=display_text)
    translator_label.config(text="")

def on_translate():
    translate_text()

def on_backspace():
    global recognized_text
    recognized_text = recognized_text[:-1]
    display_text = f"Sentence: {recognized_text}"
    text_display.config(text=display_text)

# Create buttons
button_font = ('Helvetica', 18)

# Use a canvas with a scrollbar for the button frame
button_canvas = tk.Canvas(root, bg='white')
button_scrollbar = tk.Scrollbar(root, orient="vertical", command=button_canvas.yview)
button_frame = tk.Frame(button_canvas, bg='white')

button_canvas.create_window((0, 0), window=button_frame, anchor='nw')
button_canvas.configure(yscrollcommand=button_scrollbar.set)

button_scrollbar.pack(side="right", fill="y")
button_canvas.pack(side="right", fill="both", expand=True)
button_frame.bind("<Configure>", lambda e: button_canvas.configure(scrollregion=button_canvas.bbox("all")))

# Buttons
buttons = [
    ("Next", on_next),
    ("Space", on_space),
    ("Speak", on_speak),
    ("Translate", on_translate),
    ("Clear", on_clear),
    ("Backspace", on_backspace),
    ("Quit", on_quit)
]

for (text, command) in buttons:
    button = tk.Button(button_frame, text=text, command=command, font=button_font, height=2, width=15)
    button.pack(pady=5, padx=20)

# Create label to display the webcam feed
image_label = tk.Label(root, bg='white')
image_label.pack(side=tk.LEFT, padx=20, pady=20, fill=tk.BOTH, expand=True)

# Start the video capture and update loop
def update_frame():
    global recognized_text, gesture_detected, last_character, current_character

    ret, frame = cap.read()
    if not ret:
        print("Failed to capture image")
        root.quit()
        return

    H, W, _ = frame.shape
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    results = hands.process(frame_rgb)
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            data_aux = []
            x_, y_ = [], []

            for lm in hand_landmarks.landmark:
                x_.append(lm.x)
                y_.append(lm.y)

            for lm in hand_landmarks.landmark:
                data_aux.append(lm.x - min(x_))
                data_aux.append(lm.y - min(y_))

            # Predict the character
            prediction = model.predict([np.asarray(data_aux)])
            predicted_label = prediction[0]

            # Check if the predicted label is in the dictionary
            if predicted_label in labels_dict:
                predicted_character = labels_dict[predicted_label]

                # Detect gesture
                if not gesture_detected:
                    if predicted_character != last_character:  # Check if it's different from the last character
                        current_character = predicted_character
                        last_character = predicted_character
                        gesture_detected = True
                else:
                    if predicted_character != last_character:  # Check if it's different from the last character
                        current_character = predicted_character
                        last_character = predicted_character

                # Draw a rectangle with a border around the detected gesture area
                x1 = int(min(x_) * W) - 10
                y1 = int(min(y_) * H) - 10
                x2 = int(max(x_) * W) + 10
                y2 = int(max(y_) * H) + 10

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)  # Border color

                # Display the current character in the middle of the gesture box
                cv2.putText(frame, predicted_character, (x1 + (x2 - x1) // 4, y1 + (y2 - y1) // 2), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

    else:
        # Reset detection when no hand is detected
        if gesture_detected:
            gesture_detected = False

    # Convert the frame to RGB for Tkinter
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = ImageTk.PhotoImage(image=Image.fromarray(frame_rgb))
    image_label.config(image=img)
    image_label.image = img

    # Update the frame every 30 ms
    root.after(30, update_frame)

# Start the Tkinter event loop
update_frame()
root.mainloop()

cap.release()
cv2.destroyAllWindows()
