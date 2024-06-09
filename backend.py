import json
import os
from flask import *
import pymongo
from pymongo.errors import DuplicateKeyError
from flask_socketio import SocketIO, close_room, emit, join_room, leave_room
from werkzeug.utils import secure_filename
import logging
import redis
import db_manager as db
import enum_class
import time
from celery import Celery
import helper
# r = redis.Redis(host='localhost', port=6379, decode_responses=True)

UPLOAD_FOLDER = 'D:/com.backend.do.an.tot.nghiep/file_folder'
UPLOAD_AVATAR = 'D:/com.backend.do.an.tot.nghiep/avatar'
UPLOAD_BANNER = 'D:/com.backend.do.an.tot.nghiep/banner'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

app = Flask(__name__)
app.config['SECRET_KEY'] = 'DUCANH_DATN'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['UPLOAD_AVATAR'] = UPLOAD_AVATAR
app.config['UPLOAD_BANNER'] = UPLOAD_BANNER

celery = Celery('backend', 
                broker='redis://127.0.0.1', 
                backend='redis://127.0.0.1', 
                broker_connection_retry_on_startup = True)

celery.conf.update(app.config)

socketio = SocketIO(app)

import handler
isHandling = False
room_status = {}

myClient = pymongo.MongoClient("mongodb://127.0.0.1:27017")

myDb = myClient["my_datn_db"]

user_col = myDb['user_col']
file_col = myDb['file_col']
cmt_col = myDb['cmt_col']


@app.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        try:
            _id = helper.generate_user_id()
            userName = request.json['userName']
            passWord = request.json['passWord']
        except:
            return jsonify({"error": "missing arg"})

        if user_col.find_one({'userName': userName}) is not None:
            return jsonify({"error": "Username already exists"})
        while user_col.find_one({'_id': _id}) is not None:
            _id = helper.generate_user_id()

        account = {
            "_id": _id,
            "userName": userName,
            "passWord": passWord,
            "email": "",
            "follow": [],
            "avatar": "/get_avatar/default_avatar.png"
        }

        try:
            user_col.insert_one(account)
        except DuplicateKeyError:
            return jsonify({"error": "Duplicate key error"})
        except Exception as e:
            return jsonify({"error": "An error occurred"})

        user = user_col.find_one({'_id': _id})
        return jsonify(user)

# @app.post('/register')
# def register():
#     if request.method == 'POST':
#         _id = None
#         userName = ""
#         passWord = ""
#         try: 
#             _id = helper.generate_user_id()
#             userName = request.json['userName']
#             passWord = request.json['passWord']
#         except: return "missing arg"
#         account = {
#                 "_id": _id,
#                 "userName": userName,
#                 "passWord": passWord,
#                 "email": "",
#                 "follow": [],
#                 "avatar": "/get_avatar/default_avatar.png"
#                 }    
#         try:
#             if account: user_col.insert_one(account)
#         except DuplicateKeyError as d: 
#             pass
#         except Exception as e: logging.error(f'Error occurred: {e}')
#         print(user_col.find_one({'_id': _id}))
#         return user_col.find_one({'_id': _id})

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
            return jsonify(user)
        else:
            return jsonify({})

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

@app.post('/get-profile')
def get_profile_by_user_id():
    if request.method == 'POST':
        idUser = ""
        try: 
            idUser = request.json['_id']
        except: return jsonify({"err": "missing arg"}) 
        
        print('idUser to get profile: ', idUser)
        print("---------------------ket qua", db.get_profile_by_id_user(idUser))
        return db.get_profile_by_id_user(idUser)

@app.post('/get-user-by-name')
def get_user_by_name():
    if request.method == 'POST':
        userName = ""
        try: 
            userName = request.json['userName']
        except: return jsonify({"err": "missing arg"}) 
        
        print('idUser to get profile: ', userName)
        print("---------------------ket qua", db.get_user_by_name(userName))
        return db.get_user_by_name(userName)

