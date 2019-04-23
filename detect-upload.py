import os
import sys
import cv2
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


app = Flask(__name__)
socketio = SocketIO(app)
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
violenceDetector = ViolenceDetector.ViolenceDetector()

@app.route("/")
def index():
    return render_template("index_upload.html")

@app.route("/upload", methods=["POST"])
def upload():
    target = os.path.join(APP_ROOT, 'videos/')
    print(target)
    if not os.path.isdir(target):
        os.mkdir(target)
    print(request.files.getlist("file"))
    for upload in request.files.getlist("file"):
        print(upload)
        print("{} is the file name".format(upload.filename))
        filename = upload.filename
        # This is to verify files are supported
        ext = os.path.splitext(filename)[1]
        if (ext == ".mp4") or (ext == ".mov"):
            print("File supported moving on...")
        else:
            render_template("index_upload.html", message="Files uploaded are not supported...")
        destination = "/".join([target, filename])
        print("Accept incoming file:", filename)
        print("Save it to:", destination)
        upload.save(destination)

        vidcap = cv2.VideoCapture(destination)
        success, image = vidcap.read()
        count = 0
        message = ""
        while success:
            netInput = ImageUtils.ConvertImageFrom_CV_to_NetInput(image)
            isFighting = violenceDetector.Detect(netInput)
            #siddet tespit edildi
            if isFighting:
                message+="Siddet Basladi."
            else:
                message+="Siddet Bitti."
            count += 1
            success, image = vidcap.read()
    # return send_from_directory("images", filename, as_attachment=True)
    return render_template("index_upload.html", message=message)


@app.route('/upload/<filename>')
def send_image(filename):
    return send_from_directory("images", filename)


@app.route('/gallery')
def get_gallery():
    image_names = os.listdir('./images')
    print(image_names)
    return render_template("gallery.html", image_names=image_names)


if __name__ == "__main__":
    socketio.run(app, debug=True)