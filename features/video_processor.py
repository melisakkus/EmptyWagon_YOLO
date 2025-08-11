# video_processor.py
import cv2
import numpy as np
from ultralytics import YOLO
import os
import time
import config
# Sadece create_document kullanacağız, update_document'ı ihtiyacımız yoksa kaldırabiliriz
from features.database.firestore_crud import create_document
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
WAGON_CURRENT_FULLNESS_COLLECTION = "wagon_fullness_current" # Vagonların anlık doluluk durumları
WAGON_HISTORICAL_LOGS_COLLECTION = "wagon_fullness_history"   # Vagonların geçmiş doluluk kayıtları

# BURADAN KALDIRILACAK: Bu satırlar kaldırılmalı
# PROCESSING_STATUS_COLLECTION = "processing_status"
# PROCESSING_COMPLETE_DOC_ID = "video_analysis_status"


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
    height = y2 - y1

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
    wagon_document_id = os.path.splitext(video_name)[0]

    output_video_name = "ov_" + video_name
    output_path = os.path.join("outputs", "videos", output_video_name)

    cap = cv2.VideoCapture(video_file)
    if not cap.isOpened():
        print(f"Error: Could not open video file {video_file}")
        return

    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = config.VIDEO_WIDTH
    height = config.VIDEO_HEIGHT
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    model = YOLO(model_name)

    # BURADAN KALDIRILACAK: Bu blok kaldırılmalı, mantık main.py'ye taşındı
    # if db:
    #     try:
    #         create_document(db, PROCESSING_STATUS_COLLECTION, {"completed": False, "last_update_time": firestore.SERVER_TIMESTAMP}, document_id=PROCESSING_COMPLETE_DOC_ID)
    #         print(f"Firestore: Video işleme durumu '{wagon_document_id}' için başlatıldı.")
    #     except Exception as e:
    #         print(f"UYARI: Firestore'a işlem durumu yazılırken hata oluştu: {e}")

    frame_count = 0
    last_log_time = time.time()
    log_interval_seconds = 1

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1

        frame = cv2.resize(frame, (width, height))
        cv2.polylines(frame, [counting_zone_polygon], isClosed=True,
                      color=config.ZONE_POLYGON_COLOR, thickness=config.POLYGON_THICKNESS)

        result = model.track(
            frame,
            persist=config.YOLO_TRACK_PERSIST,
            verbose=False,
            conf=config.YOLO_CONF_THRESHOLD,
            iou=config.YOLO_IOU_THRESHOLD,
            max_det=config.YOLO_MAX_DETECTIONS,
            tracker=config.YOLO_TRACKER,
            classes=[person_id],
            agnostic_nms=True
        )[0]

        bboxes = np.array([])

        if result.boxes is not None and len(result.boxes) > 0:
            bboxes_raw = np.array(result.boxes.data.tolist(), dtype="int")

            valid_bboxes = []
            for box in bboxes_raw:
                if is_valid_detection(box, width, height):
                    valid_bboxes.append(box)

            if valid_bboxes:
                bboxes = np.array(valid_bboxes, dtype="int")

                def filter_duplicate_detections(boxes, iou_threshold=config.DETECTION_IOU_THRESHOLD):
                    if len(boxes) == 0:
                        return boxes

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

                bboxes = filter_duplicate_detections(bboxes)


        detected_people_in_zone = set()

        for box in bboxes:
            if len(box) >= 6:
                if len(box) == 7:
                    x1, y1, x2, y2, track_id, score, class_id = box
                elif len(box) == 6:
                    x1, y1, x2, y2, score, class_id = box
                    track_id = None
                else:
                    continue

                if track_id is None:
                    continue

                track_id = int(track_id)

                if class_id == person_id:
                    person_anchor_point = (int((x1 + x2) / 2), int(y2))
                    is_inside = cv2.pointPolygonTest(counting_zone_polygon, person_anchor_point, False) >= 0

                    if is_inside:
                        detected_people_in_zone.add(track_id)
                        people_tracked.add(track_id)

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

        people_in_zone = detected_people_in_zone
        current_count = len(people_tracked)
        count_text = f"Wagon Count: {current_count}/{wagon_capacity}"
        cv2.putText(frame, count_text, config.COUNT_TEXT_POSITION,
                    config.FONT_HERSHEY_SIMPLEX, config.FONT_SCALE_LARGE,
                    config.IN_ZONE_COLOR, config.FONT_THICKNESS_LARGE)

        debug_text = f"In Zone: {len(people_in_zone)} | Tracked: {len(people_tracked)} | Detections: {len(bboxes)}"
        cv2.putText(frame, debug_text, config.DEBUG_TEXT_POSITION,
                    config.FONT_HERSHEY_SIMPLEX, config.FONT_SCALE_MEDIUM,
                    (255, 255, 255), config.FONT_THICKNESS_MEDIUM)

        percent_Full = (current_count / wagon_capacity * 100)
        percent_Full = max(0, min(100, percent_Full))

        fullness_text = f"Fullness: {percent_Full:.1f}%"
        fullness_color = (0, 255, 0) if percent_Full < 80 else (0, 165, 255) if percent_Full < 95 else (0, 0, 255)
        cv2.putText(frame, fullness_text, (50, 150),
                    config.FONT_HERSHEY_SIMPLEX, config.FONT_SCALE_MEDIUM,
                    fullness_color, config.FONT_THICKNESS_MEDIUM)

        # Firestore'a anlık doluluk oranını yazma (canlı Streamlit görünümü için)
        if db:
            try:
                data_to_save_current = {
                    "fullness_percentage": float(f"{percent_Full:.2f}"),
                    "last_updated": firestore.SERVER_TIMESTAMP
                }
                create_document(db, WAGON_CURRENT_FULLNESS_COLLECTION, data_to_save_current, document_id=wagon_document_id)
            except Exception as e:
                print(f"UYARI: Firestore'a anlık doluluk oranı yazılırken hata oluştu: {e}")

            # Firestore'a tarihsel log kaydını yazma (oynatma özelliği için)
            current_time = time.time()
            if current_time - last_log_time >= log_interval_seconds:
                try:
                    data_to_save_history = {
                        "wagon_id": wagon_document_id, # Hangi vagona ait olduğunu belirt
                        "fullness_percentage": float(f"{percent_Full:.2f}"),
                        "timestamp": firestore.SERVER_TIMESTAMP,
                        "frame_count": frame_count
                    }
                    create_document(db, WAGON_HISTORICAL_LOGS_COLLECTION, data_to_save_history)
                    last_log_time = current_time
                except Exception as e:
                    print(f"UYARI: Firestore'a tarihsel log yazılırken hata oluştu: {e}")

        out.write(frame)

    cap.release()
    out.release()
    print(f"✅ Video kaydedildi: {output_path}")
    print(f"📊 Toplam tespit edilen kişi (işlem sonunda): {len(people_tracked)}")


