from flask import Flask, render_template, request, redirect, Response, jsonify, url_for, send_from_directory
import os
from time import sleep
import cv2
import numpy as np
from datetime import datetime

app = Flask(__name__)

class VideoCamera(object):
    def __init__(self):
        self.video = cv2.VideoCapture(0)

    def __del__(self):
        self.video.release()        

    def get_frame(self):
        success, frame = self.video.read()
        if not success:
            return None, None
        frame = cv2.flip(frame, 1)
        """
         add'l frame processing 

         insert here
        """

        ret, jpeg = cv2.imencode('.jpg', frame)
        return frame, jpeg.tobytes() if ret else None


video_stream = VideoCamera()
last_capture = None

@app.route('/')
def index():
    return render_template('index.html', last_capture=last_capture)

def gen(camera):
    while True:
        _, jpeg = camera.get_frame()
        if jpeg is not None:
            yield b'--frame\r\n'
            yield b'Content-Type: image/jpeg\r\n\r\n'
            yield jpeg
            yield b'\r\n\r\n'

@app.route('/video_feed')
def video_feed():
    return Response(gen(video_stream),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/capture')
def capture():
    global video_stream, last_capture
    if video_stream is None:
        return "Camera not initialized", 500
        
    # Capture frame
    frame, _ = video_stream.get_frame()
    if frame is None:
        return "Failed to capture frame", 500
        
    # Create captures directory if it doesn't exist
    if not os.path.exists('static/captures'):
        os.makedirs('static/captures')
        
    # Save the image
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'capture_{timestamp}.jpg'
    filepath = os.path.join('static/captures', filename)
    cv2.imwrite(filepath, frame)
    
    # Update last capture path
    last_capture = f'captures/{filename}'
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
