import cv2
import numpy as np
from ultralytics import YOLO
import os
import time
import config
# firestore_crud'dan hem create_document hem de update_document'ı import ediyoruz
# Çünkü initialize_firebase içinde hala update_document çağrısı var, ama esas sorunlu yerleri create_document ile değiştireceğiz.
from features.database.firestore_crud import create_document, update_document, get_all_documents
from features.database.initialize_firebase import initialize_firebase
from firebase_admin import firestore # Firestore'un SERVER_TIMESTAMP'ını kullanmak için

# Firebase istemcisini bir kez başlat
db = None
try:
    db = initialize_firebase()
    if db:
        print("Firebase istemcisi video_processor için başarıyla başlatıldı.")
    else:
        print("UYARI: Firebase istemcisi başlatılamadı. Doluluk oranları Firestore'a yazılmayacak.")
except Exception as e:
    print(f"HATA: video_processor içinde Firebase başlatılırken hata oluştu: {e}")
    db = None

# Firestore koleksiyon adları
WAGON_FULLNESS_COLLECTION = "wagon_fullness_logs"
PROCESSING_STATUS_COLLECTION = "processing_status"
PROCESSING_COMPLETE_DOC_ID = "video_analysis_status"


# Global ayarlar
model_name = config.MODEL_NAME
person_id = config.PERSON_ID
wagon_capacity = config.WAGON_CAPACITY

# Sayım bölgesi
counting_zone_polygon = np.array(config.COUNTING_ZONE_POLYGON, np.int32)


def is_valid_detection(box, frame_width, frame_height):
    """Detection'ın geçerli boyutta olup olmadığını kontrol eder"""
    if len(box) < 4:
        return False

    x1, y1, x2, y2 = box[:4]
    width = x2 - x1
    height = y2 - y1 # Buradaki hata düzeltildi: y2 - y1 olmalıydı, y2 - y2 değil.

    # Minimum boyut kontrolü
    if width < config.MIN_DETECTION_WIDTH or height < config.MIN_DETECTION_HEIGHT:
        return False

    # Maksimum boyut kontrolü
    max_width = frame_width * config.MAX_DETECTION_WIDTH_RATIO
    max_height = frame_height * config.MAX_DETECTION_HEIGHT_RATIO

    if width > max_width or height > max_height:
        return False

    return True


