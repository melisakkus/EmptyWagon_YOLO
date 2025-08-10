import os
import subprocess
from multiprocessing import Process, freeze_support
import glob
import time # İstersen zaman ölçümü için kalsın, şu an yorum satırı

# features.video_processor artık doluluk oranlarını Firestore'a yazıyor
from features.video_processor import process_video

# features.langchain_weather artık doğrudan streamlit_app.py içinde kullanılacak
# from features.langchain_weather import get_langchain_weather_response


if __name__ == '__main__':
    freeze_support()

    # İşlenecek video dosyalarını bul
    # "data" klasörünüzün projenin kök dizininde olduğundan emin olun.
    video_files = glob.glob("data/videos/*.mp4")

    # --- ESKİ YEREL LOG TEMİZLEME KISMI - ARTIK GEREKLİ DEĞİL (Firestore kullanıyoruz) ---
    # Log dosyaları artık Firebase Firestore'a yazıldığı için yerel temizlemeye gerek yok.
    # Bu kısmı silin veya yorum satırı yapın:
    # log_dir = os.path.join("outputs", "logs")
    # os.makedirs(log_dir, exist_ok=True)
    # for f in os.listdir(log_dir):
    #     if f.endswith(("_fullness.txt", "video_processing_complete.txt")):
    #         os.remove(os.path.join(log_dir, f))
    # print("Firestore'a geçildiği için yerel log temizleme kaldırıldı.")
    # ---------------------------------------------------------------------------------

    print("🧵 Video işleme süreçleri başlatılıyor...")
    # start = time.time() # Zaman ölçümü istersen aktif et

    processes = []

    # Her bir video için ayrı bir işlem başlat
    for video_file in video_files:
        p = Process(target=process_video, args=(video_file,))
        p.start()
        processes.append(p)

    # Streamlit uygulamasını başlat
    print("🚀 Streamlit uygulamasını başlatılıyor...")
    try:
        # Hava durumu bilgisini Streamlit uygulaması kendi içinde çekecek.
        # Bu nedenle 'env' değişkenine ve 'WEATHER_INFO'ya artık gerek yok.
        subprocess.Popen(["streamlit", "run", "features/streamlit_app.py"])
        print("✅ Streamlit uygulaması başarıyla başlatıldı.")
    except Exception as e:
        print(f"🚨 Streamlit uygulamasını başlatırken bir hata oluştu: {e}")

    # Video işleme süreçlerinin tamamlanmasını bekle
    for p in processes:
        p.join()

    print("✅ Tüm video işleme tamamlandı.")

    # --- ESKİ YEREL TAMAMLAMA BAYRAĞI OLUŞTURMA KISMI - ARTIK GEREKLİ DEĞİL ---
    # video_processor.py zaten tüm videolar işlendikten sonra Firestore'daki
    # 'video_analysis_status' dokümanını 'completed: True' olarak güncelliyor.
    # Bu kısmı silin veya yorum satırı yapın:
    # processing_complete_flag_path = os.path.join(log_dir, "video_processing_complete.txt")
    # with open(processing_complete_flag_path, "w") as f:
    #     f.write("completed")
    # print("Firestore'a geçildiği için yerel tamamlama bayrağı kaldırıldı.")
    # ---------------------------------------------------------------------------------

    # end = time.time() # Zaman ölçümü istersen aktif et
    # print(f"✅ Processing süresi: {end - start:.2f} saniye\n")