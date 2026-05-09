from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import cv2
import base64
import traceback

app = Flask(__name__)
CORS(app)

# Beginner-friendly settings
FOCAL_LENGTH = 800.0  # camera focal length proxy (tune for your device)
MAX_DISTANCE_M = 100.0  # max detectable distance in meters

# Warning thresholds in meters (distance estimation based on bounding box width)
CAUTION_DISTANCE_M = 3.0  # distance > 3m: SAFE
STOP_DISTANCE_M = 1.0    # distance < 1m: STOP, 1-3m: CAUTION

# Approximate real object widths in meters (based on pinhole camera model)
# Used for distance formula: D = (Real_Width * Focal_Length) / Pixel_Width
REAL_WIDTHS_M = {
    'person': 0.5,      # average shoulder width
    'car': 1.8,         # average car width
    'bike': 0.7,        # average bike width
    'truck': 2.5,       # average truck width
}

# Allowed COCO class labels mapped into our categories
ALLOWED_LABELS = {
    'person': 'person',
    'car': 'car',
    'bicycle': 'bike',
    'motorcycle': 'bike',
    'truck': 'truck',
    'bus': 'truck',
}


def decode_base64_image(b64_string):
    try:
        img_bytes = base64.b64decode(b64_string)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return img
    except Exception:
        return None


def estimate_distance_from_bbox(bbox_width_px, object_type):
    """
    Estimate distance using pinhole camera model.
    Formula: Distance = (Real Object Width in meters × Focal Length) / Bounding Box Width in pixels
    
    Args:
        bbox_width_px: width of bounding box in pixels
        object_type: label (person, car, bike, truck)
    
    Returns:
        Distance in meters (float), clamped to [0, MAX_DISTANCE_M]
    """
    if bbox_width_px <= 0 or object_type not in REAL_WIDTHS_M:
        return MAX_DISTANCE_M

    real_width_m = REAL_WIDTHS_M[object_type]
    # Distance in meters = (real width × focal length) / pixel width
    distance_m = (real_width_m * FOCAL_LENGTH) / bbox_width_px
    # Clamp to valid range
    distance_m = float(max(0.0, min(distance_m, MAX_DISTANCE_M)))
    return round(distance_m, 2)


# Try to load YOLOv8 model (ultralytics). This will fail gracefully if not installed.
MODEL = None
MODEL_NAMES = {}
try:
    from ultralytics import YOLO

    # This uses the official YOLOv8 nano weights. Make sure you have internet
    # or the file 'yolov8n.pt' in the working directory. ultralytics will
    # download the weights automatically on first use if necessary.
    MODEL = YOLO('yolov8n.pt')
    MODEL_NAMES = MODEL.names if hasattr(MODEL, 'names') else {}
except Exception as e:
    MODEL = None
    MODEL_NAMES = {}
    print('Warning: ultralytics YOLO model not loaded:', str(e))


def detect_primary_object(frame_bgr):
    """
    Runs YOLOv8 and returns a list of detections (allowed classes only).
    Each detection is a dict: { label, confidence, box } where box is [x1,y1,x2,y2].
    Returns (detections_list, status_str).
    """
    if MODEL is None:
        return None, 'model_unavailable'

    try:
        # ultralytics expects RGB images
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

        # Run inference (imgs size and confidence threshold chosen for speed)
        results = MODEL(frame_rgb, imgsz=640, conf=0.25, verbose=False)
        if len(results) == 0:
            return [], 'no_result'

        r = results[0]
        boxes = getattr(r, 'boxes', None)
        if boxes is None:
            return [], 'no_boxes'

        # Extract arrays of boxes, confidences and class ids in a robust way
        xyxy = np.array(boxes.xyxy.cpu()) if hasattr(boxes.xyxy, 'cpu') else np.array(boxes.xyxy)
        confs = np.array(boxes.conf.cpu()) if hasattr(boxes.conf, 'cpu') else np.array(boxes.conf)
        cls_ids = np.array(boxes.cls.cpu()).astype(int) if hasattr(boxes.cls, 'cpu') else np.array(boxes.cls).astype(int)

        detections = []
        for (box, conf, cid) in zip(xyxy, confs, cls_ids):
            label_raw = MODEL_NAMES.get(int(cid), str(cid))
            if label_raw in ALLOWED_LABELS:
                detections.append({
                    'label': ALLOWED_LABELS[label_raw],
                    'confidence': float(conf),
                    'box': [float(x) for x in box],
                })

        return detections, 'ok' if len(detections) > 0 else 'no_allowed_object'
    except Exception:
        traceback.print_exc()
        return None, 'detection_error'


