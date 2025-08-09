# 🚇 MetroWagon: Metro Duraklarında Akıllı Vagon Doluluk Gösterge Sistemi

MetroWagon, metro duraklarında yerleştirilen akıllı ekranlar aracılığıyla gelen trenlerin vagon doluluk oranlarını gerçek zamanlı olarak gösteren, AI destekli yenilikçi bir toplu taşıma optimizasyon projesidir. Bu sistem sayesinde yolcular, hangi vagonların daha boş olduğunu önceden görebilir ve metro kullanım deneyimlerini optimize edebilirler.

---

## 📖 Proje Amacı ve Faydaları

### Ana Hedef
Metro duraklarında yerleştirilen ekranlarda, gelen trenlerin her vagonunun doluluk oranını gerçek zamanlı olarak göstermek ve yolcuların daha bilinçli vagon seçimi yapmasını sağlamak.

### Toplu Taşıma Optimizasyonu
- **Yolcu Dağılımı:** Merdivenlere yakın vagonların aşırı dolmasını önlemek
- **Zaman Tasarrufu:** Yolcuların daha boş vagonları tercih etmesini sağlamak
- **Konfor Artışı:** Metro kullanım deneyimini iyileştirmek
- **Verimlilik:** Vagon kapasitesinin daha dengeli kullanılması

---

## 🚀 Kullanılan Teknolojiler

- **Python 3.x**  
  Projenin ana programlama dili.

- **OpenCV**  
  Görüntü işleme ve video analizi için.

- **YOLO (You Only Look Once)**  
  Derin öğrenme tabanlı kişi sayısı tespiti (vagon doluluk analizi için).

- **Streamlit**  
  Kullanıcı dostu, etkileşimli web arayüzü.


- **LangChain**  
  Doğal dil işleme ve yapay zeka destekli analizler için.

---

## 📖 Proje Tanıtımı

MetroWagon sistemi, metro vagonlarına yerleştirilen kameralardan alınan görüntüleri AI teknolojileriyle analiz ederek kişi sayısını tespit eder. Bu sayı, her vagon için optimum kapasiteye bölünerek doluluk yüzdesi hesaplanır. Sonuçlar, metro duraklarındaki ekranlarda gerçek zamanlı olarak gösterilir.

### Sistem Bileşenleri
1. **Vagon Kameraları:** Her vagonda kişi sayısını tespit eden AI destekli kamera sistemi
2. **Durak Ekranları:** Merkezi ve aktarma duraklarda vagon doluluk bilgilerini gösteren dijital ekranlar
3. **AI Analiz Merkezi:** Görüntü işleme ve doluluk hesaplama algoritmaları
4. **Gerçek Zamanlı Veri Aktarımı:** Durak ekranlarına anlık bilgi gönderimi

---

## 🗺️ Proje Geliştirme Akışı

### 1. Proje Planlama ve Tasarım
- **Claude üzerinde proje akışı hazırlama** 

### 2. Kod Geliştirme
- **PyCharm üzerinde Object Tracking ve Counting için kod yazma** - Kişi sayısı tespit algoritmaları geliştirildi

### 3. AI Model ve Dataset Hazırlığı
- **Runway, Hailuo AI gibi AI Toollar ile video üretimi** - Metro vagon senaryoları için test verileri oluşturuldu
- **Roboflow hazır dataset ile Google Colab üzerinde YOLOv8 fine tune işlemi** - Metro ortamına özel kişi tespit modeli optimize edildi

### 4. API Entegrasyonları
- **OpenWeather üzerinde hava durumu apisi alma** - Metro konumunun hava durumu bilgisi alındı
- **LangChain frameworku ile OpenWeather Api'sinden gelen hava durumunu Gemini 2.5Flash ile kullanıcı dostu bir şekilde yorumlayarak gösterme** - AI destekli hava durumu yorumu kullanıcılara sunuldu

### 5. Kullanıcı Arayüzü ve Dağıtım
- **Streamlit ile kullanıcı sayfası** - Metro kullanıcıları için ekran tasarımı geliştirildi
- **Git - Github ile versiyon kontrolü** - Proje versiyon yönetimi

---

## 🛠️ Kullanılan AI Tool & Model

- **Geliştirme Araçları:** PyCharm, Cursor, Claude, Google AI Studio, ChatGPT
- **AI Modeller:** Gemini, YOLO
- **AI Video Üretim:** Runway, Hailuo AI
- **Dataset ve Model Eğitimi:** Roboflow, Google Colab
- **API ve Framework:** OpenWeather, LangChain
- **Web Framework:** Streamlit
- **Versiyon Kontrolü:** Git, GitHub

---

## 📖 Sistem İşleyişi

1. **Veri Toplama:**  
   - Metro vagonlarındaki kameralardan gerçek zamanlı görüntü akışı alınır.

2. **AI Tabanlı Kişi Sayısı Tespiti:**  
   - `features/video_processor.py` ve YOLO modelleri ile vagon içindeki kişi sayısı tespit edilir.
   - Sonuçlar `outputs/` klasöründe görsel ve metin olarak kaydedilir.

3. **Doluluk Oranı Hesaplama:**  
   - Tespit edilen kişi sayısı, vagon optimum kapasitesine bölünerek doluluk yüzdesi hesaplanır.

4. **Gerçek Zamanlı Veri Aktarımı:**  
   - Hesaplanan doluluk oranları, metro duraklarındaki ekranlara anlık olarak gönderilir.

5. **Durak Ekranları:**  
   - Merkezi ve aktarma duraklardaki ekranlarda her vagonun doluluk oranı görsel olarak gösterilir.

6. **Ek Özellikler:**  
   - Hava durumu entegrasyonu (`features/get_weather.py`, `features/langchain_weather.py`) ile konum hava durumu hakkında bilgi verilir.

---

## 🗂️ Özellikler (`features/` klasörü)

- **get_weather.py**  
  OpenWeatherMap API ile hava durumu verisi çekme.

- **langchain_weather.py**  
  Hava durumunu AI ile kullanıcı dostu bir şekilde yorumlama.

- **reference_setup.py**  
  Metro vagonu ilgili alan referans değerleri.

- **streamlit_app.py**  
  Metro kullanıcıları için sunum ekranı.

- **video_processor.py**  
  Metro vagon görüntülerinden kişi sayısı tespiti ve doluluk hesaplama.

---

## 🎯 Gelecek Geliştirmeler

- **Mobil Uygulama:** Yolcuların kişisel cihazlarından doluluk bilgilerine erişimi
- **Tahmin Algoritmaları:** Makine öğrenimi ile doluluk tahminleri
- **Çoklu Metro Hattı Desteği:** Farklı metro hatlarında sistem entegrasyonu

