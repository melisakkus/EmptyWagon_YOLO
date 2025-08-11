import streamlit as st
import os
import time
import sys
import json

# Proje ana dizinini Python arama yoluna ekle
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

# Firebase ve Firestore import'ları
from features.database.initialize_firebase import initialize_firebase
from features.database.firestore_crud import get_all_documents, get_document
from firebase_admin import firestore

# Hava durumu için gerekli import'lar
# Eski importları kaldırıyoruz, çünkü get_langchain_weather_response'u doğrudan import edeceğiz
# from langchain.prompts import PromptTemplate
# from langchain.chains import LLMChain
# from langchain_google_genai import GoogleGenerativeAI
# from features.get_weather import get_weather # Bu hala get_weather API'si için gerekli
# from config import ANKARA_KORU_SUBWAY_LAT, ANKARA_KORU_SUBWAY_LON, LOCATION_MAPPINGS
# from dotenv import load_dotenv

# Yeni import: langchain.weather.py dosyasındaki fonksiyonu içe aktar
from features.langchain_weather import get_langchain_weather_response as get_weather_report_from_llm # Fonksiyon adını çakışmaması için değiştirdim

# --- Firebase Bağlantısı ---
@st.cache_resource
def get_firestore_client_wrapper():
    client = initialize_firebase()
    if client:
        pass
    else:
        st.error("🚨 HATA: Firebase'e bağlanılamadı. Lütfen Firebase yapılandırmanızı kontrol edin.")
    return client


db = get_firestore_client_wrapper()

if db is None:
    st.error("Uygulama başlatılamadı: Firebase bağlantısı kurulamadı.")
    st.stop()  # Firebase bağlantısı yoksa uygulamayı durdur

# Firestore Koleksiyon Adları
WAGON_CURRENT_FULLNESS_COLLECTION = "wagon_fullness_current"
WAGON_HISTORICAL_LOGS_COLLECTION = "wagon_fullness_history"
PROCESSING_STATUS_COLLECTION = "processing_status"
PROCESSING_COMPLETE_DOC_ID = "video_analysis_status"


# --- Hava Durumu Bilgisini Alan Fonksiyon (Bu fonksiyonu kaldırıyoruz veya içe aktardığımızı çağırıyoruz) ---
# @st.cache_data(ttl=3600) # Bu dekoratör artık langchain.weather.py'deki fonksiyonda olacak
# def get_langchain_weather_response():
#     # ... bu fonksiyonun tüm içeriğini kaldırın ...


# --- Streamlit Uygulaması Başlangıcı ---
st.set_page_config(layout="wide")
st.markdown("<h1 style='text-align: center; color: #add8e6;'>Metro Vagonu Doluluk Oranları</h1>",
            unsafe_allow_html=True)

# Hava durumu bilgisini artık içe aktardığımız fonksiyondan alıyoruz
# weather_info = get_langchain_weather_response() # Eski çağrı
weather_info = get_weather_report_from_llm() # Yeni çağrı

# LLM'den gelen metnin doğrudan basılmasını sağlıyoruz, çünkü giriş cümlesi ve emoji LLM tarafından üretilecek.
st.markdown(f"<h4 style='text-align: center; color: #add8e6;'>{weather_info}</h4>", unsafe_allow_html=True)

# CSS stillerini başlangıçta bir kez yükle (tren tasarımınız)
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
def replay_historical_logs(db_client, wagon_map, display_placeholder, status_placeholder):
    # Bu fonksiyondaki tüm mesajları `status_placeholder` aracılığıyla göster
    status_placeholder.info("Loglar yeniden oynatılıyor... Lütfen bekleyin.")
    try:
        docs = db_client.collection(WAGON_HISTORICAL_LOGS_COLLECTION).order_by("timestamp").stream()
        historical_logs = [doc.to_dict() for doc in docs]

        if not historical_logs:
            status_placeholder.warning("Oynatmak için tarihsel log bulunamadı.")
            return

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
                    current_dt = timestamp
                    last_dt = last_timestamp
                    time_diff = (current_dt - last_dt).total_seconds()
                    sleep_time = max(0.02, min(0.5, time_diff * 0.1))
                    time.sleep(sleep_time)
                else:
                    time.sleep(0.05)
                last_timestamp = timestamp

        status_placeholder.success("Log oynatma tamamlandı!")

    except Exception as e:
        status_placeholder.error(f"Tarihsel loglar oynatılırken hata: {e}")


# --- Streamlit Uygulamasının Ana Akışı ---

