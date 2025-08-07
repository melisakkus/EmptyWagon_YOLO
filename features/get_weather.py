import os
import requests
from dotenv import load_dotenv

def get_weather(lat: float, lon: float):
    """
    Belirtilen enlem ve boylama göre OpenWeatherMap API'sinden hava durumu bilgisini çeker.
    API anahtarı .env dosyasından okunur.
    """
    load_dotenv()  # .env dosyasını yükle
    api_key = os.getenv("OPENWEATHER_API_KEY")

    if not api_key:
        print("Hata: OPENWEATHER_API_KEY .env dosyasında tanımlı değil.")
        return

    base_url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": api_key,
        "units": "metric"  # Santigrat derece cinsinden almak için
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # HTTP hataları için istisna fırlat

        weather_data = response.json()
        print("Hava Durumu Verileri:")
        print(weather_data)
        return weather_data
    except requests.exceptions.RequestException as e:
        print(f"Hava durumu bilgisi alınırken hata oluştu: {e}")
        return None

if __name__ == '__main__':
    # Örnek kullanım: İstanbul için enlem ve boylam
    istanbul_lat = 41.0082
    istanbul_lon = 28.9784
    get_weather(istanbul_lat, istanbul_lon)

    # Kendi enlem ve boylamınızı girerek test edebilirsiniz
    # get_weather(latitude, longitude)
