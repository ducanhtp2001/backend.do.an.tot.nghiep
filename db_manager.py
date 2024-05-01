from flask import jsonify
import pymongo
from pymongo.errors import DuplicateKeyError
import enum_class

myClient = pymongo.MongoClient("mongodb://localhost:27017/")

myDb = myClient["my_datn_db"]

user_col = myDb['user_col']
file_col = myDb['file_col']
# comment_col = myDb['file_col']
# like_col = myDb['file_col']

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

# print(get_user_sub_by_id('1713019909558'))

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
    print('============= delete file id:', fileId)
    if result.deleted_count == 1:
        return True
    else: 
        return False
    
def change_state(fileId):  
    result = file_col.find_one_and_update({"_id": fileId}, {"$set": {"isPublic": {"$not": "$isPublic"}}})
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
        evaluation_query = {"likes": {"$elemMatch": {"idUser": evaluationEntity['idUser']}}} 

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