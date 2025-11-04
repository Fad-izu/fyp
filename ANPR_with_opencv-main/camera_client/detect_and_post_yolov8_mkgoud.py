import cv2
import serial
import time
import requests
from ultralytics import YOLO
import torch
import easyocr

# =====================================================
# CONFIGURATION
# =====================================================
MODEL_PATH = "best.pt"   # YOLOv8 model for Malaysian plates
BACKEND_URL = "http://127.0.0.1:5000/api/log_detection"
SERIAL_PORT = "COM5"     # Change this to your Arduino COM port
BAUD_RATE = 9600
DETECTION_COOLDOWN = 3   # seconds between same-plate submissions

# =====================================================
# INITIALIZATION
# =====================================================
print("🚀 Starting YOLOv8 + EasyOCR License Plate Recognition")

device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"🧠 Using device: {device}")
model = YOLO(MODEL_PATH)

# Initialize OCR reader
reader = easyocr.Reader(['en'], gpu=torch.cuda.is_available())

# Initialize webcam
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
if not cap.isOpened():
    raise Exception("❌ Webcam not detected!")

# Initialize Arduino
arduino = None
try:
    arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)
    print("✅ Arduino connected successfully.")
except Exception as e:
    print(f"⚠️ Arduino not connected: {e}")

# =====================================================
# FUNCTION: Send Detected Plate to Flask
# =====================================================
def send_plate_to_backend(plate_number):
    """Send plate number to Flask backend with retry logic"""
    for attempt in range(3):
        try:
            response = requests.post(
                BACKEND_URL,
                json={"plate_number": plate_number},
                headers={"Content-Type": "application/json"},
                timeout=2
            )
            if response.status_code == 200:
                data = response.json()
                print(f"📨 Backend: {data}")
                return data.get("status", "DENIED")
            else:
                print(f"⚠️ Server error: {response.status_code}")
        except Exception as e:
            print(f"❌ Error connecting to backend (attempt {attempt+1}/3): {e}")
            time.sleep(0.5)
    return "DENIED"

# =====================================================
# FUNCTION: OCR Plate Text
# =====================================================
def extract_plate_text(image):
    """Extract text from the detected plate region using EasyOCR"""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    results = reader.readtext(gray)
    if results:
        text = " ".join([res[1] for res in results])
        text = text.replace(" ", "").upper()
        return text
    return None

# =====================================================
# MAIN LOOP
# =====================================================
last_detected = {}

while True:
    ret, frame = cap.read()
    if not ret:
        print("⚠️ Camera frame not captured.")
        break

    results = model(frame, verbose=False)
    annotated_frame = frame.copy()

    for result in results:
        boxes = result.boxes
        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])
            if conf < 0.5:
                continue

            plate_crop = frame[y1:y2, x1:x2]
            plate_text = extract_plate_text(plate_crop)

            if plate_text:
                now = time.time()
                if plate_text in last_detected and now - last_detected[plate_text] < DETECTION_COOLDOWN:
                    continue
                last_detected[plate_text] = now

                print(f"🔍 Detected Plate: {plate_text}")

                # Send plate to Flask backend
                status = send_plate_to_backend(plate_text)

                # Send to Arduino
                if arduino:
                    arduino.write((status + "\n").encode())
                    print(f"➡️ Sent to Arduino: {status}")

                # Draw annotations
                color = (0, 255, 0) if status == "GRANTED" else (0, 0, 255)
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(annotated_frame, plate_text, (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
                cv2.putText(annotated_frame, status, (x1, y2 + 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

    annotated_frame = cv2.resize(annotated_frame, (640, 400))
    cv2.imshow("YOLOv8 + EasyOCR ANPR", annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# =====================================================
# CLEANUP
# =====================================================
cap.release()
cv2.destroyAllWindows()
if arduino:
    arduino.close()
print("🛑 Program stopped successfully.")
