const BASE_URL = 'http://192.168.100.155:8000';
const TIMEOUT_MS = 8000;

async function sendFrame(base64Image) {
  if (!base64Image || typeof base64Image !== 'string' || base64Image.length < 100) {
    return { distance: 0, status: 'invalid_input' };
  }

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), TIMEOUT_MS);

    const res = await fetch(`${BASE_URL}/upload-frame`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image: base64Image }),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    let data;
    try {
      data = await res.json();
    } catch {
      return { distance: 0, status: 'invalid_response' };
    }

    if (data && typeof data.distance === 'number' && isFinite(data.distance)) {
      return data;
    }
    return { distance: 0, status: data?.status || 'no_distance' };
  } catch (e) {
    const isTimeout = e.name === 'AbortError';
    return {
      distance: 0,
      status: isTimeout ? 'timeout' : 'network_error',
      error: isTimeout ? 'Request timed out' : e.message,
    };
  }
}

async function resetBackend() {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);
    await fetch(`${BASE_URL}/reset`, { method: 'POST', signal: controller.signal });
    clearTimeout(timeoutId);
  } catch {
    // ignore reset failures
  }
}

export { sendFrame, resetBackend, BASE_URL };