def process_video(video_file):
    people_in_zone = set()
    people_tracked = set()

    video_name = os.path.basename(video_file)
    # Firestore doküman ID'si için dosya adından uzantıyı kaldırıyoruz (örn: "wagon1.mp4" -> "wagon1")
    wagon_document_id = os.path.splitext(video_name)[0]

    output_video_name = "ov_" + video_name
    output_path = os.path.join("outputs", "videos", output_video_name)

    # Fullness log dosyası artık kullanılmıyor, ancak eğer Firestore bağlantısı yoksa
    # yerel bir fallback olarak tutulabilir (bu örnekte kaldırıldı).
    # fullness_log_dir = os.path.join("outputs", "logs")
    # os.makedirs(fullness_log_dir, exist_ok=True)
    # fullness_log_file = os.path.join(fullness_log_dir, f"{wagon_document_id}_fullness.txt")


    cap = cv2.VideoCapture(video_file)
    if not cap.isOpened():
        print(f"Error: Could not open video file {video_file}")
        return

    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = config.VIDEO_WIDTH
    height = config.VIDEO_HEIGHT
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    # Model yükleme - tracking ayarları ile
    model = YOLO(model_name)

    # Video işlenmeye başlandığında Firestore'daki durumu "işleniyor" olarak ayarla
    # ARTIK create_document KULLANILIYOR: İlk kez çalışırken dokümanı oluşturacak, sonraki çağrılarda üzerine yazacak.
    if db:
        try:
            create_document(db, PROCESSING_STATUS_COLLECTION, {"completed": False, "last_update_time": firestore.SERVER_TIMESTAMP}, document_id=PROCESSING_COMPLETE_DOC_ID)
            print(f"Firestore: Video işleme durumu '{wagon_document_id}' için başlatıldı.")
        except Exception as e:
            print(f"UYARI: Firestore'a işlem durumu yazılırken hata oluştu: {e}")


    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.resize(frame, (width, height))
        cv2.polylines(frame, [counting_zone_polygon], isClosed=True,
                      color=config.ZONE_POLYGON_COLOR, thickness=config.POLYGON_THICKNESS)

        # İyileştirilmiş YOLO tracking
        result = model.track(
            frame,
            persist=config.YOLO_TRACK_PERSIST,
            verbose=False,
            conf=config.YOLO_CONF_THRESHOLD,
            iou=config.YOLO_IOU_THRESHOLD,
            max_det=config.YOLO_MAX_DETECTIONS,
            tracker=config.YOLO_TRACKER,  # Daha iyi tracker kullan
            classes=[person_id],  # Sadece kişi sınıfını tespit et
            agnostic_nms=True  # Daha iyi NMS için
        )[0]

        bboxes = np.array([]) # Varsayılan olarak boş array

        if result.boxes is not None and len(result.boxes) > 0:
            bboxes_raw = np.array(result.boxes.data.tolist(), dtype="int")

            # Geçerli detection'ları filtrele
            valid_bboxes = []
            for box in bboxes_raw:
                if is_valid_detection(box, width, height):
                    valid_bboxes.append(box)

            if valid_bboxes:
                bboxes = np.array(valid_bboxes, dtype="int")

                # İyileştirilmiş çift detection filtreleme (güven skoru dikkate alınarak)
                def filter_duplicate_detections(boxes, iou_threshold=config.DETECTION_IOU_THRESHOLD):
                    if len(boxes) == 0:
                        return boxes

                    # Güven (confidence) skoruna göre sırala (yüksekten düşüğe)
                    # Eğer 5. indexte confidence yoksa, varsayılan olarak 1.0 kullan
                    sorted_boxes = sorted(boxes, key=lambda x: x[4] if len(x) > 4 else 1.0, reverse=True)

                    filtered_boxes = []
                    used_indices = set()

                    for i, box1 in enumerate(sorted_boxes):
                        if i in used_indices:
                            continue

                        filtered_boxes.append(box1)
                        used_indices.add(i)

                        for j, box2 in enumerate(sorted_boxes):
                            if j <= i or j in used_indices:
                                continue

                            # IoU hesapla
                            x1_1, y1_1, x2_1, y2_1 = box1[:4]
                            x1_2, y1_2, x2_2, y2_2 = box2[:4]

                            x1_inter = max(x1_1, x1_2)
                            y1_inter = max(y1_1, y1_2)
                            x2_inter = min(x2_1, x2_2)
                            y2_inter = min(y2_1, y2_2)

                            inter_area = 0
                            if x2_inter > x1_inter and y2_inter > y1_inter:
                                inter_area = (x2_inter - x1_inter) * (y2_inter - y1_inter)

                            area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
                            area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
                            union_area = area1 + area2 - inter_area

                            if union_area > 0:
                                iou = inter_area / union_area
                                if iou > iou_threshold:
                                    used_indices.add(j)

                    return np.array(filtered_boxes, dtype="int") if filtered_boxes else np.array([])

                # Çift detection'ları filtrele
                bboxes = filter_duplicate_detections(bboxes)


        # Bu frame'de tespit edilen kişiler
        detected_people_in_zone = set()

        for box in bboxes:
            if len(box) >= 6:  # Track ID, score ve class_id bekleniyor
                if len(box) == 7:
                    x1, y1, x2, y2, track_id, score, class_id = box
                elif len(box) == 6:
                    x1, y1, x2, y2, score, class_id = box
                    track_id = None # Eğer track_id yoksa None olarak ayarla
                else: # Daha az eleman varsa atla
                    continue

                if track_id is None: # Sadece track_id'si olanları işle
                    continue

                track_id = int(track_id)

                if class_id == person_id:
                    person_anchor_point = (int((x1 + x2) / 2), int(y2)) # Kişinin merkez alt noktası (ayaklar)
                    is_inside = cv2.pointPolygonTest(counting_zone_polygon, person_anchor_point, False) >= 0

                    if is_inside:
                        detected_people_in_zone.add(track_id)
                        people_tracked.add(track_id) # Zone'a giren herkesi takip etmeye başla

                    # Renk belirleme ve çizim
                    color = config.TRACKED_COLOR if track_id in people_tracked else config.OUTSIDE_COLOR
                    status = "TRACKED" if track_id in people_tracked else "OUTSIDE"
                    if is_inside:
                        color = config.IN_ZONE_COLOR
                        status = "IN_ZONE"


                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, config.BBOX_THICKNESS)

                    conf_text = f"{score:.2f}" if len(box) >= 5 else "N/A"
                    text = f"ID:{track_id} {status} ({conf_text})"

                    text_size = cv2.getTextSize(text, config.FONT_HERSHEY_SIMPLEX,
                                                config.FONT_SCALE_SMALL, config.FONT_THICKNESS_SMALL)[0]
                    cv2.rectangle(frame, (x1, y1 - 25), (x1 + text_size[0], y1), color, -1)
                    cv2.putText(frame, text, (x1, y1 - 5), config.FONT_HERSHEY_SIMPLEX,
                                config.FONT_SCALE_SMALL, (0, 0, 0), config.FONT_THICKNESS_SMALL)

                    cv2.circle(frame, person_anchor_point, 5, color, -1)
            else:
                # Bbox'ta yeterli bilgi yoksa, sadece debug amaçlı buraya düşülür.
                # print(f"UYARI: Beklenenden az bounding box verisi: {box}")
                pass

        # Zone içindeki kişileri güncelle
        people_in_zone = detected_people_in_zone

        # Sayım ve görselleştirme
        current_count = len(people_tracked)
        count_text = f"Wagon Count: {current_count}/{wagon_capacity}"
        cv2.putText(frame, count_text, config.COUNT_TEXT_POSITION,
                    config.FONT_HERSHEY_SIMPLEX, config.FONT_SCALE_LARGE,
                    config.IN_ZONE_COLOR, config.FONT_THICKNESS_LARGE)

        # Debug bilgileri
        debug_text = f"In Zone: {len(people_in_zone)} | Tracked: {len(people_tracked)} | Detections: {len(bboxes)}"
        cv2.putText(frame, debug_text, config.DEBUG_TEXT_POSITION,
                    config.FONT_HERSHEY_SIMPLEX, config.FONT_SCALE_MEDIUM,
                    (255, 255, 255), config.FONT_THICKNESS_MEDIUM)

        # Doluluk yüzdesi
        percent_Full = (current_count / wagon_capacity * 100)
        percent_Full = max(0, min(100, percent_Full)) # Yüzdeyi 0-100 arasında tut

        # Fullness göstergesi
        fullness_text = f"Fullness: {percent_Full:.1f}%"
        fullness_color = (0, 255, 0) if percent_Full < 80 else (0, 165, 255) if percent_Full < 95 else (0, 0, 255)
        cv2.putText(frame, fullness_text, (50, 150),
                    config.FONT_HERSHEY_SIMPLEX, config.FONT_SCALE_MEDIUM,
                    fullness_color, config.FONT_THICKNESS_MEDIUM)

        # Firestore'a doluluk oranını yazma
        if db:
            try:
                data_to_save = {
                    "fullness_percentage": float(f"{percent_Full:.2f}"), # Float olarak kaydet
                    "last_updated": firestore.SERVER_TIMESTAMP # Sunucu zaman damgası ekle
                }
                # ARTIK create_document KULLANILIYOR: İlk kez çalışırken dokümanı oluşturacak, sonraki çağrılarda üzerine yazacak.
                create_document(db, WAGON_FULLNESS_COLLECTION, data_to_save, document_id=wagon_document_id)
            except Exception as e:
                print(f"UYARI: Firestore'a doluluk oranı yazılırken hata oluştu: {e}")

        out.write(frame)

    cap.release()
    out.release()
    print(f"✅ Video kaydedildi: {output_path}")
    print(f"📊 Toplam tespit edilen kişi (işlem sonunda): {len(people_tracked)}")