# Yer tutucuları tanımla. Bunlar, dinamik olarak değişecek veya boşaltılacak alanlardır.
train_display_placeholder = st.empty()
completion_message_placeholder = st.empty()
button_container_placeholder = st.empty()
loading_status_placeholder = st.empty()  # Yükleme/işlem durumu mesajları için TEK YER!

# Oturum durum değişkenlerini başlat
if 'show_replay_ui' not in st.session_state:
    st.session_state.show_replay_ui = False
if 'replay_active' not in st.session_state:
    st.session_state.replay_active = False


# Canlı doluluk verilerini çeken ve ekranı güncelleyen yardımcı fonksiyon
def update_current_fullness_and_display_live():
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
        # Hata durumunda da `loading_status_placeholder`'ı kullan
        loading_status_placeholder.error(f"Firestore'dan anlık vagon doluluk verisi okunurken hata: {e}")
        for display_name in video_names.keys():
            current_fullness[display_name] = 0.0

    # Tren görüntüsünü her zaman dedike placeholder'ı kullanarak güncelle
    update_train_display(current_fullness, train_display_placeholder)


# --- Streamlit Uygulamasının Ana Mantığı (Durum Yönetimi) ---

# 1. Durum: Logları yeniden oynatma modu aktif
if st.session_state.replay_active:
    # Bu modda diğer tüm mesajları ve butonları temizle
    completion_message_placeholder.empty()
    button_container_placeholder.empty()
    # loading_status_placeholder mesajları replay_historical_logs fonksiyonu tarafından yönetilecek

    replay_historical_logs(db, video_names, train_display_placeholder, loading_status_placeholder)

    st.session_state.replay_active = False
    st.session_state.show_replay_ui = True
    st.rerun()  # Oynatma bittikten sonra 'tamamlandı' arayüzüne geçiş için yeniden çalıştır

# 2. Durum: Başlangıç yüklemesi veya video işleme devam ediyor (tamamlanma kontrolü)
elif not st.session_state.show_replay_ui:
    # Firebase'den genel işlem tamamlanma durumunu kontrol et
    is_processing_complete_from_firebase = False
    try:
        if db:
            status_doc = get_document(db, PROCESSING_STATUS_COLLECTION, PROCESSING_COMPLETE_DOC_ID)
            if status_doc and status_doc.get("completed", False):
                is_processing_complete_from_firebase = True
    except Exception as e:
        # Hata durumunda da `loading_status_placeholder`'ı kullan
        loading_status_placeholder.warning(
            f"Firestore'dan işlem durumu okunurken hata: {e}. Varsayılan olarak 'tamamlandı' durumu ele alınıyor.")
        is_processing_complete_from_firebase = True

    if is_processing_complete_from_firebase:
        # İşlem tamamlandıysa, oturum durumunu ayarla ve 'tamamlandı' arayüzüne geçmek için yeniden çalıştır
        st.session_state.show_replay_ui = True
        st.rerun()  # Bu rerun, bir sonraki çalışmada alttaki `elif st.session_state.show_replay_ui:` bloğuna düşecek
    else:
        # İşlem hala devam ediyorsa: Yükleme mesajını göster ve anlık verileri güncelle
        loading_status_placeholder.info("Veriler yükleniyor ve durum kontrol ediliyor... Lütfen bekleyin.")
        update_current_fullness_and_display_live()  # Canlı tren verilerini çek ve göster

        time.sleep(1)  # Bir sonraki yeniden çalıştırmadan önce 1 saniye bekle
        st.rerun()  # Streamlit'i yeniden çalıştırarak yeni veriyi çekmesini sağla

# 3. Durum: İşleme tamamlandı, nihai durumu ve yeniden oynatma butonunu göster
elif st.session_state.show_replay_ui:
    loading_status_placeholder.empty()  # Tüm yükleme/durum mesajlarını temizle
    update_current_fullness_and_display_live()  # Trenin son canlı durumunu göster (görüntüyü sabitlemek için)

    completion_message_placeholder.markdown(
        "<br><h3 style='text-align: center; color: #A0EEFF; padding: 10px; background-color: #282828; border-radius: 8px;'>✨ Tüm Vagon Görüntüleri Başarıyla Analiz Edildi! ✨</h3>",
        unsafe_allow_html=True
    )
    with button_container_placeholder:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("Logları Yeniden Oynat", key="replay_button_centered", use_container_width=True):
                st.session_state.replay_active = True
                st.rerun()  # Yeniden oynatma moduna geç