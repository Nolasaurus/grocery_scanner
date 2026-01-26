import os
import json
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, send_file

from .config import logger, PRODUCTS_DIR
from .services import save_image
bp = Blueprint("main", __name__)


@bp.route('/')
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


@bp.route('/scan')
def scan():
    """Multi-step scanning page"""
    return render_template('scan.html')


@bp.route('/image/<product_id>/<image_type>')
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


@bp.route('/submit_product', methods=['POST'])
def submit_product():
    """Submit a complete product with all 3 images"""
    logger.debug("Submit product route accessed")
    try:
        data = request.json
        
        # Generate product ID
        product_id = f"product_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Save all three images (barcode returns barcode info)
        barcode_result = save_image(data['barcode'], product_id, 'barcode')
        nutrition_saved = save_image(data['nutrition'], product_id, 'nutrition')
        label_saved = save_image(data['label'], product_id, 'label')
        
        # Check if manual barcode was provided
        manual_barcode = data.get('manual_barcode')
        if manual_barcode:
            logger.info(f"Manual barcode provided: {manual_barcode}")
            barcode_info = {
                'data': manual_barcode,
                'type': 'MANUAL',
                'rect': None
            }
        else:
            # Use barcode_result if it's a dict, otherwise None
            barcode_info = barcode_result if isinstance(barcode_result, dict) else None
        
        # Check if all images were saved successfully
        if nutrition_saved and label_saved:
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

