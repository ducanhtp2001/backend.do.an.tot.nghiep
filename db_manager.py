from flask import jsonify
import pymongo
from pymongo.errors import DuplicateKeyError
import enum_class
import time

myClient = pymongo.MongoClient("mongodb://localhost:27017/")

myDb = myClient["my_datn_db"]

user_col = myDb['user_col']
file_col = myDb['file_col']
# cmt_col = myDb['cmt_col']
notify_col = myDb['notify_col']

def insert_one_to_db(data, type):
    if type == enum_class.collection.USER:
        return user_col.insert_one(data).acknowledged
    elif type == enum_class.collection.FILE:
        return file_col.insert_one(data).acknowledged
    # elif type == enum_class.collection.COMMENT:
    #     return comment_col.insert_one(data).acknowledged
    # elif type == enum_class.collection.LIKE:
    #     return like_col.insert_one(data).acknowledged
    
def find_one_from_db(id, type):

    query = query = {'_id': id}

    if type == enum_class.collection.USER:
        data = user_col.find_one(query)
    elif type == enum_class.collection.FILE:
        data =  file_col.find_one(query)
    # elif type == enum_class.collection.COMMENT:
    #     data =  comment_col.find_one(query)
    # elif type == enum_class.collection.LIKE:
    #     data =  like_col.find_one(query)
    if data: return data
    else: return None

def get_file_to_execute():
    print('on query')
    query = {'state': False}
    cursor = file_col.find_one(query)
    if cursor:
        print(cursor)
        return cursor
    
# =====================----------------------------------------===================================
def remove_user_need_notify(id, idUser):
    notify = notify_col.find_one({'_id': id})
    received = notify['received']
    received.append(idUser)
    notify_col.update_one({'_id': id}, {"$set": {"received": received}})

# id user is id of user post action(like, cmt, upload)
# idCommentOwner is id of user post this cmt when it is liked or reply, it can be none
def insert_notify(id, idUser, idFile, idCommentOwner, type):
    match type:
        # notify to all user follow this owner
        case enum_class.notify_type.NEW_FILE, enum_class.notify_type.LIKE_FILE, enum_class.notify_type.COMMENT:
            query = {"follow": {"$in": ["1713019909558"]}}
            projection = {"_id": 1}
            cursors = user_col.find(query, projection)
            followers = [cursor['_id'] for cursor in cursors]  

        # notify to all user care this file
        case _:
            followers = [idCommentOwner]
           
    current_millis = int(round(time.time() * 1000))

    notify = {
        '_id': id,
        'idUser': idUser,
        'idFile': idFile,
        'idCommentOwner': idCommentOwner, 
        'type': type.name,  
        'time': current_millis,
        'userReceive': followers,
        'received': []
    }

    notify_col.insert_one(notify)
    print(f'------ insert new notify : {notify}')
    return notify


# insert_notify('1', '1713019909558', '1713019963759_1714189585546', enum_class.collection.COMMENT)


def remove_notify(id):
    notify_col.delete_one({'_id': id})
    print(f'------ delete notify : {id}')

def get_notifications(idUser):
    cursor = notify_col.find({'userReceive' : {'$in': [idUser]}})
    if cursor is not None:
        list_notify = [notify for notify in cursor]
        return list_notify
    return None
    
# print(get_notifications('1713019963759'))

def update_file_after_execute(fileId, origin, summary):
    query = {'_id': fileId}
    new_data = {'$set': {'recognizeText': origin, 'summaryText': summary, 'state': True}}
    print(' ============= update db', query)
    file_col.update_one(query, new_data)

def get_user_sub_by_id(idUser):
    query = {'_id': idUser}
    print(' ---------------- id: ', idUser)
    try:
        user = user_col.find_one(query)
        userData = {
            '_id': user['_id'],
            'userName': user['userName'],
            'avatar': user['avatar'],
        }
    except: return None
    return userData

def get_follow_user_by_id(idUser):
    query = {'_id': idUser}
    print(' ---------------- request follow list by id: ', idUser)
    user = user_col.find_one(query)
    follows = user['follow']
    response = []
    for item in follows:
        queryTmp = {'_id': item}
        userTmp = user_col.find_one(queryTmp)
        tmp = {}
        tmp['_id'] = userTmp['_id']
        tmp['userName'] = userTmp['userName']
        tmp['avatar'] = userTmp['avatar']
        response.append(tmp)
    return response

