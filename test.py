from pymongo import MongoClient
client = MongoClient("mongodb://localhost:27017/?replicaSet=rs0")
change_stream = client["your_db_name"]["events"].watch()
for change in change_stream:
    print("Change detected: ", change)
