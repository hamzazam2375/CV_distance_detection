from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import numpy as np
import cv2
import base64
import traceback
import os

app = Flask(__name__)
CORS(app)

FOCAL_LENGTH = 2133.0
MAX_DISTANCE_M = 100.0

CAUTION_DISTANCE_M = 3.0
STOP_DISTANCE_M = 2.0

REAL_WIDTHS_M = {
    'person': 0.5,
    'car': 1.76,
    'bike': 0.7,
    'truck': 2.5,
}

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
    if bbox_width_px <= 0 or object_type not in REAL_WIDTHS_M:
        return MAX_DISTANCE_M

    real_width_m = REAL_WIDTHS_M[object_type]
    distance_m = (real_width_m * FOCAL_LENGTH) / bbox_width_px
    distance_m = float(max(0.0, min(distance_m, MAX_DISTANCE_M)))
    return round(distance_m, 2)


MODEL = None
MODEL_NAMES = {}
try:
    from ultralytics import YOLO
    MODEL = YOLO('yolov8n.pt')
    MODEL_NAMES = MODEL.names if hasattr(MODEL, 'names') else {}
except Exception:
    MODEL = None
    MODEL_NAMES = {}


def detect_primary_object(frame_bgr):
    if MODEL is None:
        return None, 'model_unavailable'

    try:
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        results = MODEL(frame_rgb, imgsz=640, conf=0.15, verbose=False)
        if len(results) == 0:
            return [], 'no_result'

        r = results[0]
        boxes = getattr(r, 'boxes', None)
        if boxes is None:
            return [], 'no_boxes'

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

    try:
        cv2.imwrite('latest_raw.jpg', frame)
    except Exception:
        pass

    detections, status = detect_primary_object(frame)

    if status == 'model_unavailable':
        return jsonify({'object': None, 'confidence': 0.0, 'distance': MAX_DISTANCE_M, 'warning': 'safe', 'unit': 'm', 'status': 'model_unavailable'})

    if not detections:
        return jsonify({'object': None, 'confidence': 0.0, 'distance': MAX_DISTANCE_M, 'warning': 'safe', 'unit': 'm', 'status': status})

    best = max(detections, key=lambda d: d['confidence'])
    x1, y1, x2, y2 = best['box']
    bbox_w = max(1.0, abs(x2 - x1))
    distance_m = estimate_distance_from_bbox(bbox_w, best['label'])

    if distance_m < STOP_DISTANCE_M:
        warning = 'stop'
    elif distance_m < CAUTION_DISTANCE_M:
        warning = 'caution'
    else:
        warning = 'safe'

    annotated = frame.copy()
    for det in detections:
        bx = [int(v) for v in det['box']]
        lx, ly, rx, ry = bx
        label = det['label']
        conf = det['confidence']

        color = (0, 255, 0)
        if det is best:
            color = (0, 200, 255)

        cv2.rectangle(annotated, (lx, ly), (rx, ry), color, 2)
        caption = f"{label} {conf:.2f}"
        cv2.putText(annotated, caption, (lx, max(ly - 6, 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    try:
        _, img_buf = cv2.imencode('.jpg', annotated, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        annotated_b64 = base64.b64encode(img_buf.tobytes()).decode('ascii')
        try:
            with open('latest_annotated.jpg', 'wb') as f:
                f.write(img_buf.tobytes())
        except Exception:
            pass
    except Exception:
        annotated_b64 = None

    response = {
        'object': best['label'],
        'confidence': round(best['confidence'], 3),
        'distance': distance_m,
        'bbox_width_px': round(float(bbox_w), 2),
        'warning': warning,
        'unit': 'm',
        'status': 'ok',
        'detections': [
            {'label': d['label'], 'confidence': round(d['confidence'], 3), 'box': d['box']} for d in detections
        ],
        'annotated': annotated_b64,
    }

    return jsonify(response)


@app.route('/latest-annotated', methods=['GET'])
def latest_annotated():
    path = 'latest_annotated.jpg'
    if os.path.exists(path):
        return send_file(path, mimetype='image/jpeg')
    return jsonify({'error': 'not_found'}), 404


@app.route('/reset', methods=['POST'])
def reset():
    return jsonify({'status': 'reset'})


@app.route('/health', methods=['GET'])
def health():
    ok = MODEL is not None
    return jsonify({'status': 'ok' if ok else 'model_unavailable'})

if __name__ == '__main__':
    print('DriveSafe AI backend starting on http://0.0.0.0:8000')
    app.run(host='0.0.0.0', port=8000, debug=True)