@app.route('/upload-frame', methods=['POST'])
def upload_frame():
    try:
        data = request.get_json(silent=True)
    except Exception:
        data = None

    if not data or 'image' not in data:
        return jsonify({'error': 'missing_image'}), 400

    frame = decode_base64_image(data['image'])
    if frame is None:
        return jsonify({'error': 'invalid_image'}), 200

    # detect objects (returns list of allowed detections)
    detections, status = detect_primary_object(frame)

    # If model not available, return safe default with helpful status
    if status == 'model_unavailable':
        return jsonify({'object': None, 'confidence': 0.0, 'distance': MAX_DISTANCE_M, 'warning': 'safe', 'unit': 'm', 'status': 'model_unavailable'})

    # No detections -> safe
    if not detections:
        return jsonify({'object': None, 'confidence': 0.0, 'distance': MAX_DISTANCE_M, 'warning': 'safe', 'unit': 'm', 'status': status})

    # Choose the best detection (highest confidence) for distance estimate
    best = max(detections, key=lambda d: d['confidence'])
    x1, y1, x2, y2 = best['box']
    bbox_w = max(1.0, abs(x2 - x1))  # bounding box width in pixels
    distance_m = estimate_distance_from_bbox(bbox_w, best['label'])

    # Determine warning level based on distance in meters
    if distance_m < STOP_DISTANCE_M:
        warning = 'stop'  # STOP: very close (< 1m)
    elif distance_m < CAUTION_DISTANCE_M:
        warning = 'caution'  # CAUTION: medium distance (1-3m)
    else:
        warning = 'safe'  # SAFE: far distance (> 3m)

    # Draw bounding boxes and labels on the frame for visualization
    annotated = frame.copy()
    for det in detections:
        bx = [int(v) for v in det['box']]
        lx, ly, rx, ry = bx
        label = det['label']
        conf = det['confidence']

        # color per warning (green/orange/red)
        color = (0, 255, 0)
        # if this detection is the best, use a brighter color
        if det is best:
            color = (0, 200, 255)

        # draw rectangle and label
        cv2.rectangle(annotated, (lx, ly), (rx, ry), color, 2)
        caption = f"{label} {conf:.2f}"
        cv2.putText(annotated, caption, (lx, max(ly - 6, 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    # Encode annotated image as JPEG and then base64 for easy transport
    try:
        _, img_buf = cv2.imencode('.jpg', annotated, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        annotated_b64 = base64.b64encode(img_buf.tobytes()).decode('ascii')
    except Exception:
        annotated_b64 = None

    # Prepare response with list of detections and the annotated image
    response = {
        'object': best['label'],
        'confidence': round(best['confidence'], 3),
        'distance': distance_m,  # distance in meters
        'warning': warning,  # 'safe', 'caution', or 'stop'
        'unit': 'm',  # meters
        'status': 'ok',
        'detections': [
            {'label': d['label'], 'confidence': round(d['confidence'], 3), 'box': d['box']} for d in detections
        ],
        'annotated': annotated_b64,
    }

    return jsonify(response)


@app.route('/reset', methods=['POST'])
def reset():
    # nothing stateful to reset for this simple backend, but keep endpoint
    return jsonify({'status': 'reset'})


@app.route('/health', methods=['GET'])
def health():
    ok = MODEL is not None
    return jsonify({'status': 'ok' if ok else 'model_unavailable'})


if __name__ == '__main__':
    print('DriveSafe AI backend starting on http://0.0.0.0:8000')
    app.run(host='0.0.0.0', port=8000, debug=True)
