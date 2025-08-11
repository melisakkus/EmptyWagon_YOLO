import os
import sys
import streamlit as st
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_google_genai import GoogleGenerativeAI

try:
    from get_weather import get_weather
except ImportError:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from get_weather import get_weather

from config import ANKARA_KORU_SUBWAY_LAT, ANKARA_KORU_SUBWAY_LON, LOCATION_MAPPINGS


# Bu fonksiyon Streamlit'te cache'li olduğu için Streamlit'in secrets'ına doğrudan erişebilir.
@st.cache_data(ttl=3600)
def get_langchain_weather_response():
    print("get_langchain_weather_response başlatıldı")

    # API anahtarlarını Streamlit secrets'tan burada çekin - BURASI DÜZELTİLDİ
    google_api_key = st.secrets.get("general", {}).get("GOOGLE_API_KEY") # <-- BURAYI DÜZELTTİK
    openweathermap_api_key = st.secrets.get("general", {}).get("OPENWEATHER_API_KEY") # <-- BURAYI DÜZELTTİK

    # Eğer yerelde çalışıyorsa ve secrets yoksa .env'den çekmeyi dene (bu kısım Streamlit Cloud'da çalışmaz, yerel test için)
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
        return "Google API key bulunamadı, hava durumu yanıtı oluşturulamıyor. Lütfen Streamlit Secrets'ı veya .env dosyasını kontrol edin."

    if not openweathermap_api_key:
        print("UYARI: OpenWeatherMap API key bulunamadı!")
        return "OpenWeatherMap API key bulunamadı, hava durumu bilgisi alınamıyor. Lütfen Streamlit Secrets'ı veya .env dosyasını kontrol edin."

    llm = None
    try:
        llm = GoogleGenerativeAI(
            model="models/gemini-2.5-flash",
            google_api_key=google_api_key,
            temperature=0.7 # Hava durumu özetinizde daha kısıtlı bir çıktı istiyorsanız bu değeri 0.0'a düşürebilirsiniz.
        )
    except Exception as e:
        print(f"LLM oluşturulurken hata: {e}")
        return f"LLM oluşturulurken hata oluştu: {str(e)}"

    ankara_koru_subway_lat = ANKARA_KORU_SUBWAY_LAT
    ankara_koru_subway_lon = ANKARA_KORU_SUBWAY_LON

    print(f"Koordinatlar: {ankara_koru_subway_lat}, {ankara_koru_subway_lon}")

    try:
        weather_data = get_weather(ankara_koru_subway_lat, ankara_koru_subway_lon, openweathermap_api_key)
        print(f"Weather data result: {weather_data is not None}")

        if weather_data:
            print(f"Weather data keys: {list(weather_data.keys())}")

            current_temp = weather_data['main']['temp']
            feels_like_temp = weather_data['main']['feels_like']
            wind_speed = weather_data['wind']['speed']
            humidity = weather_data['main']['humidity']
            weather_description = weather_data['weather'][0]['description']
            weather_icon = weather_data['weather'][0]['icon'] # LLM'in emoji seçmesine yardımcı olması için kalabilir

            # NOT: Prompt'unuz hala bir liste veya özeti andıran bir yapı üretebilir.
            # LLM'in "Harika bir özet! İşte size daha kısa ve öz bir sunum:" gibi metinler üretmesini engellemek için
            # prompt'u daha da agresif ve direkt hale getirmeniz gerekebilir.
            # Örneğin:
            prompt_template = PromptTemplate(
                input_variables=["location", "current_temp", "feels_like_temp", "wind_speed", "humidity",
                                 "weather_description", "icon_url"],
                template=(
                    "Sadece ve sadece tek bir cümle halinde, aşağıdaki bilgileri kullanarak hava durumu raporu oluştur. "
                    "Başka hiçbir metin, başlık, özet, giriş cümlesi, liste veya madde işareti kullanma. "
                    "Cümleye hava durumuna uygun tek bir emoji ile başla. Örneğin: '☀️ Ankara Koru için hava durumu: ...'\n"
                    "Bilgiler:\n"
                    "Lokasyon: {location}\n"
                    "Sıcaklık: {current_temp}°C\n"
                    "Hissedilen Sıcaklık: {feels_like_temp}°C\n"
                    "Rüzgar Hızı: {wind_speed} km/h\n"
                    "Nem Oranı: %{humidity}\n"
                    "Genel Durum: {weather_description}\n"
                    "Hava durumu ikonu: {icon_url}\n"
                    "Cümle:" # Modele direkt olarak cümlenin başlamasını söyleyin
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
                "icon_url": weather_icon # Prompt'ta icon_url kullanıldığı için burada da olmalı
            })

            print("LangChain response başarıyla alındı")
            return cevap # LLM'in çıktısında zaten emoji ve giriş cümlesi olduğu için f-string'i kaldırdık
        else:
            print("Weather data None döndü")
            return "Hava durumu bilgisi alınamadı. API'den veri gelmedi."

    except Exception as e:
        print(f"get_langchain_weather_response'da hata: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return f"Hava durumu alınırken hata oluştu: {str(e)}"


# Test kodu kısmı (değişmedi)
if __name__ == "__main__":
    load_dotenv()
    os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
    os.environ["OPENWEATHER_API_KEY"] = os.getenv("OPENWEATHER_API_KEY")

    print("\nLütfen bu testi Streamlit uygulaması içinde çalıştırın (streamlit run main.py).")
    print("Doğrudan çalıştırmak st.secrets'a erişemediği için sorunlara neden olabilir.")