def get_follow_file_by_id(idUser):
    query = {'_id': idUser}
    print(' ---------------- request follow list by id: ', idUser)
    user = user_col.find_one(query)
    follows = user['follow']
    print(follows)
    response = []
    for item in follows:
        fileQuery = {'idUser': item, "state": True, 'isPublic': True}
        fileCursor = file_col.find(fileQuery)
        userQuery = {'_id': item}
        userCursor = user_col.find_one(userQuery)
        for file in fileCursor:
            # print(file)
            tmp = file
            tmp['userName'] = userCursor['userName']
            tmp['avatar'] = userCursor['avatar']
            response.append(tmp)
        
    return response

# print(get_follow_file_by_id("1713019909558"))
# print(get_follow_user_by_id("1713019909558"))

# print(get_user_sub_by_id('1713019909558'))

def get_public_file_by_keyword(keyword, time, searchMode, existFilesId):

    maxDoc = time * 10

    if(keyword is not None):
        if(searchMode == 1):
            regex_query = {'$regex': keyword, '$options': 'i'}
            pipeline = [
                {'$match': {'state': True,'isPublic': True, '$or': [
                                                                    {'title': regex_query},
                                                                    {'summaryText': regex_query},
                                                                    {'originText': regex_query}
                                                                ]}},
                {'$addFields': {'likesCount': {'$size': '$likes'},'commentsCount': {'$size': '$comments'}}},
                {'$sort': {'likesCount': -1,'commentsCount': -1}},
                {'$limit': maxDoc}
            ]
            cursor = file_col.aggregate(pipeline)
        else: 
            regex_query = {'$regex': keyword, '$options': 'i'}
            pipeline = [
                {'$match': {'state': True,'isPublic': True, '$or': [
                                                                    {'title': regex_query},
                                                                    {'summaryText': regex_query},
                                                                    {'originText': regex_query}
                                                                ]}},
                {'$limit': maxDoc}
            ]
            cursor = file_col.aggregate(pipeline)
    else:
        if(searchMode == 1):
            pipeline = [
                {'$match': {'state': True,'isPublic': True}},
                {'$addFields': {'likesCount': {'$size': '$likes'},'commentsCount': {'$size': '$comments'}}},
                {'$sort': {'likesCount': -1,'commentsCount': -1}},
                {'$limit': maxDoc}
            ]
            cursor = file_col.aggregate(pipeline)
        else: 
            pipeline = [
                {'$match': {'state': True,'isPublic': True}},
                {'$limit': maxDoc}
            ]
            cursor = file_col.aggregate(pipeline)

    files = list(cursor)
    globalFile = []
    for item in files:
        user = user_col.find_one({"_id":item['idUser']})
        tmp = item
        tmp['userName'] = user['userName']
        tmp['avatar'] = user['avatar']
        globalFile.append(tmp)
        
    return globalFile


# print(((get_public_file_by_keyword("title 1", 0, 0, []))))
       

def get_profile_by_id_user(id):
    query = {'_id': id}
    user = user_col.find_one(query)
    query = {'idUser': id, 'state': True, 'isPublic': True}
    files = [doc for doc in file_col.find(query)]
    query = {'follow': {'$in': [id]}}
    followers = [per for per in user_col.find(query)]
    followersResponse = []
    for item in followers:
        response = {
            '_id': item['_id'],
            'userName': item['userName'],
            'avatar': item['avatar'],
        }
        followersResponse.append(response)

    follows = []
    for item in user['follow']:
        tmp = get_user_sub_by_id(item)
        if tmp is not None:
            follows.append(tmp)

    userData = {
        '_id': user['_id'],
        'userName': user['userName'],
        'follows': follows,
        'avatar': user['avatar'],
        'followers': followersResponse,
    }
    profile = {
        'user': userData,
        'files': files
    }
    print("-------------------- size profile file: ", len(files))
    return profile

# print(get_profile_by_id_user("1713019909558"))


# query = {'follow': {'$in': ['1713019963759']}}
# followers = [per for per in user_col.find(query)]
# print(followers)

# query = {'idUser': "1713019963759", 'state': True, 'isPublic': True}
# files = [doc for doc in file_col.find(query)]
# print(len(files))

def delete_file_by_id(fileId):  
    result = file_col.delete_one({"_id": fileId})
    result = notify_col.delete_many({"idFile": fileId})
    print('============= delete file id:', fileId)
    if result.deleted_count == 1:
        return True
    else: 
        return False
    
def change_state(fileId):  
    # result = file_col.find_one_and_update({"_id": fileId}, {"$set": {"isPublic": {"$not": "$isPublic"}}})
    # result = file_col.find_one_and_update({"_id": fileId}, {"$set": {"isPublic": {"$not": {"$eq": "$isPublic"}}}})
    result = file_col.find_one_and_update(
    {"_id": fileId},
    {"$set": {"isPublic": True if file_col.find_one({"_id": fileId})["isPublic"] == False else False}})
    print('============= change state file id:', fileId)
    if result is not None:
        return True
    else: 
        return False

