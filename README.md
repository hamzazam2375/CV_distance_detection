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
npx expo start
```

Use Expo Go, Android, or iOS to open the app.

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
- Detects: car (1.76m), person (0.5m), bike (0.7m), truck (2.5m)
- Distance estimation using bounding box width
- Returns: object name, confidence score, distance, warning level, annotated image
- Endpoints: `/upload-frame` (detection), `/reset` (clear state), `/health` (status check)

## API Response Format

```json
{
  "object": "car",
  "confidence": 0.95,
  "distance": 2.34,
  "bbox_width_px": 312.5,
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
- Car width: 1.76m
- Person width: 0.5m
- Bike width: 0.7m
- Truck width: 2.5m
- Focal length: 2133 (fixed baseline from observed underestimation)

**Calibration mode**: The project currently uses a fixed no-input focal-length calibration baseline.

## Safety thresholds

- 🟢 **Safe:** distance > 3.0 m
- 🟡 **Caution:** 2.0 m – 3.0 m
- 🔴 **Danger / Stop:** distance < 2.0 m

## Project structure

- `App.js` - app navigation
- `src/screens/` - app screens
- `src/hooks/` - camera capture logic
- `src/services/` - backend request logic
- `backend/` - Flask CV server
