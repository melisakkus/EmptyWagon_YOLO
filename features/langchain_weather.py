import os
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_google_genai import GoogleGenerativeAI
from .get_weather import get_weather

# config.py dosyasından sabit değerleri içe aktar
from config import ANKARA_KORU_SUBWAY_LAT, ANKARA_KORU_SUBWAY_LON, LOCATION_MAPPINGS

# .env dosyasını yükle
load_dotenv()

# Google API key'i al
api_key = os.getenv("GOOGLE_API_KEY")

# LLM oluştur (Gemini 2.5 Flash)
llm = GoogleGenerativeAI(
    model="models/gemini-2.5-flash",
    google_api_key=api_key,
    temperature=0.7
)

def get_langchain_weather_response():
    ankara_koru_subway_lat = ANKARA_KORU_SUBWAY_LAT
    ankara_koru_subway_lon = ANKARA_KORU_SUBWAY_LON
    weather_data = get_weather(ankara_koru_subway_lat, ankara_koru_subway_lon)

    if weather_data:
        current_temp = weather_data['main']['temp']
        feels_like_temp = weather_data['main']['feels_like']
        wind_speed = weather_data['wind']['speed']
        humidity = weather_data['main']['humidity']
        weather_description = weather_data['weather'][0]['description']
        weather_icon = weather_data['weather'][0]['icon']

        # OpenWeatherMap ikon URL'si
        icon_url = f"http://openweathermap.org/img/wn/{weather_icon}@2x.png"

        prompt_template = PromptTemplate(
            input_variables=["location", "current_temp", "feels_like_temp", "wind_speed", "humidity", "weather_description", "icon_url"],
            template=(
                "Lütfen {location} yerinin hava durumunu aşağıdaki bilgilere göre arkadaşça ve samimi bir cümle yaz:\n"
                "İkon için uygun bir emoji kullan ve metnin başına ekle."
                "Termometre **{current_temp}°C** gösteriyor ama hissedilen sıcaklık **{feels_like_temp}°C**. "
                "Rüzgar **{wind_speed} km/h** hızında esiyor, nem oranı ise %**{humidity}**. "
                "Hava durumu: {weather_description}. Hava durumu ikonu: {icon_url}."
            )
        )

        #chain = LLMChain(llm=llm, prompt=prompt_template)
        chain = prompt_template | llm

        # Belirtilen koordinatlar için özel bir konum adı var mı kontrol et
        current_location_coords = (ankara_koru_subway_lat, ankara_koru_subway_lon)
        location_to_use = LOCATION_MAPPINGS.get(current_location_coords, weather_data['name'])

        cevap = chain.invoke({
            "location": location_to_use,
            "current_temp": f"{current_temp:.1f}",
            "feels_like_temp": f"{feels_like_temp:.1f}",
            "wind_speed": round(wind_speed * 3.6),
            "humidity": humidity,
            "weather_description": weather_description,
            "icon_url": icon_url
        }
        )
        return cevap
    else:
        return "Hava durumu bilgisi alınamadı."
