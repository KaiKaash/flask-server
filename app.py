# app.py
# This script is deployed to Render. It has no access to local serial ports.

from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)

# For production, you should restrict this to your frontend's actual domain
# For now, allowing all is fine for testing.
CORS(app) 

# --- IN-MEMORY DATABASE ---
# This dictionary will store the most recent data received from your gateway.
# IMPORTANT: This data will be LOST if your Render instance restarts.
# For a robust application, you should use a real database like PostgreSQL.
latest_data = {}
data_log = [] # Optional: keep a log of the last N readings in memory

@app.route("/")
def home():
    """A simple endpoint to check if the server is alive."""
    return jsonify({
        "message": "CanSat Cloud Backend is running!",
        "endpoints": {
            "/api/latest-data": "GET the most recent data point.",
            "/api/log": "POST new data points here from the gateway."
        }
    })

@app.route("/api/latest-data", methods=['GET'])
def get_latest_data():
    """Endpoint for your frontend web app to get the latest data."""
    if latest_data:
        return jsonify(latest_data)
    else:
        return jsonify({"error": "No data has been received yet."}), 404

@app.route("/api/log", methods=['POST'])
def log_new_data():
    """
    Endpoint for your local gateway.py script to send new data.
    This endpoint is the new heart of the application.
    """
    global latest_data, data_log
    
    # Get the JSON data sent from the gateway
    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid request. No JSON data received."}), 400
    
    # Update the global 'latest_data' dictionary with the new data
    latest_data = data
    
    # Optional: Add to an in-memory log (e.g., last 100 readings)
    data_log.append(data)
    if len(data_log) > 100:
        data_log.pop(0) # Keep the log from growing indefinitely

    print(f"[DATA RECEIVED] New data logged for Time: {data.get('Time', 'N/A')}")
    
    # Return a success message
    return jsonify({"message": "Data logged successfully"}), 201

# This block is for local testing only.
# Gunicorn on Render will not use this.
if __name__ == "__main__":
    # Note: Running this locally won't receive data unless you also run the gateway.py
    # and point its RENDER_API_URL to http://127.0.0.1:5000/api/log
    app.run(host='0.0.0.0', debug=True)