def get_file_executed_by_id_user(idUser, isPublic):
    query = {'idUser': idUser, 'state': True, 'isPublic': isPublic}
    files = file_col.find(query)
    files_list = list(files)
    
    # print(files_list)
    print('find: ', len(files_list))
    return files_list

# =========================================================================================================================
def get_list_id_room(idUser):
    setFileId = {}
    setFollowerId = {}
    try:
        idFiles = file_col.find({'followers': {'$elemMatch': {'_id': idUser}}}, {'idUser' : 1})
        id_list = [doc['idUser'] for doc in idFiles]
        if id_list is not None: setFileId = set(id_list)
    except: pass

    try:
        user = user_col.find_one({'_id': idUser})
        if user is not None: idFollowers = user['follow']
        if idFollowers is not None and id_list is not None: setFollowerId = set(idFollowers)
    except: pass

    return list(setFileId), list(setFollowerId)

def get_notify_by_id(idUser):
    try: 
        cursor  = notify_col.find({'userReceive': {'$elemMatch': {'$in': [idUser]}}})
        if cursor is not None:
            notify_list = [notify for notify in cursor]
            return notify_list
    except: return None

# print(get_notify_by_id('1713019963759'))        

# a, b = get_list_id_room('1713019963759')
# print(a)
# print(b)

def get_user_by_id(idUser):
    query = {'_id': idUser}
    print(' ---------------- id: ', idUser)
    return user_col.find_one(query)

def insert_comment(commentEntity):
    query = {"_id": commentEntity['idFile']}
    update = {"$push": {"comments": commentEntity}}
    try:
        result = file_col.update_one(query, update)
        return result.matched_count > 0
    except:
        return False
    
# def insert_or_delete_like(evaluationEntity):
#     query = {"_id": evaluationEntity['idFile']}
#     update = {"$push": {"likes": evaluationEntity}}
#     try:
#         result = file_col.update_one(query, update)
#         return result.matched_count > 0
#     except:
#         return False
    
def insert_or_delete_like(evaluationEntity):
    # query = {"_id": evaluationEntity['idFile']}

    if evaluationEntity['type'] == 'FILE':
        evaluation_query = {'_id': evaluationEntity['idFile'], "likes": {"$elemMatch": {"idUser": evaluationEntity['idUser']}}} 

        try:
            existing_evaluation = file_col.find_one(evaluation_query)
            query = {"_id": evaluationEntity['idFile']}
            if existing_evaluation:
                print(' ======= xoa like file ======= ', evaluationEntity)
                update = {"$pull": {"likes": {"idUser": evaluationEntity['idUser']}}}
                result = file_col.update_one(query, update)
                return result.modified_count > 0

            else:
                print(' ======= like file ======= ', evaluationEntity)
                update = {"$push": {"likes": evaluationEntity}}
                print("--------------- update query", update)
                result = file_col.update_one(query, update)
                return result.matched_count > 0

        except Exception as e:
            print(e)
            return False
    elif evaluationEntity['type'] == 'COMMENT':    
        # evaluation_query = {"_id": evaluationEntity['idFile'],
        #         "comments._id": evaluationEntity['idComment'],
        #         "comments.likes": {"$elemMatch": {"idUser": evaluationEntity['idUser']}}}
        
        evaluation_query = {"_id": evaluationEntity['idFile'], 
         "comments": {"$elemMatch": {"_id": evaluationEntity['idComment'], 
                                     "likes": {"$elemMatch": {"idUser": evaluationEntity['idUser']}}}}}

        print(" ****************** ==  evaluation_query: ", evaluation_query)
        try:
            existing_evaluation = file_col.find_one(evaluation_query)
            query = {"_id": evaluationEntity['idFile'], "comments._id": evaluationEntity['idComment']}
            print("--------------- query", query)
            if existing_evaluation is not None:
                print(' ======= xoa like COMMENT ======= ', evaluationEntity)
                update_action = { "$pull": {"comments.$.likes": {"idUser": evaluationEntity['idUser']}} }
                print("--------------- update query", update_action)
                result = file_col.update_one(query, update_action)
                return result.modified_count > 0

            else:
                print(' ======= like COMMENT ======= ', evaluationEntity)
                # update_action = {"$push": {"comments.$[elem].likes": evaluationEntity},
                #                  "array_filters": [{"elem._id": evaluationEntity['idComment']}]}
                update_action = { "$push": { "comments.$.likes": evaluationEntity } }
                print("--------------- update query", update_action)
                result = file_col.update_one(query, update_action)
                return result.matched_count > 0

        except Exception as e:
            print(e)
            return False

