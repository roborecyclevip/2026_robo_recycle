import cv2, csv
from ultralytics import YOLO
import math
import os
import numpy as np
from itertools import permutations
os.environ["QT_LOGGING_RULES"] = "qt.qpa.fonts.warning=false"

# Total number of screws to unscrew the hard drive
TOTAL_SCREWS = 2

# x-coordinate for origin of L-fixture
X_ORIGIN = 74 #137

# y-coordinate for origin of L-fixture
Y_ORIGIN = 56 #130 5

# ratio of mm per px
# used to convert to real world coordinates
RATIO = 0.355871886121

# Number of frames to collect
NUM_FRAMES = 15

# Maximum number of frames we'll attempt to capture - including failures
MAX_ATTEMPTS = 50

# Maximum allowed distance between a screw's
# reference position and its detected position (pixels)
MAX_MATCH_DISTANCE = 30

HSV_COLOURS = {
    "purple":  [[130, 50, 50],  [160, 255, 255]],
    "blue":   [[90, 80, 60], [128, 255, 255]],
    "orange": [[10, 100, 60], [25, 255, 255]],
}

DOTS_MM = {
    "purple": (0.4, 55.3),
    "blue": (0.4, 8.9),
    "orange": (67.9, 8.1)
}


def find_screws():
    model = YOLO("screw_finding/final_final.pt")
    #model = YOLO("fake_hdd_model.pt")
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
    screw_coordinates.extend(photo_capture2(zoom_scale, cap, model, class_names))
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
    
    while num_boxes < TOTAL_SCREWS - 1:
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
                # (center_x, center_y) = find_center(x1, x2, y1, y2)
                # Original YOLO centre
                bbox_cx, bbox_cy = find_center(x1, x2, y1, y2)

                # Refined OpenCV centre
                refined_cx, refined_cy = refine_screw_center(frame,(x1, y1, x2, y2))

                # Draw original centre in red
                cv2.circle(frame, (int(bbox_cx), int(bbox_cy)), 5, (0, 0, 255), -1)

                # Draw refined centre in blue
                cv2.circle(frame, (int(refined_cx), int(refined_cy)), 5, (255, 0, 0), -1)


            # print("found center: (x = ", center_x, "y = ", center_y, ")")
                screw_centers.append((refined_cx, refined_cy))


                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2) # Green rectangle

                cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2) # Green text

                cv2.imshow('YOLOv8 Object Detection', frame)
                # img = cv2.imread(frame)

                cv2.imwrite("saved_image.jpg", frame)

    return screw_centers


def find_center(x1, x2, y1, y2):
    center_x = math.ceil((x1 + x2) / 2.0)
    center_y = math.ceil((y1 + y2) / 2.0)

    return (center_x, center_y)

def calculate_distance(center_x, center_y):

    x_real = (center_x - X_ORIGIN) * RATIO
    y_real = (center_y - Y_ORIGIN) * RATIO
    print("x_dist:", (center_x - X_ORIGIN))
    print("y_dist:", (center_y - Y_ORIGIN))
    return (x_real, y_real)




def find_coloured_dot(frame, lo, hi):
    blurred = cv2.GaussianBlur(frame, (7,7), 0)
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
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



