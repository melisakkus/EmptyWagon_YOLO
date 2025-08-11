import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st
import json


def initialize_firebase():
    """
    Firebase uygulamasını başlatır ve Firestore istemcisini döndürür.
    Streamlit Secrets'taki kimlik bilgilerini kullanır.
    """
    try:
        # Firebase uygulamasının zaten başlatılıp başlatılmadığını kontrol et
        if firebase_admin._apps:
            return firestore.client()

        # Streamlit Secrets'tan kimlik bilgilerini al
        if all(key in st.secrets for key in ["type", "project_id", "private_key", "client_email"]):
            try:
                # Private key'deki kaçış karakterlerini düzelt
                private_key = st.secrets["private_key"]
                if isinstance(private_key, str):
                    # Eğer kaçış karakterleri varsa düzelt
                    private_key = private_key.replace('\\n', '\n')

                firebase_config = {
                    "type": st.secrets["type"],
                    "project_id": st.secrets["project_id"],
                    "private_key_id": st.secrets["private_key_id"],
                    "private_key": private_key,
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

                # Bağlantıyı test et
                db = firestore.client()
                # Basit bir test sorgusu yaparak bağlantıyı doğrula
                try:
                    # Test koleksiyonuna erişmeyi dene
                    collections = db.collections()
                    st.success("✅ Firebase başarıyla bağlandı!")
                    return db
                except Exception as test_error:
                    st.error(f"Firebase bağlantı testi başarısız: {test_error}")
                    return None

            except ValueError as ve:
                st.error(f"Firebase kimlik bilgilerinde format hatası: {ve}")
                st.info("Private key formatını kontrol edin. Satır sonları (\\n) doğru şekilde kodlanmış olmalı.")
                return None
            except Exception as e:
                st.error(f"Firebase başlatma hatası: {e}")
                return None
        else:
            missing_keys = [key for key in ["type", "project_id", "private_key", "client_email"]
                            if key not in st.secrets]
            st.error(f"Eksik Firebase kimlik bilgileri: {missing_keys}")
            st.info("Lütfen .streamlit/secrets.toml dosyanızı kontrol edin.")
            return None

    except Exception as e:
        st.error(f"❗ Firebase genel hatası: {e}")
        return None
