import cv2
import numpy as np
from ultralytics import YOLO
import os
import time
import config

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
    output_video_name = "ov_" + video_name
    output_path = os.path.join("outputs", "videos", output_video_name)

    # Path for the real-time fullness log file
    fullness_log_dir = os.path.join("outputs", "logs")
    os.makedirs(fullness_log_dir, exist_ok=True)
    fullness_log_file = os.path.join(fullness_log_dir, f"{os.path.splitext(video_name)[0]}_fullness.txt")

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

        if result.boxes is None or len(result.boxes) == 0:
            # Eğer tespit yoksa, sadece sayım bilgilerini göster
            current_count = len(people_tracked)
            count_text = f"Wagon Count: {current_count}"
            cv2.putText(frame, count_text, config.COUNT_TEXT_POSITION,
                        config.FONT_HERSHEY_SIMPLEX, config.FONT_SCALE_LARGE,
                        config.IN_ZONE_COLOR, config.FONT_THICKNESS_LARGE)

            debug_text = f"In Zone: {len(people_in_zone)} | Tracked: {len(people_tracked)}"
            cv2.putText(frame, debug_text, config.DEBUG_TEXT_POSITION,
                        config.FONT_HERSHEY_SIMPLEX, config.FONT_SCALE_MEDIUM,
                        (255, 255, 255), config.FONT_THICKNESS_MEDIUM)

            percent_Full = (current_count / wagon_capacity * 100)
            try:
                with open(fullness_log_file, "w") as f:
                    f.write(f"{percent_Full:.2f}")
            except IOError as e:
                print(f"Error writing to fullness log file {fullness_log_file}: {e}")

            out.write(frame)
            continue

        bboxes = np.array(result.boxes.data.tolist(), dtype="int")

        # Geçerli detection'ları filtrele
        valid_bboxes = []
        for box in bboxes:
            if is_valid_detection(box, width, height):
                valid_bboxes.append(box)

        if not valid_bboxes:
            bboxes = np.array([])
        else:
            bboxes = np.array(valid_bboxes, dtype="int")

        # İyileştirilmiş çift detection filtreleme
        def filter_duplicate_detections(boxes, iou_threshold=config.DETECTION_IOU_THRESHOLD):
            if len(boxes) == 0:
                return boxes

            # Confidence'a göre sırala (yüksekten düşüğe)
            if len(boxes[0]) >= 5:  # confidence var mı kontrol et
                boxes = sorted(boxes, key=lambda x: x[4], reverse=True)

            filtered_boxes = []
            used_indices = set()

            for i, box1 in enumerate(boxes):
                if i in used_indices:
                    continue

                filtered_boxes.append(box1)
                used_indices.add(i)

                # IoU hesaplama için diğer box'larla karşılaştır
                for j, box2 in enumerate(boxes):
                    if j <= i or j in used_indices:
                        continue

                    # IoU hesapla
                    x1_1, y1_1, x2_1, y2_1 = box1[:4]
                    x1_2, y1_2, x2_2, y2_2 = box2[:4]

                    # Intersection area
                    x1_inter = max(x1_1, x1_2)
                    y1_inter = max(y1_1, y1_2)
                    x2_inter = min(x2_1, x2_2)
                    y2_inter = min(y2_1, y2_2)

                    if x2_inter > x1_inter and y2_inter > y1_inter:
                        inter_area = (x2_inter - x1_inter) * (y2_inter - y1_inter)

                        # Union area
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
        detected_people_outside_zone = set()

        for box in bboxes:
            if len(box) >= 6:  # Track ID olmasa bile işle
                if len(box) == 7:
                    x1, y1, x2, y2, track_id, score, class_id = box
                elif len(box) == 6:
                    x1, y1, x2, y2, score, class_id = box
                    track_id = None
                else:
                    continue

                # Track ID yoksa atlat
                if track_id is None or track_id < 0:
                    continue

                track_id = int(track_id)

                if class_id == person_id:
                    # Kişinin merkez alt noktası (ayaklar)
                    person_anchor_point = (int((x1 + x2) / 2), int(y2))
                    is_inside = cv2.pointPolygonTest(counting_zone_polygon, person_anchor_point, False) >= 0

                    # Zone durumu güncelleme
                    if is_inside:
                        detected_people_in_zone.add(track_id)
                        people_tracked.add(track_id)
                    else:
                        detected_people_outside_zone.add(track_id)

                    # Eğer kişi zone'dan çıktıysa tracking'ten çıkar
                    if track_id in people_tracked and not is_inside:
                        # Kişi tamamen frame'den çıktığında veya zone'dan uzakta olduğunda çıkar
                        center_x = int((x1 + x2) / 2)
                        center_y = int((y1 + y2) / 2)

                        # Zone'dan çok uzakta mı kontrol et
                        zone_center = np.mean(counting_zone_polygon, axis=0)
                        distance_to_zone = np.sqrt((center_x - zone_center[0]) ** 2 + (center_y - zone_center[1]) ** 2)

                        # Eğer zone'dan çok uzaktaysa tracking'ten çıkar
                        if distance_to_zone > 200:  # Bu değer ayarlanabilir
                            people_tracked.discard(track_id)

                    # Renk belirleme
                    if track_id in people_tracked:
                        if is_inside:
                            color = config.IN_ZONE_COLOR
                            status = "IN_ZONE"
                        else:
                            color = config.TRACKED_COLOR
                            status = "TRACKED"
                    else:
                        color = config.OUTSIDE_COLOR
                        status = "OUTSIDE"

                    # Bounding box ve text çizimi
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, config.BBOX_THICKNESS)

                    # Confidence bilgisi
                    conf_text = f"{score:.2f}" if len(box) >= 5 else "N/A"
                    text = f"ID:{track_id} {status} ({conf_text})"

                    # Text background
                    text_size = cv2.getTextSize(text, config.FONT_HERSHEY_SIMPLEX,
                                                config.FONT_SCALE_SMALL, config.FONT_THICKNESS_SMALL)[0]
                    cv2.rectangle(frame, (x1, y1 - 25), (x1 + text_size[0], y1), color, -1)
                    cv2.putText(frame, text, (x1, y1 - 5), config.FONT_HERSHEY_SIMPLEX,
                                config.FONT_SCALE_SMALL, (0, 0, 0), config.FONT_THICKNESS_SMALL)

                    # Anchor point
                    cv2.circle(frame, person_anchor_point, 5, color, -1)

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

        # Fullness göstergesi
        fullness_text = f"Fullness: {percent_Full:.1f}%"
        fullness_color = (0, 255, 0) if percent_Full < 80 else (0, 165, 255) if percent_Full < 95 else (0, 0, 255)
        cv2.putText(frame, fullness_text, (50, 150),
                    config.FONT_HERSHEY_SIMPLEX, config.FONT_SCALE_MEDIUM,
                    fullness_color, config.FONT_THICKNESS_MEDIUM)

        # Log dosyasına yazma
        try:
            with open(fullness_log_file, "w") as f:
                f.write(f"{percent_Full:.2f}")
        except IOError as e:
            print(f"Error writing to fullness log file {fullness_log_file}: {e}")

        out.write(frame)

    cap.release()
    out.release()
    print(f"✅ Video kaydedildi: {output_path}")
    print(f"📊 Toplam tespit edilen kişi: {len(people_tracked)}")


# Ana program
if __name__ == "__main__":
    input_video_dir = config.INPUT_VIDEO_DIRECTORY
    os.makedirs("outputs/videos", exist_ok=True)
    os.makedirs("outputs/logs", exist_ok=True)

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