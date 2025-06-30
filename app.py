import os
import sys
import subprocess
import signal
import platform
from flask import Flask, render_template, request, redirect, url_for, send_file, flash, jsonify
from werkzeug.utils import secure_filename
from main import load_attendance
from flask import send_from_directory


current_process = None


app = Flask(__name__)
app.secret_key = "your_secret_key"


HERE = os.path.dirname(__file__)
KNOWN_FACES_DIR = os.path.join(HERE, "known_faces")
ATTENDANCE_DATA_DIR = os.path.join(HERE, "attendance_data")


os.makedirs(KNOWN_FACES_DIR, exist_ok=True)
os.makedirs(ATTENDANCE_DATA_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_employee', methods=['POST'])
def add_employee():
    if 'image' not in request.files:
        flash('No file part')
        return redirect(url_for('index'))

    file = request.files['image']
    name = request.form.get('name', '').strip()

    if file.filename == '' or not name:
        flash('Missing name or file')
        return redirect(url_for('index'))

    if file and allowed_file(file.filename):
        filename = secure_filename(f"{name}.jpg")
        file.save(os.path.join(KNOWN_FACES_DIR, filename))
        flash(f'Employee "{name}" added successfully.')
    else:
        flash('Invalid file type. Only JPG/PNG allowed.')

    return redirect(url_for('index'))

@app.route('/take_attendance', methods=['POST'])
def take_attendance():
    global current_process
    date_str = request.form.get('attendance_date')
    if not date_str:
        flash('Please select a date for attendance.')
        return redirect(url_for('index'))

    if current_process and current_process.poll() is None:
        flash('Attendance scan is already running.')
        return redirect(url_for('index'))

    script_path = os.path.join(HERE, 'scan.py')
    if platform.system() == "Windows":
        current_process = subprocess.Popen(
            [sys.executable, script_path, date_str],
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
    else:
        current_process = subprocess.Popen(
            [sys.executable, script_path, date_str],
            preexec_fn=os.setsid
        )

    flash('Attendance scan started. Use Stop to end.')
    return redirect(url_for('index'))

@app.route('/stop_attendance', methods=['POST'])
def stop_attendance():
    global current_process
    if current_process and current_process.poll() is None:
        if platform.system() == "Windows":
            current_process.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            os.killpg(os.getpgid(current_process.pid), signal.SIGINT)
        current_process.wait()
        current_process = None
        return jsonify({'status': 'stopped'})
    return jsonify({'status': 'not running'})

@app.route('/attendance')
def attendance_page():
    return render_template('attendance.html')

@app.route('/api/attendance')
def api_attendance():
    date = request.args.get('date')
    for entry in load_attendance():
        if entry['date'] == date:
            return jsonify(entry['records'])
    return jsonify([])

@app.route('/api/attendance/all')
def api_attendance_all():
    return jsonify(load_attendance())

@app.route('/known_faces/<path:filename>')
def known_faces_static(filename):
    return send_from_directory(KNOWN_FACES_DIR, filename)

if __name__ == '__main__':
    app.run(debug=True)