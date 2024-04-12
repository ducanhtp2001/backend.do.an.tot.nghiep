import os
from flask import Flask, flash, redirect, session, jsonify
from flask import url_for, request
import pandas as pd
import pymongo
from pymongo.errors import DuplicateKeyError
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename
import logging

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

@socketio.on('connect')
def socket_connect(auth):
    emit('connect', {'data': 'Connected'})

@socketio.on('disconnect')
def socket_disconnect():
    emit("disconnect", {'data': 'disconnect'})

@socketio.on('connect_error')
def socket_connect_err():
    emit("disconnect", {'data': 'connect err'})


def start():
    socketio.run(app, host="0.0.0.0", port=5001, allow_unsafe_werkzeug=True)
    
if __name__ == '__main__':
    start()
