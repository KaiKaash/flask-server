from flask import Flask, jsonify
import serial
import time
import sys
import csv
import os
import threading

# Flask application for CanSat backend
from flask_cors import CORS
app = Flask(__name__)
CORS(app)  # enable all origins for testing
# Initialize serial port and CSV file
ser = None
latest_data = {}

CSV_FILE = "data_log.csv"
CSV_HEADERS = [
    "Time", "Latitude", "Longitude", "Altitude", "Speed", "Heading", "GPS_Lock",
    "AccX", "AccY", "AccZ", "MagX", "MagY", "MagZ", "GyroX", "GyroY", "GyroZ",
    "Pressure", "Altitude_Baro", "Temperature_DHT", "Humidity_DHT"
]

def init_serial():
    global ser
    try:
        ser = serial.Serial('COM7', 115200, timeout=1)  
        print(f"[INFO] Serial port {ser.port} opened")
        time.sleep(2)
    except serial.SerialException as e:
        print(f"[ERROR] Serial port failed: {e}", file=sys.stderr)
        sys.exit(1)

def create_csv_if_needed():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)
        print("[INFO] CSV created with headers")

def serial_reader():
    global ser, latest_data
    print("[INFO] Serial reader thread started")
    while True:
        if ser and ser.in_waiting > 0:
            try:
                line = ser.readline().decode('utf-8').strip()
                if line.startswith("Received:"):
                    line = line.replace("Received:", "", 1).strip()

                parts = line.split(',')
                if len(parts) >= 20:
                    data = {CSV_HEADERS[i]: parts[i] for i in range(20)}
                    latest_data = data

                    with open(CSV_FILE, mode='a', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow([data[key] for key in CSV_HEADERS])

                    print(f"[LOG] Logged: {data['Time']}")
                else:
                    print(f"[WARN] Malformed line ({len(parts)} fields): {line}")
            except Exception as e:
                print(f"[ERROR] Serial read error: {e}")
        else:
            time.sleep(0.1)

@app.route("/")
def home():
    return jsonify({"message": "CanSat backend is running!"})

@app.route("/status")
def status():
    return jsonify({"serial_open": ser.is_open if ser else False})

@app.route("/data")
def get_data():
    if latest_data:
        return jsonify(latest_data)
    else:
        return jsonify({"message": "No data available yet"})

if __name__ == "__main__":
    init_serial()
    create_csv_if_needed()
    threading.Thread(target=serial_reader, daemon=True).start()
    app.run(debug=True, use_reloader=False)