import streamlit as st
import os
import time
import sys

# Proje ana dizinini Python arama yoluna ekle
# Bu, 'config.py' gibi ana dizindeki modüllere erişimi sağlar.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

# Hava durumu için gerekli import'lar
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_google_genai import GoogleGenerativeAI

# get_weather.py'yi features paketinden mutlak olarak import et
from features.get_weather import get_weather

# config.py artık ana dizinden mutlak olarak import edilecek
from config import ANKARA_KORU_SUBWAY_LAT, ANKARA_KORU_SUBWAY_LON, LOCATION_MAPPINGS
# Eğer yerelde test ederken .env kullanmak isterseniz:
from dotenv import load_dotenv

# --- Hava Durumu Bilgisini Alan Fonksiyon (get_langchain_weather_response) ---
# DİKKAT: `@st.cache_resource` dekoratörü kaldırıldı. Bu fonksiyon artık her çağrıldığında
# hava durumu verisini API'den anlık olarak çekecek ve LLM'e gönderecektir.
# Bu durum API maliyetlerinizi artırabilir ve kota sınırlarınıza daha çabuk ulaşmanıza neden olabilir.
def get_langchain_weather_response(): # Fonksiyon adı, artık cache'lenmediğini belirtmek için değiştirildi
    # print("get_langchain_weather_response başlatıldı (önbelleksiz)") # Debug için Cloud loglarında görünür

    # API anahtarlarını Streamlit secrets'tan burada çekin
    google_api_key = st.secrets.get("GOOGLE_API_KEY")
    openweathermap_api_key = st.secrets.get("OPENWEATHER_API_KEY")

    # UYARI: Streamlit Cloud'da st.secrets kullanılması tercih edilir.
    # Bu kısım sadece yerel geliştirme için bir geri dönüş olabilir,
    # ancak Streamlit Cloud'da doğru çalışması için secrets.toml'e güvenmelisiniz.
    if not google_api_key or not openweathermap_api_key:
        load_dotenv()  # Yerel çalıştırma için .env yükle
        if not google_api_key:
            google_api_key = os.getenv("GOOGLE_API_KEY")
            # if google_api_key: print("Google API key .env dosyasından alındı") # Debug
        if not openweathermap_api_key:
            openweathermap_api_key = os.getenv("OPENWEATHER_API_KEY")
            # if openweathermap_api_key: print("OpenWeatherMap API key .env dosyasından alındı") # Debug

    if not google_api_key:
        # print("UYARI: Google API key bulunamadı!") # Debug
        return "Google API key bulunamadı, hava durumu yanıtı oluşturulamıyor. Lütfen Streamlit Secrets'ı kontrol edin."

    if not openweathermap_api_key:
        # print("UYARI: OpenWeatherMap API key bulunamadı!") # Debug
        return "OpenWeatherMap API key bulunamadı, hava durumu bilgisi alınamıyor. Lütfen Streamlit Secrets'ı kontrol edin."

    llm = None
    try:
        llm = GoogleGenerativeAI(
            model="models/gemini-2.5-flash",
            google_api_key=google_api_key,
            temperature=0.7
        )
        # print("LLM başarıyla oluşturuldu.") # Debug
    except Exception as e:
        # print(f"LLM oluşturulurken hata: {e}") # Debug
        return f"LLM oluşturulurken hata oluştu: {str(e)}"

    ankara_koru_subway_lat = ANKARA_KORU_SUBWAY_LAT
    ankara_koru_subway_lon = ANKARA_KORU_SUBWAY_LON

    # print(f"Koordinatlar: {ankara_koru_subway_lat}, {ankara_koru_subway_lon}") # Debug

    try:
        # get_weather fonksiyonuna api_key'i parametre olarak geçirin
        weather_data = get_weather(ankara_koru_subway_lat, ankara_koru_subway_lon, openweathermap_api_key)
        # print(f"Weather data result: {weather_data is not None}") # Debug

        if weather_data:
            # print(f"Weather data keys: {list(weather_data.keys())}") # Debug

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

            # print(f"Location kullanılacak: {location_to_use}") # Debug

            cevap = chain.invoke({
                "location": location_to_use,
                "current_temp": f"{current_temp:.1f}",
                "feels_like_temp": f"{feels_like_temp:.1f}",
                "wind_speed": round(wind_speed * 3.6),
                "humidity": humidity,
                "weather_description": weather_description,
                "icon_url": icon_url
            })

            # print("LangChain response başarıyla alındı") # Debug
            return cevap
        else:
            # print("Weather data None döndü") # Debug
            return "Hava durumu bilgisi alınamadı. API'den veri gelmedi."

    except Exception as e:
        # import traceback # Debug
        # print(f"get_langchain_weather_response'da hata: {e}") # Debug
        # print(f"Traceback: {traceback.format_exc()}") # Debug
        return f"Hava durumu alınırken hata oluştu: {str(e)}"


# --- Streamlit Uygulaması Başlangıcı ---

