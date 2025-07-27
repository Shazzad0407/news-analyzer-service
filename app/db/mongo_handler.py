import time
import pymongo
from pymongo import MongoClient, DESCENDING, errors
from pymongo.write_concern import WriteConcern
from app.core.config import settings
from app.core.logger import logger
from typing import List, Dict




class Mongo:
    _instance = None

    @classmethod
    def get_instance(cls):
        """Gets the singleton instance, creating it if it doesn't exist."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        if hasattr(self, 'client') and self.client:
             return # Already initialized
        
        self.client = None
        self.db = None
        self.connect_db()

    def connect_db(self):
        """Connect to MongoDB, retrying on failure."""
        while self.db is None:
            try:
                logger.info("Attempting to connect to MongoDB...")
                # Assuming your settings object has these attributes
                conn_str = (
                    f'mongodb://{settings.MONGO_USER}:{settings.MONGO_PASSWORD}@{settings.MONGO_SERVER}:'
                    f'{settings.MONGO_PORT}/{settings.MONGO_DB}?authSource=admin'
                )
                self.client = MongoClient(conn_str, serverSelectionTimeoutMS=5000)
                print("-----------settings.MONGO_URI: ", settings.MONGO_URI)
                # The ismaster command is cheap and does not require auth.
                self.client.admin.command('ismaster')
                self.db = self.client[settings.MONGO_DB]
                logger.success("+++++++++++++++++++++mongo connected succesfully++++++++++++++++++++++++")
            except errors.ConnectionFailure as e:
                logger.error(f"Could not connect to MongoDB: {e}. Retrying in 5 seconds...")
                time.sleep(5)

    def has_index(self, collection: str, key: str):
        index_info = self.db[collection].index_information()
        for value in index_info.values():
            if value['key'][0][0] == key:
                return True
        return False

    def create_index(self, collection: str, key: str, is_unique=False):
        try:
            if not self.has_index(collection, key):
                self.db[collection].create_index([(key, DESCENDING)], unique=is_unique)
                logger.success(f"indexing created successfully for collection: {collection}, key:{key}")
        except (AttributeError, pymongo.errors.OperationFailure) as e:
            logger.exception(e)

    def close_connection(self):
        self.client.close()

    def get_values_by_query(self, collection: str, key: str, values: List[str]):
        try:
            return self.db[collection].find(
                {key: {"$in": values}},
                {"_id": False, key: True}
            )
        except (AttributeError, pymongo.errors.OperationFailure) as e:
            logger.exception(e)

    def is_value_exist(self, collection: str, key: str, value) -> bool:
        try:
            # pprint(self.db[collection].find({key: value}).explain()['executionStats'])
            return self.db[collection].count_documents({key: value}) == 1
        except (AttributeError, pymongo.errors.OperationFailure) as e:
            logger.exception(e)

    def is_value_exist_query(self, collection: str, query: dict) -> bool:
        try:
            return self.db[collection].count_documents(query) == 1
        except (AttributeError, pymongo.errors.OperationFailure) as e:
            logger.exception(e)

    def read_key_value(self, collection: str, key: str, query: dict):
        try:
            return (self.db[collection].find_one(query, {key: 1}))[key]
        except Exception as e:
            logger.info(e)
            return -1

    def insert_one(self, collection: str, item: dict) -> bool:
        try:
            self.db[collection].insert_one(item)
            return True
        except (AssertionError, pymongo.errors.OperationFailure, pymongo.errors.DuplicateKeyError) as e:
            logger.exception(e)
            return False

    def insert_many(self, collection: str, items: List[dict], w=0, wtimeout=600, ordered=False):
        try:
            collection = self.db[collection]
            coll = collection.with_options(write_concern=WriteConcern(w=w))
            if w:
                coll = collection.with_options(write_concern=WriteConcern(w=w, wtimeout=wtimeout))
            result = coll.insert_many(items, ordered=ordered)
            return len(result.inserted_ids)
        except errors.BulkWriteError as e:
            return e.details['nInserted']

    def update_one(self, collection: str, query: dict, updated_value: dict, upsert: bool = True):
        try:
            self.db[collection].update_one(query, updated_value, upsert=upsert)
            return True
        except (AssertionError, pymongo.errors.OperationFailure) as e:
            logger.exception(e)
            return False

    def find_one(self, collection: str, query: dict):
        try:
            return self.db[collection].find_one(query)
        except (AttributeError, pymongo.errors.OperationFailure) as e:
            logger.exception(f"Error fetching documents from {collection}: {e}")
            return None
        
    def find_many(self, collection: str, query: dict, limit:int):
        try:
            return self.db[collection].find(query).limit(limit)
        except (AttributeError, pymongo.errors.OperationFailure) as e:
            logger.exception(f"Error fetching documents from {collection}: {e}")
            return []

    def count(self, collection: str, query: dict) -> int:
        try:
            return self.db[collection].count_documents(query)
        except (AttributeError, pymongo.errors.OperationFailure) as e:
            logger.exception(e)

    def estimate_document_count(self, collection: str) -> int:
        try:
            return self.db[collection].estimated_document_count()
        except (AttributeError, pymongo.errors.OperationFailure) as e:
            logger.exception(e)

    def estimate_word_sentence_count(self, collection: str) -> Dict[str, Dict]:
        try:
            query = [{
                "$project": {
                    "domain": 1,
                    "word_count": 1,
                    "sentence_count": 1
                }
            },
                {
                    "$group": {
                        "_id": "$domain",
                        "words": {"$sum": "$word_count"},
                        "sentences": {"$sum": "$sentence_count"},
                        "documents": {"$sum": 1}

                    }
                }]
            cursor = self.db[collection].aggregate(query)
            counts = {}
            for doc in cursor:
                domain = doc["_id"]
                counts[domain] = {
                    "words": doc["words"],
                    "sentences": doc["sentences"],
                    "documents": doc["documents"]
                }
            return counts
        except (AttributeError, pymongo.errors.OperationFailure) as e:
            logger.exception(e)
