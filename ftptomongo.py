"""Run an FTP server that uploads files to a MongoDB database."""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional
import requests  # type: ignore
import boto3
from botocore.exceptions import ClientError
from pyftpdlib.servers import FTPServer
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from pymongo.collection import Collection
from config import (
    FTP_USER,
    FTP_ROOT,
    FTP_PORT,
    MONGO_HOST,
    MONGO_PORT,
    MONGO_DB,
    MONGO_COLLECTION,
    FTP_PASSWORD,
    HOURS_KEEP,
    ERROR_LVL,
    FTP_HOST,
    FTP_PASSIVE_PORT_FROM,
    FTP_PASSIVE_PORT_TO,
    AWS_ACCESS_KEY,
    AWS_SECRET_KEY,
    AWS_BUCKET_NAME,
    USE_S3,
)

# Configure the logger (optional)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def get_external_ip() -> str | None:
    """
    Identify the external IP address.

    Returns:
        str | None: External IP address if successful, otherwise None.
    """
    try:
        response = None
        response = requests.get("https://api.ipify.org", timeout=10)
        if response.status_code == 200:
            return str(response.text)
        logger.error(f"Failed to retrieve external IP: {response.status_code}")
    except requests.RequestException as exception:
        logger.error(f"An error occurred while fetching external IP: {exception}")
    return None


def connect_to_mongodb() -> Optional[MongoClient]:
    """
    Connect to a MongoDB instance and return a collection object.

    Returns:
        Optional[MongoClient]: A MongoDB collection object if successful, otherwise None.
    """
    try:
        client = MongoClient(MONGO_HOST, MONGO_PORT)
        my_mongo_db = client[MONGO_DB]
        collection = my_mongo_db[MONGO_COLLECTION]
        if ERROR_LVL == "debug":
            logger.info(f"Connected to MongoDB: {MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}/{MONGO_COLLECTION}")
        return collection
    except ConnectionFailure as connection_error:
        logger.error("Failed to connect to MongoDB: %s", connection_error)
        return None


def delete_expired_data(collection: Collection, field_name: str, expiration_period_h: int) -> int:
    """
    Delete documents from the collection that are older than a specified expiration period.

    Args:
        collection (pymongo.collection.Collection): The MongoDB collection to delete documents from.
        field_name (str): The name of the field that stores the expiration date in the documents.
        expiration_period_days (int): The number of days that define the expiration period.

    Returns:
        int: The number of documents deleted.
    """
    # Calculate the expiration date as a datetime object
    expiration_date = datetime.utcnow() - timedelta(hours=expiration_period_h)
    logger.info(f"expiration_hour: {expiration_period_h}")
    logger.info(f"Deleting expired before: {expiration_date}")
    # Create a filter to find documents older than the expiration date
    del_filter = {field_name: {"$lt": expiration_date}}
    logger.info(f"deletion filter: {del_filter}")

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


def delete_s3_file(s3_file_url: str) -> None:
    """
    Delete a file from an S3 bucket based on its URL.

    Args:
        s3_file_url (str): The URL of the file in the S3 bucket.
    """
    try:
        bucket_name = s3_file_url.split("//")[1].split(".")[0]
        s3_key = s3_file_url.split(f"{bucket_name}.s3.amazonaws.com/")[1]
        s3_client = boto3.client("s3", aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)
        s3_client.delete_object(Bucket=bucket_name, Key=s3_key)
        logger.info(f"Deleted file from S3: {s3_file_url}")
    except Exception as exception:
        logger.error(f"Error deleting file from S3: {exception}")


class MyHandler(FTPHandler):  # type: ignore[misc]
    """
    Create a custom FTPHandler for handling FTP server operations.

    This class extends FTPHandler to handle custom operations like uploading files to MongoDB.
    """

    def on_file_received(self, received_file: str) -> None:  # pylint: disable=arguments-renamed # noqa
        """
        Process a file_received event will save it to the database(MongoDB).

        in future to a s3 with a link stored in the MongoDB
        """
        s3_file_url = ""
        if USE_S3 == "true":
            try:
                # Upload the received file to AWS S3
                s3_client = boto3.client("s3", aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)
                # AWS_bucket_name = 'nill-home-photos'
                s3_key = os.path.basename(received_file)
                s3_client.upload_file(received_file, AWS_BUCKET_NAME, s3_key)

                # Get the S3 file URL
                s3_file_url = f"https://{AWS_BUCKET_NAME}.s3.amazonaws.com/{s3_key}"
                logger.info(f"Uploading file to S3: {s3_file_url}")
            except ClientError as exception:
                logger.error(f"Error uploading file to S3: {exception}")
        else:
            logger.info("Storing to Mongo only")

        # Upload the received file to MongoDB
        collection = connect_to_mongodb()
        logger.info(f"Connected to MongoDB: {MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}/{MONGO_COLLECTION}")
        if collection is not None:  # Check if collection is not None
            try:
                with open(received_file, "rb") as file:
                    timestamp = datetime.utcnow().timestamp()
                    file_data = file.read()  # as we are using S3 it's not needed
                    # for e2e tests
                    # if file_data != 'Test content':
                    if USE_S3 == "true":
                        file_data = b""
                        logger.info("Setting file_data as empty string")
                    collection.insert_one(
                        {
                            "filename": os.path.basename(received_file),
                            "data": file_data,
                            "s3_file_url": s3_file_url,
                            "size": os.path.getsize(received_file),
                            "date": timestamp,
                            "bsonTime": datetime.now(),
                        }
                    )
                    if ERROR_LVL == "debug":
                        logger.info(f"Uploaded {os.path.basename(received_file)} to MongoDB")
            except FileNotFoundError:
                # Handle the case where the file is not found
                print("Error: The specified file was not found.")
            except PermissionError:
                # Handle the case where the script doesn't have permission to open the file
                print("Error: Permission denied to open the file.")
            except Exception as exception:
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


def run_ftp_server() -> None:
    """
    Start and run the FTP server.

    Returns:
        None
    """
    authorizer = DummyAuthorizer()
    authorizer.add_user(FTP_USER, FTP_PASSWORD, FTP_ROOT, perm="elradfmw")

    handler = MyHandler
    handler.authorizer = authorizer
    handler.passive_ports = range(FTP_PASSIVE_PORT_FROM, FTP_PASSIVE_PORT_TO)
    external_ip = get_external_ip()
    if external_ip and MONGO_DB != "nill-test":
        handler.masquerade_address = external_ip

    server = FTPServer((FTP_HOST, FTP_PORT), handler)
    server.serve_forever()