@app.post('/get-global-file')
def get_global_file():
    if request.method == 'POST':
        keyword = None
        time = ""
        searchMode = ""
        existFilesId = []
        try: 
            try:
                keyword = request.json['keyword']
            except: pass
            time = request.json['time']
            searchMode = request.json['searchMode']
            existFilesId = request.json['existFilesId']
        except: return jsonify({"err": "missing arg"}) 
        
        print('request file: ', keyword, time, searchMode, existFilesId)
        return db.get_public_file_by_keyword(keyword, time, searchMode, existFilesId)

@app.post('/get-follow-user')
def get_follow_user():
    if request.method == 'POST':
        id = None
        try: 
            id = request.json['_id']
        except: return jsonify({"err": "missing arg"}) 
        
        print('request follow list from id: ', id)
        return db.get_follow_user_by_id(id)

@app.post('/get-follow-file')
def get_follow_file():
    if request.method == 'POST':
        id = None
        try: 
            id = request.json['_id']
        except: return jsonify({"err": "missing arg"}) 
        
        print('request follow list from id: ', id)
        return db.get_follow_file_by_id(id)
    
@app.route('/test', methods=['POST'])
def test():
    if request.method == 'POST':
        msg = request.json.get('msg')
        if not msg:
            return jsonify({"err": "missing arg"})
        print('msg: ', msg)
        socketio.emit("on_msg_receive", {'msg': msg}, to='1713019963759')
        return jsonify({'msg': "msg"})
        # return {'msg': msg}

@app.post('/post-comment')
def post_comment():
    if request.method == 'POST':
        idUser = ""
        idFile = ""
        toUserId = None
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

        notifyId = f'cmt_{id}'
        if (toUserId is not None):
            type = enum_class.notify_type.REPLY
        else:
            type = enum_class.notify_type.COMMENT

        result = None

        try:
            result = db.insert_comment(commentEntity)

            if db.is_collection_exist('notify_col'):
                print('exist  ======================== idUser: ', idUser, 'idFile: ', idFile, 'idCommentOwner: ', toUserId, 'type: ', type.name)
                cmt = db.notify_col.find_one({'idUser': idUser, 'idFile': idFile, 'idCommentOwner': toUserId, 'type': type.name}, {'_id':1})

                print("=========================================================", cmt)
                if cmt is not None:
                    cmtId =  cmt['_id']
                    print("delete notify ===================cmtId: ", cmtId)
                    db.remove_notify(cmtId)
                else:
                    notify = db.insert_notify(notifyId, idUser, idFile, toUserId, type)
                    print("insert notify ===================cmtId: ", cmtId)
                    print(notify)
                    socket_send_msg(notify) 
            else:
                print(" not exist ==============================================================================")
                notify = db.insert_notify(notifyId, idUser, idFile, toUserId, type)
                print("them notify ===================cmtId: ", cmtId)
                print(notify)
                socket_send_msg(notify)
        except: pass

        if result:
            return commentEntity
        else: return None

def socket_send_msg(notify):
    msg, roomName = get_msg_to_notify(notify)
    if msg is not None:
        print(f'msg: {msg}, room name: {roomName}')
        print(f' ================ to id: {notify['_id']}')
        socketio.emit("on_msg_receive", {'msg': msg, '_id': f'{notify["_id"]}'}, to=roomName)

def get_msg_to_notify(notify):
    idUser = notify['idUser']
    idFile = notify['idFile']
    idCommentOwner = notify['idCommentOwner']
    type = notify['type']

    userName = user_col.find_one({'_id': idUser}, {'userName': 1})['userName']
    file = file_col.find_one({'_id': idFile}, {'idUser': 1})
    idSecondUser = file['idUser']
    secondUserName = user_col.find_one({'_id': idSecondUser}, {'userName': 1})['userName']

    match type:
        case enum_class.notify_type.NEW_FILE.name:
            roomName = f'follow_{idUser}'
            if idUser == idSecondUser:
                msg = f'Your file uploaded is available' 
            else:
                msg = f'{userName} uploaded a file'
        case enum_class.notify_type.LIKE_FILE.name:
            roomName = f'file_{idFile}'
            if userName == secondUserName:
                msg = None
            else:
                msg = f'{userName} has liked {secondUserName}\'s file'
        case enum_class.notify_type.COMMENT.name:
            roomName = f'file_{idFile}'
            if userName == secondUserName:
                msg = None
            else:
                msg = f'{userName} comment about {secondUserName}\'s file'
        case enum_class.notify_type.LIKE_CMT.name:
            roomName = idCommentOwner
            msg = f'{userName} liked your comment'
        case enum_class.notify_type.REPLY.name:
            roomName = idCommentOwner
            msg = f'{userName} reply your comment'
    return msg, roomName

