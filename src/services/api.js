import axios from 'axios';

// Backend API configuration
const BASE_URL = 'http://192.168.100.155:8000';
const TIMEOUT_MS = 8000;

// Create axios instance with timeout and error handling
const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: TIMEOUT_MS,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Send camera frame to backend for obstacle detection.
 *
 * Returns: { object, confidence, distance, warning, unit, status, ... }
 * - object: detected object name (car, person, bike, truck) or null
 * - confidence: detection confidence (0-1)
 * - distance: distance in meters
 * - warning: 'safe' | 'caution' | 'stop'
 * - unit: 'm' (meters)
 * - status: 'ok' | error status
 */
async function sendFrame(base64Image) {
  // Validate input
  if (!base64Image || typeof base64Image !== 'string' || base64Image.length < 100) {
    return {
      object: null,
      confidence: 0.0,
      distance: 100.0,
      warning: 'safe',
      unit: 'm',
      status: 'invalid_input',
    };
  }

  try {
    // Send frame to backend
    const response = await apiClient.post('/upload-frame', {
      image: base64Image,
    });

    // Validate response data
    const data = response.data;
    if (
      data &&
      typeof data.distance === 'number' &&
      isFinite(data.distance) &&
      data.warning &&
      data.status
    ) {
      return data;
    }

    // Fallback if response format is unexpected
    return {
      object: data?.object || null,
      confidence: 0.0,
      distance: 100.0,
      warning: 'safe',
      unit: 'm',
      status: 'invalid_response',
    };
  } catch (error) {
    // Handle different error types
    let errorStatus = 'network_error';
    let errorMessage = error.message;

    if (error.code === 'ECONNABORTED' || error.message === 'timeout of ' + TIMEOUT_MS + 'ms exceeded') {
      errorStatus = 'timeout';
      errorMessage = 'Request timed out';
    } else if (error.response) {
      // Backend responded with error
      errorStatus = 'server_error';
      errorMessage = `Server error: ${error.response.status}`;
    } else if (error.request) {
      // Request made but no response
      errorStatus = 'no_response';
      errorMessage = 'No response from server';
    }

    console.warn(`[API Error] ${errorStatus}: ${errorMessage}`);

    // Return safe default
    return {
      object: null,
      confidence: 0.0,
      distance: 100.0,
      warning: 'safe',
      unit: 'm',
      status: errorStatus,
      error: errorMessage,
    };
  }
}

/**
 * Reset backend state (clears any persistent detection state).
 */
async function resetBackend() {
  try {
    await apiClient.post('/reset');
  } catch (error) {
    // Silently ignore reset failures
    console.warn('[API] Reset backend failed:', error.message);
  }
}

export { sendFrame, resetBackend, BASE_URL };
