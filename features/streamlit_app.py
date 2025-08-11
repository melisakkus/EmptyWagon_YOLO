import streamlit as st
import os
import time
import sys

# Proje ana dizinini Python arama yoluna ekle
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

# Firebase ve Firestore import'ları
from features.database.initialize_firebase import initialize_firebase
from features.database.firestore_crud import get_all_documents, get_document
from firebase_admin import firestore

# Hava durumu için gerekli import'lar
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_google_genai import GoogleGenerativeAI
from features.get_weather import get_weather
from config import ANKARA_KORU_SUBWAY_LAT, ANKARA_KORU_SUBWAY_LON, LOCATION_MAPPINGS
from dotenv import load_dotenv

# --- Firebase Bağlantısı ---
@st.cache_resource
def get_firestore_client():
    client = initialize_firebase()
    if client:
        pass
    else:
        st.error("Firebase'e bağlanılamadı. Lütfen Firebase yapılandırmanızı kontrol edin.")
    return client

db = get_firestore_client()
if db is None:
    st.error("Uygulama başlatılamadı: Firebase bağlantısı kurulamadı.")
    st.stop()

# Firestore Koleksiyon Adları
WAGON_CURRENT_FULLNESS_COLLECTION = "wagon_fullness_current"
WAGON_HISTORICAL_LOGS_COLLECTION = "wagon_fullness_history"
PROCESSING_STATUS_COLLECTION = "processing_status"
PROCESSING_COMPLETE_DOC_ID = "video_analysis_status"

# --- Hava Durumu Bilgisini Alan Fonksiyon ---
@st.cache_data(ttl=3600)
def get_langchain_weather_response():
    google_api_key = st.secrets.get("GOOGLE_API_KEY")
    openweathermap_api_key = st.secrets.get("OPENWEATHER_API_KEY")

    if not google_api_key or not openweathermap_api_key:
        load_dotenv() # Yerel çalıştırma için .env yükle, Streamlit Cloud'da secrets kullanılır
        if not google_api_key:
            google_api_key = os.getenv("GOOGLE_API_KEY")
        if not openweathermap_api_key:
            openweathermap_api_key = os.getenv("OPENWEATHER_API_KEY")

    if not google_api_key:
        return "Google API key bulunamadı, hava durumu yanıtı oluşturulamıyor. Lütfen Streamlit Secrets'ı veya .env dosyasını kontrol edin."

    if not openweathermap_api_key:
        return "OpenWeatherMap API key bulunamadı, hava durumu bilgisi alınamıyor. Lütfen Streamlit Secrets'ı veya .env dosyasını kontrol edin."

    llm = None
    try:
        llm = GoogleGenerativeAI(
            model="models/gemini-2.5-flash",
            google_api_key=google_api_key,
            temperature=0.7
        )
    except Exception as e:
        return f"LLM oluşturulurken hata oluştu: {str(e)}"

    ankara_koru_subway_lat = ANKARA_KORU_SUBWAY_LAT
    ankara_koru_subway_lon = ANKARA_KORU_SUBWAY_LON

    try:
        weather_data = get_weather(ankara_koru_subway_lat, ankara_koru_subway_lon, openweathermap_api_key)

        if weather_data:
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

            cevap = chain.invoke({
                "location": location_to_use,
                "current_temp": f"{current_temp:.1f}",
                "feels_like_temp": f"{feels_like_temp:.1f}",
                "wind_speed": round(wind_speed * 3.6),
                "humidity": humidity,
                "weather_description": weather_description,
                "icon_url": icon_url
            })
            return cevap
        else:
            return "Hava durumu bilgisi alınamadı. API'den veri gelmedi."

    except Exception as e:
        return f"Hava durumu alınırken hata oluştu: {str(e)}"

# --- Streamlit Uygulaması Başlangıcı ---
st.set_page_config(layout="wide")
st.markdown("<h1 style='text-align: center; color: #add8e6;'>Metro Vagonu Doluluk Oranları</h1>",
            unsafe_allow_html=True)
