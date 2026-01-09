from flask import Flask, render_template, request, jsonify, send_file
import os
import base64
from datetime import datetime
from io import BytesIO
from PIL import Image, ImageOps
import logging
import sys
import json

try:
    from pyzbar.pyzbar import decode as decode_barcode
    BARCODE_AVAILABLE = True
except ImportError:
    BARCODE_AVAILABLE = False
    logging.warning("pyzbar not available - barcode scanning disabled")

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


def read_barcode(image):
    """Read barcode from image"""
    if not BARCODE_AVAILABLE:
        logger.warning("Barcode reading not available (pyzbar not installed)")
        return None
    
    try:
        # Decode barcodes from image
        barcodes = decode_barcode(image)
        
        if barcodes:
            # Return the first barcode found
            barcode = barcodes[0]
            barcode_data = barcode.data.decode('utf-8')
            barcode_type = barcode.type
            
            logger.info(f"Barcode detected: {barcode_data} (type: {barcode_type})")
            return {
                'data': barcode_data,
                'type': barcode_type,
                'rect': {
                    'left': barcode.rect.left,
                    'top': barcode.rect.top,
                    'width': barcode.rect.width,
                    'height': barcode.rect.height
                }
            }
        else:
            logger.warning("No barcode detected in image")
            return None
            
    except Exception as e:
        logger.error(f"Error reading barcode: {e}")
        return None


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
        
        # If this is a barcode image, try to read it
        barcode_info = None
        if image_type == 'barcode':
            barcode_info = read_barcode(image)
        
        # Resize
        resized_image = resize_image(image, max_dimension=1024)
        
        # Save
        product_folder = os.path.join(PRODUCTS_DIR, product_id)
        os.makedirs(product_folder, exist_ok=True)
        
        filename = f'{image_type}.jpg'
        filepath = os.path.join(product_folder, filename)
        
        resized_image.save(filepath, 'JPEG', quality=85, optimize=True)
        logger.info(f"Saved {image_type} to: {filepath}")
        
        return barcode_info
    except Exception as e:
        logger.error(f"Error saving {image_type}: {e}")
        return None


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
                            'timestamp': metadata.get('created_at'),
                            'barcode': metadata.get('barcode_data'),
                            'barcode_type': metadata.get('barcode_type'),
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
        
        # Save all three images (barcode returns barcode info)
        barcode_info = save_image(data['barcode'], product_id, 'barcode')
        nutrition_saved = save_image(data['nutrition'], product_id, 'nutrition')
        label_saved = save_image(data['label'], product_id, 'label')
        
        if nutrition_saved is not None and label_saved is not None:
            # Save metadata
            metadata = {
                'product_id': product_id,
                'timestamp': datetime.now().isoformat(),
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'barcode_data': barcode_info['data'] if barcode_info else None,
                'barcode_type': barcode_info['type'] if barcode_info else None
            }
            
            metadata_file = os.path.join(PRODUCTS_DIR, product_id, 'metadata.json')
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Product submitted successfully: {product_id}")
            
            return jsonify({
                'success': True, 
                'product_id': product_id,
                'barcode': barcode_info['data'] if barcode_info else None,
                'barcode_type': barcode_info['type'] if barcode_info else None
            })
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
