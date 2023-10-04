'''
This is a set of unit tests that will be used to test the FTP server.
'''
import os
import sys
from datetime import datetime, timedelta
import pytest

if "IS_TEST" not in os.environ:
    os.environ['IS_TEST'] = "local"

# Get the current directory of the test script
current_directory = os.path.dirname(os.path.abspath(__file__))
config_directory = os.path.join(current_directory, '..')
sys.path.append(config_directory)

# Import modules from the application
from config import ERROR_LVL  # noqa  # pylint: disable=wrong-import-position
from config import  MONGO_DB # pylint: disable=wrong-import-position  # noqa
from ftptomongo import connect_to_mongodb, delete_expired_data   # noqa   # pylint: disable=wrong-import-position


@pytest.fixture
def cleanup_testdb(request):  # pylint: disable=redefined-outer-name
    '''
    delete test data in MongoDB documents after testing
    '''
    # Define a cleanup function
    def cleanup_testdb_documents():
        # Connect to MongoDB
        collection = connect_to_mongodb()
        # Delete all documents with filename == 'test_file.txt'
        collection.delete_many({'filename': 'test_file.txt'})
    # Register the cleanup function to be called after the test
    request.addfinalizer(cleanup_testdb_documents)

def test_returns_number_of_documents_deleted(cleanup_testdb):  # pylint: disable=unused-argument,redefined-outer-name # noqa
    '''
    test the delete_expired_data function
    '''
    # Create a mock collection
    assert MONGO_DB == "nill-test"
    if ERROR_LVL == 'debug':
        print('test_connect_to_mongodb')
    collection = connect_to_mongodb()
    print("collection "+str(collection))
    assert collection is not None

    # Set the expiration period to 30 days
    expiration_period_days = 30

    # Set the current date to 2022-01-01
    current_date = datetime.utcnow()

    # Set the expiration date to 2021-12-02 (30 days before the current date)
    expiration_date = datetime.utcnow() - timedelta(days=expiration_period_days)

    # Create a mock document that is older than the expiration date
    old_document = {"date": expiration_date, "filename": "test_file.txt"}

    # Create a mock document that is not older than the expiration date
    recent_document = {"date": current_date, "filename": "test_file.txt"}

    # Add docs to collection
    collection.insert_one(old_document)
    collection.insert_one(recent_document)

    # Call the delete_expired_data function
    deleted_count = delete_expired_data(collection, "date", expiration_period_days)

    # Assert that the number of deleted documents is correct
    assert deleted_count == 1


def test_connect_to_mongodb():
    '''
    test the connect_to_mongodb function
    check if collection is not None
    '''
    if ERROR_LVL == 'debug':
        print('test_connect_to_mongodb')
    collection = connect_to_mongodb()
    assert collection is not None


if __name__ == "__main__":
    pytest.main(["-v", "tests/test_unit.py"])
