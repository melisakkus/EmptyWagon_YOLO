import os
import sys
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_google_genai import GoogleGenerativeAI

# Absolute import kullan
try:
    from get_weather import get_weather
except ImportError:
    # Eğer bu da çalışmazsa, sys.path'e ekle
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from get_weather import get_weather

# config.py dosyasından sabit değerleri içe aktar
from config import ANKARA_KORU_SUBWAY_LAT, ANKARA_KORU_SUBWAY_LON, LOCATION_MAPPINGS


def get_api_key():
    """API key'i önce Streamlit secrets'tan, sonra .env'den al"""
    api_key = None

    # Önce Streamlit secrets'tan dene
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and "GOOGLE_API_KEY" in st.secrets:
            api_key = st.secrets["GOOGLE_API_KEY"]
            print("Google API key Streamlit secrets'tan alındı")
        else:
            print("Streamlit secrets'ta GOOGLE_API_KEY bulunamadı")
    except Exception as e:
        print(f"Streamlit secrets'tan API key alınamadı: {e}")

    if not api_key:
        # Streamlit yoksa veya secret bulunamazsa .env'den dene
        load_dotenv()
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            print("Google API key .env dosyasından alındı")

    return api_key


def create_llm():
    """LLM oluşturmak için ayrı fonksiyon - bu sayıda import sırasında hata olursa yakalanır"""
    try:
        google_api_key = get_api_key()
        if not google_api_key:
            print("UYARI: Google API key bulunamadı!")
            return None

        llm = GoogleGenerativeAI(
            model="models/gemini-2.5-flash",
            google_api_key=google_api_key,
            temperature=0.7
        )
        return llm
    except Exception as e:
        print(f"LLM oluşturulurken hata: {e}")
        return None


def get_langchain_weather_response():
    print("get_langchain_weather_response başlatıldı")

    # Her çağrıda LLM'i yeniden oluştur
    llm = create_llm()
    if not llm:
        return "Google API key bulunamadı, hava durumu yanıtı oluşturulamıyor."

    ankara_koru_subway_lat = ANKARA_KORU_SUBWAY_LAT
    ankara_koru_subway_lon = ANKARA_KORU_SUBWAY_LON

    print(f"Koordinatlar: {ankara_koru_subway_lat}, {ankara_koru_subway_lon}")

    try:
        weather_data = get_weather(ankara_koru_subway_lat, ankara_koru_subway_lon)
        print(f"Weather data result: {weather_data is not None}")

        if weather_data:
            print(f"Weather data keys: {list(weather_data.keys())}")

            current_temp = weather_data['main']['temp']
            feels_like_temp = weather_data['main']['feels_like']
            wind_speed = weather_data['wind']['speed']
            humidity = weather_data['main']['humidity']
            weather_description = weather_data['weather'][0]['description']
            weather_icon = weather_data['weather'][0]['icon']

            # OpenWeatherMap ikon URL'si
            icon_url = f"http://openweathermap.org/img/wn/{weather_icon}@2x.png"

            prompt_template = PromptTemplate(
                input_variables=["location", "current_temp", "feels_like_temp", "wind_speed", "humidity",
                                 "weather_description", "icon_url"],
                template=(
                    "Lütfen {location} yerinin hava durumunu aşağıdaki bilgilere göre arkadaşça ve samimi bir cümle yaz:\n"
                    "İkon için uygun bir emoji kullan ve metnin başına ekle. "
                    "Termometre **{current_temp}°C** gösteriyor ama hissedilen sıcaklık **{feels_like_temp}°C**. "
                    "Rüzgar **{wind_speed} km/h** hızında esiyor, nem oranı ise %**{humidity}**. "
                    "Hava durumu: {weather_description}. Hava durumu ikonu: {icon_url}."
                )
            )

            # Yeni LangChain syntax'ı kullanın
            chain = prompt_template | llm

            # Belirtilen koordinatlar için özel bir konum adı var mı kontrol et
            current_location_coords = (ankara_koru_subway_lat, ankara_koru_subway_lon)
            location_to_use = LOCATION_MAPPINGS.get(current_location_coords, weather_data['name'])

            print(f"Location kullanılacak: {location_to_use}")

            cevap = chain.invoke({
                "location": location_to_use,
                "current_temp": f"{current_temp:.1f}",
                "feels_like_temp": f"{feels_like_temp:.1f}",
                "wind_speed": round(wind_speed * 3.6),
                "humidity": humidity,
                "weather_description": weather_description,
                "icon_url": icon_url
            })

            print("LangChain response başarıyla alındı")
            return cevap
        else:
            print("Weather data None döndü")
            return "Hava durumu bilgisi alınamadı. API'den veri gelmedi."

    except Exception as e:
        print(f"get_langchain_weather_response'da hata: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return f"Hava durumu alınırken hata oluştu: {str(e)}"


# Test kodu
if __name__ == "__main__":
    result = get_langchain_weather_response()
    print(f"\nSonuç: {result}")