from flask import Flask
import os

from routes import bp
from config import logger

app = Flask(__name__)
app.register_blueprint(bp)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