st.set_page_config(layout="wide")

st.markdown("<h1 style='text-align: center; color: #add8e6;'>Metro Vagonu Doluluk Oranları</h1>",
            unsafe_allow_html=True)

# Hava durumu bilgisini doğrudan fonksiyondan al ve göster
# Bu kısım, uygulamanın her çalışmasında bir kere çağrılacak (artık önbellek yok)
weather_info = get_langchain_weather_response() # Fonksiyon adı güncellendi
st.markdown(f"<h4 style='text-align: center; color: #add8e6;'>{weather_info}</h4>", unsafe_allow_html=True)

# CSS stillerini başlangıçta bir kez yükle
st.markdown("""
<style>
    .train-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-top: 30px;
        padding: 20px;
        background-color: #1a1a1a; /* Raylar için koyu arka plan */
        border-radius: 15px;
        box-shadow: inset 0 0 10px rgba(0,0,0,0.7);
        width: 100%;
        overflow-x: auto;
        position: relative;
    }
    .wagon-shell, .locomotive-shell {
        width: 250px; /* Büyütüldü */
        height: 125px; /* Büyütüldü */
        background-color: #333;
        border: 2px solid #555;
        border-radius: 15px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        align-items: center;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        color: white;
        box-shadow: 3px 3px 8px rgba(0,0,0,0.4);
        flex-shrink: 0;
        padding: 5px;
        position: relative;
    }
    .locomotive-shell {
        width: 180px; /* Büyütüldü */
    }
    .wagon-content {
        width: 90%;
        height: 70px; /* Yüksekliği biraz daha artırdık */
        border-radius: 8px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        transition: background-color 0.5s ease;
        margin-top: 0px;
        margin-bottom: 0px;
        padding: 5px 0; /* Üstten ve alttan biraz dolgu ekleyelim */
    }
    .wagon-name {
        font-size: 0.8em; /* Yazı boyutu küçültüldü */
        font-weight: bold;
        margin: 0; /* Boşlukları sıfırla */
        line-height: 1.1; /* Satır yüksekliğini ayarla */
    }
    .wagon-percentage {
        font-size: 1.2em; /* Yüzde yazısı küçültüldü */
        font-weight: bold;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
        line-height: 1.1; /* Satır yüksekliğini ayarla */
        margin: 0; /* Boşlukları sıfırla */
    }
    .wagon-status-text {
        font-size: 0.6em; /* Durum yazısı daha da küçültüldü */
        font-style: italic;
        margin: 0; /* Boşlukları sıfırla */
        line-height: 1.1; /* Satır yüksekliğini ayarla */
    }
    .window-row {
        display: flex;
        justify-content: space-around;
        width: 90%;
        margin-top: 5px;
    }
    .window, .door {
        background-color: #add8e6;
        border: 1px solid #222;
        border-radius: 3px;
        height: 30px; /* Büyütüldü */
    }
    .window {
        width: 40px; /* Büyütüldü */
    }
    .door {
        width: 30px; /* Büyütüldü */
        background-color: #444;
    }
    .loco-window {
        width: 50px; /* Büyütüldü */
        height: 35px; /* Büyütüldü */
        background-color: #add8e6;
        border: 1px solid #222;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .connector {
        width: 35px; /* Büyütüldü */
        height: 12px; /* Büyütüldü */
        background-color: #666;
        border-radius: 5px;
        flex-shrink: 0;
        position: relative;
        margin: 0 -5px;
        z-index: 1;
    }
    .connector::before, .connector::after {
        content: '';
        position: absolute;
        top: -6px; /* Büyütüldü */
        width: 10px; /* Büyütüldü */
        height: 24px; /* Büyütüldü */
        background-color: #555;
        border-radius: 3px;
    }
    .connector::before { left: 0; }
    .connector::after { right: 0; }

    .locomotive-front .loco-body {
        border-top-left-radius: 40px;
        border-bottom-left-radius: 40px;
        border-top-right-radius: 15px;
        border-bottom-right-radius: 15px;
    }
    .locomotive-rear .loco-body {
        border-top-right-radius: 40px;
        border-bottom-right-radius: 40px;
        border-top-left-radius: 15px;
        border-bottom-left-radius: 15px;
    }
    .loco-body {
         display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        height: 100%;
        width: 100%;
        background-color: #333;
        border-radius: 15px;
    }
</style>
""", unsafe_allow_html=True)

# Video dosyası yolları (sadece isimler, log dosyası için kullanılacak)
video_names = {
    "Vagon 1": "wagon1.mp4",
    "Vagon 2": "wagon2.mp4",
    "Vagon 3": "wagon3.mp4"
}

# Log dosyalarının dizini
fullness_log_dir = os.path.join("outputs", "logs")

# Video işleme tamamlanma bayrağının yolu
processing_complete_flag_path = os.path.join(fullness_log_dir, "video_processing_complete.txt")

