import json
import os
from flask import *
import pymongo
from pymongo.errors import DuplicateKeyError
from flask_socketio import SocketIO, emit, join_room
from werkzeug.utils import secure_filename
import logging
import redis
import handler

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

UPLOAD_FOLDER = 'D:/com.backend.do.an.tot.nghiep/file_folder'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

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
            _id = request.json['_id']
            userName = request.json['userName']
            passWord = request.json['passWord']
        except: return "missing arg"

        account = {
                "_id": _id,
                "userName": userName,
                "passWord": passWord,
                "email": "",
                "follow": [],
                "avatar": "/get_avatar/default_avatar.png"
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
            print("session: " + session['name'])
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
        title, isTableStr, isPublicStr = request.form.get('description').split("-")
        name = request.form.get('fileName')
        idUser = request.form.get('id')
        isTable = False
        isPublic = False
        if isTableStr == "true": isTable = True
        if isPublicStr == "true": isPublic = True

        print("description: ", title, isTableStr, isPublicStr)
        print("name: ", name)
        print("id: ", idUser)

        if file.filename == '':
            print('No selected file')
            return {'msg': 'No selected file'}
        if file and allowed_file(file.filename):
            

            try:
                filename = secure_filename(file.filename)
                filename = name
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

                fileData = {
                "_id": filename,
                "idUser": idUser,
                "title": title,
                "recognizeText": "",
                "summaryText": "",
                "state": False,
                "isPublic": isPublic,
                "isTable": isTable,
                "evaluation": None,
                "comments": None
                }    

                if fileData: file_col.insert_one(fileData)
            except: {'msg': 'File uploaded false'}
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
    id = data['id']
    join_room(id)
    print(f"data: {data}")
    print(f"id: {id} join to room: {id}")
    msg = "Login Success"
    emit("on_login_receive", {'msg':msg}, to=id)

@app.route('/start_task')
def start_task():
    handler.long_running_task.delay()

@app.route('/get_avatar/<filename>', methods=['GET'])
def get_avatar(filename):
    directory = 'D:/com.backend.do.an.tot.nghiep/avatar'
    try:
        print(send_from_directory(directory, filename))
        return send_from_directory(directory, filename)
    except Exception as e:
        return jsonify({"error": str(e)})

def start():
    socketio.run(app, host="0.0.0.0", port=5000, allow_unsafe_werkzeug=True, debug=True)
    
if __name__ == '__main__':
    start()
