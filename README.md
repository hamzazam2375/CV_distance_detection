# DriveSafe AI

DriveSafe AI is a simple mobile app that uses the phone camera and a Python backend to estimate obstacle distance in real time.

## What it does

- Opens the camera in the app
- Captures frames at a fixed interval
- Sends each frame to the backend
- Tracks motion between frames and estimates obstacle distance in cm
- Shows the live distance and a short status message

## How to run

### 1. Start the backend

```bash
cd backend
pip install -r requirements.txt
python app.py
```

The backend runs on port `8000`.

### 2. Start the app

```bash
npm install
npm start
```

Use Expo Go, Android, or iOS to open the app.

### 3. Check the backend address

If your device cannot reach the backend, update the IP address in `src/services/api.js`.

## Main CV concepts used

- Frame capture: the app takes camera snapshots instead of streaming full video. See `src/hooks/useCamera.js` and `src/screens/CameraScreen.js`.
- Image encoding and decoding: frames are sent as base64 and decoded on the backend. See `src/services/api.js` and `backend/app.py`.
- Resizing: frames are resized before analysis to keep processing lighter. See `backend/app.py`.
- Grayscale conversion: frames are converted to grayscale before motion tracking. See `backend/app.py`.
- Noise reduction: Gaussian blur is used to reduce noise. See `backend/app.py`.
- Feature detection: Shi-Tomasi corners are detected with `goodFeaturesToTrack`. See `backend/app.py`.
- Optical flow tracking: Lucas-Kanade optical flow tracks feature movement between frames. See `backend/app.py`.
- Motion estimation: point displacement is measured and turned into distance. See `backend/app.py`.
- Smoothing and filtering: weighted averaging and spike handling keep the distance stable. See `backend/app.py`.

## Project structure

- `App.js` - app navigation
- `src/screens/` - app screens
- `src/hooks/` - camera capture logic
- `src/services/` - backend request logic
- `backend/` - Flask CV server
