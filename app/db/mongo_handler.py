from typing import List, Dict

import pymongo.errors
from pymongo import MongoClient, DESCENDING, errors
from pymongo.write_concern import WriteConcern

from app.core.config import settings
from app.core.logger import logger


class Mongo:
    def __init__(self):
        self.client = None
        self.db = self.connect_db()

    def connect_db(self):
        try:
            self.client = MongoClient(
                f'mongodb://{settings.MONGO_USER}:{settings.MONGO_PASSWORD}@{settings.MONGO_SERVER}:'
                f'{settings.MONGO_PORT}/{settings.MONGO_DB}?authSource=admin')
            return self.client[settings.MONGO_DB]
        except pymongo.errors.ConnectionFailure as e:
            logger.exception(f"Could not connect to server: {e}")

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
            logger.exception(e)
            return None

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


mongodb = Mongo()
