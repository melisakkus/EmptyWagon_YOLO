import os
import subprocess
from multiprocessing import Process, freeze_support
import glob
import time

# Firebase istemcisini ve CRUD fonksiyonlarını main.py için import et
from features.database.initialize_firebase import initialize_firebase
# delete_all_documents_in_collection fonksiyonunu import et
from features.database.firestore_crud import create_document, delete_all_documents_in_collection
from firebase_admin import firestore # SERVER_TIMESTAMP için gerekli

# Video işleme fonksiyonunu import et
from features.video_processor import process_video

# Firestore status sabitleri (streamlit_app.py ile eşleşmeli)
PROCESSING_STATUS_COLLECTION = "processing_status"
PROCESSING_COMPLETE_DOC_ID = "video_analysis_status"
WAGON_HISTORICAL_LOGS_COLLECTION = "wagon_fullness_history" # Yeni eklendi: Tarihsel log koleksiyon adı

if __name__ == '__main__':
    freeze_support()

    # main.py için Firebase istemcisini başlat (bu kritik)
    db = initialize_firebase()
    if not db:
        print("🚨 HATA: Firebase istemcisi main.py içinde başlatılamadı. İşlem durumu Firestore'a yazılamayacak.")
        exit() # Firebase bağlantısı olmadan devam etmeyelim

    video_files = glob.glob("data/videos/*.mp4")

    # --- ESKİ TARİHSEL LOGLARI TEMİZLE ---
    try:
        delete_all_documents_in_collection(db, WAGON_HISTORICAL_LOGS_COLLECTION)
    except Exception as e:
        print(f"UYARI: Tarihsel loglar temizlenirken hata oluştu: {e}")
    # --- TEMİZLEME BİTTİ ---

    # --- İşlem başlangıcında 'completed' bayrağını FALSE olarak ayarla ---
    try:
        create_document(db, PROCESSING_STATUS_COLLECTION, {"completed": False, "last_update_time": firestore.SERVER_TIMESTAMP}, document_id=PROCESSING_COMPLETE_DOC_ID)
        print("Firestore: Toplam video işleme başlangıcı için tamamlanma bayrağı sıfırlandı.")
    except Exception as e:
        print(f"UYARI: Firestore'a başlangıç bayrağı yazılırken hata oluştu: {e}")
    # --- DURUM SIFIRLAMA BİTTİ ---


    print("🧵 Video işleme süreçleri başlatılıyor...")
    processes = []

    for video_file in video_files:
        p = Process(target=process_video, args=(video_file,))
        p.start()
        processes.append(p)



    # Video işleme süreçlerinin tamamlanmasını bekle
    for p in processes:
        p.join()

    print("✅ Tüm video işleme tamamlandı.")

    # --- İşlem tamamlandıktan sonra 'completed' bayrağını TRUE olarak ayarla ---
    try:
        create_document(db, PROCESSING_STATUS_COLLECTION, {"completed": True, "last_completion_time": firestore.SERVER_TIMESTAMP}, document_id=PROCESSING_COMPLETE_DOC_ID)
        print("Firestore: Tüm video işleme tamamlandı bayrağı ayarlandı.")
    except Exception as e:
        print(f"UYARI: Firestore'a tamamlama bayrağı yazılırken hata oluştu: {e}")
    # --- DURUM AYARLAMA BİTTİ ---