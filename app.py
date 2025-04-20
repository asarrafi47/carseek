from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from dashboard import dashboard_bp
import secrets
from cryptography.fernet import Fernet

app = Flask(__name__)

# Generate a strong secret key for session management
app.secret_key = secrets.token_hex(32)

# Encryption key setup
# You could store this securely or generate dynamically at startup
encryption_key = Fernet.generate_key()
cipher_suite = Fernet(encryption_key)

DATABASE = 'users.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        conn.commit()

def init_cars_table():
    with get_db_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS cars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                make TEXT NOT NULL,
                model TEXT NOT NULL,
                year INTEGER NOT NULL,
                mileage INTEGER,
                price INTEGER,
                location TEXT,
                color TEXT,
                image_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()


# Register the dashboard blueprint
app.register_blueprint(dashboard_bp)

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard_bp.dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        if not username or not password:
            flash('Please fill in all fields.', 'warning')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)

        try:
            with get_db_connection() as conn:
                conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
                conn.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists.', 'danger')

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        with get_db_connection() as conn:
            user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard_bp.dashboard'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))

# Example routes to show encryption/decryption
@app.route('/encrypt/<text>')
def encrypt_text(text):
    encrypted_text = cipher_suite.encrypt(text.encode()).decode()
    return f'Encrypted: {encrypted_text}'

@app.route('/decrypt/<encrypted_text>')
def decrypt_text(encrypted_text):
    try:
        decrypted_text = cipher_suite.decrypt(encrypted_text.encode()).decode()
        return f'Decrypted: {decrypted_text}'
    except Exception as e:
        return f'Error decrypting: {str(e)}'

if __name__ == '__main__':
    init_db()
    app.run(debug=True)

@app.route('/discover')
def discover():
    with get_db_connection() as conn:
        cars = conn.execute('SELECT * FROM cars ORDER BY created_at DESC').fetchall()
    return render_template('discover.html', cars=cars)

@app.route('/saved')
def saved():
    if 'saved_cars' not in session:
        session['saved_cars'] = []

    with get_db_connection() as conn:
        cars = conn.execute(
            'SELECT * FROM cars WHERE id IN ({seq})'.format(seq=','.join(['?']*len(session['saved_cars']))),
            session['saved_cars']
        ).fetchall() if session['saved_cars'] else []

    return render_template('saved.html', cars=cars)

@app.route('/save_car/<int:car_id>', methods=['POST'])
def save_car(car_id):
    if 'saved_cars' not in session:
        session['saved_cars'] = []

    if car_id not in session['saved_cars']:
        session['saved_cars'].append(car_id)
        session.modified = True

    flash('Car saved!', 'success')
    return redirect(url_for('discover'))

