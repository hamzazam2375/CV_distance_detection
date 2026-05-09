import React, { useCallback, useEffect, useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { CameraView } from 'expo-camera';
import useCamera from '../hooks/useCamera';
import DistanceDisplay from '../components/DistanceDisplay';
import { sendFrame, resetBackend } from '../services/api';
import { COLORS } from '../constants/theme';

// Warning levels in meters
const CAUTION_DISTANCE_M = 3.0;  // distance > 3m: safe
const STOP_DISTANCE_M = 1.0;     // distance < 1m: stop

export default function CameraScreen({ navigation }) {
  const { cameraRef, permission, processing, askPermission, startCapture, stopCapture } =
    useCamera();

  const [distance, setDistance] = useState(0);
  const [status, setStatus] = useState('initializing');
  const [running, setRunning] = useState(false);

  const handleFrame = useCallback(async (photo) => {
    if (!photo?.base64) return;
    setStatus('processing');

    try {
      // Send frame to backend and receive detection results
      const result = await sendFrame(photo.base64);
      const receivedDistance = typeof result.distance === 'number' ? result.distance : 0;
      setDistance(receivedDistance);

      // Handle error statuses
      if (
        result.error ||
        result.status === 'timeout' ||
        result.status === 'network_error' ||
        result.status === 'no_response' ||
        result.status === 'server_error' ||
        result.status === 'invalid_input' ||
        result.status === 'invalid_response'
      ) {
        setStatus('error');
      } else if (
        result.status === 'no_object' ||
        result.status === 'no_allowed_object' ||
        result.status === 'no_result' ||
        result.status === 'model_unavailable'
      ) {
        setStatus('no_object');
      } else if (result.warning === 'stop') {
        setStatus('stop');
      } else if (result.warning === 'caution') {
        setStatus('caution');
      } else {
        setStatus('tracking');
      }
    } catch (err) {
      console.warn('Error in handleFrame:', err);
      setDistance(0);
      setStatus('error');
    }
  }, []);

  async function handleStart() {
    const granted = await askPermission();
    if (!granted) {
      setStatus('permission_denied');
      return;
    }
    await resetBackend();
    setDistance(0);
    startCapture(handleFrame);
    setStatus('tracking');
    setRunning(true);
  }

  function handleStop() {
    stopCapture();
    setRunning(false);
    setStatus('initializing');
  }

  const statusConfig = {
    initializing: { text: 'Starting...', color: COLORS.textMuted },
    tracking: { text: 'Monitoring', color: COLORS.success },
    caution: { text: 'Obstacle Nearby', color: COLORS.warning },
    stop: { text: 'Stop Immediately', color: COLORS.danger },
    processing: { text: 'Checking distance...', color: COLORS.primary },
    no_object: { text: 'Path Clear', color: COLORS.success },
    error: { text: 'Connection Error', color: COLORS.danger },
    permission_denied: { text: 'Camera Access Denied', color: COLORS.danger },
  };

  const currentStatus = statusConfig[status] || statusConfig.tracking;

  function getWarningMessage(currentDistance, currentStatusKey) {
    if (currentStatusKey === 'error') {
      return 'Unable to read the camera data right now.';
    }

    if (currentStatusKey === 'permission_denied') {
      return 'Camera access is required to estimate obstacle distance.';
    }

    if (currentStatusKey === 'stop' || currentDistance < STOP_DISTANCE_M) {
      return 'Obstacle is very close (< 1m). Stop the vehicle immediately!';
    }

    if (currentStatusKey === 'caution' || (currentDistance >= STOP_DISTANCE_M && currentDistance < CAUTION_DISTANCE_M)) {
      return 'Obstacle detected nearby (1-3m). Move slowly and keep watching the screen.';
    }

    return 'No nearby obstacle detected. Path is clear. Continue checking the camera.';
  }

  if (!permission) {
    return (
      <SafeAreaView style={styles.container}>
        <ActivityIndicator size="large" color={COLORS.primary} />
      </SafeAreaView>
    );
  }

  if (!permission.granted) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.permissionCard}>
          <Text style={styles.permissionTitle}>Camera access denied</Text>
          <Text style={styles.permissionText}>
            DriveSafe AI needs the camera to estimate obstacle distance.
          </Text>
          <TouchableOpacity style={styles.btn} onPress={askPermission}>
            <Text style={styles.btnText}>Grant Permission</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>DriveSafe AI</Text>
        <Text style={styles.subtitle}>Rear parking sensor style distance detection</Text>
      </View>

      <View style={styles.cameraWrapper}>
        <CameraView ref={cameraRef} style={styles.camera} facing="back" mute={true} />

        <View style={styles.distanceOverlay}>
          <DistanceDisplay distance={distance} />
          <Text style={styles.distanceLabel}>Distance to obstacle</Text>
        </View>
      </View>

      <View style={styles.statusBar}>
        <View style={styles.statusRow}>
          {status === 'processing' && (
            <ActivityIndicator size="small" color={COLORS.primary} style={{ marginRight: 8 }} />
          )}
          <View style={[styles.statusDot, { backgroundColor: currentStatus.color }]} />
          <Text style={[styles.statusText, { color: currentStatus.color }]}>{currentStatus.text}</Text>
        </View>
      </View>

      <View style={styles.warningCard}>
        <Text style={styles.warningTitle}>Warning Message</Text>
        <Text style={styles.warningText}>{getWarningMessage(distance, status)}</Text>
      </View>

      {!running ? (
        <TouchableOpacity style={styles.btnStart} activeOpacity={0.8} onPress={handleStart}>
          <Text style={styles.btnStartText}>Start Camera</Text>
        </TouchableOpacity>
      ) : (
        <TouchableOpacity style={styles.stopBtn} activeOpacity={0.8} onPress={handleStop}>
          <Text style={styles.stopBtnText}>Stop Camera</Text>
        </TouchableOpacity>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
    paddingHorizontal: 16,
    paddingBottom: 16,
  },
  header: {
    paddingTop: 12,
    paddingBottom: 16,
    alignItems: 'center',
  },
  title: {
    fontSize: 28,
    fontWeight: '800',
    color: COLORS.textPrimary,
    letterSpacing: 0.5,
  },
  subtitle: {
    marginTop: 6,
    fontSize: 13,
    color: COLORS.textSecondary,
    textAlign: 'center',
  },
  cameraWrapper: {
    width: '100%',
    flex: 1,
    position: 'relative',
    borderRadius: 24,
    overflow: 'hidden',
    backgroundColor: '#090910',
  },
  camera: {
    width: '100%',
    flex: 1,
  },
  distanceOverlay: {
    position: 'absolute',
    bottom: 20,
    alignSelf: 'center',
    alignItems: 'center',
  },
  statusBar: {
    width: '100%',
    paddingVertical: 8,
    backgroundColor: COLORS.surface,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
  },
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 8,
  },
  statusText: {
    fontSize: 14,
    fontWeight: '500',
  },
  distanceLabel: {
    marginTop: 8,
    fontSize: 12,
    color: COLORS.textSecondary,
    fontWeight: '600',
    letterSpacing: 0.5,
  },
  warningCard: {
    width: '100%',
    marginTop: 12,
    backgroundColor: COLORS.surface,
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  warningTitle: {
    fontSize: 14,
    color: COLORS.textPrimary,
    fontWeight: '700',
    marginBottom: 8,
  },
  warningText: {
    fontSize: 14,
    color: COLORS.textSecondary,
    lineHeight: 20,
  },
  permissionCard: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 24,
  },
  permissionTitle: {
    fontSize: 20,
    color: COLORS.textPrimary,
    fontWeight: '700',
    marginBottom: 10,
  },
  permissionText: {
    color: COLORS.textSecondary,
    fontSize: 15,
    lineHeight: 22,
    textAlign: 'center',
    marginBottom: 20,
  },
  btn: {
    backgroundColor: COLORS.primary,
    paddingHorizontal: 40,
    paddingVertical: 14,
    borderRadius: 30,
  },
  btnText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
  stopBtn: {
    backgroundColor: COLORS.danger,
    paddingHorizontal: 40,
    paddingVertical: 14,
    borderRadius: 30,
    marginVertical: 16,
    alignSelf: 'center',
  },
  stopBtnText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  btnStart: {
    backgroundColor: COLORS.primary,
    paddingHorizontal: 40,
    paddingVertical: 14,
    borderRadius: 30,
    marginVertical: 16,
    alignSelf: 'center',
  },
  btnStartText: {
    color: '#000',
    fontSize: 16,
    fontWeight: '700',
  },
});
