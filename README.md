# 🚂 EmptyWagon: Akıllı Vagon Takip ve Analiz Sistemi

EmptyWagon, demiryolu vagonlarının doluluk oranını ve konumunu gerçek zamanlı olarak analiz eden, modern teknolojilerle geliştirilmiş yenilikçi bir projedir. Görüntü işleme, makine öğrenimi ve bulut tabanlı veri yönetimiyle, demiryolu taşımacılığında verimliliği artırmayı hedefler.

---

## 🚀 Kullanılan Teknolojiler

- **Python 3.x**  
  Projenin ana programlama dili.

- **OpenCV**  
  Görüntü işleme ve video analizi için.

- **YOLO (You Only Look Once)**  
  Derin öğrenme tabanlı nesne tespiti (vagon doluluk analizi için).

- **Streamlit**  
  Kullanıcı dostu, etkileşimli web arayüzü.

- **Google Firebase (Firestore)**  
  Gerçek zamanlı veri tabanı ve bulut entegrasyonu.

- **LangChain**  
  Doğal dil işleme ve yapay zeka destekli analizler için.

---

## 📖 Proje Tanıtımı

EmptyWagon, demiryolu vagonlarının iç doluluk oranını ve konumunu otomatik olarak tespit eder. Video ve görsel verilerden alınan bilgiler, makine öğrenimi modelleriyle analiz edilir ve sonuçlar hem görsel olarak hem de bulut tabanlı veri tabanında saklanır. Kullanıcılar, Streamlit arayüzü üzerinden anlık raporlar ve geçmiş analizlere kolayca erişebilir.

---

## 🗺️ Proje Akışı

1. **Veri Toplama:**  
   - Vagonlara ait videolar ve referans görseller `data/` klasöründe saklanır.

2. **Görüntü İşleme & Analiz:**  
   - `features/video_processor.py` ve YOLO modelleri ile vagon doluluk oranı tespit edilir.
   - Sonuçlar `outputs/` klasöründe görsel ve metin olarak kaydedilir.

3. **Gerçek Zamanlı Takip:**  
   - `features/real_time_tracking.py` ile vagonların anlık konumu ve durumu izlenir.

4. **Veri Tabanı Entegrasyonu:**  
   - `features/database/` altındaki modüller ile analiz sonuçları Firestore'a kaydedilir.

5. **Web Arayüzü:**  
   - `features/streamlit_app.py` ile kullanıcılar, analizleri ve raporları interaktif olarak görüntüler.

6. **Ekstra Özellikler:**  
   - Hava durumu entegrasyonu (`features/get_weather.py`, `features/langchain_weather.py`) ile analizlere çevresel faktörler de eklenir.

---

## 🗂️ Özellikler (`features/` klasörü)

- **database/**  
  Firestore/Firebase ile veri tabanı işlemleri (CRUD, bağlantı, başlatma).

- **get_weather.py**  
  OpenWeatherMap API ile hava durumu verisi çekme.

- **langchain_weather.py**  
  Hava durumu bilgisini LLM (LangChain + Google GenAI) ile doğal dilde özetleme.

- **reference_setup.py**  
  Referans görsel ve veri ayarları.

- **streamlit_app.py**  
  Kullanıcı arayüzü ve görsel raporlama (Streamlit tabanlı).

- **video_processor.py**  
  Video işleme, YOLO ile doluluk tespiti ve analiz.

---

