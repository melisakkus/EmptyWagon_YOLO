# features/database/initialize_firebase.py

import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

# Firebase kimlik bilgilerini Streamlit secrets'tan alır
# Bu kısım sadece bu fonksiyon içinde veya çağrılmadan önce tanımlanmalı
# çünkü @st.cache_resource tarafından yakalanacaktır.

# Bu fonksiyon Streamlit uygulaması tarafından çağrılacaktır.
# Fonksiyonun adı 'initialize_firebase' olsun.
@st.cache_resource
def initialize_firebase():
    """
    Firebase uygulamasını başlatır ve Firestore istemcisini döndürür.
    Bu fonksiyon Streamlit tarafından yalnızca bir kez çalıştırılır.
    """
    try:
        # Streamlit secrets'tan Firebase kimlik bilgilerini yükle
        # Bu dictionary'nin her zaman doğru formatta ve erişilebilir olduğundan emin olmalıyız.
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

        # Debugging için: Private key'in doğru okunup okunmadığını kontrol edin.
        # Bu satırı sadece hata ayıklarken kullanın, üretimde kaldırabilirsiniz.
        # st.write(f"Private Key (repr): {repr(firebase_credentials_dict['private_key'])}")


        # Firebase varsayılan uygulamasının zaten başlatılıp başlatılmadığını kontrol edin.
        if not firebase_admin._apps:
            cred = credentials.Certificate(firebase_credentials_dict)
            firebase_admin.initialize_app(cred)
            #st.success("Firebase uygulaması başarıyla başlatıldı!")
        else:
            # st.info("Firebase uygulaması zaten başlatılmıştı.") # Cache_resource kullanıldığında bu mesajı görmeyeceğiz.
            pass # Zaten başlatılmışsa bir şey yapmaya gerek yok, sadece istemciyi döndüreceğiz.

        # Firestore istemcisini döndür
        return firestore.client()
    except Exception as e:
        st.error(f"Firebase başlatılırken veya bağlanılırken hata oluştu: {e}")
        return None # Hata durumunda None döndür

# Bu dosyada başka bir kod olmamalı (global değişken atamaları vb.)
# initialize_firebase fonksiyonu Streamlit_app.py tarafından çağrılacaktır.