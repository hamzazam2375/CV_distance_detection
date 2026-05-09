import React from 'react';
import { View, ActivityIndicator, Text, StyleSheet } from 'react-native';
import { COLORS } from '../constants/theme';

// Simple reusable loading overlay component
export default function LoadingOverlay({ visible = false, text = 'Loading...' }) {
  if (!visible) return null;
  return (
    <View style={styles.overlay} pointerEvents="none">
      <View style={styles.box}>
        <ActivityIndicator size="large" color={COLORS.primary} />
        <Text style={styles.text}>{text}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  overlay: {
    ...StyleSheet.absoluteFillObject,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(0,0,0,0.35)',
  },
  box: {
    padding: 18,
    borderRadius: 12,
    backgroundColor: 'rgba(0,0,0,0.7)',
    alignItems: 'center',
  },
  text: {
    marginTop: 10,
    color: COLORS.textPrimary,
    fontWeight: '600',
  },
});