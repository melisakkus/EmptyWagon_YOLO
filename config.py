# langchain_weather.py için sabit koordinat ve konum eşleşmeleri
ANKARA_KORU_SUBWAY_LAT = 39.8875
ANKARA_KORU_SUBWAY_LON = 32.686944

LOCATION_MAPPINGS = {
    (ANKARA_KORU_SUBWAY_LAT, ANKARA_KORU_SUBWAY_LON): "Koru Metro",
    # Buraya diğer sabit konum eşleşmelerini ekleyebilirsiniz
}

# video_processor.py için sabitler
MODEL_NAME = "models/best.pt"
PERSON_ID = 0
WAGON_CAPACITY = 25
COUNTING_ZONE_POLYGON = [
    [565, 372],
    [853, 374],
    [1177, 703],
    [213, 709]
]
VIDEO_WIDTH = 1200
VIDEO_HEIGHT = 750

# YOLO ayarları - Daha iyi tespit için optimize edildi
YOLO_CONF_THRESHOLD = 0.3  # 0.5'ten 0.3'e düşürüldü - daha fazla kişi tespit edilecek
YOLO_IOU_THRESHOLD = 0.5   # 0.3'ten 0.5'e çıkarıldı - daha az false positive
YOLO_MAX_DETECTIONS = 100  # 50'den 100'e çıkarıldı - daha fazla nesne tespit edebilir

# Çift detection filtreleme ayarları
DETECTION_IOU_THRESHOLD = 0.4  # 0.3'ten 0.4'e çıkarıldı - daha az agresif filtreleme

# Tracking ayarları - Yeni eklenmiş
YOLO_TRACKER = "bytetrack.yaml"  # Daha iyi tracking için
YOLO_TRACK_PERSIST = True        # Tracking ID'lerini korumak için

# Minimum detection boyutu (piksel cinsinden)
MIN_DETECTION_WIDTH = 20   # Çok küçük detection'ları filtrele
MIN_DETECTION_HEIGHT = 40  # Çok küçük detection'ları filtrele

# Maksimum detection boyutu (frame boyutunun yüzdesi)
MAX_DETECTION_WIDTH_RATIO = 0.8   # Frame genişliğinin %80'i
MAX_DETECTION_HEIGHT_RATIO = 0.9  # Frame yüksekliğinin %90'ı

INPUT_VIDEO_DIRECTORY = "data/videos"

# Renk ayarları
TRACKED_COLOR = (0, 255, 255)  # Sarı
IN_ZONE_COLOR = (0, 255, 0)    # Yeşil
OUTSIDE_COLOR = (0, 0, 255)    # Kırmızı
ZONE_POLYGON_COLOR = (255, 0, 0) # Mavi
BBOX_THICKNESS = 2
POLYGON_THICKNESS = 2

# Font ayarları
FONT_HERSHEY_SIMPLEX = 0
FONT_SCALE_SMALL = 0.4
FONT_SCALE_MEDIUM = 0.7
FONT_SCALE_LARGE = 1.5
FONT_THICKNESS_SMALL = 1
FONT_THICKNESS_MEDIUM = 2
FONT_THICKNESS_LARGE = 3
COUNT_TEXT_POSITION = (50, 50)
DEBUG_TEXT_POSITION = (50, 100)