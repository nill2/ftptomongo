import os
import socket
import tempfile
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pymongo.server_api import ServerApi
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from config import FTP_ROOT, FTP_PORT, MONGO_HOST, MONGO_PORT, MONGO_DB, MONGO_COLLECTION, FTP_USER, FTP_PASSWORD, ERROR_LVL, FTP_HOST
from pyftpdlib.servers import FTPServer
from datetime import datetime, timedelta
import time
import bson


def connect_to_mongodb():
    try:
        client = MongoClient(MONGO_HOST, MONGO_PORT)
        db = client[MONGO_DB]
        collection = db[MONGO_COLLECTION]
        if ERROR_LVL=="debug" :
            print(f"Connected to MongoDB at {MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}/{MONGO_COLLECTION}")       
        return collection
    except ConnectionFailure as e:
        print(f"Failed to connect to MongoDB: {e}")
        return None

def db_cleanup(collection):
        if collection is not None:  # Check if collection is not None
            collection.delete_many({})
            if ERROR_LVL=="debug" :
                print(f"Deleted all documents from MongoDB")
        else:
            print("Failed to connect to MongoDB. File not uploaded.")

def delete_expired_data(collection, field_name, expiration_period_days):
    # Calculate the expiration date as a datetime object
    expiration_date = datetime.utcnow() - timedelta(days=expiration_period_days)
    
    # Create a filter to find documents older than the expiration date
    filter = {field_name: {"$lt": expiration_date}}
    
    # Delete the expired documents and get the count of deleted documents
    result = collection.delete_many(filter)
    
    return result.deleted_count


class MyHandler(FTPHandler):
    def on_file_received(self, file_path):
        # Upload the received file to MongoDB
        collection = connect_to_mongodb()
        if collection is not None:  # Check if collection is not None
            with open(file_path, "rb") as file:
                timestamp = datetime.now().timestamp()
                file_data = file.read()
                bsonTime = bson.Int64(timestamp * 1000)
                collection.insert_one({"filename": os.path.basename(file_path), "data": file_data, "size": os.path.getsize(file_path), "date": timestamp, "bsonTime": datetime.now()})
                if ERROR_LVL=="debug" :
                    print(f"Uploaded {os.path.basename(file_path)} to MongoDB")
            
            # Clean up the expired documents in the database
            expired_docs_deleted = delete_expired_data(collection, "date", 365)
            print(f"Deleted " + expired_docs_deleted + " documents")
                           
            # Delete the file from the FTP server
            file_to_del = os.path.join(FTP_ROOT, file_path)
            os.remove(file_to_del)
            if ERROR_LVL=="debug" :
                print(f"deleted {os.path.basename(file_path)} from the FTP server")
        else:
            print("Failed to connect to MongoDB. File not uploaded.")
            
    

def run_ftp_server():
    authorizer = DummyAuthorizer()
    authorizer.add_user(FTP_USER, FTP_PASSWORD, FTP_ROOT, perm="elradfmw")
    
    handler = MyHandler
    handler.authorizer = authorizer
    
    # Explicitly bind the socket to the desired host and port
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((FTP_HOST, FTP_PORT))  # Adjust host and port as needed
    server_socket.listen(5)  # Start listening for incoming connections
    
    server = FTPServer(server_socket, handler)
    server.serve_forever()

if __name__ == "__main__":
    if not os.path.exists(FTP_ROOT):
        os.makedirs(FTP_ROOT)
    
    try:
        run_ftp_server()
    except KeyboardInterrupt:
        print("FTP server stopped.")