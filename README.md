# 🚇 MetroVision: Akıllı Vagon Doluluk Takip Sistemi

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-yellow.svg)
![Firebase](https://img.shields.io/badge/Firebase-Firestore-orange.svg)

## 🎯 Proje Özeti

MetroVision, metro trenlerindeki vagon doluluk oranlarını gerçek zamanlı olarak tespit eden ve yolculara görselleştiren yapay zeka destekli bir sistemdir. Günlük yaşantımızda sıkça karşılaştığımız "hangi vagona bineyim?" sorusuna AI tabanlı bir çözüm getirerek, metro istasyonlarında daha verimli yolcu dağılımı sağlamayı hedefler.

## 🚀 Problem & Çözüm

### Mevcut Durum
Modern toplu taşıma sistemlerinde yolcular, tren gelmeden önce hangi vagonların daha az dolu olduğunu bilemez. Bu durum özellikle yoğun saatlerde:
- Dengesiz yolcu dağılımına (bazı vagonlar çok dolu, bazıları boş)
- İstasyon peronlarında kalabalık oluşumuna
- Yolcu konfor ve güvenlik sorunlarına
- Toplu taşımada verimsizliğe
sebep olmaktadır.

### Önerilen Çözüm
MetroVision, yapay zeka destekli görüntü analizi ile metro vagonlarındaki yolcu yoğunluğunu gerçek zamanlı olarak tespit eder. İstasyon peronlarına yerleştirilecek dijital ekranlar aracılığıyla yolculara vagon bazında doluluk bilgisi sunarak:
- Yolcu trafiğinin vagonlar arasında dengeli dağılımını
- İstasyon peronlarında daha düzenli bekleyiş sürecini
- Toplu taşımada artan konfor ve verimliliği
sağlamayı hedefler.

## 🏗️ Sistem Mimarisi

### Sistem Akışı
```
Video Input → Fine-tuned YOLOv8 Detection → Person Tracking → 
Count Zone Analysis → Occupancy Calculation → Firebase Firestore → 
Streamlit Cloud Dashboard → "Logları Getir" Button → Historical Data Visualization

OpenWeather API → LangChain + Gemini AI → User-friendly Weather Info
```

## ✨ Özellikler (Features)

### 🎥 **Video Analizi & Deep Learning**
- **Fine-tuned YOLOv8**: Özel eğitilmiş model ile yüksek doğrulukta kişi tespiti
- **Person Tracking**: İnsan varlığının sürekli takibi ve izlenmesi
- **Sayım Bölgesi**: Vagon için optimize edilmiş analiz bölgesi
- **Gerçek Zamanlı Doluluk**: Anlık yolcu sayısına göre doluluk oranı hesaplama

### 📊 **Veri Yönetimi & Depolama**
- **Firebase Firestore Entegrasyonu**: Bulut tabanlı NoSQL veri saklama
- **Çoklu Koleksiyon Yapısı**: Anlık durum ve geçmiş kayıtları ayrı tutma
- **Paralel Video İşleme**: `multiprocessing` ile çoklu video dosyası eşzamanlı analizi
- **Otomatik Veri Temizleme**: Sistem başlangıcında eski logları temizleme

### 🌐 **Kullanıcı Arayüzü & Görselleştirme**
- **Streamlit Cloud Dashboard**: Production-ready web arayüzü
- **"Logları Getir" Butonu**: Firebase'deki işlenmiş verileri manuel yükleme
- **Dinamik Renk Kodlama**: Doluluk oranına göre vagon renklendirme
  - 🔵 Boş (0-9%)
  - 🟢 Az Dolu (10-29%)
  - 🟠 Orta Dolu (30-59%)
  - 🔴 Çok Dolu (60%+)
- **Tarihsel Log Oynatma**: "Logları Yeniden Oynat" ile animasyonlu veri görüntüleme
- **İki Mod Desteği**: Yerel geliştirme için canlı güncelleme, cloud için manuel veri çekimi

### 🌤️ **Akıllı Hava Durumu Entegrasyonu**
- **OpenWeather API**: Güncel meteorolojik veri çekimi
- **LangChain Framework**: Yapılandırılmış prompt yönetimi
- **Google Gemini 2.5 Flash**: Ham veriyi kullanıcı dostu metne dönüştürme
- **Emoji Destekli Açıklamalar**: Samimi ve anlaşılır hava durumu yorumları
- **Akıllı Cache**: 1 saatlik veri önbellekleme ile performans optimizasyonu

### 🔧 **Teknik Özellikler**
- **Ayrık İşlem Mimarisi**: Video işleme ve web arayüzü bağımsız çalışma
- **Cloud-Ready Deployment**: Streamlit Cloud için optimize edilmiş yapı
- **Manuel Veri Senkronizasyonu**: "Logları Getir" ile kontrollü veri yükleme
- **Kaynak Optimizasyonu**: Firebase bağlantısı tek instance yönetimi
- **Güvenli Konfigürasyon**: API anahtarları `st.secrets` ile yönetimi

## 🛠️ Teknoloji Stack'i

### **Deep Learning & Computer Vision**
- **Fine-tuned YOLOv8**: Özel eğitilmiş nesne tespit modeli
- **Google Gemini 2.5 Flash**: Doğal dil işleme
- **LangChain**: LLM orkestrasyon framework'ü

### **Backend & Database**
- **Python 3.8+**: Ana programlama dili
- **Firebase Firestore**: NoSQL bulut veritabanı
- **OpenWeather API**: Hava durumu servisi

### **Frontend & Deployment**
- **Streamlit**: Web uygulaması framework'ü
- **Streamlit Cloud**: Bulut deployment platformu
- **HTML/CSS**: Özel görselleştirmeler

### **Development Tools & IDEs**
- **PyCharm**: Ana geliştirme ortamı
- **Cursor**: AI destekli kod editörü
- **Google Colab**: Model fine-tuning ortamı
- **Git/GitHub**: Versiyon kontrol sistemi

### **AI Assistant & Development**
- **Claude**: AI destekli kod geliştirme ve problem çözme
- **Google AI Studio**: Kod geliştirme, debugging
- **ChatGPT**: Geliştirme sürecinde danışmanlık

### **AI Content Creation & Media**
- **Runway ML**: AI video üretimi
- **Hailuo AI**: Video generation platformu

### **Data & Model Management**
- **Roboflow**: Dataset hazırlama ve yönetimi
- **YOLOv8 (Ultralytics)**: Custom model fine-tuning

## 📁 Proje Yapısı

```
EmptyWagon/
├── 📁 .cursor/                    # Cursor editor konfigürasyonu
├── 📁 .devcontainer/             # Development container ayarları  
├── 📁 .streamlit/                # Streamlit konfigürasyon dosyaları
├── 📁 .venv/                     # Python sanal ortamı
├── 📁 data/                      # Giriş veri dosyaları
├── 📁 features/                  # Ana uygulama modülleri
│   ├── 📁 database/
│   │   └── 🐍 __init__.py
│   ├── 🐍 get_weather.py        # OpenWeather API entegrasyonu
│   ├── 🐍 langchain_weather.py  # AI destekli hava durumu yorumlama
│   ├── 🐍 reference_setup.py    # Koordinat işaretleme ve kaydetme
│   ├── 🐍 streamlit_app.py      # Ana Streamlit web arayüzü
│   └── 🐍 video_processor.py    # Video analiz ve işleme modülü
├── 📁 models/                    # YOLO modelleri ve ağırlık dosyaları
├── 📁 outputs/                   # İşlenmiş video çıkışları
├── 📄 .env                       # Çevre değişkenleri
├── 📄 .gitignore                # Git ignore dosyası
├── 🐍 config.py                 # Ana konfigürasyon ayarları
├── 🐍 main.py                   # Ana orkestratör betik (video multiprocessing ve logging) 
├── 📖 README.md                 # Proje dokümantasyonu
├── 📄 requirements.txt          # Python bağımlılıkları
```

## 🚀 Kurulum & Çalıştırma

### 1. Repository'yi Klonlayın
```bash
git clone https://github.com/melisakkus/EmptyWagon_YOLO.git
cd EmptyWagon_YOLO
```

### 2. Bağımlılıkları Yükleyin
```bash
pip install -r requirements.txt
```

### 3. Çevre Değişkenlerini Ayarlayın
Streamlit secrets dosyasını oluşturun:
```toml
# .streamlit/secrets.toml
[firebase]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\nyour-private-key\n-----END PRIVATE KEY-----\n"
client_email = "your-service-account-email@your-project.iam.gserviceaccount.com"
client_id = "your-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "your-cert-url"

[api_keys]
openweather_api_key = "your_openweather_key"
google_api_key = "your_gemini_key"
```

### 4. Video Dosyalarını Ekleyin
MP4 formatındaki video dosyalarınızı `data/videos/` klasörüne yerleştirin.

### 5. Uygulamayı Başlatın
```bash
# Video analiz işlemcisi (Firebase'e log kaydeder)
python main.py

# Ayrı terminalde Streamlit arayüzü
streamlit run features/streamlit_app.py
```

## 🎮 Kullanım

### **Yerel Geliştirme Ortamı**
1. **Video Yükleme**: MP4 video dosyalarınızı `data/videos/` klasörüne koyun
2. **Video Analizi**: `python main.py` komutuyla video işleme sürecini başlatın
3. **Dashboard Başlatma**: Ayrı terminalde `streamlit run features/streamlit_app.py` ile arayüzü açın
4. **Canlı Takip**: Video analizi devam ederken Firebase'den canlı veri güncellemeleri

### **Streamlit Cloud (Canlı Demo)**
1. **Log İşleme**: "Logları Getir" butonuna basarak Firebase'deki işlenmiş verileri yükleyin
2. **Tarihsel Analiz**: "Logları Yeniden Oynat" ile zaman serisi animasyonu görüntüleyin
3. **Doluluk Takibi**: Renk kodlu vagon durumu görselleştirmesi
4. **Hava Durumu**: AI destekli güncel hava durumu bilgisi

## 🎯 Öne Çıkan Özellikler

### 🔄 **Paralel İşleme**
`multiprocessing` kütüphanesi ile çoklu video dosyası eş zamanlı işleme

### 📈 **Cloud-First Deployment**
Firebase Firestore üzerinden video işleme sonuçlarının Streamlit Cloud'a iletimi

### 🎨 **Dinamik Veri Yükleme**
"Logları Getir" butonu ile manuel veri çekimi ve görselleştirme

### 🧠 **AI Destekli Hava Durumu**
Ham meteoroloji verilerini samimi, anlaşılır metne dönüştürme

## 📊 Performans & Optimizasyon

- **Önbellekleme**: Hava durumu verileri 1 saat cache'leniyor
- **Kaynak Yönetimi**: Firebase bağlantısı tek instance olarak yönetiliyor
- **Asenkron İşleme**: Video analizi arka planda, UI responsive kalıyor

## 🔧 Modül Detayları

### **main.py** - Ana Orkestratör
Ana orchestrator olarak Firebase bağlantısını kurar, tarihsel verileri temizler, paralel video işleme süreçlerini başlatır ve Streamlit arayüzünü çalıştırır.

### **video_processor.py** - Video Analiz Modülü  
YOLOv8 ile kişi tespiti, multi-object tracking, sayım bölgesi analizi ve Firebase'e veri kaydı gerçekleştirir.

### **features/streamlit_app.py** - Web Arayüzü
Dinamik dashboard ile vagon doluluk görselleştirmesi, tarihsel log animasyonu ve hava durumu entegrasyonu sunar.

### **features/get_weather.py** - Hava Durumu API
OpenWeatherMap API'si ile koordinat bazlı hava durumu verisi çeker.

### **features/langchain_weather.py** - AI Hava Durumu
LangChain ve Gemini ile ham hava durumu verilerini kullanıcı dostu metne dönüştürür.

## 🔮 Gelecek Hedefler

- Gerçek zamanlı kamera entegrasyonu
- Farklı şehir metroları için adaptasyon
- Makine öğrenmesi ile yoğunluk tahmini
- Metro istasyonlarına fiziksel ekran entegrasyonu

## 👥 İletişim

**Proje Sahibi**: Melisa Akkuş  
**Demo**: https://emptywagons.streamlit.app/

---

⭐ **Bu projeyi beğendiyseniz, yıldız vermeyi unutmayın!**

*"Akıllı şehirler, akıllı çözümlerle mümkün"* 🌟

## 📸 Proje Görselleri ve Videolar

### 📊 **Sistem Ekran Görüntüleri**

#### Streamlit Dashboard
<img width="1920" height="1200" alt="Ekran görüntüsü 2025-08-11 213018" src="https://github.com/user-attachments/assets/9d7869b7-7f3f-492f-b5b1-3660cb657b37" />

<img width="1920" height="1200" alt="Ekran görüntüsü 2025-08-11 213023" src="https://github.com/user-attachments/assets/d9a8162a-c303-4a56-9a64-af5637b264e2" />

<img width="1920" height="1200" alt="Ekran görüntüsü 2025-08-11 213029" src="https://github.com/user-attachments/assets/e5861937-7a98-4321-ab25-18669f383b9a" />

#### YOLOv8 Video Analizi

https://github.com/user-attachments/assets/c13e53c5-70aa-4295-acf1-4287f1024e8e
