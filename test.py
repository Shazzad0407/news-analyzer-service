from app.core.config import settings
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import os

# Print out the effective environment variables within the container
print(f"MONGO_SERVER: {os.getenv('MONGO_SERVER')}")
print(f"MONGO_PORT: {os.getenv('MONGO_PORT')}")
print(f"MONGO_USER: {os.getenv('MONGO_USER')}")
print(f"MONGO_DB: {os.getenv('MONGO_DB')}")
print(f"MONGO_URI from settings: {settings.MONGO_URI}")

# Attempt to connect using the settings
try:
    # Use the MONGO_SERVER and MONGO_PORT directly, as that's what PyMongo uses
    # when constructing the URI from individual components.
    # Alternatively, you can use settings.MONGO_URI directly as shown below.
    client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command('ismaster') # This command is cheap and tests connectivity
    print("+++++++++++++++++++++MongoDB connected successfully from inside worker!++++++++++++++++++++++++")
    print(f"Connected to database: {client.server_info()}")
    # You can also try to list databases to ensure authentication works
    print(f"Databases: {client.list_database_names()}")
    client.close()
except ConnectionFailure as e:
    print(f"ERROR: Could not connect to MongoDB from inside worker: {e}")
except Exception as e:
    print(f"AN UNEXPECTED ERROR OCCURRED: {e}")

exit() # To exit the Python interpreter