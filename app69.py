import pickle
import cv2
import mediapipe as mp
import numpy as np
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from gtts import gTTS
import os
from googletrans import Translator
import pygame
import time
import logging
import requests

# Initialize logging
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize pygame mixer
pygame.mixer.init()

# Load the trained model
try:
    with open('model.p', 'rb') as f:
        model_dict = pickle.load(f)
    model = model_dict['model']
except Exception as e:
    logging.error(f"Failed to load model: {e}")
    raise

# Initialize webcam
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    logging.error("Failed to initialize webcam.")
    raise SystemExit("Webcam not accessible.")

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
hold_start_time = None  # Variable to track hold start time

# Initialize translator
translator = Translator()
translated_text = ""  # Store translated text

# Initialize suggestions list
suggestions = []  # Example suggestions
suggestion_buttons = []

# Function to speak recognized text or translated text
def speak_text():
    global translated_text, recognized_text
    text_to_speak = translated_text if translated_text else recognized_text
    lang = 'en' if not translated_text else translated_lang_code  # Use translated language code

    if text_to_speak:
        file_name = "temp.mp3"
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()

            if os.path.exists(file_name):
                os.remove(file_name)

            tts = gTTS(text=text_to_speak, lang=lang)
            tts.save(file_name)

            pygame.mixer.music.load(file_name)
            pygame.mixer.music.play()

        except Exception as e:
            logging.error(f"Error in speak_text: {e}")

# Function to translate recognized text
def translate_text():
    global translated_text, translated_lang_code
    languages = {
        'Hindi': 'hi',
        'Bengali': 'bn',
        'Telugu': 'te',
        'Marathi': 'mr',
        'Tamil': 'ta',
        'Gujarati': 'gu',
        'Malayalam': 'ml',
        'Kannada': 'kn',
        'Punjabi': 'pa',
        'Urdu': 'ur',
        'English':'en'
    }

    def on_language_select(lang_code):
        global translated_text, translated_lang_code
        try:
            translated = translator.translate(recognized_text, dest=lang_code)
            translated_text = translated.text
            translated_lang_code = lang_code  # Store the selected language code
            translator_label.config(text=f"Translated: {translated_text}")
            speak_text()  # Speak translated text
        except Exception as e:
            logging.error(f"Translation Error: {e}")
            translated_text = ""
            translated_lang_code = ''
        finally:
            lang_window.destroy()

    lang_window = tk.Toplevel(root)
    lang_window.title("Select Language")
    lang_window.geometry("300x510")

    tk.Label(lang_window, text="Select a language:", font=language_font).pack(pady=10)

    for lang_name, lang_code in languages.items():
        tk.Button(lang_window, text=lang_name, command=lambda code=lang_code: on_language_select(code), font=language_font).pack(pady=5)

# Create the main window
root = tk.Tk()
root.title("Sign Language Recognition")
root.configure(bg='#f7f7f7')  # Change background to #f7f7f7
root.attributes('-fullscreen', True)

# Define fonts
heading_font = ('Helvetica', 30, 'bold')
text_font = ('Helvetica', 24)
translator_font = ('Helvetica', 20)
button_font = ('Helvetica', 16)
language_font = ('Helvetica', 12)

# Create a frame to add a border effect
border_frame = ttk.Frame(root, padding=20)
border_frame.pack(fill=tk.BOTH, expand=True)

# Create a heading
heading = tk.Label(border_frame, text="Sign Language to Text & Speech Translator-DeafTech©", bg=None, fg='#000000', font=heading_font)
heading.pack(pady=20)

# Create a frame inside the border frame for content
content_frame = tk.Frame(border_frame, bg='#f7f7f7')
content_frame.pack(fill=tk.BOTH, expand=True)

# Create and place the widgets
text_display = tk.Label(content_frame, text="Sentence: ", bg='#f7f7f7', fg='#000000', font=text_font)
text_display.pack(pady=20, anchor='w', padx=20)

# Translator label
translator_label = tk.Label(content_frame, text="", bg='#f7f7f7', fg='#333333', font=translator_font)
translator_label.pack(pady=10, anchor='w', padx=20)

# Button functions
def on_space():
    global recognized_text
    recognized_text += ' '
    display_text = f"Sentence: {recognized_text}"
    text_display.config(text=display_text)
    clear_suggestions()

def on_backspace():
    global recognized_text
    recognized_text = recognized_text[:-1]
    display_text = f"Sentence: {recognized_text}"
    text_display.config(text=display_text)
    clear_suggestions()
    show_suggestions()

def on_clear():
    global recognized_text, translated_text
    recognized_text = ""
    translated_text = ""
    display_text = "Sentence: "
    text_display.config(text=display_text)
    translator_label.config(text="")
    clear_suggestions()

def on_quit():
    pygame.mixer.music.stop()
    cap.release()  # Release the webcam
    cv2.destroyAllWindows()  # Destroy any OpenCV windows
    root.quit()

def on_speak():
    speak_text()
    clear_suggestions()

def on_translate():
    translate_text()
    clear_suggestions()

# Intellisense suggestion functionality
def clear_suggestions():
    for button in suggestion_buttons:
        button.config(text="", state=tk.DISABLED)


