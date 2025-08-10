# features/database/initialize_firebase.py
import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st # Streamlit secrets'a erişim için
import json # JSON string'i ayrıştırmak için
import os   # <-- BU SATIR ÇOK ÖNEMLİ! Eksik olmadığından emin olun!

def initialize_firebase():
    """
    Firebase uygulamasını başlatır ve Firestore istemcisini döndürür.
    Öncelik sırası: Streamlit Secrets -> serviceAccountKey.json -> Application Default Credentials.
    """
    try:
        # Firebase uygulamasının zaten başlatılıp başlatılmadığını kontrol et
        # Streamlit'in sıcak yeniden yüklemesi sırasında birden fazla başlatmayı önlemek için
        if firebase_admin._apps:
            # print("Firebase zaten başlatılmış, mevcut istemci kullanılıyor.")
            return firestore.client()

        # 1. Streamlit Secrets'tan kimlik bilgilerini almayı dene (Cloud için tercih edilir)
        if "firebase_credentials" in st.secrets:
            try:
                cred_info = json.loads(st.secrets["firebase_credentials"])
                cred = credentials.Certificate(cred_info)
                firebase_admin.initialize_app(cred)
                print("Firebase Streamlit secrets ile başarılı bir şekilde başlatıldı.")
                return firestore.client()
            except Exception as e:
                print(f"Streamlit secrets'tan Firebase başlatılırken hata: {e}")
                # Hata olursa diğer yöntemlere geç
                pass

        # 2. serviceAccountKey.json dosyasından kimlik bilgilerini almayı dene (Yerel geliştirme için)
        # '../..' ifadesi, initialize_firebase.py'nin bulunduğu dizinden (features/database)
        # iki üst dizine (proje köküne) gitmeyi sağlar.
        local_key_path = os.path.join(os.path.dirname(__file__), '..', '..', 'serviceAccountKey.json')

        # Dosyanın varlığını kontrol et
        if os.path.exists(local_key_path):
            try:
                cred = credentials.Certificate(local_key_path)
                firebase_admin.initialize_app(cred)
                print("Firebase serviceAccountKey.json ile başarılı bir şekilde başlatıldı.")
                return firestore.client()
            except Exception as e:
                print(f"serviceAccountKey.json ile Firebase başlatılırken hata: {e}")
                # Hata olursa diğer yöntemlere geç
                pass
        else:
            print(f"UYARI: 'serviceAccountKey.json' bulunamadı: {local_key_path}")


        # 3. Application Default Credentials (ADC) ile başlatmayı dene (Ortam değişkenleri/gcloud config)
        firebase_admin.initialize_app()
        print("Firebase (ADC) ile başarılı bir şekilde başlatıldı.")
        return firestore.client()

    except Exception as e:
        print(f"❗ Firebase başlatılırken beklenmeyen bir hata oluştu: {e}")
        print("Lütfen kimlik bilgilerini kontrol edin: Streamlit Secrets, serviceAccountKey.json veya Application Default Credentials.")
        return None