from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import cv2
import base64
import time
from collections import deque
import traceback

app = Flask(__name__)
CORS(app)

MAX_DISTANCE_CM = 200.0
MIN_DISTANCE_CM = 20.0
WARNING_DISTANCE_CM = 100.0
DANGER_DISTANCE_CM = 40.0

SAFE_RESPONSE = {'distance': MAX_DISTANCE_CM, 'status': 'safe_default', 'unit': 'cm'}

prev_gray = None
prev_points = None
prev_time = None
frame_number = 0
stationary_count = 0

MAX_DISTANCE_SPAN_CM = MAX_DISTANCE_CM - MIN_DISTANCE_CM
SMOOTH_WINDOW = 6
DISTANCE_SCALE = 2.0
MIN_FEATURES = 5
SPIKE_THRESHOLD = 2.5
MIN_MOTION_PX = 2.0
BLUR_KERNEL = (15, 15)
STATIONARY_COUNT_MAX = 1
FRAME_WIDTH = 640
WARMUP_FRAMES = 1

distance_history = deque(maxlen=SMOOTH_WINDOW)

LK_PARAMS = dict(
    winSize=(21, 21),
    maxLevel=3,
    criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01),
)

FEATURE_PARAMS = dict(
    maxCorners=80,
    qualityLevel=0.3,
    minDistance=5,
    blockSize=5,
)


def detect_features(gray):
    try:
        return cv2.goodFeaturesToTrack(gray, **FEATURE_PARAMS)
    except Exception:
        return None


def preprocess(frame_bgr):
    try:
        h, w = frame_bgr.shape[:2]
        if w > FRAME_WIDTH:
            scale = FRAME_WIDTH / w
            frame_bgr = cv2.resize(frame_bgr, (FRAME_WIDTH, int(h * scale)),
                                   interpolation=cv2.INTER_AREA)
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        return cv2.GaussianBlur(gray, BLUR_KERNEL, 0)
    except Exception:
        return None


def smooth_distance(raw_distance):
    raw_distance = max(MIN_DISTANCE_CM, min(float(raw_distance), MAX_DISTANCE_CM))

    if len(distance_history) >= 3:
        current_avg = sum(distance_history) / len(distance_history)
        if current_avg < MAX_DISTANCE_CM and raw_distance < current_avg / SPIKE_THRESHOLD:
            raw_distance = current_avg

    distance_history.append(raw_distance)

    weights = list(range(1, len(distance_history) + 1))
    weighted_sum = sum(s * w for s, w in zip(distance_history, weights))
    return round(weighted_sum / sum(weights), 1)


def estimate_distance(current_frame):
    global prev_gray, prev_points, prev_time, stationary_count, frame_number

    frame_number += 1
    gray = preprocess(current_frame)
    if gray is None:
        return MAX_DISTANCE_CM, "preprocess_failed"

    if frame_number <= WARMUP_FRAMES:
        prev_gray = gray
        prev_points = detect_features(gray)
        prev_time = time.time()
        distance_history.append(MAX_DISTANCE_CM)
        return MAX_DISTANCE_CM, "warming_up"

    if prev_gray is None:
        prev_gray = gray
        prev_points = detect_features(gray)
        prev_time = time.time()
        return MAX_DISTANCE_CM, "initializing"

    if prev_points is None or len(prev_points) < MIN_FEATURES:
        prev_points = detect_features(prev_gray)
        if prev_points is None or len(prev_points) < MIN_FEATURES:
            prev_gray = gray
            prev_time = time.time()
            stationary_count += 1
            return smooth_distance(MAX_DISTANCE_CM), "no_object"

    try:
        next_points, status, _ = cv2.calcOpticalFlowPyrLK(
            prev_gray, gray, prev_points, None, **LK_PARAMS
        )
    except Exception:
        prev_gray = gray
        prev_points = detect_features(gray)
        prev_time = time.time()
        return smooth_distance(MAX_DISTANCE_CM), "flow_error"

    if next_points is None or status is None:
        prev_gray = gray
        prev_points = detect_features(gray)
        prev_time = time.time()
        stationary_count += 1
        return smooth_distance(MAX_DISTANCE_CM), "tracking_lost"

    good_old = prev_points[status.flatten() == 1]
    good_new = next_points[status.flatten() == 1]

    if len(good_new) < MIN_FEATURES:
        prev_gray = gray
        prev_points = detect_features(gray)
        prev_time = time.time()
        stationary_count += 1
        return smooth_distance(MAX_DISTANCE_CM), "no_object"

    displacements = np.sqrt(np.sum((good_new - good_old) ** 2, axis=1))
    median_displacement = float(np.median(displacements))

    current_time = time.time()
    dt = max(current_time - prev_time, 0.1)

    if median_displacement < MIN_MOTION_PX:
        stationary_count += 1
        prev_gray = gray
        prev_points = detect_features(gray)
        prev_time = current_time
        status_str = "no_object" if stationary_count >= STATIONARY_COUNT_MAX else "minimal_motion"
        return smooth_distance(MAX_DISTANCE_CM), status_str

    stationary_count = 0
    proximity_score = min((median_displacement / dt) * DISTANCE_SCALE, MAX_DISTANCE_SPAN_CM)
    estimated_distance = MAX_DISTANCE_CM - proximity_score
    estimated_distance = smooth_distance(estimated_distance)

    if estimated_distance <= DANGER_DISTANCE_CM:
        status_str = "danger"
    elif estimated_distance <= WARNING_DISTANCE_CM:
        status_str = "warning"
    else:
        status_str = "tracking"

    prev_gray = gray
    prev_points = good_new.reshape(-1, 1, 2)
    prev_time = current_time

    if len(prev_points) < MIN_FEATURES * 2:
        new_features = detect_features(gray)
        if new_features is not None:
            prev_points = new_features

    return estimated_distance, status_str


@app.route('/upload-frame', methods=['POST'])
def upload_frame():
    try:
        data = request.get_json(silent=True)
    except Exception:
        data = None

    if not data or not isinstance(data, dict) or 'image' not in data:
        return jsonify(SAFE_RESPONSE), 200

    try:
        image_data = data['image']
        if not isinstance(image_data, str) or len(image_data) < 100:
            return jsonify(SAFE_RESPONSE), 200

        # faster decode: base64 -> numpy buffer -> cv2.imdecode (returns BGR)
        try:
            img_bytes = base64.b64decode(image_data)
            nparr = np.frombuffer(img_bytes, np.uint8)
            frame_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if frame_bgr is None:
                return jsonify(SAFE_RESPONSE), 200
        except Exception:
            return jsonify(SAFE_RESPONSE), 200

        distance, status = estimate_distance(frame_bgr)
        distance = max(MIN_DISTANCE_CM, min(float(distance), MAX_DISTANCE_CM))

        return jsonify({'distance': distance, 'status': status, 'unit': 'cm'})

    except (base64.binascii.Error, ValueError):
        return jsonify(SAFE_RESPONSE), 200
    except Exception:
        traceback.print_exc()
        return jsonify(SAFE_RESPONSE), 200


@app.route('/reset', methods=['POST'])
def reset():
    global prev_gray, prev_points, prev_time, stationary_count, frame_number
    prev_gray = None
    prev_points = None
    prev_time = None
    stationary_count = 0
    frame_number = 0
    distance_history.clear()
    return jsonify({'status': 'reset'})


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'frames_processed': frame_number})


if __name__ == '__main__':
    print('Server running on http://0.0.0.0:8000')
    app.run(host='0.0.0.0', port=8000, debug=True)
