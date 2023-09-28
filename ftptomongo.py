"""
This script implements an FTP server that uploads files to a MongoDB database.
"""

import os
import socket
from datetime import datetime, timedelta
from pyftpdlib.servers import FTPServer
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from config import FTP_ROOT, FTP_PORT, MONGO_HOST, MONGO_PORT, MONGO_DB, MONGO_COLLECTION
from config import FTP_USER, FTP_PASSWORD, ERROR_LVL, FTP_HOST


def connect_to_mongodb():
    """
    Connects to a MongoDB instance and returns a collection object.

    Returns:
        pymongo.collection.Collection: A MongoDB collection object.
            Returns None if the connection fails.
    """
    try:
        client = MongoClient(MONGO_HOST, MONGO_PORT)
        my_mongo_db = client[MONGO_DB]
        collection = my_mongo_db[MONGO_COLLECTION]
        if ERROR_LVL=="debug" :
            print(f"Connected to MongoDB: {MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}/{MONGO_COLLECTION}")
        return collection
    except ConnectionFailure as collection_error:
        print(f"Failed to connect to MongoDB: {collection_error}")
        return None

def db_cleanup(collection):
    """
    Cleans up the MongoDB collection by deleting all documents.

    Args:
        collection (pymongo.collection.Collection): The MongoDB collection to clean up.

    Returns:
        None
    """
    if collection is not None:  # Check if collection is not None
        collection.delete_many({})
        if ERROR_LVL=="debug" :
            print("Deleted all documents from MongoDB")
    else:
        print("Failed to connect to MongoDB. File not uploaded.")

def delete_expired_data(collection, field_name, expiration_period_days):
    """
    Deletes documents from the collection that are older than a specified expiration period.

    Args:
        collection (pymongo.collection.Collection): The MongoDB collection to delete documents from.
        field_name (str): The name of the field that stores the expiration date in the documents.
        expiration_period_days (int): The number of days that define the expiration period.

    Returns:
        int: The number of documents deleted.
    """
    # Calculate the expiration date as a datetime object
    expiration_date = datetime.utcnow() - timedelta(days=expiration_period_days)
    # Create a filter to find documents older than the expiration date
    del_filter = {field_name: {"$lt": expiration_date}}
    # Delete the expired documents and get the count of deleted documents
    result = collection.delete_many(del_filter)
    return result.deleted_count


class MyHandler(FTPHandler):
    """
    Custom FTPHandler for handling FTP server operations.

    This class extends FTPHandler to provide custom functionality for handling FTP server
    operations such as uploading files to MongoDB and cleaning up expired documents.

    Attributes:
        authorizer: The authorizer for user authentication.
    """
    def on_file_received(self, received_file): # pylint: disable=arguments-renamed
        # Upload the received file to MongoDB
        collection = connect_to_mongodb()
        if collection is not None:  # Check if collection is not None
            with open(received_file, "rb") as file:
                timestamp = datetime.now().timestamp()
                file_data = file.read()
                collection.insert_one({
                "filename": os.path.basename(received_file),
                "data": file_data,
                "size": os.path.getsize(received_file),
                "date": timestamp,
                "bsonTime": datetime.now()
                })
                if ERROR_LVL=="debug" :
                    print("Uploaded"+os.path.basename(received_file)+"to MongoDB")

            # Clean up the expired documents in the database
            expired_docs_deleted = delete_expired_data(collection, "date", 365)
            print("Deleted " + str(expired_docs_deleted) + " documents")
            # Delete the file from the FTP server
            file_to_del = os.path.join(FTP_ROOT, received_file)
            os.remove(file_to_del)
            if ERROR_LVL=="debug" :
                print(f"deleted {os.path.basename(received_file)} from the FTP server")
        else:
            print("Failed to connect to MongoDB. File not uploaded.")

def run_ftp_server():
    """
    Start and run the FTP server.

    This function starts the FTP server and listens for incoming connections.
    It performs the necessary setup and configuration for the server.

    Returns:
        None
    """
    authorizer = DummyAuthorizer()
    authorizer.add_user(FTP_USER, FTP_PASSWORD, FTP_ROOT, perm="elradfmw")

    print("My: Starting FTP server..." + FTP_ROOT+ "\n")

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
