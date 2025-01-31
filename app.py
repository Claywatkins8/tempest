from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import socket
import json
import os
import struct
from threading import Thread

# Initialize Flask app and Flask-SocketIO
app = Flask(__name__)
socketio = SocketIO(app)

# Initialize weather data (will be updated with the latest data)
weather_data = {
    "wind_gust_mph": 0,
    "wind_direction": "N",
    "temperature_fahrenheit": 0
}

# Multicast group and port for Tempest Hub
MULTICAST_GROUP = "239.255.255.250"
PORT = 50222

def listen_for_data():
    """Listen for UDP multicast data from Tempest Hub and update weather_data."""
    global weather_data

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    sock.bind(("", PORT))

    group = socket.inet_aton(MULTICAST_GROUP)
    mreq = struct.pack("4sL", group, socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    try:
        while True:
            data, _ = sock.recvfrom(4096)
            json_data = json.loads(data.decode('utf-8'))

            if json_data.get("type") == "rapid_wind":
                # Process rapid_wind data (wind gust and direction)
                wind_gust_mps = json_data["ob"][1]
                wind_gust_mph = wind_gust_mps * 2.23694
                wind_direction = json_data["ob"][2]
                cardinal_direction = get_cardinal_direction(wind_direction)

                # Update weather_data for rapid_wind
                weather_data = {
                    "wind_gust_mph": round(wind_gust_mph, 2),
                    "cardinal_direction": cardinal_direction,
                    "wind_direction": wind_direction,
                    "temperature_fahrenheit": None  # No temperature data for rapid_wind
                }

                # Emit the updated weather data to the frontend using WebSocket
                socketio.emit('weather_update', weather_data)

            elif json_data.get("type") == "obs_st":
                # Extract temperature from the first observation (index 7)
                temperature_celsius = json_data["obs"][0][7]
                temperature_fahrenheit = (temperature_celsius * 9/5) + 32

                # Update weather_data with temperature from obs_st
                weather_data["temperature_fahrenheit"] = round(temperature_fahrenheit, 2)

                # Emit the updated weather data to the frontend using WebSocket
                socketio.emit('weather_update', weather_data)

    except KeyboardInterrupt:
        print("Data listening stopped.")
    finally:
        sock.close()

def get_cardinal_direction(degrees):
    """Convert wind direction in degrees to cardinal direction."""
    cardinal_directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", 
                           "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    cardinal_index = round(degrees / 22.5) % 16
    return cardinal_directions[cardinal_index]

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

if __name__ == "__main__":
    # Start the data listener in a separate thread
    data_thread = Thread(target=listen_for_data)
    data_thread.daemon = True
    data_thread.start()

    # Run the Flask server with WebSocket support
    socketio.run(app, debug=True, host="0.0.0.0", port=8081)
