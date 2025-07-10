from flask import Flask, render_template, request, jsonify
import time
from threading import Thread
from w1thermsensor import W1ThermSensor
import plotly.graph_objs as go
import plotly
import json
from simple_pid import PID
import RPi.GPIO as GPIO



app = Flask(__name__)

# Setup the temperature sensor
sensor = W1ThermSensor()

# Global variables for temperature readings and history
temperature_history = []
setpoint_history = []
time_history = []
setpoint = 25.0  # Default setpoint in Celsius
PWMsetpoint = 0  # PWM vallue in %
PWMactive = 0    # 0 when PID mode is active, 1 when PWM mode is active. 

#setting up the pid controller 
pid = PID(40, 0.05, 0.0, setpoint=setpoint)
pid.output_limits = (0, 100)    # Output value will be between 0 and 100 PWM
pid.sample_time = 1

#setting up PWM for controlling SSR 
GPIO.setmode(GPIO.BOARD)
GPIO.setup(12, GPIO.OUT)

# Function to read temperature every second
def read_temperature():
    global setpoint
    global PWMsetpoint
    global PWMactive

    p = GPIO.PWM(12, 0.5)
    p.start(1);

    while True:
        # Read the current temperature
        temperature = sensor.get_temperature()
        current_time = time.time()
        Setp = setpoint

        print("setpoint = %d",setpoint)
        # Append the temperature and timestamp to the history
        temperature_history.append(temperature)
        time_history.append(current_time)
        setpoint_history.append(Setp)

        # Limit the history to the last 50 readings
        if len(temperature_history) > 50:
            temperature_history.pop(0)
            setpoint_history.pop(0)
            time_history.pop(0)
        
        if PWMactive = 0
            #pid controller
            pid.setpoint = Setp
            error = pid(temperature)
            #PWM
            p.ChangeDutyCycle(error)
            print("error = %d",error)
        else
            p.ChangeDutyCycle(PWMsetpoint)

        # Wait for one second before reading again
        time.sleep(1)

# Start the background thread for reading temperature
@app.before_first_request
def start_background_thread():
    thread = Thread(target=read_temperature)
    thread.daemon = True
    thread.start()

@app.route('/')
def index():
    
    # Get the most recent temperature and setpoint from the sensor (updated every second)
    temperature = temperature_history[-1] if temperature_history else None
    setpoint = setpoint_history[-1] if setpoint_history else None

    # Create the Plotly graph
    trace = go.Scatter(
        x=time_history,
        y=temperature_history,
        mode='lines',
        name='Temperature (°C)'
    )

    # Add a horizontal line for the setpoint
    setpoint_trace = go.Scatter(
        x=time_history,
        y=setpoint_history,
        mode='lines',
        name=f'Setpoint (°C)',
        line=dict(dash='dash', color='red')  # Dashed red line for setpoint
    )

    layout = go.Layout(
        title="Temperature vs Time",
        xaxis={'title': 'Time (s)'},
        yaxis={'title': 'Temperature (°C)'},
        yaxis2={'title': 'Setpoint (°C)'},
        showlegend=True
    )

    figure = go.Figure(data=[trace, setpoint_trace], layout=layout)

    # Convert Plotly graph to JSON
    graphJSON = json.dumps(figure, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template('index.html', temperature=temperature, graphJSON=graphJSON, setpoint=setpoint)

@app.route('/setpoint', methods=['POST'])
def set_setpoint():
    global setpoint
    global PWMactive
    # Get the setpoint from the form (ensure it's converted to a float)
    try:
        setpoint = float(request.form['setpoint'])
        PWMactive = 0
        return jsonify({'status': 'success', 'setpoint': setpoint})
    except ValueError:
        return jsonify({'status': 'error', 'message': 'Invalid setpoint value'}), 400

@app.route('/PWMsetpoint', methods=['POST'])
def set_PWMsetpoint():
    global PWMsetpoint
    global PWMactive
    # Get the setpoint from the form (ensure it's converted to a float)
    try:
        setpoint = float(request.form['setpoint'])
        PWMactive = 1
        return jsonify({'status': 'success', 'setpoint': setpoint})
    except ValueError:



@app.route('/temperature_data', methods=['GET'])
def get_temperature_data():
    # Return the current temperature and time history in JSON format
    return jsonify({
        'time': time_history,
        'temperature': temperature_history,
        'setpoint': setpoint_history
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
