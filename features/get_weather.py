import os
import requests
from dotenv import load_dotenv


def get_weather(lat: float, lon: float):
    """
    Belirtilen enlem ve boylama göre OpenWeatherMap API'sinden hava durumu bilgisini çeker.
    API anahtarı önce Streamlit secrets'tan, sonra .env dosyasından okunur.
    """
    api_key = None

    # Önce Streamlit secrets'tan dene
    try:
        import streamlit as st
        api_key = st.secrets["OPENWEATHER_API_KEY"]
        print("API key Streamlit secrets'tan alındı")
    except (ImportError, KeyError, FileNotFoundError, AttributeError) as e:
        print(f"Streamlit secrets'tan API key alınamadı: {e}")
        # Streamlit yoksa veya secret bulunamazsa .env'den dene
        load_dotenv()
        api_key = os.getenv("OPENWEATHER_API_KEY")
        if api_key:
            print("API key .env dosyasından alındı")

    if not api_key:
        print("Hata: OPENWEATHER_API_KEY ne secrets'ta ne de .env dosyasında tanımlı.")
        return None

    # API key'in ilk ve son birkaç karakterini göster (güvenlik için)
    print(f"API key bulundu: {api_key[:8]}...{api_key[-4:]}")

    base_url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": api_key,
        "units": "metric"  # Santigrat derece cinsinden almak için
    }

    print(f"API çağrısı yapılıyor: {base_url}")
    print(f"Parametreler: lat={lat}, lon={lon}")

    try:
        response = requests.get(base_url, params=params)
        print(f"HTTP Status Code: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")

        # Yanıtı yazdır (hata ayıklama için)
        print(f"Response text: {response.text[:500]}...")

        response.raise_for_status()  # HTTP hataları için istisna fırlat
        weather_data = response.json()

        # Beklenen anahtarların varlığını kontrol et
        required_keys = ['main', 'weather', 'wind', 'name']
        missing_keys = [key for key in required_keys if key not in weather_data]
        if missing_keys:
            print(f"Eksik anahtarlar: {missing_keys}")
            print(f"Mevcut anahtarlar: {list(weather_data.keys())}")
            return None

        print("Hava durumu başarıyla alındı")
        return weather_data

    except requests.exceptions.HTTPError as e:
        print(f"HTTP hatası: {e}")
        print(f"Response content: {response.text}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"İstek hatası: {e}")
        return None
    except ValueError as e:
        print(f"JSON parse hatası: {e}")
        print(f"Response content: {response.text}")
        return None
    except Exception as e:
        print(f"Beklenmeyen hata: {e}")
        return None


if __name__ == '__main__':
    # Test için
    ankara_lat = 39.9334
    ankara_lon = 32.8597
    result = get_weather(ankara_lat, ankara_lon)
    if result:
        print("Başarılı!")
        print(f"Şehir: {result['name']}")
        print(f"Sıcaklık: {result['main']['temp']}°C")
    else:
        print("Başarısız!")