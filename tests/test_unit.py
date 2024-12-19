"""This is a set of unit tests that will be used to test the FTP server."""

import os
import sys
from datetime import datetime, timedelta
import pytest
import logging
from pymongo.collection import Collection  # Import Collection type
from typing import Optional
from pytest import FixtureRequest

# Configure the logger (optional)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Define the logger
logger = logging.getLogger(__name__)

if "IS_TEST" not in os.environ:
    os.environ["IS_TEST"] = "local"

# Get the current directory of the test script
current_directory = os.path.dirname(os.path.abspath(__file__))
config_directory = os.path.join(current_directory, "..")
sys.path.append(config_directory)

# Import modules from the application
from config import ERROR_LVL  # noqa  # pylint: disable=all
from config import MONGO_DB  # pylint: disable=all  # noqa
from ftptomongo import (  # noqa
    connect_to_mongodb,
    delete_expired_data,
    delete_s3_file,
)  # pylint: disable=all  # noqa


@pytest.fixture
def cleanup_testdb(request: FixtureRequest) -> None:  # Fix the untyped decorator error
    """Delete test data in MongoDB documents after testing."""

    # Define a cleanup function
    def cleanup_testdb_documents() -> None:
        # Connect to MongoDB
        collection: Optional[Collection] = connect_to_mongodb()
        if collection is None:
            logger.error("MongoDB connection failed, cannot clean up test data.")
            return  # Exit if the collection is None

        # Delete all documents with filename == 'test_file.txt'
        del_filter = {"filename": "test_file.txt"}
        logger.info("deletion filter: %s" % del_filter)

        # Delete the expired documents and get the count of deleted documents
        result = collection.find(del_filter)

        for doc in result:
            # Check if the document has a non-empty "s3_file_url" field
            if doc.get("s3_file_url"):
                # Extract the S3 file URL from the document
                s3_file_url = doc["s3_file_url"]
                # Delete the file from the S3 bucket
                delete_s3_file(s3_file_url)
            collection.delete_one({"_id": doc["_id"]})

    # Register the cleanup function to be called after the test
    request.addfinalizer(cleanup_testdb_documents)


def test_returns_number_of_documents_deleted(
    cleanup_testdb: None,
) -> None:
    """Test the delete_expired_data function."""
    # Create a mock collection
    assert MONGO_DB == "nill-test"
    collection: Optional[Collection] = connect_to_mongodb()
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


def test_connect_to_mongodb() -> None:
    """Test the connect_to_mongodb function.

    Check if collection is not None.
    """
    collection: Optional[Collection] = connect_to_mongodb()
    assert collection is not None


if __name__ == "__main__":
    pytest.main(["-v", "tests/test_unit.py"])
