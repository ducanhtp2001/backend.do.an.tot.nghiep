import json
import os
from flask import *
import pymongo
from pymongo.errors import DuplicateKeyError
from flask_socketio import SocketIO, emit, join_room
from werkzeug.utils import secure_filename
import logging
import redis
import db_manager as db
import enum_class


r = redis.Redis(host='localhost', port=6379, decode_responses=True)

UPLOAD_FOLDER = 'D:/com.backend.do.an.tot.nghiep/file_folder'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

app = Flask(__name__)
app.config['SECRET_KEY'] = 'DUCANH_DATN'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config.update(
    CELERY_BROKER_URL='redis://localhost:6379/0',
    CELERY_RESULT_BACKEND='redis://localhost:6379/0'
)
socketio = SocketIO(app)

import handler

isHandling = False


myClient = pymongo.MongoClient("mongodb://localhost:27017/")

myDb = myClient["my_datn_db"]

user_col = myDb['user_col']
file_col = myDb['file_col']
cmt_col = myDb['cmt_col']

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

@app.post('/get-private-file')
def get_private_file_by_user_id():
    if request.method == 'POST':
        idUser = ""
        try: 
            idUser = request.json['_id']
        except: return "missing arg" 

        print('idUser to get private file: ', idUser)
        return jsonify(db.get_file_executed_by_id_user(idUser, False))
    
@app.post('/get-public-file')
def get_public_file_by_user_id():
    if request.method == 'POST':
        idUser = ""
        try: 
            idUser = request.json['_id']
        except: return "missing arg" 

        print('idUser to get public file: ', idUser)

        return jsonify(db.get_file_executed_by_id_user(idUser, True))

@app.post('/post-comment')
def post_comment():
    if request.method == 'POST':
        idUser = ""
        idFile = ""
        toUserId = ""
        id = ""
        content = ""
        try: 
            id = request.json['_id']
            idUser = request.json['idUser']
            idFile = request.json['idFile']
            content = request.json['content']
            try:
                toUserId = request.json['toUserId']
            except: pass
        except: return "missing arg" 

        print('post comment: : ', id, idUser, idFile, toUserId, content)

        user = db.get_user_by_id(idUser)

        print("============== user post cmt: ", user)

        commentEntity = {
            "_id": id,
            "idUser": idUser,
            "avatar": user['avatar'],
            "userName": user['userName'],
            "idFile": idFile,
            "toUserId": toUserId,
            "content": content,            
            "likes": [],
        }

        result = None

        try:
            result = db.insert_comment(commentEntity)
        except: pass

        if result:
            return commentEntity
        else: return None
        # return jsonify({'message': 'Comment posted successfully'})
        # return jsonify(db.get_file_executed_by_id_user(idUser, True))


@app.post('/post-like')
def post_like():
    if request.method == 'POST':
        id = ""
        idUser = ""
        idFile = ""
        idComment = ""
        type = ""
        try: 
            id = request.json['_id']
            idUser = request.json['idUser']
            idFile = request.json['idFile']
            idComment = request.json['idComment']
            type = request.json['type']
        except: return "missing arg" 

        print('post like: : ', id, idUser, idFile, idComment, type)

        user = db.get_user_by_id(idUser)

        print("============== user post like: ", user)

        evaluationEntity = {
            "_id": id,
            "idUser": idUser,
            "avatar": user['avatar'],
            "userName": user['userName'],
            "idFile": idFile,
            "idComment": idComment,
            "type": type,
        }

        result = None

        try:
            result = db.insert_or_delete_like(evaluationEntity)
        except: pass

        if result:
            return evaluationEntity
        else: return None


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
        fileName = request.form.get('fileName')
        fileId = request.form.get('fileId')
        print(fileId)
        idUser = request.form.get('id')
        isTable = False
        isPublic = False
        if isTableStr == "true": isTable = True
        if isPublicStr == "true": isPublic = True

        # print("description: ", title, isTableStr, isPublicStr)
        print("fileName: ", fileName)
        print("fileId: ", fileId)
        # print("id: ", idUser)

        if file.filename == '':
            print('No selected file')
            return {'msg': 'No selected file'}
        if file and allowed_file(file.filename):

            try:
                filename = secure_filename(fileName)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                print("fileName save: ", filename)

                fileData = {
                "_id": fileId,
                "idUser": idUser,
                "title": title,
                "fileName": filename,
                "recognizeText": "",
                "summaryText": "",
                "state": False,
                "isPublic": isPublic,
                "isTable": isTable,
                "likes": [],
                "comments": []
                }  

                # if fileData: file_col.insert_one(fileData)
                if db.insert_one_to_db(fileData, enum_class.collection.FILE):
                    return {'msg': 'File uploaded successfully'}
            except: {'msg': 'File uploaded false'}
            
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

@socketio.on('start_task')
def start_task():
    global isHandling
    print('on task')
    if (not isHandling):
        isHandling = True
        handler.file_execute_task(onExecuteDone=notify_file_executed_done, onDone=onDoneAll)

def notify_file_executed_done(userId, fileTitle):
    print('on Done execute file')
    emit("on_file_execute_done", {'fileTitle': fileTitle}, to=userId)

def onDoneAll():
    global isHandling
    isHandling = False

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
