import cv2, csv
from ultralytics import YOLO
import math
import os
os.environ["QT_LOGGING_RULES"] = "qt.qpa.fonts.warning=false"

# Total number of screws to unscrew the hard drive
TOTAL_SCREWS = 5

# x-coordinate for origin of L-fixture
X_ORIGIN = 72

# y-coordinate for origin of L-fixture
Y_ORIGIN = 169

# ratio of mm per px
# used to convert to real world coordinates
RATIO = 0.43668122271


def find_screws():
    model = YOLO("screw_finding/final_final.pt")
    cap = cv2.VideoCapture(0)
    zoom_scale = 1.5
    if not cap.isOpened():
        print(cap)
        raise Exception("Cap not opened, whatever that means")
        
    
    class_names = model.names
    
    screw_coordinates = []
    screw_coordinates.extend(photo_capture(zoom_scale, cap, model, class_names))
    final_coords = [("x_coord", "y_coord")]

    for screw in screw_coordinates:
        final_coords.append(calculate_distance(screw[0], screw[1]))

    cap.release()
    cv2.destroyAllWindows()

    with open("coordinates.csv", mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerows(final_coords)

    with open('coordinates.csv', 'r') as file:
        print("File is generated with coordinates!")
        return True
    
    return False


def photo_capture(zoom_scale, cap, model, class_names):
    num_boxes = 0
    screw_centers = []
    
    while num_boxes < TOTAL_SCREWS:
        screw_centers = []
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

def calculate_distance(center_x, center_y):

    x_real = (center_x - X_ORIGIN) * RATIO
    y_real = (center_y - Y_ORIGIN) * RATIO
    print("x_dist:", (center_x - X_ORIGIN))
    print("y_dist:", (center_y - Y_ORIGIN))
    return (x_real, y_real)

if __name__ == "__main__":
    find_screws();