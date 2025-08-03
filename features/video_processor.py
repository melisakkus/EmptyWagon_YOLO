import cv2
import numpy as np
from ultralytics import YOLO
import os
import time

# Global ayarlar
model_name = "models/best.pt"
person_id = 0

wagon_capacity = 30

# Sayım bölgesi
counting_zone_polygon = np.array([
    [565, 372],
    [853, 374],
    [1177, 703],
    [213, 709]
], np.int32)

# Tek video işleme fonksiyonu
def process_video(video_file):
#    time.sleep(3)
    video_name = os.path.basename(video_file)
    output_video_name = "ov_" + video_name
    output_path = os.path.join("outputs", "videos", output_video_name)

    # Path for the real-time fullness log file
    fullness_log_dir = os.path.join("outputs", "logs")
    os.makedirs(fullness_log_dir, exist_ok=True) # Ensure directory exists
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
        people_inside_zone = set()
        cv2.polylines(frame, [counting_zone_polygon], isClosed=True, color=(255, 0, 0), thickness=2)

        result = model.track(frame, persist=True, verbose=False)[0]
        bboxes = np.array(result.boxes.data.tolist(), dtype="int")

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

            if class_id == person_id:
                person_anchor_point = (int((x1 + x2) / 2), int(y2))
                is_inside = cv2.pointPolygonTest(counting_zone_polygon, person_anchor_point, False) >= 0

                color = (0, 255, 0) if is_inside else (0, 0, 255)
                if is_inside:
                    people_inside_zone.add(track_id)

                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                text = f"ID:{track_id}"
                cv2.putText(frame, text, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                cv2.circle(frame, person_anchor_point, 5, color, -1)

        current_count = len(people_inside_zone)
        count_text = f"Wagon Count: {current_count}"
        cv2.putText(frame, count_text, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)

        #print(f"Kişi Sayısı: {current_count} kişi")

        percent_Full = (current_count/wagon_capacity * 100)
        #print(f"Vagon Doluluğu : %{percent_Full:.2f}")

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
    # No return value needed anymore as it's written to a file
