from flask import Flask, render_template, request, jsonify
import os
import base64
from datetime import datetime
from io import BytesIO
from PIL import Image, ImageOps
import requests
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Get the directory where app.py is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
logger.info(f"Base directory: {BASE_DIR}")

app = Flask(__name__)

# Use absolute path for captures directory
CAPTURES_DIR = os.path.join(BASE_DIR, 'static', 'captures')
logger.info(f"Captures directory: {CAPTURES_DIR}")

# Create captures directory if it doesn't exist
if not os.path.exists(CAPTURES_DIR):
    os.makedirs(CAPTURES_DIR)
    logger.info(f"Created captures directory at: {CAPTURES_DIR}")
else:
    logger.info(f"Captures directory already exists: {CAPTURES_DIR}")

@app.route('/')
def index():
    logger.debug("Index route accessed")
    # Get list of captured images
    captures = []
    if os.path.exists(CAPTURES_DIR):
        captures = sorted([f for f in os.listdir(CAPTURES_DIR) if f.endswith('.jpg')], reverse=True)
        logger.info(f"Found {len(captures)} captures in {CAPTURES_DIR}")
    
    return render_template('index.html', captures=captures)

@app.route('/capture', methods=['POST'])
def capture():
    logger.debug("Capture route accessed")
    try:
        # Get the image data from the request
        data = request.json
        logger.debug(f"Received data keys: {data.keys() if data else 'None'}")
        
        image_data = data['image'].split(',')[1]  # Remove the data:image/jpeg;base64, part
        logger.debug(f"Base64 data length: {len(image_data)}")
        
        # Decode base64 image
        image_bytes = base64.b64decode(image_data)
        logger.debug(f"Decoded image bytes: {len(image_bytes)}")
        
        image = Image.open(BytesIO(image_bytes))
        logger.info(f"Image opened: size={image.size}, format={image.format}, mode={image.mode}")
        
        # Save the image
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'capture_{timestamp}.jpg'
        filepath = os.path.join(CAPTURES_DIR, filename)
        
        logger.info(f"Saving image to: {filepath}")
        image.save(filepath)

        # Verify the file was created
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            logger.info(f"File saved successfully: {filepath} ({file_size} bytes)")
            return jsonify({'success': True, 'filename': filename})
        else:
            logger.error(f"File was not created: {filepath}")
            return jsonify({'success': False, 'error': 'File was not created'}), 500
            
    except Exception as e:
        logger.error(f"Error capturing: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
