import json
from flask import Flask, render_template, redirect, request, session, jsonify
import requests
from flask_session import Session
from flask_socketio import SocketIO
from random import random
from threading import Lock
from datetime import datetime
import csv
import time
"""
Background Thread
"""
thread = None
thread_lock = Lock()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'donsky!'
socketio = SocketIO(app, cors_allowed_origins='*')

"""
Get current date time
"""
def get_current_datetime():
    now = datetime.now()
    return now.strftime("%H:%M:%S")


def background_thread():
    print("Sensor Data Thread Started...") 
    while True:
        with open('PdM_telemetry.csv', 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                time_stamp = row[0]
                volt_sensor_value = float(row[2])
                rotate_sensor_value = float(row[3])
                pressure_sensor_value = float(row[4])
                vibration_sensor_value = float(row[5])


                socketio.emit('updateSensorData', {
                    'volt_value':volt_sensor_value,
                    "time_stamp": time_stamp,
                    "rotate_value":rotate_sensor_value,
                    "pressure_value":pressure_sensor_value,
                    "vibration_value":vibration_sensor_value
                    })
                socketio.sleep(2)

"""
Serve root index file
"""

@app.route("/", methods=["POST", "GET"])
def index():
    if not session.get("userWID"):
        return redirect("/login")
    return render_template('index.html')



 
 
@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        session["userWID"] = request.form.get("userWID")
        return redirect("/")
    return render_template("login.html")
 
 
@app.route("/logout")
def logout():
    session["userWID"] = None
    session["machineID"] = None
    return redirect("/")

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/machineRegistration')
def machineRegistration():
    return render_template('machineRegistration.html')

@app.route('/machineDashboard' , methods=["POST", "GET"])
def machineDashboard():
    if request.method == "POST":
        session["machineID"] = request.form.get("machineID")
        return render_template('machineDashboard.html')

@app.route('/getInfo' , methods=["POST", "GET"])
def getInfo():
    if request.method == "GET":
        info = {
            "machineID": session["machineID"],
            "userWID": session["userWID"]
        }
        return jsonify(info)

@app.route('/getLastTransaction/<address>', methods=["POST", "GET"])
def getLastTransaction(address):
    machineContractAddress = address
    print(machineContractAddress)
    url = "https://console.kaleido.io/api/v1/ledger/u0sdbvxn14/u0anrngbym/addresses/"+machineContractAddress+"/transactions?limit=1"
    payload={}
    headers = {
    'Authorization': 'Bearer u0bt01lis8-YaONAPbJ287Vj4FhH06clwCQRse+dPwwKrPhlpuWpkQ='
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    print(response.json)
    return response.json()



"""
Decorator for connect
"""
@socketio.on('connect')
def connect():
    global thread
    print('Client connected')

    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(background_thread)

"""
Decorator for disconnect
"""
@socketio.on('disconnect')
def disconnect():
    print('Client disconnected',  request.sid)

if __name__ == '__main__':
    socketio.run(app)