import cv2, csv
from ultralytics import YOLO
import math


# Total number of screws to unscrew the hard drive
TOTAL_SCREWS = 7

# x-coordinate for origin of L-fixture
X_ORIGIN = 0

# y-coordinate for origin of L-fixture
Y_ORIGIN = 0

# ratio of mm per px
# used to convert to real world coordinates
RATIO = 0.2293578


def find_screws():
    model = YOLO("final_model.pt")
    cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)
    zoom_scale = 1.5
    if not cap.isOpened():
        print("error")
        return
    
    class_names = model.names
    screw_coordinates = [("x_coord", "y_coord")]

    screw_coordinates.append(photo_capture(zoom_scale, cap, model, class_names))
    
    cap.release()
    cv2.destroyAllWindows()

    with open("coordinates.csv", mode="w", newline="", encoding="utf-8") as file:
      writer = csv.writer(file)
      writer.writerows(screw_coordinates)


def photo_capture(zoom_scale, cap, model, class_names):
    num_boxes = 0
    screw_centers = []
    
    while num_boxes < TOTAL_SCREWS:
        ret, frame = cap.read()
        if not ret:
            print("End of stream or error reading frame.")
            return

        height, width, channels = frame.shape
        
        center_x, center_y = int(width / 2), int(height / 2)
        radius_x, radius_y = int(center_x / zoom_scale), int(center_y / zoom_scale)
    
        min_x, max_x = int(center_x - radius_x), int(center_x + radius_x)
        min_y, max_y = int(center_y - radius_y), int(center_y + radius_y)
    
        cropped_frame = frame[min_y:max_y, min_x:max_x]
        zoomed_frame = cv2.resize(cropped_frame, (width, height))

        # Run YOLOv8 inference on the frame
        results = model(zoomed_frame, conf=0.5) # conf=0.5 means 50% confidence threshold

        # Process and draw detections
        for r in results:
            boxes = r.boxes.xyxy.cpu().numpy()
            confidences = r.boxes.conf.cpu().numpy()
            class_ids = r.boxes.cls.cpu().numpy()

            num_boxes = len(boxes);
            print("num boxes is", boxes)
            print("confidence", confidences)
            print('class_ids', class_ids)
            print("HERERERERE", num_boxes);

            for box, conf, class_id in zip(boxes, confidences, class_ids):
                x1, y1, x2, y2 = map(int, box)
                label = f"{class_names[int(class_id)]}: {conf:.2f}"
            # print(f"Coordinates: {x1}, {y1}, {x2}, {y2}")
                (center_x, center_y) = find_center(x1, x2, y1, y2)
            # print("found center: (x = ", center_x, "y = ", center_y, ")")
                screw_centers.append((center_x, center_y))


                cv2.rectangle(zoomed_frame, (x1, y1), (x2, y2), (0, 255, 0), 2) # Green rectangle

                cv2.putText(zoomed_frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2) # Green text

                cv2.imshow('YOLOv8 Object Detection', zoomed_frame)
                # img = cv2.imread(frame)

                cv2.imwrite("saved_image.jpg", zoomed_frame)

    return screw_centers


def find_center(x1, x2, y1, y2):
    center_x = math.ceil((x1 + x2) / 2)
    center_y = math.ceil((y1 + y2) / 2)

    return (center_x, center_y)

def calculate_distance(screw_centers):
    real_coords = []

    for (screw_x, screw_y) in screw_centers:
        x_real = (screw_x - X_ORIGIN) * RATIO
        y_real = (screw_y - Y_ORIGIN) * RATIO

        real_coords.append((x_real, y_real))

    print(real_coords)
    return real_coords