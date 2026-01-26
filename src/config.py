import logging
import sys
import os
# BASE_DIR, PRODUCTS_DIR (Railway/local), settings

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

# Use Railway persistent volume if available, otherwise use local storage
RAILWAY_VOLUME_PATH = os.environ.get('RAILWAY_VOLUME_MOUNT_PATH', '/data')
if os.path.exists(RAILWAY_VOLUME_PATH):
    PRODUCTS_DIR = os.path.join(RAILWAY_VOLUME_PATH, 'products')
    logger.info(f"Using Railway persistent volume: {PRODUCTS_DIR}")
else:
    PRODUCTS_DIR = os.path.join(BASE_DIR, 'data', 'products')
    logger.info(f"Railway volume not found, using local storage: {PRODUCTS_DIR}")

# Create products directory if it doesn't exist
if not os.path.exists(PRODUCTS_DIR):
    os.makedirs(PRODUCTS_DIR)
    logger.info(f"Created products directory at: {PRODUCTS_DIR}")
else:
    logger.info(f"Products directory already exists: {PRODUCTS_DIR}")
