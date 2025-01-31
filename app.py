import socket
import json
import os
import struct
from dotenv import load_dotenv
import time

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
                # Receive data from the hub (increase buffer size to 4096 bytes)
                data, address = sock.recvfrom(4096)  # Increased buffer size
                
                # Debugging: Print the raw data
                print(f"Received raw data: {data}")
                
                # Decode and process the data (usually JSON format)
                try:
                    json_data = json.loads(data.decode('utf-8'))
                    # Check the type of message and process accordingly
                    if json_data.get("type") == "obs_st":
                        self.process_weather_data(json_data)
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON data: {e}")
                    
        except KeyboardInterrupt:
            print("Listening for data stopped by user")
        finally:
            sock.close()

    def process_weather_data(self, data):
        """Process and display the weather data."""
        if "obs" in data:
            obs_data = data["obs"][0]  # Get the first observation (latest data)
            
            # Parse the weather data
            timestamp = obs_data[0]
            wind_lull = obs_data[1]
            wind_avg = obs_data[2]
            wind_gust = obs_data[3]
            wind_direction = obs_data[4]
            air_temperature = obs_data[7]
            
            # Print out the weather data
            print(f"Timestamp: {timestamp}")
            print(f"Wind Lull: {wind_lull} m/s")
            print(f"Wind Avg: {wind_avg} m/s")
            print(f"Wind Gust: {wind_gust} m/s")
            print(f"Wind Direction: {wind_direction}°")
            print(f"Air Temperature: {air_temperature}°C")


def main():
    # Get the Hub IP from the environment variable
    hub_ip = os.getenv("TEMPEST_HUB_IP")
    
    if not hub_ip:
        print("Please set TEMPEST_HUB_IP in your .env file")
        return
    
    # Create weather object
    weather = TempestWeather(hub_ip)
    
    print("Starting UDP listening for weather data...")
    weather.listen_for_data()

if __name__ == "__main__":
    main()