# Ana program
if __name__ == "__main__":
    input_video_dir = config.INPUT_VIDEO_DIRECTORY
    os.makedirs("outputs/videos", exist_ok=True)
    # os.makedirs("outputs/logs", exist_ok=True) # Firestore'a geçince bu klasöre gerek kalmaz

    # İşlem başlamadan önce Firestore'daki tamamlanma bayrağını sıfırla
    # ARTIK create_document KULLANILIYOR: İlk kez çalışırken dokümanı oluşturacak, sonraki çağrılarda üzerine yazacak.
    if db:
        try:
            create_document(db, PROCESSING_STATUS_COLLECTION, {"completed": False, "last_update_time": firestore.SERVER_TIMESTAMP}, document_id=PROCESSING_COMPLETE_DOC_ID)
            print("Firestore: İşlem başlangıcı için tamamlanma bayrağı sıfırlandı.")
        except Exception as e:
            print(f"UYARI: Firestore'a başlangıç bayrağı yazılırken hata oluştu: {e}")

    video_files = []
    if os.path.exists(input_video_dir):
        video_files = [os.path.join(input_video_dir, f) for f in os.listdir(input_video_dir)
                       if f.endswith(('.mp4', '.avi', '.mov', '.mkv'))]
        if not video_files:
            print(f"'{input_video_dir}' klasöründe işlenecek video bulunamadı.")
            print("Lütfen videolarınızı bu klasöre koyun.")
        else:
            for video_file in video_files:
                print(f"İşleniyor: {video_file}")
                process_video(video_file)
                print("-" * 50)
    else:
        print(f"'{input_video_dir}' klasörü bulunamadı. Lütfen giriş videolarınızı bu klasöre koyun.")

    # Tüm videolar işlendikten sonra Firestore'daki tamamlanma bayrağını ayarla
    # ARTIK create_document KULLANILIYOR: İlk kez çalışırken dokümanı oluşturacak, sonraki çağrılarda üzerine yazacak.
    if db and video_files: # Sadece eğer gerçekten videolar işlendiyse
        try:
            create_document(db, PROCESSING_STATUS_COLLECTION, {"completed": True, "last_completion_time": firestore.SERVER_TIMESTAMP}, document_id=PROCESSING_COMPLETE_DOC_ID)
            print("Firestore: Tüm video işleme tamamlandı bayrağı ayarlandı.")
        except Exception as e:
            print(f"UYARI: Firestore'a tamamlama bayrağı yazılırken hata oluştu: {e}")