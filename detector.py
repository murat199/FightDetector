import os
import sys
import cv2
import json
from flask import Flask, request, render_template, send_from_directory
from flask_socketio import SocketIO
import base64
import datetime
import numpy as np
import time
import src.ViolenceDetector as ViolenceDetector
import src.data.ImageUtils as ImageUtils
import operator
import random
import glob
import os.path
from processor import process_image
from keras.models import load_model
from PIL import Image
from io import BytesIO

app = Flask(__name__,static_url_path='/static')
app.config['SECRET_KEY'] = 'vnkdjnfjknfl1232#'
socketio = SocketIO(app)

violenceDetector = ViolenceDetector.ViolenceDetector()

@app.route("/")
def DetectorHome():
    return render_template("index.html")

@app.route("/DetectorWebcam")
def DetectorWebcam():
    return render_template("webcam.html")

@app.route("/DetectorStream")
def DetectorStream():
    return render_template("stream.html")

@socketio.on('SocketDetectorWebcam')
def SocketDetectorWebcam(frames, methods=['GET', 'POST']):
    dataJson = json.loads(str(frames).replace('\'','\"'))
    isStarted=0
    for item in dataJson['data']:
        netInput = ImageUtils.ConvertImageFrom_CV_to_NetInput(readb64(item["img"]))
        isFighting = violenceDetector.Detect(netInput)
        #Siddet tespit edildi
        if isFighting:
            isStarted=1
            response={'isComplete':'false','isStarted':''+str(isStarted),'isDone':'false','message':''+str(item['time'])}
            socketio.emit('SocketDetectorComplete', response, callback=MessageReceived)
        else:
            response={'isComplete':'false','isStarted':''+str(isStarted),'isDone':'true','message':''+str(item['time'])}
            socketio.emit('SocketDetectorComplete', response, callback=MessageReceived)
            isStarted=0
    response={'isComplete':'true','message':'tespit bitti'}
    socketio.emit('SocketDetectorComplete', response, callback=MessageReceived)

def readb64(base64_string):
   cleanData = str(base64_string)[len("data:image/jpeg;base64,"):]
   imgdata = base64.b64decode(cleanData)
   image = Image.open(BytesIO(imgdata))
   return np.array(image)

def MessageReceived(methods=['GET', 'POST']):
   print('Message was received!!!')

if __name__ == "__main__":
    socketio.run(app, debug=True)