@app.post('/post-like')
def post_like():
    idComment = None
    try: 
        id = request.json['_id']
        idUser = request.json['idUser']
        idFile = request.json['idFile']
        type = request.json['type']
        try:
            idComment = request.json['idComment']
        except: pass
    except KeyError:
        return jsonify({'error': 'Missing required argument(s)'})
    
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

    notifyId = f'cmt_{id}'
    if (idComment is not None):
        type = enum_class.notify_type.LIKE_CMT
    else:
        type = enum_class.notify_type.LIKE_FILE

    file_comments = db.file_col.find_one({'_id': idFile})['comments']
    print("================== file cmt:", file_comments)
    toUserId = ""
    for item in file_comments:
        if item['_id'] == idComment:
            toUserId = item['idUser']
    print("================== to user id:", toUserId)

    try:
        result = db.insert_or_delete_like(evaluationEntity)
        if db.is_collection_exist('notify_col'):
            print('exist  ======================== idUser: ', idUser, 'idFile: ', idFile, 'idCommentOwner: ', toUserId, 'type: ', type.name)
            notify = db.notify_col.find_one({'idUser': idUser, 'idFile': idFile, 'idCommentOwner': toUserId, 'type': type.name}, {'_id':1})

            print("=========================================================", notify)
            if notify is not None:
                notifyId =  notify['_id']
                print("delete notify ===================notifyId: ", notifyId)
                db.remove_notify(notifyId)
            else:
                notify = db.insert_notify(notifyId, idUser, idFile, toUserId, type)
                print("insert notify ===================notifyId: ", notifyId)
                print(notify)
                socket_send_msg(notify) 
        else:
            print(" not exist ==============================================================================")
            notify = db.insert_notify(notifyId, idUser, idFile, toUserId, type)
            print("them notify ===================notifyId: ", notifyId)
            print(notify)
            socket_send_msg(notify) 
               
        if result:
            return jsonify(evaluationEntity)
        else:
            return jsonify({'error': 'Failed to process like'})
    except Exception as e:
        return jsonify({'error': str(e)})
    return jsonify({'error': 'Unknown error occurred'})

@app.post('/delete-file')
def delete_file():
    try: 
        id = request.json['_id']
    except KeyError:
        return jsonify({'error': 'Missing required argument(s)'})

    print('...........delete file: ', id)

    result = db.delete_file_by_id(id)

    if result:
        try:
            file_path = os.path.join(UPLOAD_FOLDER, f"{id}.pdf")
            os.remove(file_path)
            print(f"Deleted {file_path} success")
        except OSError as e: 
            print(f"err delete: {e.filename}")
        except Exception as ex:
            print(f"err: {ex}")
        return {"status": result, "msg": "Delete Success"}
    else :
        return {"status": result, "msg": "Delete Failure"}
    
@app.post('/change-state')
def change_state():
    try: 
        id = request.json['_id']
    except KeyError:
        return jsonify({'error': 'Missing required argument(s)'})

    print('...........change state file: ', id)

    result = db.change_state(id)

    if result:
        return {"status": result, "msg": "Change State Success"}
    else :
        return {"status": result, "msg": "Change State Failure"}

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

                userEntity = {'_id': idUser}

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
                "comments": [],
                "followers": [userEntity],}  
                # if fileData: file_col.insert_one(fileData)
                if db.insert_one_to_db(fileData, enum_class.collection.FILE):
                    return {'msg': 'File uploaded successfully'}
            except: {'msg': 'File uploaded false'}
    return {'msg': 'File uploaded false'}

