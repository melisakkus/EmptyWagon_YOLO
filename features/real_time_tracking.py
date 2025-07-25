import numpy as np
import os
from ultralytics import YOLO
import cv2

model_name = "models/best.pt"
#model_name = "models/yolov8n.pt"
#model_name = "models/yolo11n.pt"
model = YOLO(model_name)
person_id = 0

counting_zone_polygon = np.array([
    [565,372],  # Referans çizgisinin sol üstü
    [853,374],  # Referans çizgisinin sağ üstü
    [1177,703], # Çerçevenin sağ altı (veya vagonun görünen sınırı)
    [213,709]   # Çerçevenin sol altı (veya vagonun görünen sınırı)
], np.int32)

width = 1200
height = 750

def process_video(video_path, output_path):
    cap = cv2.VideoCapture(video_path)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    all_people_inside_zone = set()

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
            x1, y1, x2, y2, track_id, score, class_id = box
            if class_id == person_id:
                person_anchor_point = (int((x1 + x2) / 2), int(y2))
                is_inside = cv2.pointPolygonTest(counting_zone_polygon, person_anchor_point, False) >= 0
                if is_inside:
                    color = (0, 255, 0)
                    people_inside_zone.add(track_id)
                    all_people_inside_zone.add(track_id)
                else:
                    color = (0, 0, 255)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                text = f"ID:{track_id}"
                cv2.putText(frame, text, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                cv2.circle(frame, person_anchor_point, 5, color, -1)
        current_count = len(people_inside_zone)
        count_text = f"Wagon Count: {current_count}"
        cv2.putText(frame, count_text, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
        out.write(frame)
        #cv2.imshow("Subway Object Counting", frame)
        #if cv2.waitKey(10) & 0xFF == ord('q'):
        #    break
    cap.release()
    out.release()
    #cv2.destroyAllWindows()
    return len(all_people_inside_zone)

def main():
    videos_dir = "data/videos"
    output_dir = "outputs/videos"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    for filename in os.listdir(videos_dir):
        if filename.endswith(".mp4"):
            video_path = os.path.join(videos_dir, filename)
            output_path = os.path.join(output_dir, f"ov_{os.path.splitext(filename)[0]}.mp4")
            count = process_video(video_path, output_path)
            print(f"{filename} = {count}")

if __name__ == "__main__":
    main()