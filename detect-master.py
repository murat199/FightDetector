from flask import Flask, render_template
from flask_socketio import SocketIO
import json
import base64
import datetime
import numpy as np
import cv2
import os
import sys
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

app = Flask(__name__)
app.config['SECRET_KEY'] = 'vnkdjnfjknfl1232#'
socketio = SocketIO(app)

violenceDetector = ViolenceDetector.ViolenceDetector()

@app.route('/')
def sessions():
   return render_template('index_webcam.html')

def MessageReceived(methods=['GET', 'POST']):
   print('Message was received!!!')

@socketio.on('Detector')
def Detector(frames, methods=['GET', 'POST']):
   dataJson = json.loads(str(frames).replace('\'','\"'))
   for item in dataJson['data']:
      netInput = ImageUtils.ConvertImageFrom_CV_to_NetInput(readb64(item["img"]))
      isFighting = violenceDetector.Detect(netInput)
      #siddet tespit edildi
      if isFighting:
         response={'isDone':'false','message':'Baslangic:'+str(item['time'])}
         socketio.emit('Detector', response, callback=MessageReceived)
      else:
         response={'isDone':'false','message':'Bitis:'+str(item['time'])}
         socketio.emit('Detector', response, callback=MessageReceived)
   response={'isDone':'true','message':'tespit bitti'}
   socketio.emit('Detector', response, callback=MessageReceived)

def readb64(base64_string):
   cleanData = str(base64_string)[len("data:image/jpeg;base64,"):]
   imgdata = base64.b64decode(cleanData)
   image = Image.open(BytesIO(imgdata))
   return np.array(image)

if __name__ == '__main__':
   socketio.run(app, debug=True)