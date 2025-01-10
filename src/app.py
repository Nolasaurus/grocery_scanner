from flask import Flask, render_template, request, redirect, Response, jsonify, url_for, send_from_directory
import os
import cv2
import numpy as np

app = Flask(__name__)

class VideoCamera(object):
    def __init__(self):
        self.video = cv2.VideoCapture(0)


    def __del__(self):
        self.video.release()        

    def get_frame(self):
        ret, frame = self.video.read()
        frame = cv2.flip(frame, 1)
        """
         add'l frame processing 

         insert here
        """

        ret, jpeg = cv2.imencode('.jpg', frame)

        return jpeg.tobytes()


video_stream = VideoCamera()

@app.route('/')
def index():
    return render_template('index.html')

def gen(camera):
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen(video_stream),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/capture')
def capture():
    frame = video_stream.get_frame()
    if frame is not None:
        # Create a directory for saved images if it doesn't exist
        if not os.path.exists('captures'):
            os.makedirs('captures')
            
        # Save the frame
        img_path = os.path.join('captures', f'capture_{len(os.listdir("captures"))}.jpg')
        with open(img_path, 'wb') as f:
            f.write(frame)
            
#         return redirect(url_for('index'))
#     return "Failed to capture image", 400

if __name__ == '__main__':
    app.run(debug=True)
