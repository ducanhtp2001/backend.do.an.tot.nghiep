import json
import os
from flask import *
import pymongo
from pymongo.errors import DuplicateKeyError
from flask_socketio import SocketIO, emit, join_room, leave_room
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

# ///////////////////////////
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
        # return jsonify({'message': 'Comment posted successfully'})
        # return jsonify(db.get_file_executed_by_id_user(idUser, True))

def socket_send_msg(notify):
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
            msg = f'{userName} uploaded a file'
        case enum_class.notify_type.LIKE_FILE.name:
            roomName = f'follow_{idUser}'
            if userName == secondUserName:
                msg = None
            else:
                msg = f'{userName} has liked {secondUserName}\'s file'
        case enum_class.notify_type.COMMENT.name:
            roomName = f'follow_{idUser}'
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

    if msg is not None:
        print(f'msg: {msg}, room name: {roomName}')
        print(f' ================ tooooooooo id: {notify['_id']}')
        socketio.emit("on_msg_receive", {'msg': msg, '_id': f'{notify["_id"]}'}, to=roomName)
    

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
                "followers": [],
                }  
                # if fileData: file_col.insert_one(fileData)
                if db.insert_one_to_db(fileData, enum_class.collection.FILE):
                    return {'msg': 'File uploaded successfully'}
            except: {'msg': 'File uploaded false'}
    return {'msg': 'File uploaded false'}

@app.post('/download')
def download_file():
    try: 
        id = request.json['_id']
    except KeyError:
        return jsonify({'error': 'Missing required argument(s)'})

    file_path = os.path.join(UPLOAD_FOLDER, f"{id}.pdf")
    print(file_path)
    return send_file(file_path, as_attachment=True)

@socketio.on('connect')
def socket_connect(auth):
    emit('connect', {'data': 'Connected'})

@socketio.on('disconnect')
def socket_disconnect():
    print("disconnect")
    # emit("disconnect", {'data': 'disconnect'})@socketio.on('disconnect')

#==============-=-=-=-=-=-=-==-=-=-=-==-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=--==--=
#==============-=-=-=-=-=-=-==-=-=-=-==-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=--==--=
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

@socketio.on('login')
def socket_login(data):
    id = data['id']
    join_room(id)
    print(f"data: {data}")
    print(f"id: {id} join to room: {id}")
    msg = "Login Success"
    emit("on_login_receive", {'msg':msg}, to=id)

@socketio.on('logout')
def socket_logout(data):
    id = data['id']
    leave_room(id)
    print(f"data: {data}")
    print(f"id: {id} leave to room: {id}")
    msg = "logout Success"
    emit("on_logout_receive", {'msg':msg}, to=id)

@socketio.on('start_task')
def start_task():
    global isHandling
    print('on task')
    if (not isHandling):
        isHandling = True
        handler.file_execute_task(onExecuteDone=notify_file_executed_done, onDone=onDoneAll)


def notify_file_executed_done(userId, fileTitle):
    print('on Done execute file')
    socketio.emit("on_file_execute_done", {'fileTitle': fileTitle}, to=userId)

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
        print(send_from_directory(directory, filename))
        return send_from_directory(directory, filename)
    except Exception as e:
        return jsonify({"error": str(e)})

def start():
    socketio.run(app, host="0.0.0.0", port=5000, allow_unsafe_werkzeug=True, debug=True)
    
if __name__ == '__main__':
    start()