def get_suggestions(prefix, max_words=10):
    url = f"https://api.datamuse.com/words?sp={prefix}*&max={max_words}"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises an error for bad responses
        words = [word['word'] for word in response.json()]
        return words
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching suggestions from API: {e}")
        return []

# Function to get word suggestions
def get_word_suggestions(word):
    dynamic_suggestions = get_suggestions(word, 10)  # Removed the extra list
    if not dynamic_suggestions:
        # If no suggestions, clear and log error
        logging.error("No suggestions found.")
        return ["No suggestions available"]
    
    # Ensure you handle case insensitivity and filtering correctly
    return [s.upper() for s in dynamic_suggestions if s.upper().startswith(word.upper())][:8]



# Show suggestions
def show_suggestions():
    global recognized_text
    clear_suggestions()

    words = recognized_text.split()
    if words:
        current_word = words[-1]
        matching_suggestions = get_word_suggestions(current_word)

        for i in range(len(suggestion_buttons)):
            if i < len(matching_suggestions):
                suggestion_buttons[i].config(text=matching_suggestions[i], state=tk.NORMAL)
            else:
                suggestion_buttons[i].config(state=tk.DISABLED)


# Select suggestion
# Select suggestion and add space
def select_suggestion(index):
    global recognized_text
    selected_suggestion = suggestion_buttons[index].cget('text')
    words = recognized_text.split()

    if words:
        words[-1] = selected_suggestion
        recognized_text = ' '.join(words) + ' '  # Add a space after the selected suggestion
        text_display.config(text=f"Sentence: {recognized_text}")
        clear_suggestions()
        show_suggestions()

        
def create_rounded_button(text, command, row, col):
    button = tk.Button(button_frame, text=text, command=command, font=button_font, height=2, width=12, relief=None, borderwidth=4, bg='#d3d3d3', fg='#000000')
    button.grid(row=row, column=col, padx=20, pady=10, sticky="nsew")
    button.bind("<Enter>", lambda e: e.widget.config(bg='#b0b0b0'))  # Shade of gray for hover effect
    button.bind("<Leave>", lambda e: e.widget.config(bg='#d3d3d3'))
# Create suggestion buttons
suggestion_frame = tk.Frame(content_frame, bg='#f7f7f7')
suggestion_frame.pack(pady=10, anchor='w', padx=20)
for i in range(8):
    btn = tk.Button(suggestion_frame, text="", font=button_font, height=2, width=14, state=tk.DISABLED, command=lambda i=i: select_suggestion(i))
    btn.grid(row=0, column=i, padx=10)
    suggestion_buttons.append(btn)

# Create buttons (without "Next")
button_canvas = tk.Canvas(content_frame, bg='#f7f7f7')
button_frame = tk.Frame(button_canvas, bg='#f7f7f7')

button_canvas.create_window((0, 0), window=button_frame, anchor='nw')
button_canvas.pack(side="right", fill="both", expand=True)
button_frame.bind("<Configure>", lambda e: button_canvas.configure(scrollregion=button_canvas.bbox("all")))

buttons = [
    ("Space", on_space),
    ("Speak", on_speak),
    ("Translate", on_translate),
    ("Clear", on_clear),
    ("Backspace", on_backspace),
    ("Quit", on_quit)
]

for i, (text, command) in enumerate(buttons):
    row = i // 2
    col = i % 2
    create_rounded_button(text, command, row, col)

# Create label to display the webcam feed
image_label = tk.Label(content_frame)
image_label.pack(side=tk.TOP, padx=20, pady=10)

# Update frame function with 3-second hold logic
def update_frame():
    global recognized_text, gesture_detected, last_character, current_character, hold_start_time

    try:
        ret, frame = cap.read()
        if not ret:
            logging.warning("Failed to capture image")
            root.after(30, update_frame)
            return  # Retry frame capture

        H, W, _ = frame.shape
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        results = hands.process(frame_rgb)
        if results.multi_hand_landmarks:
            for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                handedness = results.multi_handedness[idx].classification[0].label
                if handedness == "Left":
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
                    if predicted_label in labels_dict:
                        predicted_character = labels_dict[predicted_label]

                        if not gesture_detected:
                            if predicted_character != last_character:
                                current_character = predicted_character
                                last_character = predicted_character
                                hold_start_time = time.time()  # Start hold timer
                                gesture_detected = True
                        else:
                            if predicted_character != last_character:
                                current_character = predicted_character
                                last_character = predicted_character
                                hold_start_time = time.time()  # Reset hold timer
                            elif time.time() - hold_start_time >= 0.5:
                                recognized_text += current_character
                                current_character = ""
                                hold_start_time = None  # Reset timer
                                display_text = f"Sentence: {recognized_text}"
                                text_display.config(text=display_text)
                                clear_suggestions()
                                show_suggestions()
        else:
            if gesture_detected:
                gesture_detected = False
                show_suggestions()

        img = ImageTk.PhotoImage(image=Image.fromarray(frame_rgb))
        image_label.config(image=img)
        image_label.image = img

    except Exception as e:
        logging.error(f"Error in update_frame: {e}")

    root.after(30, update_frame)

# Start the Tkinter event loop
update_frame()
root.mainloop()
