import requests
import json
from datetime import datetime
import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import time

# Load environment variables from .env file
load_dotenv()

# https://swd.weatherflow.com/swd/rest/observations/station/164312?token=3a75ad3e-5b0d-4f72-9220-b2a7f3ee27e3
# https://swd.weatherflow.com/swd/rest/observations/station/00166889?token=3a75ad3e-5b0d-4f72-9220-b2a7f3ee27e3
class TempestWeather:
    BASE_URL = "https://swd.weatherflow.com/swd/rest"
    
    def __init__(self, api_key: str, station_id: str):
        """Initialize with API key and station ID."""
        self.api_key = api_key
        self.station_id = station_id
        
    def get_current_conditions(self) -> Optional[Dict[str, Any]]:
        """
        Fetch current weather conditions from the Tempest API.
        Returns None if the request fails.
        """
        endpoint = f"{self.BASE_URL}/observations/station/{self.station_id}"
        
        params = {
            "token": self.api_key
        }
        
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching weather data: {e}")
            return None

    def get_wind_reading(self) -> None:
        """Fetch and display the current wind conditions."""
        data = self.get_current_conditions()
        
        if not data:
            print("Unable to fetch wind data")
            return
            
        try:
            # Extract wind data from the observation data
            obs = data.get('obs', [{}])[0]  # Get the latest observation
            
            # Get wind speed (convert m/s to mph)
            wind_speed_ms = obs.get('wind_avg', 0)
            wind_speed_mph = wind_speed_ms * 2.237  # Convert m/s to mph
            
            # NEW: Get wind gust speed
            wind_gust_ms = obs.get('wind_gust', 0)
            wind_gust_mph = wind_gust_ms * 2.237  # Convert m/s to mph
            
            # Get wind direction in degrees
            wind_direction = obs.get('wind_direction', 0)
            
            # Convert direction to cardinal directions
            cardinal_directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                                 "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
            cardinal_index = round(wind_direction / 22.5) % 16
            cardinal_direction = cardinal_directions[cardinal_index]
            
            # Get timestamp
            timestamp = datetime.now().strftime('%H:%M:%S')
            
            # NEW: Updated print statement to include gust speed
            print(f"[{timestamp}] Wind Speed: {wind_speed_mph:.1f} mph, Gusts: {wind_gust_mph:.1f} mph, Direction: {cardinal_direction} ({wind_direction:.0f}°)")
            
        except (KeyError, IndexError) as e:
            print(f"Error parsing wind data: {e}")
    def get_temperature(self) -> None:
        """Fetch and display the current temperature."""
        data = self.get_current_conditions()
        
        if not data:
            print("Unable to fetch temperature data")
            return
        
        try:
            # Extract temperature data from the observation data
            obs = data.get('obs', [{}])[0]  # Get the latest observation
            
            # Get temperature (in Celsius by default)
            temperature_celsius = obs.get('air_temperature', None)
            
            if temperature_celsius is None:
                print("Temperature data not available")
                return
            
            # Optionally convert to Fahrenheit
            temperature_fahrenheit = (temperature_celsius * 9/5) + 32
            
            # Get timestamp
            timestamp = datetime.now().strftime('%H:%M:%S')
            
            # Display temperature
            print(f"[{timestamp}] Temperature: {temperature_celsius:.1f}°C / {temperature_fahrenheit:.1f}°F")
        
        except (KeyError, IndexError) as e:
            print(f"Error parsing temperature data: {e}")

def main():
    # Get API key and station ID from environment variables
    api_key = os.getenv("TEMPEST_API_KEY")
    station_id = os.getenv("TEMPEST_STATION_ID")
    
    if not api_key or not station_id:
        print("Please set TEMPEST_API_KEY and TEMPEST_STATION_ID in your .env file")
        return
    
    # Create weather object
    weather = TempestWeather(api_key, station_id)
    
    print("Starting wind monitoring for 60 seconds...")
    start_time = time.time()
    
    try:
        while time.time() - start_time < 60:  # Run for 60 seconds
            weather.get_wind_reading()
            weather.get_temperature()
            time.sleep(1)  # Wait 1 second before next reading
            
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")
    
    print("Monitoring complete")

if __name__ == "__main__":
    main()