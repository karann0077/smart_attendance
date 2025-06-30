import os
import json
import face_recognition
import cv2
from datetime import datetime

#Directories
BASE_DIR  = os.path.dirname(__file__)
KNOWN_DIR = os.path.join(BASE_DIR, "known_faces")
ATT_DIR   = os.path.join(BASE_DIR, "attendance_data")
JSON_PATH = os.path.join(ATT_DIR, "attendance.json")


os.makedirs(KNOWN_DIR, exist_ok=True)
os.makedirs(ATT_DIR, exist_ok=True)

#JSON
def load_attendance():
    try:
        with open(JSON_PATH, 'r') as jf:
            data = json.load(jf)
    except (json.JSONDecodeError, IOError):
        data = []
    if isinstance(data, dict):
        data = [{"date": d, "records": data[d]} for d in data]
    if not isinstance(data, list):
        data = []
    return data


def save_attendance(data):
    print("💾 Writing attendance to JSON...")
    data.sort(key=lambda r: r['date'])
    with open(JSON_PATH, 'w') as jf:
        json.dump(data, jf, indent=2)


def recognize(date_str, capture_duration=30):
    """
    Recognize faces for a fixed duration (in seconds) and record attendance in JSON.
    """
    attendance = load_attendance()
    today = next((r for r in attendance if r['date'] == date_str), None)
    if not today:
        today = {"date": date_str, "records": []}
        attendance.append(today)

    #Load known faces
    known_encodings, known_names = [], []
    for fn in os.listdir(KNOWN_DIR):
        if fn.lower().endswith((".jpg", ".jpeg", ".png")):
            img = face_recognition.load_image_file(os.path.join(KNOWN_DIR, fn))
            encs = face_recognition.face_encodings(img)
            if encs:
                known_encodings.append(encs[0])
                known_names.append(os.path.splitext(fn)[0])

    #Start video capture
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Could not open webcam.")
        return

    present = {e['name'] for e in today['records']}
    start_time = datetime.now()

    try:
        while (datetime.now() - start_time).seconds < capture_duration:
            ret, frame = cap.read()
            if not ret:
                break

          
            small = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

    
            locations = face_recognition.face_locations(rgb)
            encodings = face_recognition.face_encodings(rgb, locations)

            for loc, enc in zip(locations, encodings):
                matches = face_recognition.compare_faces(known_encodings, enc)
                if True in matches:
                    idx = matches.index(True)
                    name = known_names[idx]
                    if name not in present:
                        present.add(name)
                        now = datetime.now().strftime("%H:%M:%S")
                        today['records'].append({"name": name, "time": now})
                
                    top, right, bottom, left = loc
                    top *= 4; right *= 4
                    bottom *= 4; left *= 4
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                    cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)

            cv2.imshow("Attendance", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("User ended capture early.")
                break
    except KeyboardInterrupt:
        print("Interrupted by user, saving attendance.")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        save_attendance(attendance)
        print(f"✅ Attendance saved for {date_str}")


if __name__ == '__main__':
    import sys
    if len(sys.argv) not in (2, 3):
        print("Usage: python main.py YYYY-MM-DD [capture_seconds]")
    else:
        date = sys.argv[1]
        secs = int(sys.argv[2]) if len(sys.argv) == 3 else 30
        recognize(date, capture_duration=secs)
