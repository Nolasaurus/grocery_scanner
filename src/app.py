from flask import Flask, render_template, request, jsonify, send_file
import os
import base64
from datetime import datetime
from io import BytesIO
from PIL import Image, ImageOps
import logging
import sys
import json

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

# Use Railway persistent volume if available, otherwise use local storage
RAILWAY_VOLUME_PATH = os.environ.get('RAILWAY_VOLUME_MOUNT_PATH', '/data')
if os.path.exists(RAILWAY_VOLUME_PATH):
    PRODUCTS_DIR = os.path.join(RAILWAY_VOLUME_PATH, 'products')
    logger.info(f"Using Railway persistent volume: {PRODUCTS_DIR}")
else:
    PRODUCTS_DIR = os.path.join(BASE_DIR, 'static', 'products')
    logger.info(f"Railway volume not found, using local storage: {PRODUCTS_DIR}")

# Create products directory if it doesn't exist
if not os.path.exists(PRODUCTS_DIR):
    os.makedirs(PRODUCTS_DIR)
    logger.info(f"Created products directory at: {PRODUCTS_DIR}")
else:
    logger.info(f"Products directory already exists: {PRODUCTS_DIR}")


def resize_image(image, max_dimension=1024):
    """Resize image maintaining aspect ratio"""
    original_size = image.size
    resized_image = ImageOps.contain(image, (max_dimension, max_dimension), method=Image.Resampling.LANCZOS)
    logger.info(f"Resized from {original_size[0]}x{original_size[1]} to {resized_image.size[0]}x{resized_image.size[1]}")
    return resized_image


def save_image(image_base64, product_id, image_type):
    """Save a single image for a product"""
    try:
        # Decode base64
        image_data = image_base64.split(',')[1]
        image_bytes = base64.b64decode(image_data)
        image = Image.open(BytesIO(image_bytes))
        
        # Resize
        resized_image = resize_image(image, max_dimension=1024)
        
        # Save
        product_folder = os.path.join(PRODUCTS_DIR, product_id)
        os.makedirs(product_folder, exist_ok=True)
        
        filename = f'{image_type}.jpg'
        filepath = os.path.join(product_folder, filename)
        
        resized_image.save(filepath, 'JPEG', quality=85, optimize=True)
        logger.info(f"Saved {image_type} to: {filepath}")
        
        return True
    except Exception as e:
        logger.error(f"Error saving {image_type}: {e}")
        return False


@app.route('/')
def index():
    """Home page showing all products"""
    logger.debug("Index route accessed")
    
    products = []
    if os.path.exists(PRODUCTS_DIR):
        for product_id in sorted(os.listdir(PRODUCTS_DIR), reverse=True):
            product_path = os.path.join(PRODUCTS_DIR, product_id)
            if os.path.isdir(product_path):
                # Load product metadata
                metadata_file = os.path.join(product_path, 'metadata.json')
                if os.path.exists(metadata_file):
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                        products.append({
                            'id': product_id,
                            'timestamp': metadata.get('timestamp'),
                            'barcode_url': f'/image/{product_id}/barcode',
                            'nutrition_url': f'/image/{product_id}/nutrition',
                            'label_url': f'/image/{product_id}/label'
                        })
    
    logger.info(f"Found {len(products)} products")
    return render_template('index.html', products=products)


@app.route('/scan')
def scan():
    """Multi-step scanning page"""
    return render_template('scan.html')


@app.route('/image/<product_id>/<image_type>')
def serve_image(product_id, image_type):
    """Serve a specific image from a product"""
    try:
        filepath = os.path.join(PRODUCTS_DIR, product_id, f'{image_type}.jpg')
        if os.path.exists(filepath):
            return send_file(filepath, mimetype='image/jpeg')
        else:
            logger.warning(f"Image not found: {filepath}")
            return jsonify({'error': 'Image not found'}), 404
    except Exception as e:
        logger.error(f"Error serving image: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/submit_product', methods=['POST'])
def submit_product():
    """Submit a complete product with all 3 images"""
    logger.debug("Submit product route accessed")
    try:
        data = request.json
        
        # Generate product ID
        product_id = f"product_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Save all three images
        barcode_saved = save_image(data['barcode'], product_id, 'barcode')
        nutrition_saved = save_image(data['nutrition'], product_id, 'nutrition')
        label_saved = save_image(data['label'], product_id, 'label')
        
        if barcode_saved and nutrition_saved and label_saved:
            # Save metadata
            metadata = {
                'product_id': product_id,
                'timestamp': datetime.now().isoformat(),
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            metadata_file = os.path.join(PRODUCTS_DIR, product_id, 'metadata.json')
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Product submitted successfully: {product_id}")
            return jsonify({'success': True, 'product_id': product_id})
        else:
            logger.error(f"Failed to save all images for product: {product_id}")
            return jsonify({'success': False, 'error': 'Failed to save images'}), 500
            
    except Exception as e:
        logger.error(f"Error submitting product: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
