import os
import time
import pytest
from tempfile import TemporaryDirectory
from ftplib import FTP
import sys

# Get the current directory of the test script
current_directory = os.path.dirname(os.path.abspath(__file__))

# Add the directory containing config.py to sys.path
config_directory = os.path.join(current_directory, '..')
print(config_directory)
sys.path.append(config_directory)

from config import FTP_ROOT, FTP_PORT, MONGO_HOST, MONGO_PORT, MONGO_DB, MONGO_COLLECTION, FTP_USER, FTP_PASSWORD
from ftptomongo import connect_to_mongodb, MyHandler, run_ftp_server    
import sys

# Get the current directory
current_directory = os.path.dirname(os.path.realpath(__file__))

# Append the current directory to sys.path
sys.path.append(current_directory)

# FTP server configuration for testing
#FTP_ROOT = "/"
#FTP_PORT = 21  # Use a different port for testing

@pytest.fixture
def temp_ftp_root():
    with TemporaryDirectory() as temp_dir:
        yield temp_dir

# Define a fixture for the cleanup function
@pytest.fixture
def cleanup_files(request):
    # This function will be called after the test has completed
    def finalizer():
        # Clean up the temporary files
        files_to_delete = ['test_file.txt', 'downloaded_file.txt']
        for file in files_to_delete:
            if os.path.exists(file):
                os.remove(file)

@pytest.fixture
def ftp_server(temp_ftp_root):
    run_ftp_server()
    yield
    # Teardown: Stop the FTP server

def test_connect_to_mongodb():
    print('test_connect_to_mongodb')
    collection = connect_to_mongodb()
    assert collection is not None

@pytest.mark.timeout(10)  # Adjust the timeout value as needed
def test_ftp_upload_and_download(): #(ftp_server, temp_ftp_root):
    # Set a timeout value (in seconds)
    timeout = 5  # You can adjust this value as needed
    test_data = 'Test content'
    
    print('test_ftp_upload_and_download')
    #  test code  to perform FTP upload and download
    
    ftp = FTP()
    ftp.connect('localhost', FTP_PORT)  # Set the timeout when connecting
    ftp.login(user=FTP_USER, passwd=FTP_PASSWORD)
    print('Connected to FTP server')
    # Simulate file upload
    with open('test_file.txt', 'w') as file:
        file.write(test_data)
    with open('test_file.txt', 'rb') as file:
        ftp.storbinary('STOR test_file.txt', file)
    print('file uploaded to FTP server')   
    
    
    with open('test_file.txt', 'rb') as file:
        data = file.read()
    assert data is not None
    
    # Convert the bytes data to a string
    data_str = data.decode('utf-8')
    assert data_str == test_data
     # Connect to MongoDB
    collection = connect_to_mongodb()
    
    assert collection is not None
    
    start_time = time.time()
    while time.time() - start_time < 5:
        retrieved_file = collection.find_one({'filename': 'test_file.txt'})
        if retrieved_file:
            assert retrieved_file['data'] == data
            collection.delete_many({'filename': 'test_file.txt'})
            break  # File found, exit the loop
        time.sleep(1)  # Wait for 1 second before the next attempt

    else:
        pytest.fail("Timeout: File was not found in MongoDB within the specified timeout")

   
# Define a fixture to clean up MongoDB documents
@pytest.fixture
def cleanup_mongodb(request):
    # Define a cleanup function
    def cleanup_mongodb_documents():
             # Connect to MongoDB
        collection = connect_to_mongodb()
        # Delete all documents with filename == 'test_file.txt'
        collection.delete_many({'filename': 'test_file.txt'})
    # Register the cleanup function to be called after the test
    request.addfinalizer(cleanup_mongodb_documents)
   
   
if __name__ == "__main__":
    pytest.main(["-v", "tests/tests.py"])