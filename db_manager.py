import pymongo
from pymongo.errors import DuplicateKeyError

myClient = pymongo.MongoClient("mongodb://localhost:27017/")

myDb = myClient["my_datn_db"]

user_col = myDb['user_col']
file_col = myDb['file_col']

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





# get_file_by_id_user("1713019963759")

# get_file_to_execute()