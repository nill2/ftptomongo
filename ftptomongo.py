"""
This script implements an FTP server that uploads files to a MongoDB database.
"""

import os
import boto3
import logging
import requests
from datetime import datetime, timedelta
from botocore.exceptions import ClientError  # Import ClientError
from pyftpdlib.servers import FTPServer
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from config import FTP_USER, FTP_ROOT, FTP_PORT, MONGO_HOST, HOURS_KEEP  # pylint: disable=import-error
from config import MONGO_PORT, MONGO_DB, MONGO_COLLECTION, FTP_PASSWORD  # pylint: disable=import-error
from config import ERROR_LVL, FTP_HOST, FTP_PASSIVE_PORT_FROM, FTP_PASSIVE_PORT_TO  # pylint: disable=import-error
from config import AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_BUCKET_NAME, USE_S3  # pylint: disable=import-error


# Configure the logger (optional)
logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

# Define the logger
logger = logging.getLogger(__name__)


def get_external_ip():
    """
    Identify the external IP address
    Returns:
        string: external IP address
    """
    try:
        response = requests.get('https://api.ipify.org', timeout=10)
        if response.status_code == 200:
            return response.text
        else:
            print(f"Failed to retrieve external IP: {response.status_code}")
    except Exception as e:  # pylint: disable=all
        print(f"An error occurred: {e}")


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
        if ERROR_LVL == "debug":
            logger.info(
                f"Use MongoDB: {MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}/{MONGO_COLLECTION}"
                ) # noqa
        return collection
    except ConnectionFailure as connection_error:
        logger.error("Failed to connect to MongoDB: %s", connection_error)
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
        if ERROR_LVL == "debug":
            logger.info("Deleted all documents from MongoDB")
    else:
        logger.error("Failed to connect to MongoDB. File not uploaded.")


def delete_expired_data(collection, field_name, expiration_period_h):
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
    expiration_date = datetime.utcnow() - timedelta(hours=expiration_period_h)
    logger.info("expiration_hour: %s" % expiration_period_h)
    logger.info("Deleting expired before: %s" % expiration_date)
    # Create a filter to find documents older than the expiration date
    del_filter = {field_name: {"$lt": expiration_date}}
    logger.info("deletion filter: %s" % del_filter)

    # Delete the expired documents and get the count of deleted documents
    result = collection.find(del_filter)

    # Initialize counter for deleted documents
    deleted_count = 0

    for doc in result:
        # Check if the document has a non-empty "s3_file_url" field
        if doc.get("s3_file_url"):
            # Extract the S3 file URL from the document
            s3_file_url = doc["s3_file_url"]
            # Delete the file from the S3 bucket
            delete_s3_file(s3_file_url)

        # Delete the MongoDB document
        collection.delete_one({"_id": doc["_id"]})
        deleted_count += 1

    return deleted_count


def delete_s3_file(s3_file_url):
    """
    Deletes a file from an S3 bucket based on its URL.

    Args:
        s3_file_url (str): The URL of the file in the S3 bucket.
    """
    try:
        # Extract bucket name and key from the S3 file URL
        bucket_name = s3_file_url.split("//")[1].split(".")[0]
        s3_key = s3_file_url.split(bucket_name + ".s3.amazonaws.com/")[1]

        # Create an S3 client
        s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)

        # Delete the file from the S3 bucket
        s3.delete_object(Bucket=bucket_name, Key=s3_key)
        logger.info(f"Deleted file from S3: {s3_file_url}")
    except Exception as e:
        logger.error(f"Error deleting file from S3: {e}")


class MyHandler(FTPHandler):
    """
    Custom FTPHandler for handling FTP server operations.

    This class extends FTPHandler to provide custom functionality for handling FTP server
    operations such as uploading files to MongoDB and cleaning up expired documents.

    Attributes:
        authorizer: The authorizer for user authentication.
    """

    def on_file_received(self, received_file):  # pylint: disable=arguments-renamed # noqa
        """
        key function that on a file_received event will save it to the database(MongoDB)
        in future to a s3 with a link stored in the MongoDB
        """
        s3_file_url = ""
        if USE_S3 == "true":
            try:
                # Upload the received file to AWS S3
                s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)
                # AWS_bucket_name = 'nill-home-photos'
                s3_key = os.path.basename(received_file)
                s3.upload_file(received_file, AWS_BUCKET_NAME, s3_key)

                # Get the S3 file URL
                s3_file_url = f"https://{AWS_BUCKET_NAME}.s3.amazonaws.com/{s3_key}"
                logger.info(f"Uploading file to S3: {s3_file_url}")
            except ClientError as e:
                logger.error(f"Error uploading file to S3: {e}")
        else:
            logger.info("Storing to Mongo only")

        # Upload the received file to MongoDB
        collection = connect_to_mongodb()
        logger.info(
            f"Connected to MongoDB: {MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}/{MONGO_COLLECTION}"
            )
        if collection is not None:  # Check if collection is not None
            try:
                with open(received_file, "rb") as file:
                    timestamp = datetime.utcnow().timestamp()
                    file_data = file.read()  # as we are using S3 it's not needed
                    # for e2e tests
                    # if file_data != 'Test content':
                    if USE_S3 == "true":
                        file_data = ""
                        logger.info("Setting file_data as empty string")
                    collection.insert_one({
                                        "filename": os.path.basename(received_file),
                                        "data": file_data,
                                        "s3_file_url": s3_file_url,
                                        "size": os.path.getsize(received_file),
                                        "date": timestamp,
                                        "bsonTime": datetime.now()
                                        })
                    if ERROR_LVL == "debug":
                        logger.info(f"Uploaded {os.path.basename(received_file)} to MongoDB")
            except FileNotFoundError:
                # Handle the case where the file is not found
                print("Error: The specified file was not found.")
            except PermissionError:
                # Handle the case where the script doesn't have permission to open the file
                print("Error: Permission denied to open the file.")
            except Exception as exception:  # pylint: disable=W0718
                # Handle other types of exceptions
                print(f"An unexpected error occurred: {exception} ")

            # Clean up the expired documents in the database
            expired_docs_deleted = delete_expired_data(collection, "bsonTime", HOURS_KEEP)
            logger.info(f"Deleted {str(expired_docs_deleted)} documents")
            # Delete the file from the FTP server
            file_to_del = os.path.join(FTP_ROOT, received_file)
            os.unlink(file_to_del)
            if ERROR_LVL == "debug":
                logger.info(f"deleted {os.path.basename(received_file)} from the FTP server")
        else:
            logger.error("Failed to connect to MongoDB. File not uploaded.")


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

    logger.info(f"FTP server:{FTP_ROOT}"
                f"and ports {FTP_PASSIVE_PORT_FROM} - {FTP_PASSIVE_PORT_TO}")

    # Define the passive port range (e.g., 52000-60000)
    passive_ports = range(FTP_PASSIVE_PORT_FROM, FTP_PASSIVE_PORT_TO)

    handler = MyHandler
    handler.authorizer = authorizer
    handler.passive_ports = passive_ports
    external_ip = get_external_ip()
    if external_ip and MONGO_DB != "nill-test":
        print("External IP: {}".format(external_ip))
        handler.masquerade_address = external_ip

    # Explicitly bind the socket to the desired host and port
    # server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # server_socket.bind((FTP_HOST, FTP_PORT))  # Adjust host and port as needed
    # server_socket.listen(5)  # Start listening for incoming connections

    server = FTPServer((FTP_HOST, FTP_PORT), handler)  # server_socket
    server.serve_forever()
