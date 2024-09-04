from flask import Flask, render_template
import subprocess
import logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

@app.route('/')
@app.route('/home')
def home():
    return render_template('deaf.html')

@app.route('/start.html')
def start():
    logging.info("Running the inference classifier script...")
    result = subprocess.run(
        ['python', r'C:\Users\Subhobroto Sasmal\Downloads\DeafTech---SignLanguageDetector-main\DeafTech---SignLanguageDetector-main\Backend\app69.py'], 
        capture_output=True, 
        text=True
    )
    logging.info(f"Script output: {result.stdout}")
    logging.error(f"Script error (if any): {result.stderr}")
    if result.returncode != 0:
        return f"Error: {result.stderr}"
    return result.stdout  # or you can process and display this output as needed

@app.route('/contact.html')
def contact():
    return render_template('contact.html')

@app.route('/faq.html')
def faq():
    return render_template('faq.html')

@app.route('/signin.html')
def signin():
    return render_template('signin.html')

@app.route('/login.html')
def login():
    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)
