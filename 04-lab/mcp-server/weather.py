from typing import Any
import asyncio
import httpx
import os
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

# Initialize FastMCP server
port = int(os.getenv("PORT", 8085))
mcp = FastMCP("weather", host="0.0.0.0", port=port)

# Constants
WEATHERAPI_BASE = "https://api.weatherapi.com/v1"
USER_AGENT = "weather-app/1.0"

# Get API key from environment variable or .env
API_KEY = os.getenv("WEATHERAPI_KEY")

async def make_weather_request(endpoint: str, params: dict[str, str]) -> dict[str, Any] | None:
    """Make a request to the WeatherAPI with proper error handling."""
    # Check if API key is set
    if not API_KEY:
        print("ERROR: WeatherAPI key not set. Please set WEATHERAPI_KEY environment variable.")
        return None
        
    headers = {
        "User-Agent": USER_AGENT,
    }
    # Add API key to parameters
    params["key"] = API_KEY
    
    url = f"{WEATHERAPI_BASE}/{endpoint}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params=params, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"HTTP Error {e.response.status_code}: {e.response.text}")
            return None
        except httpx.RequestError as e:
            print(f"Request Error: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None

@mcp.tool()
async def get_current_weather(city: str) -> str:
    """Get current weather conditions for a city.

    Args:
        city: City name (e.g., "Hanoi", "Haiphong", "Danang", "Brisbane", "Sydney")
    """
    params = {
        "q": city,
        "aqi": "no"
    }
    
    data = await make_weather_request("current.json", params)

    if not data:
        city_lower = city.lower().strip()
        demo_db = {
            "hanoi": ("Hanoi", "Ha Noi", "Vietnam", 29.0, 84.2, 32.0, 89.6, "Trời nhiều mây, mưa nhẹ", 80, 12.0, 7.5, "SE", 1010.0, 5.0, 10.0),
            "danang": ("Da Nang", "Da Nang", "Vietnam", 30.0, 86.0, 33.0, 91.4, "Nắng đẹp, thoáng đãng", 75, 10.0, 6.2, "E", 1012.0, 6.0, 10.0),
            "brisbane": ("Brisbane", "Queensland", "Australia", 24.0, 75.2, 25.0, 77.0, "Sunny", 65, 15.0, 9.3, "NE", 1015.0, 7.0, 10.0),
            "sydney": ("Sydney", "New South Wales", "Australia", 22.0, 71.6, 22.0, 71.6, "Clear", 60, 18.0, 11.2, "S", 1018.0, 6.0, 10.0),
            "tokyo": ("Tokyo", "Tokyo", "Japan", 19.0, 66.2, 19.0, 66.2, "Clear", 55, 8.0, 5.0, "N", 1020.0, 4.0, 10.0),
            "new york": ("New York", "New York", "USA", 16.0, 60.8, 16.0, 60.8, "Cloudy", 50, 14.0, 8.7, "W", 1016.0, 3.0, 10.0),
        }
        if not API_KEY and city_lower in demo_db:
            name, reg, cntry, tc, tf, flc, flf, cond, hum, wk, wm, wd, pr, uv, vis = demo_db[city_lower]
            return f"""Current Weather for {name}, {reg}, {cntry} (Demo mode):

Temperature: {tc}°C ({tf}°F)
Feels like: {flc}°C ({flf}°F)
Condition: {cond}
Humidity: {hum}%
Wind: {wk} km/h ({wm} mph) {wd}
Pressure: {pr} mb
UV Index: {uv}
Visibility: {vis} km

Note: Set WEATHERAPI_KEY in .env or environment for real-time live data from WeatherAPI.com."""

        if not API_KEY:
            return f"❌ WeatherAPI key not configured. Please set WEATHERAPI_KEY environment variable with your API key from weatherapi.com"
        return f"Unable to fetch current weather data for {city}. Please check the city name and API key configuration."

    current = data["current"]
    location = data["location"]
    
    return f"""
Current Weather for {location['name']}, {location['region']}, {location['country']}:

Temperature: {current['temp_c']}°C ({current['temp_f']}°F)
Feels like: {current['feelslike_c']}°C ({current['feelslike_f']}°F)
Condition: {current['condition']['text']}
Humidity: {current['humidity']}%
Wind: {current['wind_kph']} km/h ({current['wind_mph']} mph) {current['wind_dir']}
Pressure: {current['pressure_mb']} mb
UV Index: {current['uv']}
Visibility: {current['vis_km']} km

Last updated: {current['last_updated']}
"""

@mcp.tool()
async def get_forecast(city: str, days: int = 3) -> str:
    """Get weather forecast for a city.

    Args:
        city: City name (e.g., "Hanoi", "Haiphong", "Danang", "Brisbane", "Sydney", "Melbourne")
        days: Number of days to forecast (1-3 for free tier, max 10 for paid)
    """
    # Limit days to 3 for free tier
    days = min(days, 3)
    
    params = {
        "q": city,
        "days": str(days),
        "aqi": "no",
        "alerts": "no"
    }
    
    data = await make_weather_request("forecast.json", params)

    if not data:
        city_lower = city.lower().strip()
        demo_forecast_cities = {
            "hanoi": ("Hanoi", "Ha Noi", "Vietnam", [
                ("2026-10-14", 30.0, 86.0, 24.0, 75.2, "Mưa nhẹ rải rác", 65, 12.0, 4.0),
                ("2026-10-15", 31.0, 87.8, 25.0, 77.0, "Nhiều mây, trưa chiều có nắng", 30, 10.0, 6.0),
                ("2026-10-16", 29.0, 84.2, 23.0, 73.4, "Mưa rào và dông", 80, 15.0, 3.0),
            ]),
            "danang": ("Da Nang", "Da Nang", "Vietnam", [
                ("2026-10-14", 31.0, 87.8, 26.0, 78.8, "Nắng đẹp", 10, 10.0, 7.0),
                ("2026-10-15", 32.0, 89.6, 26.0, 78.8, "Nắng nóng nhẹ", 15, 12.0, 7.0),
                ("2026-10-16", 30.0, 86.0, 25.0, 77.0, "Có mây thay đổi", 25, 11.0, 6.0),
            ]),
            "brisbane": ("Brisbane", "Queensland", "Australia", [
                ("2026-10-14", 25.0, 77.0, 16.0, 60.8, "Sunny and pleasant", 10, 15.0, 7.0),
                ("2026-10-15", 26.0, 78.8, 17.0, 62.6, "Clear skies", 5, 14.0, 8.0),
                ("2026-10-16", 24.0, 75.2, 18.0, 64.4, "Partly cloudy", 20, 16.0, 6.0),
            ]),
            "tokyo": ("Tokyo", "Tokyo", "Japan", [
                ("2026-10-14", 20.0, 68.0, 14.0, 57.2, "Clear", 0, 8.0, 5.0),
                ("2026-10-15", 21.0, 69.8, 15.0, 59.0, "Sunny", 10, 9.0, 5.0),
                ("2026-10-16", 18.0, 64.4, 13.0, 55.4, "Light rain", 70, 12.0, 3.0),
            ]),
        }
        if not API_KEY and city_lower in demo_forecast_cities:
            loc_name, loc_reg, loc_cntry, dlist = demo_forecast_cities[city_lower]
            forecasts = [f"Weather Forecast for {loc_name}, {loc_reg}, {loc_cntry} (Demo mode):"]
            for date_str, mx_c, mx_f, mn_c, mn_f, c_txt, ch_rain, m_wind, uvi in dlist[:days]:
                f_entry = f"""
{date_str}:
High: {mx_c}°C ({mx_f}°F)
Low: {mn_c}°C ({mn_f}°F)
Condition: {c_txt}
Chance of Rain: {ch_rain}%
Max Wind: {m_wind} km/h
UV Index: {uvi}
"""
                forecasts.append(f_entry)
            forecasts.append("\nNote: Set WEATHERAPI_KEY in .env or environment for real-time live data from WeatherAPI.com.")
            return "\n---\n".join(forecasts)

        if not API_KEY:
            return f"❌ WeatherAPI key not configured. Please set WEATHERAPI_KEY environment variable with your API key from weatherapi.com"
        return f"Unable to fetch forecast data for {city}. Please check the city name and API key configuration."

    location = data["location"]
    forecast_days = data["forecast"]["forecastday"]
    
    forecasts = []
    forecasts.append(f"Weather Forecast for {location['name']}, {location['region']}, {location['country']}:")
    
    for day in forecast_days:
        day_data = day["day"]
        date = day["date"]
        
        forecast = f"""
{date}:
High: {day_data['maxtemp_c']}°C ({day_data['maxtemp_f']}°F)
Low: {day_data['mintemp_c']}°C ({day_data['mintemp_f']}°F)
Condition: {day_data['condition']['text']}
Chance of Rain: {day_data['daily_chance_of_rain']}%
Max Wind: {day_data['maxwind_kph']} km/h
UV Index: {day_data['uv']}
"""
        forecasts.append(forecast)

    return "\n---\n".join(forecasts)

@mcp.tool()
async def health_check() -> str:
    """Health check endpoint for deployment verification."""
    return "✅ Weather MCP Server is running! Ready to provide weather data for Australian cities and worldwide."

print("✅ MCP server initialized with Streamable HTTP transport")
print("🔧 Available tools: get_current_weather, get_forecast, health_check")

if __name__ == "__main__":
    import sys
    
    if "--stdio" in sys.argv:
        print("Starting FastMCP server in stdio mode for local client", file=sys.stderr)
        mcp.run()
    else:
        print(f"🚀 Starting MCP server on http://0.0.0.0:{port}/mcp")
        mcp.run(transport="streamable-http")