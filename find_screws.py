import cv2, csv
from ultralytics import YOLO
import math
import os
import numpy as np
os.environ["QT_LOGGING_RULES"] = "qt.qpa.fonts.warning=false"

# Total number of screws to unscrew the hard drive
TOTAL_SCREWS = 5

# x-coordinate for origin of L-fixture
X_ORIGIN = 74 #137

# y-coordinate for origin of L-fixture
Y_ORIGIN = 56 #130 5

# ratio of mm per px
# used to convert to real world coordinates
RATIO = 0.355871886121

HSV_COLOURS = {
    "green":  [[40, 80, 60],  [83, 255, 255]],
    "blue":   [[85, 80, 60], [100, 255, 255]],
    "orange": [[5, 80, 60], [20, 255, 255]],
}

DOTS_MM = {
    "green": (65, 12),
    "blue": (0.15, 11),
    "orange": (0.15, 55.7)
}


def find_screws():
    model = YOLO("screw_finding/final_final.pt")
    cap = cv2.VideoCapture(0)
    zoom_scale = 1.5
    if not cap.isOpened():
        print(cap)
        raise Exception("Cap not opened, whatever that means")

    M = calibrate(cap)
    if M is None:
        raise Exception("Could not find all 3 calibration dots")
    
    class_names = model.names
    
    screw_coordinates = []
    screw_coordinates.extend(photo_capture(zoom_scale, cap, model, class_names))
    final_coords = [("x_coord", "y_coord")]

    for screw in screw_coordinates:
        # final_coords.append(calculate_distance(screw[0], screw[1]))
        x_mm, y_mm = pixel_to_mm(M, screw[0], screw[1])
        final_coords.append((float(x_mm), float(y_mm)))

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
    
        # cropped_frame = frame[min_y:max_y, min_x:max_x]
        # zoomed_frame = cv2.resize(cropped_frame, (width, height))

        # Run YOLOv8 inference on the frame
        results = model(frame, conf=0.5) # conf=0.5 means 50% confidence threshold

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


                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2) # Green rectangle

                cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2) # Green text

                cv2.imshow('YOLOv8 Object Detection', frame)
                # img = cv2.imread(frame)

                cv2.imwrite("saved_image.jpg", frame)

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




def find_coloured_dot(frame, lo, hi):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array(lo), np.array(hi))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return None
    c = max(cnts, key=cv2.contourArea)
    m = cv2.moments(c)
    if m["m00"] == 0:
        return None
    return (m["m10"] / m["m00"], m["m01"] / m["m00"])



# def test_coloured_dots(colour):
#     cap = cv2.VideoCapture(0)
#     if not cap.isOpened():
#         raise SystemExit("Camera not opened")
    
#     lo, hi = HSV_COLOURS[colour]
#     while True:
#         ok, frame = cap.read()
#         if not ok:
#             break
    
#         p = find_coloured_dot(frame, lo, hi)
#         if p is None:
#             cv2.putText(frame, f"{colour}: NOT FOUND", (10, 30),
#                         cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
#         else:
#             cx, cy = int(p[0]), int(p[1])
#             cv2.circle(frame, (cx, cy), 12, (0, 255, 0), 2)
#             cv2.circle(frame, (cx, cy), 2, (0, 255, 0), -1)
#             cv2.putText(frame, f"{colour}: ({p[0]:.1f}, {p[1]:.1f})", (10, 30),
#                         cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    
#         cv2.imshow("detection", frame)
#         if cv2.waitKey(1) & 0xFF == ord("q"):
#             break
    
#     cap.release()
#     cv2.destroyAllWindows()


def get_affine(frame):
    src, dst = [], []
    for name, (lo, hi) in HSV_COLOURS.items():
        p = find_coloured_dot(frame, lo, hi)
        if p is None:
            return None            # a dot was not found
        src.append(p)
        dst.append(DOTS_MM[name])
    return cv2.getAffineTransform(np.float32(src), np.float32(dst))

def pixel_to_mm(M, cx, cy):
    x, y = M @ np.array([cx, cy, 1.0])
    return (x, y)

def calibrate(cap, n=10):
    """Average the transform over a few frames to reduce noise."""
    Ms = []
    for _ in range(n):
        ok, frame = cap.read()
        if not ok:
            continue
        M = get_affine(frame)
        if M is not None:
            Ms.append(M)
    return np.mean(Ms, axis=0) if Ms else None



if __name__ == "__main__":
    find_screws();
    # test_coloured_dots("green")