weather_info = get_langchain_weather_response()
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
        background-color: #1a1a1a;
        border-radius: 15px;
        box-shadow: inset 0 0 10px rgba(0,0,0,0.7);
        width: 100%;
        overflow-x: auto;
        position: relative;
    }
    .wagon-shell, .locomotive-shell {
        width: 250px;
        height: 125px;
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
        width: 180px;
    }
    .wagon-content {
        width: 90%;
        height: 70px;
        border-radius: 8px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        transition: background-color 0.5s ease;
        margin-top: 0px;
        margin-bottom: 0px;
        padding: 5px 0;
    }
    .wagon-name {
        font-size: 0.8em;
        font-weight: bold;
        margin: 0;
        line-height: 1.1;
    }
    .wagon-percentage {
        font-size: 1.2em;
        font-weight: bold;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
        line-height: 1.1;
        margin: 0;
    }
    .wagon-status-text {
        font-size: 0.6em;
        font-style: italic;
        margin: 0;
        line-height: 1.1;
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
        height: 30px;
    }
    .window {
        width: 40px;
    }
    .door {
        width: 30px;
        background-color: #444;
    }
    .loco-window {
        width: 50px;
        height: 35px;
        background-color: #add8e6;
        border: 1px solid #222;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .connector {
        width: 35px;
        height: 12px;
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
        top: -6px;
        width: 10px;
        height: 24px;
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

# Video dosyası yolları (Firestore doküman ID'leri ile eşleşmeli)
video_names = {
    "Vagon 1": "wagon1",
    "Vagon 2": "wagon2",
    "Vagon 3": "wagon3"
}

# Tren çizimini güncelleyen fonksiyon
def update_train_display(fullness_data, placeholder):
    train_html_parts = []
    train_html_parts.append("""<div class="train-container">""")

    train_html_parts.append("""
        <div class="locomotive-shell locomotive-front">
            <div class="loco-body">
                <div class="loco-window"></div>
                🚂
            </div>
        </div>
        <div class="connector"></div>
    """)

    for i, (wagon_display_name, wagon_doc_id) in enumerate(video_names.items()):
        fullness_value = fullness_data.get(wagon_display_name, 0.0)

        color = "#6c757d"  # Varsayılan gri (Veri Yok)
        status_text = "VERİ BEKLENİYOR"

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

            percentage_text = f"{fullness_value:.2f}%"
        else:
            percentage_text = "N/A"

        train_html_parts.append(f"""
        <div class="wagon-shell">
            <div class="window-row">
                <div class="window"></div>
                <div class="door"></div>
                <div class="window"></div>
            </div>
            <div class="wagon-content" style="background-color: {color};">
                <div class="wagon-name">{wagon_display_name}</div>
                <div class="wagon-percentage">{percentage_text}</div>
                <div class="wagon-status-text">{status_text}</div>
            </div>
            <div class="window-row">
                <div class="window"></div>
                <div class="door"></div>
                <div class="window"></div>
            </div>
        </div>
        """)

        if i < len(video_names) - 1:
            train_html_parts.append("""<div class="connector"></div>""")

    train_html_parts.append("""
        <div class="connector"></div>
        <div class="locomotive-shell locomotive-rear">
            <div class="loco-body">
                <div class="loco-window"></div>
                🚃
            </div>
        </div>
    </div>
    """)

    cleaned_html_parts = [part.strip().replace('\r', '') for part in train_html_parts]
    full_train_html = "\n".join(cleaned_html_parts)
    placeholder.markdown(full_train_html, unsafe_allow_html=True)

# Yeniden oynatma fonksiyonu
def replay_historical_logs(db_client, wagon_map, display_placeholder):
    st.info("Loglar yeniden oynatılıyor... Lütfen bekleyin.")
    try:
        # Tüm tarihsel logları çek ve zamana göre sırala
        # Firestore Timestamp nesnelerini doğrudan sıralayabilir.
        docs = db_client.collection(WAGON_HISTORICAL_LOGS_COLLECTION).order_by("timestamp").stream()

        # Logları listeye al
        historical_logs = []
        for doc in docs:
            historical_logs.append(doc.to_dict())

        if not historical_logs:
            st.warning("Oynatmak için tarihsel log bulunamadı.")
            return

        # Vagonların anlık doluluk durumunu tutacak geçici bir dictionary
        current_replay_fullness = {name: 0.0 for name in wagon_map.keys()}

        last_timestamp = None
        for log_entry in historical_logs:
            wagon_id = log_entry.get("wagon_id")
            fullness = log_entry.get("fullness_percentage")
            timestamp = log_entry.get("timestamp")

            if wagon_id and fullness is not None:
                display_name = next((key for key, value in wagon_map.items() if value == wagon_id), wagon_id)
                current_replay_fullness[display_name] = fullness

                update_train_display(current_replay_fullness, display_placeholder)

                if last_timestamp and timestamp:
                    # Firestore'dan gelen timestamp'ler zaten Python datetime objesi olarak gelir.
                    current_dt = timestamp
                    last_dt = last_timestamp

                    time_diff = (current_dt - last_dt).total_seconds()

                    # Simülasyon hızını ayarla: Min 0.05 saniye, Maks 1.0 saniye bekle
                    # Streamlit Cloud'da hızlı oynamasını istiyorsak bu değerleri düşürebiliriz.
                    sleep_time = max(0.02, min(0.5, time_diff * 0.1)) # Oynatma hızını artırdık (0.1 çarpanı)
                    time.sleep(sleep_time)
                else:
                    time.sleep(0.05) # İlk log veya timestamp yoksa kısa bekleme
                last_timestamp = timestamp

        st.success("Log oynatma tamamlandı!")

    except Exception as e:
        st.error(f"Tarihsel loglar oynatılırken hata: {e}")

# --- Streamlit Uygulamasının Ana Akışı ---

# Tren çizimini dinamik olarak güncellemek için bir placeholder
train_display_placeholder = st.empty()

# Tamamlama mesajı ve butonlar için placeholder'lar
completion_message_placeholder = st.empty()
button_container_placeholder = st.empty()

# Session state'i başlat
# Streamlit Cloud'da uygulamanın "işlem tamamlandı" modunda başlaması beklenir.
if 'show_replay_ui' not in st.session_state:
    st.session_state.show_replay_ui = False # Başlangıçta False olarak bırak, Firebase kontrolü yapacak
if 'replay_active' not in st.session_state:
    st.session_state.replay_active = False

# Anlık doluluk verilerini çeken ve ekranı güncelleyen yardımcı fonksiyon
def update_current_fullness_and_display():
    current_fullness = {}
    try:
        all_wagon_data = get_all_documents(db, WAGON_CURRENT_FULLNESS_COLLECTION)
        for display_name, doc_id in video_names.items():
            if doc_id in all_wagon_data:
                fullness_data = all_wagon_data[doc_id]
                if "fullness_percentage" in fullness_data:
                    current_fullness[display_name] = fullness_data["fullness_percentage"]
                else:
                    current_fullness[display_name] = 0.0
            else:
                current_fullness[display_name] = 0.0
    except Exception as e:
        st.error(f"Firestore'dan anlık vagon doluluk verisi okunurken hata: {e}")
        for display_name in video_names.keys():
            current_fullness[display_name] = 0.0
    update_train_display(current_fullness, train_display_placeholder)

# Streamlit Cloud'da ana mantık:
# 1. Firebase'deki "completed" bayrağını kontrol et. Bu, lokalde bir kez çalıştırılmış ve veri Firebase'e yazılmışsa TRUE olacaktır.
# 2. Eğer TRUE ise, Streamlit UI'ı "tamamlandı" modunda başlat (son durumu göster ve 'Yeniden Oynat' butonu).
# 3. 'Yeniden Oynat' butonuna basıldığında, tarihsel logları oynat.

# İlk yüklemede veya rerunda Firebase'den tamamlanma durumunu kontrol et
# Streamlit Cloud'da, main.py'nin hiç çalışmadığı bir senaryo olmamalıdır
# çünkü veriler localde işlenip gönderilmiştir.
# Dolayısıyla `is_processing_complete_from_firebase` genellikle True dönecektir.
is_processing_complete_from_firebase = False
try:
    status_doc = get_document(db, PROCESSING_STATUS_COLLECTION, PROCESSING_COMPLETE_DOC_ID)
    if status_doc and status_doc.get("completed", False):
        is_processing_complete_from_firebase = True
except Exception as e:
    st.warning(f"Firestore'dan işlem durumu okunurken hata: {e}. Varsayılan olarak 'tamamlandı' durumu ele alınıyor.")
    is_processing_complete_from_firebase = True # Hata durumunda da UI'ı göstermek için

# Eğer Firebase'den işlem tamamlandı bilgisi gelirse, UI'ı buna göre ayarla
if is_processing_complete_from_firebase and not st.session_state.show_replay_ui:
    st.session_state.show_replay_ui = True
    st.rerun() # UI'ı doğru duruma getirmek için yeniden çalıştır

# Ana akışı yönet
if st.session_state.replay_active:
    # Oynatma aktifse, mesajı ve butonu gizle ve oynatmayı başlat
    completion_message_placeholder.empty()
    button_container_placeholder.empty()
    replay_historical_logs(db, video_names, train_display_placeholder)
    st.session_state.replay_active = False # Oynatma bitti
    st.session_state.show_replay_ui = True # Oynatma bittikten sonra tamamlama UI'ına geri dön
    st.rerun() # Oynatma bittikten sonra uygulamayı yeniden çalıştır

elif st.session_state.show_replay_ui:
    # Analiz tamamlandı (veya tamamlanmış varsayılıyor). Son durumu ve oynatma butonunu göster.
    update_current_fullness_and_display() # En son güncel doluluk verisini göster

    with completion_message_placeholder:
        st.markdown(
            "<br><h3 style='text-align: center; color: #A0EEFF; padding: 10px; background-color: #282828; border-radius: 8px;'>✨ Tüm Vagon Görüntüleri Başarıyla Analiz Edildi! ✨</h3>",
            unsafe_allow_html=True
        )
    with button_container_placeholder:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("Logları Yeniden Oynat", key="replay_button_centered", use_container_width=True):
                st.session_state.replay_active = True
                st.rerun()

else:
    # Bu blok, uygulamanın ilk kez yüklendiği ve henüz Firebase'den 'completed' durumunun alınmadığı
    # veya bir hata oluştuğu çok kısa bir başlangıç anı için bir fallback'dir.
    # Streamlit Cloud'da bu duruma genellikle düşmemeliyiz çünkü beklenen durum 'completed: True' olacaktır.
    st.info("Veriler yükleniyor ve durum kontrol ediliyor... Lütfen bekleyin.")
    # Bu durumda bile en azından varsayılan veya boş bir ekran gösterebiliriz:
    update_current_fullness_and_display() # Henüz veri yoksa sıfır dolu vagonlar gösterir.
    # Burada manuel bir time.sleep'e gerek yok, çünkü st.rerun() hemen tetiklenecektir.