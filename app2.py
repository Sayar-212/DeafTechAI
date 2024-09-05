from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import logging
import subprocess
logging.basicConfig(level=logging.DEBUG)
import bcrypt
import re

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Database connection
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

#Home
@app.route('/')
@app.route('/home')
def home():
    return render_template('deaf.html')

#Contact/Help-Desk
@app.route('/contact.html')
@app.route('/contact')
def contact():
    return render_template('contact.html')

#Start
@app.route('/start.html')
@app.route('/start')
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
        return render_template('start.html', message=f"Error: {result.stderr}")

    return render_template('deaf.html')

# Sign-up route
@app.route('/signin1.html', methods=['GET', 'POST'])
@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        # Basic email and password validation
        if not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            flash('Invalid email address.')
            return redirect(url_for('signin'))

        if len(password) < 6:
            flash('Password must be at least 6 characters long.')
            return redirect(url_for('signin'))

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        conn = get_db_connection()
        conn.execute('INSERT INTO users (name, email, password) VALUES (?, ?, ?)',
                     (name, email, hashed_password))
        conn.commit()
        conn.close()

        flash('Sign-up successful! Please log in.')
        return redirect(url_for('login'))

    return render_template('signin1.html')

# Login route
@app.route('/login.html', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()

        if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
            #flash('Login successful!')
            return redirect(url_for('start'))
        else:
            flash('Invalid credentials. Please try again or sign up.')

    return render_template('login1.html')

#Debugger
if __name__ == '__main__':
    app.run(debug=True)
