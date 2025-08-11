import streamlit as st
import json # JSON'u direkt kullanmasak bile, Firebase'in credential.Certificate'i dict alabilir.
import firebase_admin
from firebase_admin import credentials, firestore

# --- 1. Streamlit secrets'tan Firebase kimlik bilgilerini yükle ---
# Bu kısım önceki cevaptaki gibi düzgünce .streamlit/secrets.toml dosyasında tanımlanmış olmalı.
firebase_credentials_dict = {
    "type": st.secrets["firebase"]["type"],
    "project_id": st.secrets["firebase"]["project_id"],
    "private_key_id": st.secrets["firebase"]["private_key_id"],
    "private_key": st.secrets["firebase"]["private_key"],
    "client_email": st.secrets["firebase"]["client_email"],
    "client_id": st.secrets["firebase"]["client_id"],
    "auth_uri": st.secrets["firebase"]["auth_uri"],
    "token_uri": st.secrets["firebase"]["token_uri"],
    "auth_provider_x509_cert_url": st.secrets["firebase"]["auth_provider_x509_cert_url"],
    "client_x509_cert_url": st.secrets["firebase"]["client_x509_cert_url"],
    "universe_domain": st.secrets["firebase"]["universe_domain"]
}

# --- 2. Firebase Bağlantısını Tek Seferlik Başlatmak İçin Fonksiyon Tanımla ---
@st.cache_resource
def initialize_firebase_connection(creds_dict):
    """
    Firebase uygulamasını başlatır ve Firestore istemcisini döndürür.
    Bu fonksiyon Streamlit tarafından yalnızca bir kez çalıştırılır.
    """
    try:
        # Firebase varsayılan uygulamasının zaten başlatılıp başlatılmadığını kontrol edin.
        # Bu, Streamlit'in script'i yeniden çalıştırmasından kaynaklanan hataları önler.
        if not firebase_admin._apps:
            cred = credentials.Certificate(creds_dict)
            firebase_admin.initialize_app(cred)
            st.success("Firebase uygulaması başarıyla başlatıldı!")
        else:
            st.info("Firebase uygulaması zaten başlatılmıştı.") # Zaten başlatılmışsa bilgilendirme

        # Firestore istemcisini döndür
        return firestore.client()
    except Exception as e:
        st.error(f"Firebase başlatılırken veya bağlanılırken hata oluştu: {e}")
        return None # Hata durumunda None döndür

# --- 3. Firebase Bağlantısını Başlat ve Firestore İstemcisini Al ---
db = initialize_firebase_connection(firebase_credentials_dict)

# --- 4. Firestore İstemcisini Kullanma ---
if db:
    st.write("Firestore istemcisi kullanıma hazır.")
    # Örnek: Firestore'dan veri okuma veya yazma
    # try:
    #     doc_ref = db.collection('test_collection').document('test_document')
    #     doc_ref.set({'mesaj': 'Merhaba Firebase!'})
    #     st.success("Veri Firestore'a yazıldı!")
    #     # Veriyi okuma
    #     doc = doc_ref.get()
    #     if doc.exists:
    #         st.write(f"Okunan veri: {doc.to_dict()}")
    #     else:
    #         st.warning("Belge bulunamadı.")
    # except Exception as e:
    #     st.error(f"Firestore işlemi sırasında hata: {e}")
else:
    st.warning("Firebase bağlantısı kurulamadığı için Firestore istemcisi kullanılamıyor.")

# --- 5. Diğer API Anahtarlarını yükle (daha önceki gibi) ---
GOOGLE_API_KEY = st.secrets["general"]["GOOGLE_API_KEY"]
OPENWEATHER_API_KEY = st.secrets["general"]["OPENWEATHER_API_KEY"]

# Uygulamanızın geri kalanı
# ...
st.write(f"Google API Anahtarı yüklendi: {GOOGLE_API_KEY[:5]}...") # İlk 5 karakteri göster
st.write(f"OpenWeather API Anahtarı yüklendi: {OPENWEATHER_API_KEY[:5]}...") # İlk 5 karakteri göster