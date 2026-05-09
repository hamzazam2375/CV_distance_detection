# DriveSafe AI

DriveSafe AI is a simple React Native mobile app that uses the phone camera and a Python Flask backend with YOLOv8 to detect obstacles and estimate distance in real time.

## What it does

- Captures camera frames at regular intervals
- Sends frames to Flask backend via Axios API
- Uses YOLOv8 nano to detect vehicles, persons, bikes, and trucks
- Estimates distance using pinhole camera model: `Distance = (Real Width × Focal Length) / Pixel Width`
- Displays live distance in meters and warning status:
  - **SAFE**: distance > 3m (green)
  - **CAUTION**: distance 1-3m (yellow/orange)
  - **STOP**: distance < 1m (red)
- Shows annotated camera frame with bounding boxes

## How to run

### 1. Start the backend

```bash
cd backend
pip install -r requirements.txt
python app.py
```

The backend runs on `http://0.0.0.0:8000`.

### 2. Configure frontend API address

Update `src/services/api.js` with your backend IP:

```javascript
const BASE_URL = "http://<YOUR_MACHINE_IP>:8000";
```

### 3. Install dependencies and start the app

```bash
npm install
npm start
```

Use Expo Go, Android, or iOS to open the app.

### 4. Test the backend connection (optional)

```bash
cd backend
python test_upload.py sample.jpg
```

## Main features

### Frontend (React Native + Expo)

- Real-time camera capture using `expo-camera`
- Frame sending every 700ms via Axios
- Live distance display in meters
- Warning status visualization (colors + text messages)
- Start/Stop camera controls
- Silent frame capture (no shutter sound/effect)

### Backend (Flask + YOLOv8)

- YOLOv8 nano model for fast inference
- Detects: car (1.8m), person (0.5m), bike (0.7m), truck (2.5m)
- Distance estimation using bounding box width
- Returns: object name, confidence score, distance, warning level, annotated image
- Endpoints: `/upload-frame` (detection), `/reset` (clear state), `/health` (status check)

## API Response Format

```json
{
  "object": "car",
  "confidence": 0.95,
  "distance": 2.34,
  "warning": "caution",
  "unit": "m",
  "status": "ok",
  "detections": [
    { "label": "car", "confidence": 0.95, "box": [100, 50, 400, 300] }
  ],
  "annotated": "<base64_jpeg>"
}
```

## Key Technologies

### Frontend

- **React Native** + Expo: Cross-platform mobile development
- **Axios**: Simple async/await API requests with timeout handling
- **expo-camera**: Native camera access with frame capture

### Backend

- **Flask**: Lightweight Python web framework
- **YOLOv8 nano**: Fast object detection (ultralytics)
- **OpenCV**: Image processing and annotation
- **NumPy**: Numerical calculations

## How Distance Estimation Works

The app uses the pinhole camera model:

```
Distance (meters) = (Real Object Width × Focal Length) / Bounding Box Width (pixels)
```

**Calibration values** (in `backend/app.py`):

- Car width: 1.8m
- Person width: 0.5m
- Bike width: 0.7m
- Truck width: 2.5m
- Focal length: 800 (tune for your device camera)

**To calibrate**: Measure a real car 5m away, adjust FOCAL_LENGTH until the app shows ~5m.

## Project structure

- `App.js` - app navigation
- `src/screens/` - app screens
- `src/hooks/` - camera capture logic
- `src/services/` - backend request logic
- `backend/` - Flask CV server
