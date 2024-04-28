
query = {"_id": "1713019963759_1714189620474", "comments._id": "1714234870667_1713019963759"}
update_action = { "$push": { "comments.$.likes": { "idUser": "456", "userName": "exampleUser" } } }
file_col.update_one(query, update_action)