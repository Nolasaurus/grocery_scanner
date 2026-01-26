import os
from io import BytesIO
import base64
from pyzbar.pyzbar import decode as decode_barcode
from PIL import Image, ImageOps

from .config import logger, PRODUCTS_DIR

def read_barcode(image):
    """Read barcode from image"""
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
        
        return barcode_info if image_type == 'barcode' else True
    except Exception as e:
        logger.error(f"Error saving {image_type}: {e}")
        return False

