import pymongo

# MongoDB connection details
mongo_host = 'localhost'
mongo_port = 27017
mongo_db = 'nill-home'
mongo_collection = 'nill-home-photos'
mongo_username = 'user'
mongo_password = 'password'

# Create a MongoDB client
client = pymongo.MongoClient(host=mongo_host, port=mongo_port)

# Create the 'nill-home' database
db = client[mongo_db]

# Create a test user with read and write access
try:
    db.command("createUser", mongo_username, pwd=mongo_password, roles=["readWrite"])
except pymongo.errors.OperationFailure as e:
    if "already exists" in str(e):
        print(f"User '{mongo_username}' already exists.")
    else:
        raise e

# Create the 'nill-home-photos' collection
collection = db[mongo_collection]

# Perform operations on the collection (e.g., insert, update, query)

# For testing purposes, let's insert a document
document = {"title": "Test Photo", "description": "A test photo document."}
collection.insert_one(document)

# Query the collection
result = collection.find_one({"title": "Test Photo"})
print("Query result:", result)

# Close the MongoDB client when done
client.close()
