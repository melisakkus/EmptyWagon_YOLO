import cv2
import numpy as np
from ultralytics import YOLO

video_path = "data/videos/test-wagon-stable.mp4"
cap = cv2.VideoCapture(video_path)

model_name = "models/yolov8n.pt"
#model_name = "models/yolo11n.pt"
model = YOLO(model_name)
person_id = 0

output_path = "outputs/videos/ov_YOLOv8n.mp4"
fourcc = cv2.VideoWriter_fourcc(*"mp4v")
fps = int(cap.get(cv2.CAP_PROP_FPS))
width = 1200
height = 750
out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

counting_zone_polygon = np.array([
    [565,372],  # Referans çizgisinin sol üstü
    [853,374],  # Referans çizgisinin sağ üstü
    [1177,703], # Çerçevenin sağ altı (veya vagonun görünen sınırı)
    [213,709]   # Çerçevenin sol altı (veya vagonun görünen sınırı)
], np.int32)
# --------------------------------

while(True):
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.resize(frame, (1200, 750))

    # Her karede sayım için kullanılacak bir set oluştur.
    # Set, aynı ID'nin birden çok kez sayılmasını engeller.
    people_inside_zone = set()
    # Görselleştirme için poligonu çizdirelim
    cv2.polylines(frame, [counting_zone_polygon], isClosed=True, color=(255, 0, 0), thickness=2)
    # --------------------------------

    # Object tracking
    result = model.track(frame, persist=True, verbose=False)[0]
    bboxes = np.array(result.boxes.data.tolist(), dtype="int")

    for box in bboxes:
        x1, y1, x2, y2, track_id, score, class_id = box
        if class_id == person_id:
            # Kişinin alt-orta noktasını hesapla
            person_anchor_point = (int((x1 + x2) / 2), int(y2))

            # Kişinin anchor noktasının poligon içinde olup olmadığını kontrol et
            is_inside = cv2.pointPolygonTest(counting_zone_polygon, person_anchor_point, False) >= 0

            if is_inside:
                color = (0, 255, 0) # Yeşil
                people_inside_zone.add(track_id)
            else:
                color = (0, 0, 255) # Kırmızı

            # Kutuyu ve ID'yi çizdir
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            text = "ID:{}".format(track_id)
            cv2.putText(frame, text, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            # Kişinin kontrol edilen anchor noktasını da görselleştirelim (hata ayıklama için yararlı)
            cv2.circle(frame, person_anchor_point, 5, color, -1)
            # ------------------------------------

    # Her karenin sonunda, o an içeride olan kişi sayısını ekrana yazdır
    current_count = len(people_inside_zone)
    count_text = f"Wagon Count: {current_count}"
    cv2.putText(frame, count_text, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)

    out.write(frame)
    cv2.imshow("Subway Object Counting", frame)

    if cv2.waitKey(10) & 0xFF == ord('q'):
        break

cap.release()
out.release()  # Video writer'ı kapat
cv2.destroyAllWindows()
print(f"Video kaydedildi: {output_path}")
