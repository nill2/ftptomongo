"""Use a set of fixtures to test the FTP server."""

import os
import sys
import time
import subprocess
import logging
from tempfile import TemporaryDirectory
from ftplib import FTP
import psutil
import pytest
import boto3
from pytest import FixtureRequest
from botocore.exceptions import ClientError
from typing import Generator
from pymongo.collection import Collection

# set up FTP server for testing
SERVER_COMMAND = "python ftptomongo_main.py"

# Configure the logger (optional)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# set up  test environment variables
DESTINATION_DIR = "."
CONNECT_TIMEOUT = 35  # connect to FTP server timeout in seconds
if "IS_TEST" not in os.environ:
    os.environ["IS_TEST"] = "local"

# Get the current directory of the test script
current_directory = os.path.dirname(os.path.abspath(__file__))
config_directory = os.path.join(current_directory, "..")
print(config_directory)
sys.path.append(config_directory)

from config import (  # noqa
    FTP_PORT,
    FTP_USER,
    FTP_PASSWORD,
    ERROR_LVL,
)  # pylint: disable=all    # noqa
from config import (  # noqa
    AWS_ACCESS_KEY,
    AWS_SECRET_KEY,
)  # pylint: disable=all # noqa
from ftptomongo import connect_to_mongodb, delete_s3_file  # pylint: disable=all  # noqa

# Get the current directory
current_directory = os.path.dirname(os.path.realpath(__file__))
FTP_HOST = "localhost"
# Append the current directory to sys.path
sys.path.append(current_directory)


def check_file_exists(s3_file_url: str) -> bool:
    """
    Check if a file exists in an S3 bucket.

    Args:
        bucket_name (str): The name of the S3 bucket.
        file_key (str): The key (path) of the file in the bucket.

    Returns:
        bool: True if the file exists, False otherwise.
    """
    try:
        # Extract bucket name and key from the S3 file URL
        bucket_name = s3_file_url.split("//")[1].split(".")[0]
        s3_key = s3_file_url.split(bucket_name + ".s3.amazonaws.com/")[1]

        # Create an S3 client
        s3 = boto3.client("s3", aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)

        # Download the file from the S3 bucket to a temporary file
        local_temp_file_path = "temp_image.jpg"
        s3.download_file(bucket_name, s3_key, local_temp_file_path)
        return True
    except ClientError as e:
        # Catch the error if the file does not exist
        if e.response["Error"]["Code"] == "404":
            return False
        else:
            # Handle other errors
            print(f"Error: {e}")
            return False


@pytest.fixture
def temp_ftp_root() -> Generator[str, None, None]:
    """Create a temporary directory for the FTP server."""
    with TemporaryDirectory() as temp_dir:
        yield temp_dir


# Define a fixture for the cleanup function
@pytest.fixture
def cleanup_files(request: FixtureRequest) -> None:  # pylint: disable=redefined-outer-name
    """Clean up the temporary files after testing."""

    def cleanup_files_local() -> None:
        # This function will be called after the test has completed
        files_to_delete = ["test_file.txt", "downloaded_file.txt"]
        for file in files_to_delete:
            if os.path.exists(file):
                os.remove(file)

    request.addfinalizer(cleanup_files_local)


def is_ftp_server_running() -> bool:
    """Check if the FTP server is running."""
    for process in psutil.process_iter(attrs=["name"]):
        if process.info["name"] == "python" and "__main__.py" in process.cmdline():
            return True
    return False


# @pytest.fixture(scope="module", autouse=True)
def start_ftp_test_server() -> Generator[None, None, None]:
    """Start the FTP server as a subprocess to check the fuctionality of the application."""
    if is_ftp_server_running():
        print("FTP server is already running")
        logger.info("FTP server is already running")
        yield
        # FTP server is already running, no need to start a new instance
    else:
        # Start the FTP server as a subprocess
        try:
            print("FTP is not running. Starting a new one")
            logger.info("FTP is not running. Starting a new one")
            with subprocess.Popen(
                SERVER_COMMAND,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            ) as process:

                # Wait for the server to start (you may need to adjust the timing)
                time.sleep(10)

                # Yield control to the test
                yield

                # Stop the server when the tests are done
                logger.info("stopping FTP server")
                process.terminate()
                process.wait()
        except Exception as ftp_exception:  # pylint: disable=broad-exception-caught
            print(f"FTP server can be launched as: {ftp_exception}")