# Ana program (Sadece doğrudan video_processor.py çalıştırıldığında)
# Buradaki global status yönetimi KALDIRILACAK, main.py'ye taşınacak.

# İsteğe bağlı: Tüm tarihsel logları temizlemek için yardımcı fonksiyon
# Bu fonksiyon main.py'den çağrılabilir veya burada kalabilir ama dikkatli kullanılmalı
# Bu fonksiyon artık firestore_crud.py'ye taşındığı için buradan kaldırılabilir
# def delete_all_historical_logs(db_client, collection_name):
#     """Belirtilen koleksiyondaki tüm dokümanları siler."""
#     if db_client is None:
#         print("❌ Hata: Firebase istemcisi başlatılmamış, tarihsel loglar silinemedi.")
#         return

#     print(f"⏳ '{collection_name}' koleksiyonundaki eski tarihsel loglar temizleniyor...")
#     deleted_count = 0
#     batch_size = 500
#     while True:
#         docs = db_client.collection(collection_name).limit(batch_size).stream()
#         documents = list(docs)
#         if not documents:
#             break

#         batch = db_client.batch()
#         for doc in documents:
#             batch.delete(doc.reference)
#             deleted_count += 1
#         batch.commit()
#         time.sleep(0.1)

#     print(f"🗑️ '{collection_name}' koleksiyonundan {deleted_count} doküman silindi.")