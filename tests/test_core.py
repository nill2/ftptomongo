import os
import time
import pytest
from tempfile import TemporaryDirectory
import subprocess
from ftplib import FTP
import sys

# Get the current directory of the test script
current_directory = os.path.dirname(os.path.abspath(__file__))

# Add the directory containing config.py to sys.path
config_directory = os.path.join(current_directory, '..')
print(config_directory)
sys.path.append(config_directory)

from config import FTP_ROOT, FTP_PORT, MONGO_HOST, MONGO_PORT, MONGO_DB, MONGO_COLLECTION, FTP_USER, FTP_PASSWORD, FTP_HOST, ERROR_LVL
from ftptomongo import connect_to_mongodb, MyHandler, run_ftp_server    
import sys

# Get the current directory
current_directory = os.path.dirname(os.path.realpath(__file__))

# Append the current directory to sys.path
sys.path.append(current_directory)

# FTP server configuration for testing
FTP_PORT = 2121

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
'''
@pytest.fixture
def ftp_server(temp_ftp_root):
    run_ftp_server()
    yield
    # Teardown: Stop the FTP server
'''
#set up FTP server for testing  
SERVER_COMMAND = "python ftptomongo.py"
FTP_HOST = os.getenv("FTP_HOST", "localhost")
FTP_PORT = 2121  # Port used for testing

#set up FTP test
DESTINATION_DIR = "/ftp"
    
@pytest.fixture(scope="module", autouse=True)
def start_ftp_test_server():
    # Start the FTP server as a subprocess
    process = subprocess.Popen(SERVER_COMMAND, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Wait for the server to start (you may need to adjust the timing)
    time.sleep(45)

    # Yield control to the test
    yield

    # Stop the server when the tests are done
    process.terminate()
    process.wait()    
    

def test_connect_to_mongodb():
    if ERROR_LVL == 'debug':
        print('test_connect_to_mongodb')
    collection = connect_to_mongodb()
    assert collection is not None

@pytest.mark.timeout(90)   # Adjust the timeout
@pytest.mark.skip(reason="Test not implemented yet")
def test_ftp_upload_and_download(): #(ftp_server, temp_ftp_root):
    # Set a timeout value (in seconds)
    timeout = 5  # You can adjust this value as needed
    test_data = 'Test content'
    
    if ERROR_LVL=="debug" :
        print('test_ftp_upload_and_download')
   
    #test upload and download
    ftp = FTP()
    ftp.connect(FTP_HOST, FTP_PORT)  # Set the timeout when connecting
    ftp.login(user=FTP_USER, passwd=FTP_PASSWORD)
    if ERROR_LVL=="debug" :
        print('Connected to FTP server')
    # Simulate file upload
    with open('test_file.txt', 'w') as file:
        file.write(test_data)
     # Specify the destination directory and file name
    dest_path = f"{DESTINATION_DIR}/test_file.txt"
    with open('test_file.txt', 'rb') as file:
        ftp.storbinary(f'STOR {dest_path}', file)
    if ERROR_LVL=="debug" :
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
