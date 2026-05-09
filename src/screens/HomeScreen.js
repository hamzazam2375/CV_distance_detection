import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { COLORS } from '../constants/theme';

export default function HomeScreen({ navigation }) {
  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>DriveSafe AI</Text>
        <Text style={styles.subtitle}>Real-time obstacle distance detection</Text>
      </View>

      <View style={styles.resultsCard}>
        <Text style={styles.resultsTitle}>Camera Monitoring</Text>
        <Text style={styles.resultsText}>
          Open the camera to see the live distance estimate, status, and warning message.
        </Text>
        <Text style={styles.thresholdText}>
          {/* Beginner-friendly threshold info */}
          🟢 SAFE: Distance > 3m{"\n"}
          🟡 CAUTION: 2m - 3m{"\n"}
          🔴 STOP: Distance {'<'} 2m
        </Text>
      </View>

      <View style={styles.bottom}>
        <TouchableOpacity
          style={styles.startBtn}
          activeOpacity={0.8}
          onPress={() => navigation.navigate('Camera')}
        >
          <View style={styles.startBtnInner}>
            <Text style={styles.startIcon}>▶</Text>
          </View>
        </TouchableOpacity>
        <Text style={styles.startLabel}>Open Camera</Text>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 40,
  },
  header: {
    alignItems: 'center',
    marginTop: 40,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: COLORS.textPrimary,
    letterSpacing: 1,
  },
  subtitle: {
    fontSize: 14,
    color: COLORS.textMuted,
    marginTop: 8,
  },
  resultsCard: {
    width: '85%',
    backgroundColor: COLORS.surface,
    borderRadius: 16,
    padding: 20,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  resultsTitle: {
    fontSize: 16,
    color: COLORS.textPrimary,
    textAlign: 'center',
    marginBottom: 12,
    fontWeight: '700',
  },
  resultsText: {
    fontSize: 15,
    color: COLORS.textSecondary,
    textAlign: 'center',
    lineHeight: 22,
  },
  thresholdText: {
    fontSize: 13,
    color: COLORS.textSecondary,
    textAlign: 'center',
    lineHeight: 20,
    marginTop: 12,
    fontWeight: '500',
  },
  bottom: {
    alignItems: 'center',
    marginBottom: 20,
  },
  startBtn: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: COLORS.primaryDim,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: COLORS.primary,
  },
  startBtnInner: {
    width: 70,
    height: 70,
    borderRadius: 35,
    backgroundColor: COLORS.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  startIcon: {
    fontSize: 28,
    color: COLORS.background,
    marginLeft: 4,
  },
  startLabel: {
    marginTop: 16,
    fontSize: 16,
    color: COLORS.textSecondary,
    fontWeight: '500',
  },
});