# Define a fixture to clean up MongoDB documents
@pytest.fixture
def cleanup_mongodb(request: FixtureRequest) -> None:  # pylint: disable=redefined-outer-name
    """Delete test data in MongoDB documents after testing."""

    # Define a cleanup function
    def cleanup_mongodb_documents() -> None:
        # Connect to MongoDB
        collection: Collection = connect_to_mongodb()
        # Delete all documents with filename == 'test_file.txt'
        collection.delete_many({"filename": "test_file.txt"})

    # Register the cleanup function to be called after the test
    request.addfinalizer(cleanup_mongodb_documents)


# Key e2e tests
@pytest.mark.timeout(CONNECT_TIMEOUT)  # Adjust the timeout
# @pytest.mark.skip(reason="Skipping this test until fixed")
def test_ftp_e2e(
    cleanup_files: None, cleanup_mongodb: None
) -> None:  # pylint: disable=unused-argument,redefined-outer-name # noqa
    """Test the application fucntionality.

    Checks file upload and transfer to mongodb functionality
    """
    # Set a timeout value (in seconds)
    timeout = 5  # You can adjust this value as needed
    test_data = "Test content"
    
    # start_ftp_test_server() #  run it separately for testing

    if ERROR_LVL == "debug":
        print("test_ftp_upload_and_download")

    # test upload and download
    start_time = time.time()
    ftp_tries = 0
    ftp = FTP()
    while time.time() - start_time < CONNECT_TIMEOUT:
        try:
            ftp_tries = ftp_tries + 1
            ftp.connect(FTP_HOST, FTP_PORT, timeout)
            ftp.login(user=FTP_USER, passwd=FTP_PASSWORD)
            break
        except Exception as ftp_exception:  # pylint: disable=broad-exception-caught
            print(f"Retrying ({ftp_tries}) after error: {ftp_exception}")

    if ERROR_LVL == "debug":
        print("Connected to FTP server")
    # Simulate file upload
    with open("test_file.txt", "w", encoding="utf8") as file:
        file.write(test_data)
    # Specify the destination directory and file name
    dest_path = f"{DESTINATION_DIR}/test_file.txt"
    with open("test_file.txt", "rb") as file:
        try:
            ftp.storbinary(f"STOR {dest_path}", file)
            if ERROR_LVL == "debug":
                print("file uploaded to FTP server")
        except Exception as upload_exception:  # pylint: disable=broad-exception-caught
            print(f"Failed upload the file  : {upload_exception}")

    with open("test_file.txt", "rb") as file:
        data = file.read()
    assert data is not None

    # Convert the bytes data to a string
    data_str = data.decode("utf-8")
    assert data_str == test_data
    collection = connect_to_mongodb()

    assert collection is not None

    start_time = time.time()
    while time.time() - start_time < 7:
        retrieved_file = collection.find_one({"filename": "test_file.txt"})
        if retrieved_file:
            if retrieved_file.get("s3_file_url") and retrieved_file.get("s3_file_url") != "":
                file_name = retrieved_file.get("s3_file_url")
                assert check_file_exists(file_name)
                delete_s3_file(file_name)
            else:
                assert retrieved_file["data"] == data
            collection.delete_many({"filename": "test_file.txt"})
            break  # File found, exit the loop
        time.sleep(1)  # Wait for 1 second before the next attempt
    else:
        pytest.fail("Timeout: File was not found in MongoDB within the specified timeout")


if __name__ == "__main__":
    pytest.main(["-v", "tests/test_core.py"])
