import os
import sys
import streamlit as st  # Streamlit'i burada import edin
from dotenv import load_dotenv  # Yerel çalıştırma için hala lazım olabilir
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_google_genai import GoogleGenerativeAI

try:
    from get_weather import get_weather  # Artık bu get_weather_with_key gibi düşünün
except ImportError:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from get_weather import get_weather

from config import ANKARA_KORU_SUBWAY_LAT, ANKARA_KORU_SUBWAY_LON, LOCATION_MAPPINGS


def get_langchain_weather_response():
    print("get_langchain_weather_response başlatıldı")

    # API anahtarlarını Streamlit secrets'tan burada çekin
    google_api_key = st.secrets.get("GOOGLE_API_KEY")
    openweathermap_api_key = st.secrets.get("OPENWEATHER_API_KEY")

    # Eğer yerelde çalışıyorsa ve secrets yoksa .env'den çekmeyi dene
    if not google_api_key or not openweathermap_api_key:
        load_dotenv()
        if not google_api_key:
            google_api_key = os.getenv("GOOGLE_API_KEY")
            if google_api_key: print("Google API key .env dosyasından alındı")
        if not openweathermap_api_key:
            openweathermap_api_key = os.getenv("OPENWEATHER_API_KEY")
            if openweathermap_api_key: print("OpenWeatherMap API key .env dosyasından alındı")

    if not google_api_key:
        print("UYARI: Google API key bulunamadı!")
        return "Google API key bulunamadı, hava durumu yanıtı oluşturulamıyor."

    if not openweathermap_api_key:
        print("UYARI: OpenWeatherMap API key bulunamadı!")
        return "OpenWeatherMap API key bulunamadı, hava durumu bilgisi alınamıyor."

    llm = None
    try:
        llm = GoogleGenerativeAI(
            model="models/gemini-2.5-flash",
            google_api_key=google_api_key,
            temperature=0.7
        )
    except Exception as e:
        print(f"LLM oluşturulurken hata: {e}")
        return f"LLM oluşturulurken hata oluştu: {str(e)}"

    ankara_koru_subway_lat = ANKARA_KORU_SUBWAY_LAT
    ankara_koru_subway_lon = ANKARA_KORU_SUBWAY_LON

    print(f"Koordinatlar: {ankara_koru_subway_lat}, {ankara_koru_subway_lon}")

    try:
        # get_weather fonksiyonuna api_key'i parametre olarak geçirin
        weather_data = get_weather(ankara_koru_subway_lat, ankara_koru_subway_lon, openweathermap_api_key)
        print(f"Weather data result: {weather_data is not None}")

        if weather_data:
            print(f"Weather data keys: {list(weather_data.keys())}")

            current_temp = weather_data['main']['temp']
            feels_like_temp = weather_data['main']['feels_like']
            wind_speed = weather_data['wind']['speed']
            humidity = weather_data['main']['humidity']
            weather_description = weather_data['weather'][0]['description']
            weather_icon = weather_data['weather'][0]['icon']

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

            chain = prompt_template | llm

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


# Test kodu (anahtar manuel olarak sağlanmalı veya .env'den okunmalı)
if __name__ == "__main__":
    # Test için st.secrets'tan çekme simülasyonu yapamayız, .env kullanmalıyız
    load_dotenv()
    os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
    os.environ["OPENWEATHER_API_KEY"] = os.getenv("OPENWEATHER_API_KEY")

    # st.secrets'ı simüle etmek için dummy bir Streamlit modülü oluşturabilirsiniz
    # Ancak en basit yol, test kodu için doğrudan get_langchain_weather_response'ı çağırmak değil,
    # ilgili fonksiyona anahtarları sağlamaktır.
    # Bu test kodu, Streamlit ortamı dışında çalışırken doğru çalışmayabilir,
    # çünkü get_langchain_weather_response artık st.secrets'ı kullanıyor.
    # En iyi uygulama, bu tür testleri Streamlit'in kendi test çerçevesi ile yapmaktır.

    print("\nLütfen bu testi Streamlit uygulaması içinde çalıştırın (streamlit run main.py).")
    print("Doğrudan çalıştırmak st.secrets'a erişemediği için sorunlara neden olabilir.")
    # result = get_langchain_weather_response() # Bu artık st.secrets'a bağlı olduğu için doğrudan çalışmaz
    # print(f"\nSonuç: {result}")