# eval = {'_id': '1715525712319_1713019963759', 'idUser': '1713019963759', 'avatar': '/get_avatar/default_avatar.png', 'userName': 'a', 'idFile': '1715524865759_1713019963759', 'idComment': None, 'type': 'FILE'}

# print(insert_or_delete_like(eval))
# evaluation_query = {'_id': evaluationEntity['idFile'], "likes": {"$elemMatch": {"idUser": evaluationEntity['idUser']}}}
# evaluation_query = {"likes": {"$elemMatch": {"idUser": ['1713019963759']}}} 
# existing_evaluation = file_col.find_one(evaluation_query)
# print(existing_evaluation)

def is_collection_exist(name):
    return name in myDb.list_collection_names()
# print(is_collection_exist('notify_com'))

# cmt = notify_col.find_one({'idUser': '1713019963759', 'idFile': '1713019963759_1714189620474', 'idCommentOwner': '1713019963759', 'type': 'LIKE_CMT'}, {'_id':1})
# print(cmt)

        # evaluation_query = {"_id": evaluationEntity['idFile'],
        #         "comments._id": evaluationEntity['idComment'],
        #         "comments.likes": {"$elemMatch": {"idUser": evaluationEntity['idUser']}
        #         }}

# , 
#                       "likes": {"$elemMatch": {"idUser": "1713019963759"}}

# mquery = {"_id": "1713019963759_1714189585546", 
#          "comments": {"$elemMatch": {"_id": "1714290521831_1713019963759", 
#                                      "likes": {"$elemMatch": {"idUser": "1713019963759"}}}}}
# result = file_col.find_one(mquery)
# print(result['comments'])
        
        

# query = {"_id": "1713019963759_1714189585546", "comments._id": "1714233396941_1713019963759"}
# update_action = { "$push": { "comments.$.likes": { "idUser": "456", "userName": "exampleUser" } } }
# file_col.update_one(query, update_action)
        

# query = {"_id": "1713019963759_1714189585546", "comments._id": "1714233396941_1713019963759"}
# update_action = { "$pull": {"comments.$.likes": {"idUser": "456"}} }
# file_col.update_one(query, update_action)



# get_file_by_id_user("1713019963759")

# get_file_to_execute()
        

# username = user_col.find_one({'_id': '1713019909558'}, {'userName': 1})['userName']
# print(username)
        
# fileTitle = file_col.find_one({'_id': '1713019963759_1714189585546'}, {'title': 1, 'idUser': 1})
# print(fileTitle)
        
# def socket_send_msg(notify):
#     idUser = notify['idUser']
#     idFile = notify['idFile']
#     idCommentOwner = notify['idCommentOwner']
#     type = notify['type']

#     userName = user_col.find_one({'_id': idUser}, {'userName': 1})['userName']
#     file = file_col.find_one({'_id': idFile}, {'idUser': 1})
#     idSecondUser = file['idUser']
#     secondUserName = user_col.find_one({'_id': idSecondUser}, {'userName': 1})['userName']

#     match type:
#         case enum_class.notify_type.NEW_FILE.name:
#             roomName = f'follow_{idUser}'
#             msg = f'{userName} uploaded a file'
#         case enum_class.notify_type.LIKE_FILE.name:
#             roomName = f'follow_{idUser}'
#             if userName == secondUserName:
#                 msg = None
#             else:
#                 msg = f'{userName} has liked {secondUserName}\'s file'
#         case enum_class.notify_type.COMMENT.name:
#             roomName = f'follow_{idUser}'
#             if userName == secondUserName:
#                 msg = None
#             else:
#                 msg = f'{userName} comment about {secondUserName}\'s file'
#         case enum_class.notify_type.LIKE_CMT.name:
#             roomName = idCommentOwner
#             msg = f'{userName} liked your comment'
#         case enum_class.notify_type.REPLY.name:
#             roomName = idCommentOwner
#             msg = f'{userName} reply your comment'

#     if msg is not None:
#         print(f'msg: {msg}, room name: {roomName}')


# socket_send_msg(notify = {
#         '_id': 'id',
#         'idUser': '1713019963759',
#         'idFile': '1713019963759_1714189585546',
#         # 'idCommentOwner': idCommentOwner, 
#         'idCommentOwner': None, 
#         'type': enum_class.notify_type.COMMENT.name,  
#     })
        

# cmt = notify_col.find_one({'idUser': "1713019963759", 'idFile': "1713019963759_1714189585546", 'idCommentOwner': '1713019963759', 'type': enum_class.notify_type.LIKE_CMT.name}, {'_id':1})['_id']
# print(cmt)

# notify = notify_col.find_one({'idUser': '1', 'idFile': '1713019963759_1715523648366', 'idCommentOwner': None, 'type': 'NEW_FILE'}, {'_id':1})
# print(notify)