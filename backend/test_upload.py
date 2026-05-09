#!/usr/bin/env python3
"""
Simple test script to verify the /upload-frame endpoint.
Loads a sample image, converts to base64, and sends to Flask backend.

Usage:
  python test_upload.py <image_path>

Example:
  python test_upload.py sample.jpg
"""

import sys
import base64
import json
import requests
from pathlib import Path

# Backend configuration
BACKEND_URL = 'http://localhost:8000'
ENDPOINT = f'{BACKEND_URL}/upload-frame'


def test_upload_frame(image_path):
    """Test the /upload-frame endpoint with a sample image."""
    
    # Verify image exists
    if not Path(image_path).exists():
        print(f'Error: Image file not found: {image_path}')
        return False
    
    print(f'Loading image: {image_path}')
    
    # Read and encode image as base64
    try:
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
        image_b64 = base64.b64encode(image_bytes).decode('ascii')
        print(f'✓ Image encoded to base64 ({len(image_b64)} chars)')
    except Exception as e:
        print(f'Error encoding image: {e}')
        return False
    
    # Prepare request
    payload = {'image': image_b64}
    
    # Send request to backend
    print(f'\nSending POST request to {ENDPOINT}...')
    try:
        response = requests.post(ENDPOINT, json=payload, timeout=10)
        print(f'✓ Response status: {response.status_code}')
    except requests.exceptions.ConnectionError:
        print(f'Error: Cannot connect to backend at {BACKEND_URL}')
        print('Make sure Flask backend is running: python app.py')
        return False
    except requests.exceptions.Timeout:
        print('Error: Request timed out (backend taking too long)')
        return False
    except Exception as e:
        print(f'Error: {e}')
        return False
    
    # Parse and display response
    try:
        data = response.json()
        print('\nBackend Response:')
        print(f'  Object: {data.get(\"object\")}')
        print(f'  Confidence: {data.get(\"confidence\", 0.0):.3f}')
        print(f'  Distance: {data.get(\"distance\", 0.0):.2f} {data.get(\"unit\", \"m\")}')
        print(f'  Warning: {data.get(\"warning\", \"unknown\")}')
        print(f'  Status: {data.get(\"status\", \"unknown\")}')
        
        # Display detections if available
        detections = data.get('detections', [])
        if detections:
            print(f'  Detections ({len(detections)}):')
            for det in detections:
                print(f'    - {det.get(\"label\")}: confidence={det.get(\"confidence\", 0):.3f}')
        
        print(f'\n✓ Test passed! Backend is working correctly.')
        return True
    except json.JSONDecodeError:
        print(f'Error: Invalid JSON response')
        print(f'Response text: {response.text[:200]}')
        return False
    except Exception as e:
        print(f'Error parsing response: {e}')
        return False


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print('Usage: python test_upload.py <image_path>')
        print('')
        print('Example: python test_upload.py sample.jpg')
        print('')
        print('Before running this test:')
        print('  1. Make sure Flask backend is running: python app.py')
        print('  2. Install dependencies: pip install -r requirements.txt')
        print('  3. Ensure YOLOv8 model is available (will auto-download on first run)')
        sys.exit(1)
    
    image_path = sys.argv[1]
    success = test_upload_frame(image_path)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
