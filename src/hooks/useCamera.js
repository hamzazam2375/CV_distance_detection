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

    const captureLoop = async () => {
      if (busyRef.current) return;
      busyRef.current = true;

      try {
        const photo = await cameraRef.current.takePictureAsync({
          quality: 0.2,
          base64: true,
          skipProcessing: true,
          mute: true,  // Disable shutter sound
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
