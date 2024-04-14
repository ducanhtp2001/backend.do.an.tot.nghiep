import pymongo
from pymongo.errors import DuplicateKeyError

myClient = pymongo.MongoClient("mongodb://localhost:27017/")

myDb = myClient["my_datn_db"]

user_col = myDb['user_col']
file_col = myDb['file_col']

def get_file_to_execute():
    print('on fun')
    query = {'state': False}
    cursor = file_col.find_one(query)
    if cursor:
        print(cursor)
        return cursor



# get_file_to_execute()