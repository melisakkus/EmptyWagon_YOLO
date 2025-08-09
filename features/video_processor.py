import cv2
import numpy as np
from ultralytics import YOLO
import os
import time

# Global ayarlar
model_name = "models/best.pt"
person_id = 0

wagon_capacity = 25

# Sayım bölgesi
counting_zone_polygon = np.array([
    [565, 372],
    [853, 374],
    [1177, 703],
    [213, 709]
], np.int32)

# Tek video işleme fonksiyonu
def process_video(video_file):
    # Bu değişkenler, fonksiyon her çağrıldığında (yani her yeni video için) sıfırlanır.
    people_in_zone = set()  # Şu anda zone içindeki insanlar
    people_tracked = set()  # Bir kez zone'a girmiş ve hala sayılan insanlar

    video_name = os.path.basename(video_file)
    output_video_name = "ov_" + video_name
    output_path = os.path.join("outputs", "videos", output_video_name)

    # Path for the real-time fullness log file
    fullness_log_dir = os.path.join("outputs", "logs")
    os.makedirs(fullness_log_dir, exist_ok=True)  # Ensure directory exists
    fullness_log_file = os.path.join(fullness_log_dir, f"{os.path.splitext(video_name)[0]}_fullness.txt")

    cap = cv2.VideoCapture(video_file)
    if not cap.isOpened():
        print(f"Error: Could not open video file {video_file}")
        return

    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = 1200
    height = 750
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    model = YOLO(model_name)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.resize(frame, (width, height))
        cv2.polylines(frame, [counting_zone_polygon], isClosed=True, color=(255, 0, 0), thickness=2)

        result = model.track(frame, persist=True, verbose=False,
                             conf=0.5,  # Confidence threshold
                             iou=0.3,  # NMS IoU threshold
                             max_det=50  # Maximum detections
                             )[0]

        bboxes = np.array(result.boxes.data.tolist(), dtype="int")

        # Çift detection'ları filtreleme fonksiyonu
        def filter_duplicate_detections(boxes, iou_threshold=0.3):
            if len(boxes) == 0:
                return boxes

            filtered_boxes = []
            used_indices = set()

            for i, box1 in enumerate(boxes):
                if i in used_indices:
                    continue

                # Bu box'ı kullan
                filtered_boxes.append(box1)
                used_indices.add(i)

                # Aynı kişi için overlapping box'ları bul ve kaldır
                for j, box2 in enumerate(boxes):
                    if j <= i or j in used_indices:
                        continue

                    # Aynı class_id kontrolü
                    if len(box1) >= 6 and len(box2) >= 6:
                        if box1[-1] == box2[-1] == person_id:  # Aynı class (person)
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

                                # IoU
                                if union_area > 0:
                                    iou = inter_area / union_area

                                    # Yüksek overlap varsa, confidence'ı daha yüksek olanı seç
                                    if iou > iou_threshold:
                                        conf1 = box1[4] if len(box1) > 4 else 0.5
                                        conf2 = box2[4] if len(box2) > 4 else 0.5

                                        # Daha düşük confidence'lı olan'ı kaldır
                                        if conf2 > conf1:
                                            # box2 daha iyi, box1'i değiştir
                                            filtered_boxes[-1] = box2

                                        used_indices.add(j)

            return np.array(filtered_boxes, dtype="int") if filtered_boxes else np.array([])

        # Çift detection'ları filtrele
        bboxes = filter_duplicate_detections(bboxes, iou_threshold=0.3)

        # Bu frame'de tespit edilen kişiler ve zone durumları
        detected_people_in_zone = set()
        detected_people_outside_zone = set()

        for box in bboxes:
            if len(box) == 7:
                x1, y1, x2, y2, track_id, score, class_id = box
            elif len(box) == 6:
                x1, y1, x2, y2, score, class_id = box
                track_id = -1  # or None, depending on desired handling
            else:
                # Handle unexpected box format, e.g., skip or log an error
                print(f"Uyarı: Beklenmeyen kutu formatı: {box}")
                continue

            if class_id == person_id and track_id != -1:
                person_anchor_point = (int((x1 + x2) / 2), int(y2))
                is_inside = cv2.pointPolygonTest(counting_zone_polygon, person_anchor_point, False) >= 0

                # Kişinin zone durumunu kaydet
                if is_inside:
                    detected_people_in_zone.add(track_id)
                    people_tracked.add(track_id)  # Zone'a giren kişiyi track et
                else:
                    detected_people_outside_zone.add(track_id)

                # Eğer kişi daha önce track ediliyordu ama şimdi zone dışında görüldüyse, tracking'ten çıkar
                if track_id in people_tracked and not is_inside:
                    people_tracked.discard(track_id) # remove() yerine discard() kullanmak daha güvenlidir, yoksa hata vermez

                # Renk belirleme
                if track_id in people_tracked:
                    if is_inside:
                        color = (0, 255, 0)  # Yeşil - zone içinde
                    else:
                        color = (0, 255, 255)  # Sarı - takip ediliyor ama zone dışında
                else:
                    color = (0, 0, 255)  # Kırmızı - zone'a hiç girmemiş veya tracking'ten çıkarılmış

                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

                # Status text
                if track_id in people_tracked:
                    status = "TRACKED"
                    if is_inside:
                        status = "IN_ZONE"
                else:
                    status = "OUTSIDE"

                text = f"ID:{track_id} {status}"
                cv2.putText(frame, text, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
                cv2.circle(frame, person_anchor_point, 5, color, -1)

        # Zone içinde olan kişileri güncelle
        people_in_zone = detected_people_in_zone

        # Sayım: Takip edilen tüm kişiler (zone içinde + zone'a daha önce girmiş olanlar)
        current_count = len(people_tracked)
        count_text = f"Wagon Count: {current_count}"
        cv2.putText(frame, count_text, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)

        # Debug bilgileri
        debug_text = f"In Zone: {len(people_in_zone)} | Tracked: {len(people_tracked)}"
        cv2.putText(frame, debug_text, (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        percent_Full = (current_count / wagon_capacity * 100)

        # Write fullness to log file
        try:
            with open(fullness_log_file, "w") as f:
                f.write(f"{percent_Full:.2f}")
        except IOError as e:
            print(f"Error writing to fullness log file {fullness_log_file}: {e}")

        out.write(frame)

    cap.release()
    out.release()
    print(f"✅ Video kaydedildi: {output_path}")

# Örnek kullanım (eğer birden fazla video işleyecekseniz):
if __name__ == "__main__":
    # Örneğin, 'input_videos' klasöründeki tüm videoları işle
    input_video_dir = "input_videos" # Bu klasörü projenizin kök dizininde oluşturmanız gerekebilir
    os.makedirs("outputs/videos", exist_ok=True)
    os.makedirs("outputs/logs", exist_ok=True)


    if os.path.exists(input_video_dir):
        video_files = [os.path.join(input_video_dir, f) for f in os.listdir(input_video_dir) if f.endswith(('.mp4', '.avi', '.mov'))]
        if not video_files:
            print(f"'{input_video_dir}' klasöründe işlenecek video bulunamadı.")
            print("Lütfen videolarınızı 'input_videos' klasörüne koyun.")
        for video_file in video_files:
            print(f"İşleniyor: {video_file}")
            process_video(video_file)
            print("-" * 50)
    else:
        print(f"'{input_video_dir}' klasörü bulunamadı. Lütfen giriş videolarınızı bu klasöre koyun.")