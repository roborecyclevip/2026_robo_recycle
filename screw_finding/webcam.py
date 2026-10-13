import cv2
from ultralytics import YOLO
import numpy as np
import sys, math

# Total number of screws to unscrew the hard drive
TOTAL_SCREWS = 5

# x-coordinate for origin of L-fixture
X_ORIGIN = 0

# y-coordinate for origin of L-fixture
Y_ORIGIN = 0

# ratio of mm per px
# used to convert to real world coordinates
RATIO = 0.21834061135



def main():
    is_video = None;
    if len(sys.argv) < 2:
        print("Please provide a valid flag! \n Usage: \n -v provides video output \n -p provides single picture output")
        return

    if sys.argv[1] == '-p':
        is_video = False;
    elif sys.argv[1] == '-v':
        is_video = True;
    else:
        print("Please provide a valid flag \n Usage: \n -v provides video output \n -p provides single picture output")
        return

    screw_centers = run_model(is_video)
    real_coords = calculate_distance(screw_centers)

    return real_coords


'''

'''
def run_model(is_video: bool):
    model = YOLO("final_final.pt")
    cap = cv2.VideoCapture(0)
    zoom_scale = 1.5
    if not cap.isOpened():
        print("error")
        return
    
    class_names = model.names

    if is_video:
        video_capture(zoom_scale, cap, model, class_names)
    else:
        photo_capture(zoom_scale, cap, model, class_names)
    
    cap.release()
    cv2.destroyAllWindows()
    


def video_capture(zoom_scale, cap, model, class_names):
    while True:
        # print("in while loop")
        ret, frame = cap.read()
        if not ret:
            print("End of stream or error reading frame.")
            break
        

        height, width, channels = frame.shape

        center_x, center_y = int(width / 2), int(height / 2)
        radius_x, radius_y = int(center_x / zoom_scale), int(center_y / zoom_scale)

        min_x, max_x = int(center_x - radius_x), int(center_x + radius_x)
        min_y, max_y = int(center_y - radius_y), int(center_y + radius_y)

        cropped_frame = frame[min_y:max_y, min_x:max_x]
        zoomed_frame = cv2.resize(cropped_frame, (width, height))



        # Run YOLOv8 inference on the frame
        results = model(zoomed_frame, conf=0.3) # conf=0.5 means 50% confidence threshold

        # Process and draw detections
        for r in results:
            boxes = r.boxes.xyxy.cpu().numpy()
            confidences = r.boxes.conf.cpu().numpy()
            class_ids = r.boxes.cls.cpu().numpy()

            print('boxes', boxes)

            for box, conf, class_id in zip(boxes, confidences, class_ids):
                x1, y1, x2, y2 = map(int, box)
                label = f"{class_names[int(class_id)]}: {conf:.2f}"

                cv2.rectangle(zoomed_frame, (x1, y1), (x2, y2), (0, 255, 0), 2) # Green rectangle
                cv2.putText(zoomed_frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2) # Green text

        cv2.imshow('YOLOv8 Object Detection', zoomed_frame)
        # print(frame)

        # Press 'q' to quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print('oh no')
            break

    return []

       

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

    print(screw_centers)
    return screw_centers


def find_center(x1, x2, y1, y2):
    center_x = math.ceil((x1 + x2) / 2)
    center_y = math.ceil((y1 + y2) / 2)

    return (center_x, center_y)

def calculate_distance(screw_centers):
    if not screw_centers:
        return []
    real_coords = []

    for (screw_x, screw_y) in screw_centers:
        x_real = (screw_x - X_ORIGIN) * RATIO
        y_real = (screw_y - Y_ORIGIN) * RATIO

        real_coords.append((x_real, y_real))

    print(real_coords)
    return real_coords


if __name__ == '__main__':
    main()