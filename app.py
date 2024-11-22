import json
import os
import sqlite3
from datetime import datetime

from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './uploads'
app.config['DATABASE'] = './database.db'
app.config['TEMPLATES_AUTO_RELOAD'] = True

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize Database
def init_db():
    with sqlite3.connect(app.config['DATABASE']) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS photos (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT,
                            description TEXT,
                            last_watered TEXT,
                            watering_history TEXT
                        )''')
init_db()

# Serve uploaded files
@app.route('/uploads/<int:photo_id>')
def uploaded_file(photo_id):
    filename = f"{photo_id}.jpg"
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/list', methods=['GET'])
def list_photos():
    with sqlite3.connect(app.config['DATABASE']) as conn:
        cursor = conn.cursor()
        # Fetch and sort by `last_watered` (nulls last)
        photos = cursor.execute('''
            SELECT id, name, last_watered, description 
            FROM photos 
            ORDER BY 
                CASE WHEN last_watered IS NULL THEN 1 ELSE 0 END,
                last_watered ASC
        ''').fetchall()

        # Calculate time since last watered
        photo_data = []
        for photo in photos:
            id, name, last_watered, description = photo
            if last_watered:
                time_since_watered = (datetime.now() - datetime.fromisoformat(last_watered)).total_seconds()
                days_since = int(time_since_watered // 86400)
            else:
                days_since = None
            photo_data.append({
                "id": id,
                "name": name,
                "days_since_watered": days_since,
                "description": description
            })

        return jsonify(photo_data)


# API to create a photo
@app.route('/api/create', methods=['POST'])
def create_photo():
    if 'photo' not in request.files:
        return "No file uploaded", 400
    file = request.files['photo']
    if file.filename == '':
        return "No file selected", 400
    
    temp_filename = secure_filename(file.filename)
    temp_filepath = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
    file.save(temp_filepath)
    
    with sqlite3.connect(app.config['DATABASE']) as conn:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO photos (name, description, last_watered, watering_history) VALUES (?, ?, ?, ?)',
            (None, None, None, json.dumps([]))
        )
        photo_id = cursor.lastrowid
        conn.commit()
    
    new_filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{photo_id}.jpg")
    os.rename(temp_filepath, new_filepath)
    return jsonify({"id": photo_id})

# API to delete a photo
@app.route('/api/delete/<int:photo_id>', methods=['POST'])
def delete_photo(photo_id):
    with sqlite3.connect(app.config['DATABASE']) as conn:
        cursor = conn.cursor()
        # Delete photo from database
        cursor.execute('DELETE FROM photos WHERE id = ?', (photo_id,))
        conn.commit()

    # Delete associated file
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{photo_id}.jpg")
    if os.path.exists(filepath):
        os.remove(filepath)
    
    return jsonify({"message": "Photo deleted successfully"})

# API to update watering details
@app.route('/api/water/<int:photo_id>', methods=['POST'])
def update_watering(photo_id):
    current_time = datetime.now().isoformat()
    with sqlite3.connect(app.config['DATABASE']) as conn:
        cursor = conn.cursor()
        # Fetch current last_watered and history
        photo = cursor.execute(
            'SELECT last_watered, watering_history FROM photos WHERE id = ?', (photo_id,)
        ).fetchone()

        last_watered = photo[0]
        watering_history = json.loads(photo[1]) if photo[1] else []

        # Update watering details
        if last_watered:
            watering_history.append(last_watered)
        cursor.execute(
            'UPDATE photos SET last_watered = ?, watering_history = ? WHERE id = ?',
            (current_time, json.dumps(watering_history), photo_id)
        )
        conn.commit()
    
    return jsonify({"message": "Watering updated successfully", "last_watered": current_time})

# Modify Page
@app.route('/api/modify/<int:photo_id>', methods=['GET', 'POST'])
def modify_photo(photo_id):
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        with sqlite3.connect(app.config['DATABASE']) as conn:
            conn.execute(
                'UPDATE photos SET name = ?, description = ? WHERE id = ?',
                (name, description, photo_id)
            )
            conn.commit()

        # Clicked save so go back to index
        return redirect(url_for('index'))
    
    with sqlite3.connect(app.config['DATABASE']) as conn:
        photo = conn.execute(
            'SELECT id, name, description, last_watered, watering_history FROM photos WHERE id = ?',
            (photo_id,)
        ).fetchone()
    return render_template('modify.html', photo=photo)

# Index Page
@app.route('/')
def index():
    return render_template('index.html')