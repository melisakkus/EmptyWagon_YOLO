import requests
import os # os modülü hata ayıklama mesajları için tutulabilir ama artık doğrudan kullanılmayacak

def get_weather(lat: float, lon: float, api_key: str): # api_key parametresini ekledik
    """
    Belirtilen enlem ve boylama göre OpenWeatherMap API'sinden hava durumu bilgisini çeker.
    API anahtarı bir parametre olarak sağlanmalıdır.
    """
    if not api_key:
        print("Hata: OPENWEATHER_API_KEY sağlanmadı.")
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

# __name__ == '__main__': bloğunu isterseniz kaldırabilirsiniz,
# veya test için api_key'i manuel olarak tanımlamanız gerekir.
# Test için:
if __name__ == '__main__':
    # .env dosyasından anahtarı okuyarak test edebilirsiniz
    from dotenv import load_dotenv
    load_dotenv()
    test_api_key = os.getenv("OPENWEATHER_API_KEY")

    if test_api_key:
        ankara_lat = 39.9334
        ankara_lon = 32.8597
        result = get_weather(ankara_lat, ankara_lon, test_api_key) # api_key'i geçin
        if result:
            print("Başarılı!")
            print(f"Şehir: {result['name']}")
            print(f"Sıcaklık: {result['main']['temp']}°C")
        else:
            print("Başarısız!")
    else:
        print("Test için OPENWEATHER_API_KEY bulunamadı.")