import firebase_admin
from firebase_admin import credentials, firestore

def initialize_firebase():
    try:
        # Önce serviceAccountKey.json ile başlatmayı deneyin, bu daha garanti bir yoldur.
        cred = credentials.Certificate("../../serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
        print("Firebase serviceAccountKey.json ile başarılı bir şekilde başlatıldı.")

    except Exception as e:  # Herhangi bir hatayı yakalamak için genel Exception kullanın
        print(f"Firebase başlatılırken bir hata oluştu: {e}")
        print("Alternatif olarak kimlik bilgisi olmadan başlatma deneniyor (ADC)...")
        try:
            firebase_admin.initialize_app()
            print("Firebase (ADC) ile başarılı bir şekilde başlatıldı.")
        except Exception as e_adc:
            print(f"Firebase (ADC) ile başlatılırken de hata oluştu: {e_adc}")
            print(
                "Lütfen kimlik bilgilerini kontrol edin: serviceAccountKey.json veya Application Default Credentials.")
            return None  # Hata durumunda None döndürün veya bir hata fırlatın

    """try:
        firebase_admin.get_app()
    except ValueError:
        cred = credentials.Certificate("../serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
    print("Firebase başarılı bir şekilde başlatıldı.")"""

    return firestore.client()