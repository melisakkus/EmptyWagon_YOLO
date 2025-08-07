import os
import subprocess
from multiprocessing import Process, freeze_support
import glob
from features.video_processor import process_video
from features.langchain_weather import get_langchain_weather_response

if __name__ == '__main__':
    freeze_support()

    video_files = glob.glob("data/videos/*.mp4") #glob dosya adı desenlerine göre dosya arar.
    weather_info = get_langchain_weather_response()

    #print("🧵 PROCESSING başladı...")
    #start = time.time()

    processes = []

    for video_file in video_files:
        p = Process(target=process_video, args=(video_file,))
        p.start()
        processes.append(p)

    # Streamlit uygulamasını başlat
    print("🚀 Streamlit uygulamasını başlatılıyor...")
    try:
        # Ortam değişkenini ayarlayarak hava durumu bilgisini Streamlit'e aktar
        env = os.environ.copy()
        env["WEATHER_INFO"] = weather_info # Burası önemli

        subprocess.Popen(["streamlit", "run", "features/streamlit_app.py"], env=env, shell=True)
        print("✅ Streamlit uygulaması başarıyla başlatıldı.")
    except Exception as e:
        print(f"🚨 Streamlit uygulamasını başlatırken bir hata oluştu: {e}")

    # Video işleme süreçlerinin tamamlanmasını bekle
    for p in processes:
        p.join()

    print("✅ Tüm video işleme tamamlandı.")

    #end = time.time()
    #print(f"✅ Processing süresi: {end - start:.2f} saniye\n")
"""

import glob
import threading
import time

from features.video_processor import process_video   # Aynı fonksiyon kullanılabilir

def start_thread(video_file):
    process_video(video_file)  # Her thread aynı işlevi yapar

if __name__ == '__main__':
    # 🎞️ Videoları listele
    video_files = glob.glob("data/videos/*.mp4")

    print("🧵 THREADING başladı...")
    start = time.time()

    threads = []

    for video_file in video_files:
        t = threading.Thread(target=start_thread, args=(video_file,))
        t.start()
        threads.append(t)

    # ⏳ Tüm thread'lerin bitmesini bekle
    for t in threads:
        t.join()

    end = time.time()
    print(f"✅ Threading süresi: {end - start:.2f} saniye\n")

"""