@app.route('/upload-image', methods=['GET', 'POST'])
def upload_image():
    if request.method == 'POST':

        if 'file' not in request.files:
            print('No file part')
            return {'msg': 'No file part'}
        file = request.files['file']
        fileName = request.form.get('fileName')
        fileType = request.form.get('fileType')
        idUser = fileName
        fileName = f'{fileName}.png'
        print("user id: ", idUser)
        print("fileType: ", fileType)

        if file.filename == '':
            return {'msg': 'No selected file'}
        if file:
            try:
                type = 'UPLOAD_AVATAR'
                if fileType == 'BANNER':
                    type = 'UPLOAD_BANNER'
                filename = secure_filename(fileName)
                file.save(os.path.join(app.config[type], filename))
                print("fileName save: ", filename)
                if fileType == 'AVATAR':
                    print('start update avatar')
                    if db.update_image(idUser):
                        print("success upload img")
                return {'msg': 'Uploaded successfully'}
            except: {'msg': 'Uploaded false'}
    return {'msg': 'Uploaded false'}

@app.post('/download')
def download_file():
    try: 
        id = request.json['_id']
    except KeyError:
        return jsonify({'error': 'Missing required argument(s)'})

    file_path = os.path.join(UPLOAD_FOLDER, f"{id}.pdf")
    print(file_path)
    return send_file(file_path, as_attachment=True)

@app.post('/follow-user')
def follow_user():
    try: 
        userId = request.json['userId']
        anotherId = request.json['anotherId']
    except KeyError:
        return jsonify({'error': 'Missing required argument(s)'})
    print(f'user: {userId} follow {anotherId}')

    query = {"_id": userId}
    result = user_col.update_one(
            query,
            {"$addToSet": {"follow": anotherId}},
            upsert=True
        )
    
    if result.modified_count > 0:
        return jsonify({'msg': 'Success'})
    else:
        return jsonify({'msg': 'False'})

@app.post('/get-notifications')
def get_notifications():
    try: 
        id = request.json['_id']
    except KeyError:
        return jsonify({'error': 'Missing required argument(s)'})

    list_notify = []
    notify_response = []
    list_notify = db.get_notifications(id)
    if list_notify is not None and len(list_notify) > 0:
        for item in list_notify:
            idOwner = item['idUser']
            user = db.user_col.find_one({'_id': idOwner})
            current_millis = int(round(time.time() * 1000))
            create_millis = item['time']
            last_time = str(current_millis - create_millis)
            msg, roomName = get_msg_to_notify(item)
            if msg is not None:
                print(
                    '_id', item['_id'],
                    'idFile', item['idFile'],
                    'avatar', user['avatar'],
                    'content', msg,
                    'time', last_time
                )
                notify = {
                    '_id': item['_id'],
                    'idFile': item['idFile'],
                    'avatar': user['avatar'],
                    'content': msg,
                    'time': last_time
                }
                print(notify)
                notify_response.append(notify)
                return notify_response
    else: return None

@app.post('/get-single-file')
def get_single_file():
    try: 
        id = request.json['_id']
    except KeyError:
        return jsonify({'error': 'Missing required argument(s)'})
    return db.file_col.find_one({'_id': id})

@socketio.on('connect')
def socket_connect(auth):
    emit('connect', {'data': 'Connected'})

@socketio.on('disconnect')
def socket_disconnect():
    print("disconnect")
    # emit("disconnect", {'data': 'disconnect'})@socketio.on('disconnect')

# client confirm to server that they receive this msg
@socketio.on('on_msg_receive')
def socket_on_msg_receive(data):
    id = data['id']
    idUser = data['idUser']
    print(f"id: {id} is receive notify: {id}")
    db.remove_user_need_notify(id, idUser)

@socketio.on('connect_error')
def socket_connect_err():
    emit("disconnect", {'data': 'connect err'})

