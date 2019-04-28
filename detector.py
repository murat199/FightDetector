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
    listStart=list()
    listEnd=list()
    for item in dataJson['data']:
        netInput = ImageUtils.ConvertImageFrom_CV_to_NetInput(readb64(item["img"]))
        isFighting = violenceDetector.Detect(netInput)
        timeNow=str(item['time'])
        #Siddet tespit edildi
        if isFighting:
            if len(listStart)==len(listEnd):
                timeStart=str(item['time'])
                listStart.append(timeStart)
                response={'isDone':'false','listStart':listStart,'listEnd':listEnd,'time':timeNow}
                socketio.emit('SocketDetectorComplete', response, callback=MessageReceived)
            else:
                response={'time':timeNow,'isFight':'true'}
                socketio.emit('SocketDetectorComplete', response, callback=MessageReceived)
        else:
            if len(listStart)!=len(listEnd):
                timeEnd=str(item['time'])
                listEnd.append(timeEnd)
                response={'isDone':'false','listStart':listStart,'listEnd':listEnd,'time':timeNow}
                socketio.emit('SocketDetectorComplete', response, callback=MessageReceived)
            else:
                response={'time':timeNow,'isFight':'false'}
                socketio.emit('SocketDetectorComplete', response, callback=MessageReceived)
    response={'isComplete':'true','message':'tespit bitti'}
    socketio.emit('SocketDetectorComplete', response, callback=MessageReceived)

@app.route("/DetectorStreamGet", methods=["GET"])
def DetectorStreamGet():
    return render_template("stream.html")

@app.route("/DetectorStream", methods=["POST"])
def DetectorStream():
    listStart=list()
    listEnd=list()
    listDummy=list()
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
        fps = vidcap.get(cv2.CAP_PROP_FPS)
        print("*************************************")
        print("FPS : "+str(fps))
        fps = 7
        #it will capture image in each 0.1 second
        frameRate = 0.142
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
            if(timeSecond>=60):
                timeMinute += 1
                timeSecond = 0
            if(countFrame >= round(fps)):
                countFrame = 0
                timeSecond += 1
            netInput = ImageUtils.ConvertImageFrom_CV_to_NetInput(image)
            isFighting = violenceDetector.Detect(netInput)
            #siddet tespit edildi
            
            timeNow='00:'+str(timeMinute).zfill(2)+':'+str(timeSecond).zfill(2)
            if isFighting:
                if len(listStart)==len(listEnd):
                    timeStart='00:'+str(timeMinute).zfill(2)+':'+str(timeSecond).zfill(2)
                    listStart.append(timeStart)
                    response={'isDone':'false','listStart':listStart,'listEnd':listEnd,'time':timeNow}
                    socketio.emit('SocketDetectorComplete', response, callback=MessageReceived)
                else:
                    timeDummy='00:'+str(timeMinute).zfill(2)+':'+str(timeSecond).zfill(2)
                    listDummy.append(timeDummy)
                    response={'time':timeNow,'isFight':'true'}
                    socketio.emit('SocketDetectorComplete', response, callback=MessageReceived)
            else:
                if len(listStart)!=len(listEnd):
                    timeEnd='00:'+str(timeMinute).zfill(2)+':'+str(timeSecond).zfill(2)
                    listEnd.append(timeEnd)
                    response={'isDone':'false','listStart':listStart,'listEnd':listEnd,'time':timeNow}
                    socketio.emit('SocketDetectorComplete', response, callback=MessageReceived)
                else:
                    timeDummy='00:'+str(timeMinute).zfill(2)+':'+str(timeSecond).zfill(2)
                    listDummy.append(timeDummy)
                    response={'time':timeNow,'isFight':'false'}
                    socketio.emit('SocketDetectorComplete', response, callback=MessageReceived)
            success,image = getFrame(sec,vidcap)
    if len(listEnd) == 0:
        if len(listStart) > 0:
            timeEnd='00:'+str(timeMinute).zfill(2)+':'+str(timeSecond).zfill(2)
            listEnd.append(timeEnd)
        response={'isDone':'true','listStart':listStart,'listEnd':listEnd}
        socketio.emit('SocketDetectorComplete', response, callback=MessageReceived)
    return json.dumps({'status':'OK','message':'merhaba'})

def readb64(base64_string):
    cleanData = str(base64_string)[len("data:image/jpeg;base64,"):]
    imgdata = base64.b64decode(cleanData)
    filename = 'some_image.jpg'  # I assume you have a way of picking unique filenames
    with open(filename, 'wb') as f:
        f.write(imgdata)
    retImage = cv2.imread('some_image.jpg',0)
    return retImage

def getFrame(sec,vidcap):
    vidcap.set(cv2.CAP_PROP_POS_MSEC,sec*1000)
    hasFrames,image = vidcap.read()
    return hasFrames,image

def MessageReceived(methods=['GET', 'POST']):
   print('Message was received!!!')

if __name__ == "__main__":
    socketio.run(app, debug=True)