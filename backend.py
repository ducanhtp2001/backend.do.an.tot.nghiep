import json
import os
from flask import Flask, flash, redirect, session, jsonify
from flask import url_for, request
import pandas as pd
import pymongo
from pymongo.errors import DuplicateKeyError
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename
import logging
import redis

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

UPLOAD_FOLDER = 'D:/com.backend.do.an.tot.nghiep/file_folder'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['SECRET_KEY'] = 'DUCANH_DATN'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
socketio = SocketIO(app)


myClient = pymongo.MongoClient("mongodb://localhost:27017/")

myDb = myClient["my_datn_db"]

user_col = myDb['user_col']
file_col = myDb['file_col']

@app.post('/register')
def register():
    if request.method == 'POST':
        _id = None
        userName = ""
        passWord = ""
        try: 
            _id = request.json['id']
            userName = request.json['userName']
            passWord = request.json['passWord']
        except: return "missing arg"

        account = {
                "_id": _id,
                "userName": userName,
                "passWord": passWord,
                "email": None,
                "follow": [],
                }    

        try:
            if account: user_col.insert_one(account)
        except DuplicateKeyError as d: 
                    # query = {"_id": info['_id']}
                    # update = {"$set": info}
                    # video_collection.update_one(query, update)
                    pass
        except Exception as e: logging.error(f'Error occurred: {e}')

        print(user_col.find_one({'_id': _id}))
        return user_col.find_one({'_id': _id})

@app.post('/login')
def login():
    if request.method == 'POST':
        userName = ""
        passWord = ""
        try: 
            userName = request.json['userName']
            passWord = request.json['passWord']
        except: return "missing arg"

        print(userName + "-" + passWord)

        user = user_col.find_one({'userName': userName, 'passWord': passWord})
        print(user)

        if user:
            session['name'] = user['_id']
            return user
        else:
            return None

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':

        if 'file' not in request.files:
            print('No file part')
            return {'msg': 'No file part'}
        file = request.files['file']
        description = request.form.get('description')
        name = request.form.get('fileName')
        id = request.form.get('id')

        print("description: ", description)
        print("name: ", name)
        print("id: ", id)

        if file.filename == '':
            print('No selected file')
            return {'msg': 'No selected file'}
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filename = name
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return {'msg': 'File uploaded successfully'}
    return {'msg': 'File uploaded false'}

@socketio.on('connect')
def socket_connect(auth):
    emit('connect', {'data': 'Connected'})

@socketio.on('disconnect')
def socket_disconnect():
    emit("disconnect", {'data': 'disconnect'})

@socketio.on('connect_error')
def socket_connect_err():
    emit("disconnect", {'data': 'connect err'})

@socketio.on('login')
def socket_login(data):
    room = data['room_id'] 
    id = data['sender_id']
    msg = data['msg']
    print(f"data: {data}")
    print(f"id: {id} send to room: {room}: {msg}")
    emit("on_receive", data, to=room)

def start():
    socketio.run(app, host="0.0.0.0", port=5000, allow_unsafe_werkzeug=True, debug=True)
    
if __name__ == '__main__':
    start()
