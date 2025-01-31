import socket
import json
import os
import struct
from dotenv import load_dotenv
import time
from threading import Thread

# Load environment variables from .env file
load_dotenv()

class TempestWeather:
    def __init__(self, hub_ip: str, hub_port: int = 50222):
        """Initialize with Hub IP address and port."""
        self.hub_ip = hub_ip
        self.hub_port = hub_port
        self.multicast_group = "239.255.255.250"
        
    def listen_for_data(self):
        """Listen for UDP multicast data from Tempest Hub."""
        # Create the socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        
        # Set the socket to allow broadcast and reuse address/port
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)  # Allow reuse of port
        
        # Bind to the multicast group address
        sock.bind(("", self.hub_port))
        
        # Join the multicast group
        group = socket.inet_aton(self.multicast_group)
        mreq = struct.pack("4sL", group, socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        
        try:
            while True:
                # Receive data from the hub (increased buffer size to 4096 bytes)
                data, address = sock.recvfrom(4096)
                
                # Debugging: Print the raw data
                # print(f"Received raw data: {data}")
                
                # Decode and process the data (usually JSON format)
                try:
                    json_data = json.loads(data.decode('utf-8'))
                    # Check for specific message types and process accordingly
                    if json_data.get("type") == "rapid_wind":
                        self.process_wind_gust_data(json_data)
                    elif json_data.get("type") == "obs_st":
                        self.process_weather_data(json_data)
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON data: {e}")
            
        except KeyboardInterrupt:
            print("Listening for data stopped by user")
        finally:
            sock.close()

    def process_wind_gust_data(self, data):
        """Process and display wind gust data in Imperial units."""
        if "ob" in data:
            wind_gust_mps = data["ob"][1]  # Wind gust in meters per second
            wind_gust_direction = data["ob"][2]  # Wind gust in meters per second
            
            # Convert to Imperial units (m/s to mph)
            wind_gust_mph = wind_gust_mps * 2.23694
            
            # Print the wind gust data
            print("<---------------------------->")
            print(f"Wind Gust: {wind_gust_mph:.1f} mph - {wind_gust_direction} ")
            print("<---------------------------->")
    
    def process_weather_data(self, data):
        """Process and display general weather data (e.g., wind avg, temperature)."""
        if "obs" in data:
            obs_data = data["obs"][0]  # Get the first observation (latest data)
            
            # Parse the weather data
            timestamp = obs_data[0]
            wind_avg_mps = obs_data[2]
            air_temperature_celsius = obs_data[7]
            
            # Convert units to Imperial:
            # Wind speed (m/s to mph)
            wind_avg_mph = wind_avg_mps * 2.237
            
            # Air temperature (Celsius to Fahrenheit)
            air_temperature_fahrenheit = (air_temperature_celsius * 9/5) + 32
            
            # Convert the timestamp from epoch seconds to human-readable format
            from datetime import datetime
            timestamp = datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
            
            # Print out the weather data
            print(f"Timestamp: {timestamp}")
            print(f"Wind Avg: {wind_avg_mph:.1f} mph")
            print(f"Air Temperature: {air_temperature_fahrenheit:.1f}°F")
            print("----------------------------")

# Run the UDP listener in a separate thread
def main():
    # Get the Hub IP from the environment variable
    hub_ip = os.getenv("TEMPEST_HUB_IP")
    
    if not hub_ip:
        print("Please set TEMPEST_HUB_IP in your .env file")
        return
    
    # Create weather object
    weather = TempestWeather(hub_ip)
    
    # Start listening for data in a separate thread
    listening_thread = Thread(target=weather.listen_for_data)
    listening_thread.daemon = True
    listening_thread.start()
    
    # Run other tasks (e.g., additional data processing or logging)
    try:
        while True:
            time.sleep(1)  # Keep the main thread alive
    except KeyboardInterrupt:
        print("Main program stopped by user")

if __name__ == "__main__":
    main()
