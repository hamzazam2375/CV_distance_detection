import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { COLORS } from '../constants/theme';

export default function DistanceDisplay({ distance = 0 }) {
  // When backend reports the sentinel max distance (100.0), treat as "no detection" and display '-'
  const MAX_SENTINEL = 100.0;
  const isNoDetection = Number.isFinite(distance) && distance >= MAX_SENTINEL;
  const displayDistance = isNoDetection ? '-' : (Number.isFinite(distance) ? Math.max(0, distance).toFixed(2) : '0.00');

  return (
    <View style={styles.container}>
      <Text style={styles.value}>{displayDistance}</Text>
      {isNoDetection ? null : <Text style={styles.unit}>m</Text>}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.65)',
    borderRadius: 16,
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderWidth: 1,
    borderColor: 'rgba(0, 229, 255, 0.3)',
  },
  value: {
    fontSize: 44,
    fontWeight: 'bold',
    color: COLORS.textPrimary,
    letterSpacing: -1,
  },
  unit: {
    fontSize: 14,
    color: COLORS.primary,
    fontWeight: '600',
    marginTop: -2,
  },
});