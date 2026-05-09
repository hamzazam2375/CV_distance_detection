import { useState, useRef } from 'react';
import { useCameraPermissions } from 'expo-camera';

const CAPTURE_INTERVAL_MS = 700;

export default function useCamera() {
  const [permission, requestPermission] = useCameraPermissions();
  const [capturing, setCapturing] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [frameCount, setFrameCount] = useState(0);
  const cameraRef = useRef(null);
  const timer = useRef(null);
  const callbackRef = useRef(null);
  const busyRef = useRef(false);

  async function askPermission() {
    if (permission?.granted) return true;
    const result = await requestPermission();
    return result.granted;
  }

  function startCapture(onFrameCaptured) {
    if (!cameraRef.current) return;
    if (timer.current) {
      clearTimeout(timer.current);
      timer.current = null;
    }

    callbackRef.current = onFrameCaptured || null;
    busyRef.current = false;
    setCapturing(true);
    setFrameCount(0);

    // The capture loop grabs a picture, calls the provided callback, and
    // schedules the next capture. We use a small interval to balance
    // responsiveness and CPU/bandwidth usage.
    const captureLoop = async () => {
      if (busyRef.current) return;
      busyRef.current = true;

      try {
        // takePictureAsync options:
        // - `quality`: 0-1, higher gives better image for detection but larger payload
        // - `base64`: include base64 so we can send the image over HTTP
        // - `skipProcessing`: when false, platform-specific processing (like rotation) runs
        // - `mute`: disables shutter sound on supported platforms
        const photo = await cameraRef.current.takePictureAsync({
          quality: 0.5,
          base64: true,
          skipProcessing: true,  // Skip platform processing to minimize visual/audio feedback
          mute: true,
        });
        setFrameCount(prev => prev + 1);

        if (callbackRef.current) {
          setProcessing(true);
          try {
            await callbackRef.current(photo);
          } finally {
            setProcessing(false);
          }
        }
      } catch {
        setProcessing(false);
      } finally {
        busyRef.current = false;
      }

      if (timer.current !== null) {
        timer.current = setTimeout(captureLoop, CAPTURE_INTERVAL_MS);
      }
    };

    timer.current = setTimeout(captureLoop, 0);
  }

  function stopCapture() {
    if (timer.current) {
      clearTimeout(timer.current);
      timer.current = null;
    }
    callbackRef.current = null;
    busyRef.current = false;
    setCapturing(false);
    setProcessing(false);
  }

  return {
    cameraRef, permission, capturing, processing,
    frameCount, askPermission, startCapture, stopCapture,
  };
}
