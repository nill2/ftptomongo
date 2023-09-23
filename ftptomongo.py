import os
import tempfile
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from config import FTP_ROOT, FTP_PORT, MONGO_HOST, MONGO_PORT, MONGO_DB, MONGO_COLLECTION


# FTP server configuration
FTP_ROOT = "/path/to/ftp/root"  # Change this to your desired FTP root folder
FTP_PORT = 21

# MongoDB configuration
MONGO_HOST = "localhost"  # Change this to your MongoDB server's address
MONGO_PORT = 27017
MONGO_DB = "ftp_files"
MONGO_COLLECTION = "uploaded_files"

def connect_to_mongodb():
    try:
        client = MongoClient(MONGO_HOST, MONGO_PORT)
        db = client[MONGO_DB]
        collection = db[MONGO_COLLECTION]
        return collection
    except ConnectionFailure as e:
        print(f"Failed to connect to MongoDB: {e}")
        return None

class MyHandler(FTPHandler):
    def on_file_received(self, file_path):
        # Upload the received file to MongoDB
        collection = connect_to_mongodb()
        if collection:
            with open(file_path, "rb") as file:
                file_data = file.read()
                collection.insert_one({"filename": os.path.basename(file_path), "data": file_data})
                print(f"Uploaded {os.path.basename(file_path)} to MongoDB")

def run_ftp_server():
    authorizer = DummyAuthorizer()
    authorizer.add_user("user", "password", FTP_ROOT, perm="elradfmw")
    
    handler = MyHandler
    handler.authorizer = authorizer
    
    server = FTPServer(("0.0.0.0", FTP_PORT), handler)
    server.serve_forever()

if __name__ == "__main__":
    if not os.path.exists(FTP_ROOT):
        os.makedirs(FTP_ROOT)
    
    try:
        run_ftp_server()
    except KeyboardInterrupt:
        print("FTP server stopped.")