def test_coloured_dots(colour):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise SystemExit("Camera not opened")
    
    lo, hi = HSV_COLOURS[colour]
    while True:
        ok, frame = cap.read()
        if not ok:
           break
    
        p = find_coloured_dot(frame, lo, hi)
        if p is None:
            cv2.putText(frame, f"{colour}: NOT FOUND", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        else:
            cx, cy = int(p[0]), int(p[1])
            cv2.circle(frame, (cx, cy), 12, (0, 255, 0), 2)
            cv2.circle(frame, (cx, cy), 2, (0, 255, 0), -1)
            cv2.putText(frame, f"{colour}: ({p[0]:.1f}, {p[1]:.1f})", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    
        cv2.imshow("detection", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
           break
    
    cap.release()
    cv2.destroyAllWindows()


def get_affine(frame):
    src, dst = [], []
    for name, (lo, hi) in HSV_COLOURS.items():
        p = find_coloured_dot(frame, lo, hi)
        print(name, p)
        if p is None:
            return None            # a dot was not found
        src.append(p)
        dst.append(DOTS_MM[name])
    return cv2.getAffineTransform(np.float32(src), np.float32(dst))

def pixel_to_mm(M, cx, cy):
    x, y = M @ np.array([cx, cy, 1.0])
    return (x, y)

# def calibrate(cap, n=10):
#     """Average the transform over a few frames to reduce noise."""
#     Ms = []
#     for _ in range(n):
#         ok, frame = cap.read()
#         if not ok:
#             continue
#         M = get_affine(frame)
#         if M is not None:
#             Ms.append(M)
#     return np.mean(Ms, axis=0) if Ms else None

def calibrate(cap, n=10):
    positions = {name: [] for name in HSV_COLOURS}

    for _ in range(n):
        ok, frame = cap.read()
        if not ok:
            continue

        for name, (lo, hi) in HSV_COLOURS.items():
            p = find_coloured_dot(frame, lo, hi)

            if p is not None:
                positions[name].append(p)

                cx, cy = map(int, p)

                # Draw a circle around the detected dot
                cv2.circle(
                    frame,
                    (cx, cy),
                    10,
                    (0, 255, 0),
                    2
                )

                # Draw a small centre point
                cv2.circle(
                    frame,
                    (cx, cy),
                    3,
                    (0, 0, 255),
                    -1
                )

                # Display the colour and coordinates
                cv2.putText(
                    frame,
                    f"{name}: ({cx}, {cy})",
                    (cx + 15, cy - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 255, 255),
                    2
                )

            else:
                print(f"{name} not found!")

        # Display the camera frame
        cv2.imshow("Calibration Dots", frame)
        cv2.imwrite("calibration_dots.jpg", frame)
        cv2.waitKey(100)

    cv2.destroyWindow("Calibration Dots")

    # Make sure every dot was detected
    if any(len(points) == 0 for points in positions.values()):
        return None

    # Average the pixel coordinates of each dot
    src = []
    dst = []

    for name in HSV_COLOURS:
        avg_position = np.median(positions[name], axis=0)
        print(name, avg_position)
        src.append(avg_position)
        dst.append(DOTS_MM[name])

    return cv2.getAffineTransform(
        np.float32(src),
        np.float32(dst)
    )

def match_screws(reference, current):
    """
    Match screw detections in the current frame
    to the reference frame.

    Returns detections in the same order as reference.
    """

    num_screws = len(reference)

    # if len(reference) != TOTAL_SCREWS:
    #     return None

    if len(current) != num_screws:
        return None

    best_permutation = None
    best_cost = float("inf")

    # Try every possible ordering of the six detections
    for perm in permutations(range(num_screws)):

        distances = []

        for i in range(num_screws):
            ref_x, ref_y = reference[i]
            curr_x, curr_y = current[perm[i]]

            distance = math.sqrt(
                (ref_x - curr_x) ** 2 +
                (ref_y - curr_y) ** 2
            )

            distances.append(distance)

        cost = sum(distances)

        if cost < best_cost:
            best_cost = cost
            best_permutation = perm
            best_distances = distances

    # Reject frames where a detection is too far
    if max(best_distances) > MAX_MATCH_DISTANCE:
        return None

    # Return detections in reference order
    return [
        current[i] for i in best_permutation
    ]

def photo_capture2(zoom_scale, cap, model, class_names):
    # Stores the detections from each accepted frame.
    # Each frame contains six screw centres.
    all_frames = []

    reference = None

    attempts = 0

    best_count = 0

    while len(all_frames) < NUM_FRAMES and attempts < MAX_ATTEMPTS:

        attempts += 1

        ret, frame = cap.read()

        if not ret:
            print("Error reading frame.")
            continue

        # Run YOLO inference
        results = model(frame, conf=0.5, verbose=False)

        current_centres = []
        current_boxes = []

        for r in results:

            boxes = r.boxes.xyxy.cpu().numpy()
            class_ids = r.boxes.cls.cpu().numpy()

            for box, class_id in zip(boxes, class_ids):

                # If you have multiple classes, filter here.
                # For a single-class model, this is unnecessary.

                x1, y1, x2, y2 = map(int, box)

                # First calculate the approximate centre
                # using the bounding box.
                bbox_cx, bbox_cy = find_center(x1, x2, y1, y2)
                
                # Refined OpenCV centre
                refined_cx, refined_cy = refine_screw_center(frame,(x1, y1, x2, y2))

                # Draw original centre in red
                cv2.circle(frame, (int(bbox_cx), int(bbox_cy)), 5, (0, 0, 255), -1)

                # Draw refined centre in blue
                cv2.circle(frame, (int(refined_cx), int(refined_cy)), 5, (255, 0, 0), -1)
                cv2.imwrite("saved_image.jpg", frame)


            # print("found center: (x = ", center_x, "y = ", center_y, ")")
                current_centres.append((refined_cx, refined_cy))

                current_boxes.append((x1, y1, x2, y2))


        num_detected = len(current_centres)
        if num_detected == 0:
            continue

        if num_detected > best_count:
            best_count = num_detected
            all_frames = []
            reference = current_centres.copy()

            matched_centres = current_centres
        elif num_detected < best_count:
            continue
        else:
            matched_centres = match_screws(
                reference,
                current_centres
            )

            if matched_centres is None:
                print("Rejected frame: screw matching failed")
                continue


        all_frames.append(matched_centres)
        print(
            f"Accepted frame {len(all_frames)}/{NUM_FRAMES} "
            f"({best_count} screws detected)"
        )


        # # Only accept frames with exactly six detections
        # if len(current_centres) != TOTAL_SCREWS:
        #     print(
        #         f"Rejected frame: found {len(current_centres)} screws"
        #     )
        #     continue

        # # First valid frame becomes our reference
        # if reference is None:

        #     reference = current_centres.copy()

        #     matched_centres = current_centres

        # else:

        #     # Match screws to their reference positions
        #     matched_centres = match_screws(
        #         reference,
        #         current_centres
        #     )

        #     if matched_centres is None:
        #         print("Rejected frame: screw matching failed")
        #         continue

        # # Store the matched coordinates
        # all_frames.append(matched_centres)

        # print(
        #     f"Accepted frame {len(all_frames)}/{NUM_FRAMES}"
        # )

        # Display detections
        for (x1, y1, x2, y2), (cx, cy) in zip(
            current_boxes, current_centres
        ):

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )

            cv2.circle(
                frame,
                (int(cx), int(cy)),
                4,
                (0, 0, 255),
                -1
            )

        cv2.imshow("YOLOv8 Object Detection", frame)
        cv2.waitKey(1)

    if len(all_frames) == 0:
        raise RuntimeError("No screws were detected!")

    print(f"\nHighest number of screws detected: {best_count}")
    print(f"Number of frames collected: {len(all_frames)}")

    # if len(all_frames) < NUM_FRAMES:
    #     raise RuntimeError(
    #         f"Only collected {len(all_frames)} valid frames "
    #         f"out of {NUM_FRAMES} required."
    #     )

    # Convert to numpy array:
    # Shape = (NUM_FRAMES, TOTAL_SCREWS, 2)
    all_frames = np.array(all_frames)

    # Calculate median position for each screw
    median_centres = np.median(all_frames, axis=0)

    print("\nFinal averaged screw centres:")

    for i, (x, y) in enumerate(median_centres):
        print(f"Screw {i + 1}: ({x:.2f}, {y:.2f})")

    return [
        (float(x), float(y))
        for x, y in median_centres
    ]



def refine_screw_center(frame, box):

    x1, y1, x2, y2 = box

    # Calculate bounding box dimensions
    width = x2 - x1
    height = y2 - y1

    # Original YOLO bounding box centre
    bbox_cx = (x1 + x2) / 2.0
    bbox_cy = (y1 + y2) / 2.0

    # Add some padding around the bounding box
    # This helps capture the entire screw head
    padding = int(0.2 * max(width, height))

    img_h, img_w = frame.shape[:2]

    crop_x1 = max(0, x1 - padding)
    crop_y1 = max(0, y1 - padding)

    crop_x2 = min(img_w, x2 + padding)
    crop_y2 = min(img_h, y2 + padding)

    # Crop the screw region
    crop = frame[crop_y1:crop_y2, crop_x1:crop_x2]

    if crop.size == 0:
        return bbox_cx, bbox_cy

    # Convert to grayscale
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)

    # Reduce noise
    blurred = cv2.GaussianBlur(
        gray,
        (5, 5),
        1.5
    )

    # Estimate screw radius from bounding box dimensions
    min_dim = min(width, height)

    min_radius = max(2, int(min_dim * 0.2))
    max_radius = max(min_radius + 1, int(min_dim * 0.65))

    # Detect circles
    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=max(8, min_dim // 2),
        param1=100,
        param2=25,
        minRadius=min_radius,
        maxRadius=max_radius
    )

    # If no circles are found, fall back to YOLO centre
    if circles is None:
        return bbox_cx, bbox_cy

    circles = np.round(circles[0]).astype(int)

    # Find the circle closest to the YOLO bounding box centre
    best_circle = None
    best_distance = float("inf")

    for cx, cy, radius in circles:

        # Convert crop coordinates back to full-frame coordinates
        global_x = cx + crop_x1
        global_y = cy + crop_y1

        distance = math.sqrt(
            (global_x - bbox_cx) ** 2 +
            (global_y - bbox_cy) ** 2
        )

        if distance < best_distance:
            best_distance = distance
            best_circle = (global_x, global_y)

    # Reject circles that are too far from the YOLO detection
    if best_distance > 0.35 * max(width, height):
        return bbox_cx, bbox_cy

    # with Hough circles
    
    return (
        float(best_circle[0]),
        float(best_circle[1])
    )
    
    """
    # without Hough circles
    return (
        float(bbox_cx),
        float(bbox_cy)
    )
    """


def tune_hough(cap, model):

    # Create a window for the sliders
    cv2.namedWindow("Hough Tuning")

    # Create trackbars
    cv2.createTrackbar("dp x 10", "Hough Tuning", 12, 30, lambda x: None)
    cv2.createTrackbar("param1", "Hough Tuning", 100, 300, lambda x: None)
    cv2.createTrackbar("param2", "Hough Tuning", 25, 100, lambda x: None)
    cv2.createTrackbar("minRadius", "Hough Tuning", 5, 100, lambda x: None)
    cv2.createTrackbar("maxRadius", "Hough Tuning", 40, 150, lambda x: None)

    while True:

        ret, frame = cap.read()

        if not ret:
            break

        # Run YOLO
        results = model(frame, conf=0.5, verbose=False)

        boxes = results[0].boxes.xyxy.cpu().numpy()

        if len(boxes) == 0:
            cv2.imshow("Hough Tuning", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

            continue

        # For tuning, just use the first detected screw
        x1, y1, x2, y2 = map(int, boxes[0])

        width = x2 - x1
        height = y2 - y1

        padding = int(0.2 * max(width, height))

        img_h, img_w = frame.shape[:2]

        crop_x1 = max(0, x1 - padding)
        crop_y1 = max(0, y1 - padding)
        crop_x2 = min(img_w, x2 + padding)
        crop_y2 = min(img_h, y2 + padding)

        crop = frame[crop_y1:crop_y2, crop_x1:crop_x2]

        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)

        blurred = cv2.GaussianBlur(gray, (5, 5), 1.5)

        # Read slider values
        dp = cv2.getTrackbarPos("dp x 10", "Hough Tuning") / 10.0
        param1 = cv2.getTrackbarPos("param1", "Hough Tuning")
        param2 = cv2.getTrackbarPos("param2", "Hough Tuning")
        min_radius = cv2.getTrackbarPos("minRadius", "Hough Tuning")
        max_radius = cv2.getTrackbarPos("maxRadius", "Hough Tuning")

        # Avoid invalid values
        dp = max(dp, 0.1)
        param1 = max(param1, 1)
        param2 = max(param2, 1)

        # Ensure maxRadius > minRadius
        max_radius = max(max_radius, min_radius + 1)

        # Detect circles
        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=dp,
            minDist=max(8, min(width, height) // 2),
            param1=param1,
            param2=param2,
            minRadius=min_radius,
            maxRadius=max_radius
        )
        if circles is None:
            print("no circles:(")

        # Draw results
        display = crop.copy()

        if circles is not None:

            circles = np.round(circles[0]).astype(int)

            for cx, cy, radius in circles:

                cv2.circle(
                    display,
                    (cx, cy),
                    radius,
                    (0, 255, 0),
                    2
                )

                cv2.circle(
                    display,
                    (cx, cy),
                    3,
                    (255, 0, 0),
                    -1
                )

        # Display current parameter values
        text = f"dp={dp}, p1={param1}, p2={param2}"
        cv2.putText(
            display,
            text,
            (5, 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 255),
            1
        )

        cv2.imshow("Hough Tuning", display)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cv2.destroyWindow("Hough Tuning")


def take_photos():
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print(cap)
        raise Exception("Cap not opened, whatever that means")

    count = 0
    total = 80
    while count < total:
        ret, frame = cap.read()
        if not ret:
            print("End of stream or error reading frame.")
            return

        cv2.imwrite(f"18th-nov-photos/saved_image-{count}.jpg", frame)
        print(f"18th-nov-photos/saved_image-{count}.jpg")
        count += 1


    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    find_screws()
    #test_coloured_dots("blue")


# # if __name__ == "__main__":

# #     model = YOLO("screw_finding/final_final.pt")

# #     cap = cv2.VideoCapture(0)

# #     if not cap.isOpened():
# #         raise Exception("Camera not opened")

# #     tune_hough(cap, model)

# #     cap.release()
# #     cv2.destroyAllWindows()