# Tüm tren çizimini dinamik olarak güncellemek için bir placeholder
train_display_placeholder = st.empty()

# Tamamlama mesajı için placeholder
completion_message_placeholder = st.empty()

# Anlık güncellemeler için döngü
while True:
    current_fullness = {}

    # Her bir vagonun doluluk oranını log dosyasından oku
    for wagon_name, video_filename in video_names.items():
        log_file_name = f"{os.path.splitext(video_filename)[0]}_fullness.txt"
        fullness_log_file_path = os.path.join(fullness_log_dir, log_file_name)

        if os.path.exists(fullness_log_file_path):
            try:
                with open(fullness_log_file_path, "r") as f:
                    fullness_str = f.read().strip()
                    if fullness_str:
                        current_fullness[wagon_name] = float(fullness_str)
                    else:
                        current_fullness[wagon_name] = 0.0
            except (IOError, ValueError) as e:
                current_fullness[wagon_name] = 0.0
        else:
            current_fullness[wagon_name] = 0.0

    # CSS stilleri ve tren yapısı
    train_html_parts = []
    train_html_parts.append("""<div class="train-container">""")

    # Trenin ön lokomotifi
    train_html_parts.append("""
        <div class="locomotive-shell locomotive-front">
            <div class="loco-body">
                <div class="loco-window"></div>
                🚂
            </div>
        </div>
        <div class="connector"></div>
    """)

    for i, (wagon_name, _) in enumerate(video_names.items()):
        fullness_value = current_fullness.get(wagon_name, 0.0)
        color = "#1E90FF"  # Başlangıç rengini mavi (BOŞ) olarak ayarla
        status_text = "BOŞ"  # Başlangıç durumunu BOŞ olarak ayarla

        if isinstance(fullness_value, (int, float)):
            if fullness_value < 10:
                color = "#1E90FF"  # Mavi (Boş)
                status_text = "BOŞ"
            elif fullness_value < 30:
                color = "#4CAF50"  # Yeşil (Az Dolu)
                status_text = "AZ DOLU"
            elif fullness_value < 60:
                color = "#ffa500"  # Turuncu (Orta Dolu)
                status_text = "ORTA DOLU"
            else:
                color = "#ff4b4b"  # Kırmızı (Çok Dolu)
                status_text = "ÇOK DOLU"

            # Vagon kutusunun HTML'i
            train_html_parts.append(f"""
            <div class="wagon-shell">
                <div class="window-row">
                    <div class="window"></div>
                    <div class="door"></div>
                    <div class="window"></div>
                </div>
                <div class="wagon-content" style="background-color: {color};">
                    <div class="wagon-name">{wagon_name}</div>
                    <div class="wagon-percentage">{fullness_value:.2f}%</div>
                    <div class="wagon-status-text">{status_text}</div>
                </div>
                <div class="window-row">
                    <div class="window"></div>
                    <div class="door"></div>
                    <div class="window"></div>
                </div>
            </div>
            """)
        else:
            train_html_parts.append(f"""
            <div class="wagon-shell" style="background-color: #1E90FF;">
                <div class="window-row">
                    <div class="window"></div>
                    <div class="door"></div>
                    <div class="window"></div>
                </div>
                <div class="wagon-content" style="background-color: #1E90FF;">
                    <div class="wagon-name">{wagon_name}</div>
                    <div class="wagon-percentage">0.00%</div>
                    <div class="wagon-status-text">BOŞ</div>
                </div>
                <div class="window-row">
                    <div class="window"></div>
                    <div class="door"></div>
                    <div class="window"></div>
                </div>
            </div>
            """)

        if i < len(video_names) - 1:  # Vagonlar arasına bağlantı elemanı ekle
            train_html_parts.append("""<div class="connector"></div>""")

    # Trenin arka lokomotifi/kuyruğu
    train_html_parts.append("""
        <div class="connector"></div>
        <div class="locomotive-shell locomotive-rear">
            <div class="loco-body">
                <div class="loco-window"></div>
                🚃
            </div>
        </div>
    </div> <!-- Close train-container -->
    """)

    # Her bir HTML parçasını temizle ve birleştir
    cleaned_html_parts = [part.strip().replace('\r', '') for part in train_html_parts]
    full_train_html = "\n".join(cleaned_html_parts)

    train_display_placeholder.markdown(full_train_html, unsafe_allow_html=True)

    # Video işleme tamamlandı bayrağını kontrol et ve mesajı göster
    if os.path.exists(processing_complete_flag_path):
        completion_message_placeholder.markdown(
            "<br><h3 style='text-align: center; color: #A0EEFF; padding: 10px; background-color: #282828; border-radius: 8px;'>✨ Tüm Vagon Görüntüleri Başarıyla Analiz Edildi! ✨</h3>",
            unsafe_allow_html=True
        )
    else:
        completion_message_placeholder.empty()  # Dosya yoksa mesajı temizle

    time.sleep(1)  # Her 1 saniyede bir güncelle