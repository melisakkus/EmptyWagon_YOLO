import streamlit as st
import os
import time

st.set_page_config(layout="wide")

st.title("Metro Vagonu Doluluk Oranları")

# CSS stillerini başlangıçta bir kez yükle
st.markdown("""
<style>
    .train-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-top: 30px;
        padding: 20px;
        background-color: #1a1a1a; /* Raylar için koyu arka plan */
        border-radius: 15px;
        box-shadow: inset 0 0 10px rgba(0,0,0,0.7);
        width: 100%;
        overflow-x: auto;
        position: relative;
    }
    .wagon-shell, .locomotive-shell {
        width: 200px;
        height: 100px;
        background-color: #333;
        border: 2px solid #555;
        border-radius: 15px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        align-items: center;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        color: white;
        box-shadow: 3px 3px 8px rgba(0,0,0,0.4);
        flex-shrink: 0;
        padding: 5px;
        position: relative;
    }
    .locomotive-shell {
        width: 150px;
    }
    .wagon-content {
        width: 90%;
        height: 70px; /* Yüksekliği biraz daha artırdık */
        border-radius: 8px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        transition: background-color 0.5s ease;
        margin-top: 0px;
        margin-bottom: 0px;
        padding: 5px 0; /* Üstten ve alttan biraz dolgu ekleyelim */
    }
    .wagon-name {
        font-size: 0.9em; /* Yazı boyutunu biraz küçültelim */
        font-weight: bold;
        margin: 0; /* Boşlukları sıfırla */
        line-height: 1.1; /* Satır yüksekliğini ayarla */
    }
    .wagon-percentage {
        font-size: 1.5em; /* Yüzde yazısını biraz küçültelim */
        font-weight: bold;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
        line-height: 1.1; /* Satır yüksekliğini ayarla */
        margin: 0; /* Boşlukları sıfırla */
    }
    .wagon-status-text {
        font-size: 0.7em; /* Durum yazısını daha da küçültelim */
        font-style: italic;
        margin: 0; /* Boşlukları sıfırla */
        line-height: 1.1; /* Satır yüksekliğini ayarla */
    }
    .window-row {
        display: flex;
        justify-content: space-around;
        width: 90%;
        margin-top: 5px;
    }
    .window, .door {
        background-color: #add8e6;
        border: 1px solid #222;
        border-radius: 3px;
        height: 25px;
    }
    .window {
        width: 35px;
    }
    .door {
        width: 25px;
        background-color: #444;
    }
    .loco-window {
        width: 45px;
        height: 30px;
        background-color: #add8e6;
        border: 1px solid #222;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .connector {
        width: 30px;
        height: 10px;
        background-color: #666;
        border-radius: 5px;
        flex-shrink: 0;
        position: relative;
        margin: 0 -5px;
        z-index: 1;
    }
    .connector::before, .connector::after {
        content: '';
        position: absolute;
        top: -5px;
        width: 8px;
        height: 20px;
        background-color: #555;
        border-radius: 3px;
    }
    .connector::before { left: 0; }
    .connector::after { right: 0; }

    .locomotive-front .loco-body {
        border-top-left-radius: 40px;
        border-bottom-left-radius: 40px;
        border-top-right-radius: 15px;
        border-bottom-right-radius: 15px;
    }
    .locomotive-rear .loco-body {
        border-top-right-radius: 40px;
        border-bottom-right-radius: 40px;
        border-top-left-radius: 15px;
        border-bottom-left-radius: 15px;
    }
    .loco-body {
         display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        height: 100%;
        width: 100%;
        background-color: #333;
        border-radius: 15px;
    }
</style>
""", unsafe_allow_html=True)


# Video dosyası yolları (sadece isimler, log dosyası için kullanılacak)
video_names = {
    "Vagon 1": "wagon1.mp4",
    "Vagon 2": "wagon2.mp4",
    "Vagon 3": "wagon3.mp4"
}

# Log dosyalarının dizini
fullness_log_dir = os.path.join("outputs", "logs")

st.header("Anlık Vagon Doluluk Durumu")

# Tüm tren çizimini dinamik olarak güncellemek için bir placeholder
train_display_placeholder = st.empty()

#st.info("Doluluk oranları anlık olarak güncellenmektedir. Lütfen video işleme sürecinin arka planda çalıştığından emin olun (main.py'yi çalıştırarak).")

