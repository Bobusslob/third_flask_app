import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Setup application configurations
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
DATABASE = 'database.db'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload directory exists locally
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def get_db_connection():
    """Establishes an active context connection with SQLite."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Enables dictionary-like row access
    return conn

def init_db():
    """Creates the image table if it does not already exist."""
    with get_db_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL
            )
        ''')
        conn.commit()

def allowed_file(filename):
    """Validates the file suffix against the allowed extensions safety list."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # 1. Verify if the expected file key exists in the request payload
        if 'image_file' not in request.files:
            return "No file input found in form", 400
        
        file = request.files['image_file']
        
        # 2. Handle cases where a user submits an empty form selection
        if file.filename == '':
            return "No file selected", 400
            
        # 3. Secure and save the file if it clears extension checks
        if file and allowed_file(file.filename):
            # secure_filename prevents folder traversal injection paths (e.g., ../../etc/passwd)
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Save the file physical payload to the disk path
            file.save(file_path)
            
            # 4. Save the reference filename into SQLite
            with get_db_connection() as conn:
                conn.execute('INSERT INTO images (filename) VALUES (?)', (filename,))
                conn.commit()
                
            return redirect(url_for('index'))
            
        return "Invalid file type allowed", 400

    # GET requests fetch all image metadata references from SQLite to show on-page
    with get_db_connection() as conn:
        images = conn.execute('SELECT filename FROM images').fetchall()
        
    return render_template('upload.html', images=images)

if __name__ == '__main__':
    init_db()  # Initialize the database table structure
    app.run(debug=True)