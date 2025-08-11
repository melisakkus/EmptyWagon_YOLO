# features/database/initialize_firebase.py
import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st # Streamlit secrets'a erişim için

def initialize_firebase():
    """
    Firebase uygulamasını başlatır ve Firestore istemcisini döndürür.
    Streamlit Secrets'taki kimlik bilgilerini kullanır.
    """
    try:
        # Firebase uygulamasının zaten başlatılıp başlatılmadığını kontrol et
        # Streamlit'in sıcak yeniden yüklemesi sırasında birden fazla başlatmayı önlemek için
        if firebase_admin._apps:
            # print("Firebase zaten başlatılmış, mevcut istemci kullanılıyor.") # Opsiyonel: debug için
            return firestore.client()

        # Streamlit Secrets'tan kimlik bilgilerini almayı dene
        # secrets.toml dosyasında her bir Firebase alanını ayrı anahtar olarak tanımladık
        # Örn: type = "service_account", project_id = "...", private_key = "..."
        if "project_id" in st.secrets and "private_key" in st.secrets:
            try:
                firebase_config = {
                    "type": st.secrets["type"],
                    "project_id": st.secrets["project_id"],
                    "private_key_id": st.secrets["private_key_id"],
                    "private_key": st.secrets["private_key"],
                    "client_email": st.secrets["client_email"],
                    "client_id": st.secrets["client_id"],
                    "auth_uri": st.secrets["auth_uri"],
                    "token_uri": st.secrets["token_uri"],
                    "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
                    "client_x509_cert_url": st.secrets["client_x509_cert_url"],
                    "universe_domain": st.secrets["universe_domain"]
                }
                cred = credentials.Certificate(firebase_config)
                firebase_admin.initialize_app(cred)
                # print("Firebase Streamlit secrets ile başarılı bir şekilde başlatıldı.") # Opsiyonel: debug için
                return firestore.client()
            except KeyError as e:
                # Belirli bir sır eksikse yakala
                st.error(f"Streamlit secrets'ta Firebase kimlik bilgisi eksik: '{e}'. Lütfen '.streamlit/secrets.toml' dosyanızı kontrol edin.")
                return None
            except Exception as e:
                # Diğer olası hataları yakala (örn: private_key format hatası)
                st.error(f"Streamlit secrets'tan Firebase başlatılırken hata: {e}")
                st.warning("Lütfen '.streamlit/secrets.toml' dosyasındaki Firebase kimlik bilgilerini doğru formatta girdiğinizden emin olun (özellikle 'private_key').")
                return None
        else:
            # secrets'ta gerekli Firebase anahtarları yoksa
            st.error("Streamlit secrets'ta Firebase kimlik bilgileri bulunamadı. Lütfen '.streamlit/secrets.toml' dosyanızı yapılandırın.")
            return None

    except Exception as e:
        # Tüm diğer beklenmeyen hataları yakala
        st.error(f"❗ Firebase başlatılırken genel bir hata oluştu: {e}")
        st.warning("Uygulama Firebase'e bağlanamadı. Lütfen internet bağlantınızı ve kimlik bilgilerinizi kontrol edin.")
        return None