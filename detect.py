from flask import Flask, render_template
from flask_socketio import SocketIO
import json
import base64
import datetime


app = Flask(__name__)
app.config['SECRET_KEY'] = 'vnkdjnfjknfl1232#'
socketio = SocketIO(app)

@app.route('/')
def sessions():
   return render_template('index_webcam.html')

def messageReceived(methods=['GET', 'POST']):
   print('message was received!!!')

@socketio.on('DetectFrames')
def handle_my_custom_event(frames, methods=['GET', 'POST']):
   dataFrames=list()
   dataJson = json.loads(str(frames).replace('\'','\"'))
   for item in dataJson['data']:
      imgdata = base64.b64decode(item)
      dataFrames.append(imgdata)
      now = datetime.datetime.now()
      response={'isDone':'false','message':'Cevap zamani:'+str(now.isoformat())}
      socketio.emit('DetectFramesResponse', response, callback=messageReceived)
   print("Eleman sayisi:"+str(len(dataFrames)))
   now = datetime.datetime.now()
   response={'isDone':'true','message':'Cevap zamani:'+str(now.isoformat())}
   socketio.emit('DetectFramesResponse', response, callback=messageReceived)

if __name__ == '__main__':
   socketio.run(app, debug=True)