# Anlık güncellemeler için döngü
while True:
    current_fullness = {}
    
    # Her bir vagonun doluluk oranını log dosyasından oku
    for wagon_name, video_filename in video_names.items():
        log_file_name = f"{os.path.splitext(video_filename)[0]}_fullness.txt"
        fullness_log_file_path = os.path.join(fullness_log_dir, log_file_name)
        
        if os.path.exists(fullness_log_file_path):
            try:
                with open(fullness_log_file_path, "r") as f:
                    fullness_str = f.read().strip()
                    if fullness_str:
                        current_fullness[wagon_name] = float(fullness_str)
                    else:
                        current_fullness[wagon_name] = "Veri bekleniyor..."
            except (IOError, ValueError) as e:
                current_fullness[wagon_name] = f"Hata: {e}"
        else:
            current_fullness[wagon_name] = "Dosya bulunamadı."
            
    # CSS stilleri ve tren yapısı
    train_html_parts = []
    train_html_parts.append("""<div class="train-container">""")

    # Trenin ön lokomotifi
    train_html_parts.append("""
        <div class="locomotive-shell locomotive-front">
            <div class="loco-body">
                <div class="loco-window"></div>
                🚂
            </div>
        </div>
        <div class="connector"></div>
    """)

    for i, (wagon_name, _) in enumerate(video_names.items()):
        fullness_value = current_fullness.get(wagon_name, "N/A")
        color = "grey"
        status_text = "Veri bekleniyor..."

        if isinstance(fullness_value, (int, float)):
            if fullness_value < 10:
                color = "#1E90FF" # Mavi (Boş)
                status_text = "BOŞ"
            elif fullness_value < 30:
                color = "#4CAF50" # Yeşil (Az Dolu)
                status_text = "AZ DOLU"
            elif fullness_value < 60:
                color = "#ffa500" # Turuncu (Orta Dolu)
                status_text = "ORTA DOLU"
            else:
                color = "#ff4b4b" # Kırmızı (Çok Dolu)
                status_text = "ÇOK DOLU"
            
            # Vagon kutusunun HTML'i
            train_html_parts.append(f"""
            <div class="wagon-shell">
                <div class="window-row">
                    <div class="window"></div>
                    <div class="door"></div>
                    <div class="window"></div>
                </div>
                <div class="wagon-content" style="background-color: {color};">
                    <div class="wagon-name">{wagon_name}</div>
                    <div class="wagon-percentage">{fullness_value:.2f}%</div>
                    <div class="wagon-status-text">{status_text}</div>
                </div>
                <div class="window-row">
                    <div class="window"></div>
                    <div class="door"></div>
                    <div class="window"></div>
                </div>
            </div>
            """)
        else:
            # Hata veya veri bekleniyor durumu
            train_html_parts.append(f"""
            <div class="wagon-shell" style="background-color: grey;">
                <div class="window-row">
                    <div class="window"></div>
                    <div class="door"></div>
                    <div class="window"></div>
                </div>
                <div class="wagon-content" style="background-color: grey;">
                    <div class="wagon-name">{wagon_name}</div>
                    <div class="wagon-percentage">{fullness_value}</div>
                    <div class="wagon-status-text">Yükleniyor...</div>
                </div>
                <div class="window-row">
                    <div class="window"></div>
                    <div class="door"></div>
                    <div class="window"></div>
                </div>
            </div>
            """)
            
        if i < len(video_names) - 1: # Vagonlar arasına bağlantı elemanı ekle
            train_html_parts.append("""<div class="connector"></div>""")

    # Trenin arka lokomotifi/kuyruğu
    train_html_parts.append("""
        <div class="connector"></div>
        <div class="locomotive-shell locomotive-rear">
            <div class="loco-body">
                <div class="loco-window"></div>
                🚃
            </div>
        </div>
    </div> <!-- Close train-container -->
    """)

    # Her bir HTML parçasını temizle ve birleştir
    cleaned_html_parts = [part.strip().replace('\r', '') for part in train_html_parts]
    full_train_html = "\n".join(cleaned_html_parts)
    
    train_display_placeholder.markdown(full_train_html, unsafe_allow_html=True)

    time.sleep(1) # Her 1 saniyede bir güncelle