import json
from flask import Flask, session, jsonify
from flask import url_for, request
import pandas as pd
import pymongo
from pymongo.errors import DuplicateKeyError
from flask_socketio import SocketIO
import logging

app = Flask(__name__)
app.config['SECRET_KEY'] = 'DUCANH_DATN'
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
            _id = request.json['_id']
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
        return user_col.find_one({'_id': _id}), 200

    

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

        user = user_col.find_one({'userName': userName, 'passWord': passWord}), 200
        print(user)

        if user:
            return user
        else:
            return None

    

def start():
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
    
if __name__ == '__main__':
    start()
