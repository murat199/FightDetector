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
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
app.config['SECRET_KEY'] = 'vnkdjnfjknfl1232#'
socketio = SocketIO(app)

violenceDetector = ViolenceDetector.ViolenceDetector()

@app.route("/")
def DetectorHome():
    return render_template("index.html")

@app.route("/DetectorWebcam")
def DetectorWebcam():
    return render_template("webcam.html")

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

@app.route("/DetectorStreamGet", methods=["GET"])
def DetectorStreamGet():
    return render_template("stream.html")

@app.route("/DetectorStream", methods=["POST"])
def DetectorStream():
    isStarted=0
    target = os.path.join(APP_ROOT, 'static/video/')
    if not os.path.isdir(target):
        os.mkdir(target)
    for upload in request.files.getlist("file"):
        print("{} is the file name".format(upload.filename))
        filename = upload.filename
        # This is to verify files are supported
        ext = os.path.splitext(filename)[1]
        if (ext == ".mp4") or (ext == ".mov"):
            print("File supported moving on...")
        destination = "/".join([target, filename])
        print("Accept incoming file:", filename)
        print("Save it to:", destination)
        upload.save(destination)

        vidcap = cv2.VideoCapture(destination)
        sec = 0
        #fps = vidcap.get(cv2.CAP_PROP_FPS)
        fps = 10
        #it will capture image in each 0.1 second
        frameRate = 0.1
        success,image = getFrame(sec,vidcap)
        countFrame = 0
        timeSecond=0
        timeMinute=0
        response={'path':filename}
        socketio.emit('SocketVideoSource', response, callback=MessageReceived)
        while success:
            sec = sec + frameRate
            sec = round(sec, 2)
            countFrame += 1
            if(countFrame >= round(fps)):
                countFrame = 0
                timeSecond=int(sec)
                if(timeSecond>=60):
                    timeMinute+=1
                    timeSecond = 0  
            netInput = ImageUtils.ConvertImageFrom_CV_to_NetInput(image)
            isFighting = violenceDetector.Detect(netInput)
            #siddet tespit edildi
            if isFighting:
                isStarted=1
                timeNow='00:'+str(timeMinute).zfill(2)+':'+str(timeSecond).zfill(2)
                response={'isComplete':'false','isStarted':''+str(isStarted),'isDone':'false','time':timeNow,'message':timeNow}
                socketio.emit('SocketDetectorComplete', response, callback=MessageReceived)
            else:
                timeNow='00:'+str(timeMinute).zfill(2)+':'+str(timeSecond).zfill(2)
                response={'isComplete':'false','isStarted':''+str(isStarted),'isDone':'false','time':timeNow,'message':timeNow}
                socketio.emit('SocketDetectorComplete', response, callback=MessageReceived)
                isStarted=0
            success,image = getFrame(sec,vidcap)
    return json.dumps({'status':'OK','message':'merhaba'})

def readb64(base64_string):
   cleanData = str(base64_string)[len("data:image/jpeg;base64,"):]
   imgdata = base64.b64decode(cleanData)
   image = Image.open(BytesIO(imgdata))
   return np.array(image)

def getFrame(sec,vidcap):
    vidcap.set(cv2.CAP_PROP_POS_MSEC,sec*1000)
    hasFrames,image = vidcap.read()
    return hasFrames,image

def MessageReceived(methods=['GET', 'POST']):
   print('Message was received!!!')

if __name__ == "__main__":
    socketio.run(app, debug=True)