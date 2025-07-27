import time
from datetime import datetime
from app.core.config import settings
from app.core.logger import logger
from app.schemas import Backgroud_tasks


from app.db.chromadb_handler import ChromaDB
from app.models.model_registry import ModelRegistry
from app.db.mongo_handler import Mongo

class VectorizationWorker:
    """
    A worker class that continuously finds new articles, creates vector embeddings,
    and saves them to ChromaDB.
    """
    def __init__(self):
        """
        Initializes the worker, setting up connections to MongoDB, ChromaDB,
        and loading the sentence transformer model. These resources are loaded
        only once when the worker instance is created.
        """
        logger.info("=================Initializing Vectorization Worker===================")
        self.chromadb = ChromaDB.get_instance()
        self.mongodb = Mongo.get_instance()
        self.model_registry = ModelRegistry.get_instance()
        self.embedding_model = self.model_registry.get_bangla_sentence_transformer()
        self.STATUS_FIELD = Backgroud_tasks.vectorization_and_news_search_task
        logger.info("Vectorization Worker initialized.")

    def run(self):
        """
        The main loop for the vectorization worker. It continuously fetches
        unprocessed documents from MongoDB, processes them, and stores embeddings
        in ChromaDB.
        """
        logger.info("--- Entering Vectorization Loop ---")

        while True:
            try:
                # Fetch a batch of documents that have not been processed yet.
                # The query now uses a string key and checks for non-existence or a value of 0.
                documents = list(self.mongodb.find_many(
                    collection=settings.MONGO_COLLECTION,
                    query={"$or": [{self.STATUS_FIELD: {"$exists": False}}, {self.STATUS_FIELD: 0}]},
                    limit=settings.BATCH_SIZE
                ))

                if not documents:
                    logger.info("[Vectorization Worker] No pending documents to process. Waiting...")
                    time.sleep(settings.VECTORIZATION_POLL_INTERVAL)
                    continue

                logger.info(f"Found {len(documents)} documents to process.")

                for doc in documents:
                    doc_id = doc["_id"]

                    try:
                        text = doc.get("text", "")
                        title = doc.get("title", "No Title")
                        url = doc["url"]
                        publish_date = doc.get("publish_date", datetime.utcnow())

                        if isinstance(publish_date, datetime):
                            publish_date_str = publish_date.strftime("%Y-%m-%d")
                        else:
                            publish_date_str = str(publish_date)

                        logger.info(f"Processing article: {title} ({doc_id})")

                        new_embedding = self.embedding_model.encode(text)

                        metadata = {
                            "title": title,
                            "url": url,
                            "publish_date": self.chromadb.convert_to_timestamp(publish_date_str)
                        }

                        self.chromadb.add_document(news_id=url, embedding=new_embedding, metadata=metadata)

                        # Mark the document as completed (e.g., 1)
                        self.mongodb.update_one(
                            collection=settings.MONGO_COLLECTION,
                            query={"_id": doc_id},
                            updated_value={"$set": {self.STATUS_FIELD: 1}} # 1 = complete
                        )
                        logger.success(f"Successfully processed document: {doc_id}")

                    except Exception as e:
                        logger.error(f"Failed to process document {doc_id}: {e}")

            except Exception as e:
                logger.exception(f"An unhandled error occurred in vectorization loop: {e}")
                time.sleep(settings.VECTORIZATION_POLL_INTERVAL) # Wait before retrying the whole loop

if __name__ == "__main__":
    # Create an instance of the worker and run its loop
    worker = VectorizationWorker()
    worker.run()