# ==================================================================================================================
@socketio.on('login')
def socket_login(data):
    id = data['id']
    join_room(id)
    # print(f"data: {data}")
    print(f"user: {id} join to room: {id}")

    list_id_file_follower, list_id_follower = db.get_list_id_room(id)
    for idf in list_id_file_follower:
        room_name = f'file_{idf}'
        join_room(room_name)
        print(f'user {id} join to room: {room_name}')
    for idf in list_id_follower:
        room_name = f'follow_{idf}'
        join_room(room_name)
        print(f'user {id} join to room: {room_name}')

    msg = "Login Success"
    emit("on_login_receive", {'msg':msg}, to=id)

@socketio.on('logout')
def socket_logout(data):
    id = data['id']
    leave_room(id)
    list_id_file_follower, list_id_follower = db.get_list_id_room(id)
    print(f"id: {id} leave to room: {id}")
    for idf in list_id_file_follower:
        room_name = f'file_{idf}'
        leave_room(room_name)
        check_and_close_room(room_name)
        print(f'user {id} join to room: {room_name}')

    for idf in list_id_follower:
        room_name = f'follow_{idf}'
        leave_room(room_name)
        check_and_close_room(room_name)
        print(f'user {id} join to room: {room_name}')
    
    msg = "logout Success"
    emit("on_logout_receive", {'msg':msg}, to=id)

@socketio.on('check_has_notify')
def check_has_notify(data):
    id = data['id']
    print(f'client {id} request check notify')
    notify_list = db.get_notify_by_id(id)
    if notify_list is not None:
        for item in notify_list:
            try: 
                msg, room= get_msg_to_notify(item)
                if msg is not None:
                    userReceive = item['userReceive']
                    received = item['received']
                    print("list not yet notify", userReceive)
                    print("list had notify", received)
                    for r in userReceive:
                        if r not in received: 
                            print(f"client {id} has notify")
                            print(f'send notify: {msg} to {id}')
                            socketio.emit('on_msg_receive', {'msg': msg, '_id': f'{item["_id"]}'}, to=id)
            except: pass

def check_and_close_room(room):
    room_connections = request.namespace.rooms.get(room)
    num_members_in_room = len(room_connections) if room_connections else 0
    if num_members_in_room == 0: 
        close_room(room)
        print(f'delete room: {room}')

@socketio.on('start_task')
def start_task():
    global isHandling
    if (not isHandling):
        isHandling = True
        print('on start task in backend')
        my_task.delay()
        # thay thế xem chạy được không?
        # handler.file_execute_task.delay(onExecuteDone=notify_file_executed_done, onDone=onDoneAll)

@celery.task        
def my_task():
    handler.file_execute_task(onDoneAll = onDoneAll, notify_file_executed_done= notify_file_executed_done)

def notify_file_executed_done(file):
    print('on Done execute file')
    notifyId = f'file_{file['_id']}'
    idUser = file['idUser']
    idFile = file['_id']
    toUserId = None
    type = enum_class.notify_type.NEW_FILE
    notify = db.insert_notify(notifyId, idUser, idFile, toUserId, type)
    socket_send_msg(notify)
    # socketio.emit("on_file_execute_done", {'fileTitle': fileTitle}, to=userId)

def onDoneAll():
    global isHandling
    isHandling = False

@app.errorhandler(500)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return {'msg':"Server err occur"}

@app.route('/get_avatar/<filename>', methods=['GET'])
def get_avatar(filename):
    directory = 'D:/com.backend.do.an.tot.nghiep/avatar'
    try:
        return send_from_directory(directory, filename)
    except Exception as e:
        return send_from_directory(directory, 'default_avatar.png')
    
@app.route('/get_banner/<filename>', methods=['GET'])
def get_banner(filename):
    directory = 'D:/com.backend.do.an.tot.nghiep/banner'
    try:
        return send_from_directory(directory, filename)
    except Exception as e:
        return send_from_directory(directory, 'img_banner.jpg')

def start():
    socketio.run(app, host="0.0.0.0", port=5000, allow_unsafe_werkzeug=True, debug=True, use_reloader=True)
    
if __name__ == '__main__':
    start()
