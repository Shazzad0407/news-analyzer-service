import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import chromadb
from chromadb.config import Settings
from chromadb import HttpClient
from chromadb.errors import ChromaError
from app.core.config import settings
from app.core.logger import logger




class ChromaDB:
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
        self.collection = None
        self.connect_db()

    def connect_db(self):
        """Connect to ChromaDB, retrying on failure."""
        while self.collection is None:
            try:
                logger.info(f"Attempting to connect to ChromaDB at {settings.CHROMA_HOST}:{settings.CHROMA_PORT}...")
                self.client = HttpClient(
                    host=settings.CHROMA_HOST,
                    port=settings.CHROMA_PORT,
                    settings=Settings(
                        chroma_client_auth_provider=settings.CHROMA_SERVER_AUTHN_PROVIDER,
                        chroma_client_auth_credentials=settings.CHROMA_SERVER_AUTHN_CREDENTIALS
                    )
                )
                self.client.heartbeat() # Test connection
                self.collection = self.client.get_or_create_collection(
                    name=settings.CHROMA_COLLECTION,
                    metadata={"description": "News articles embeddings collection"}
                )
                logger.success("+++++++++++++++++++++ChromaDB connected successfully++++++++++++++++++++++++")
            except Exception as e:
                logger.error(f"Could not connect to ChromaDB: {e}. Retrying in 5 seconds...")
                time.sleep(5)
    
    def close_connection(self):
        """Close ChromaDB connection"""
        try:
            if self.client:
                # ChromaDB HttpClient doesn't have explicit close method
                # but we can reset the client
                self.client = None
                logger.info("ChromaDB connection closed")
        except Exception as e:
            logger.exception(f"Error closing ChromaDB connection: {e}")
    
    def convert_to_timestamp(self, date_str: str) -> int:
        """Convert date string to timestamp"""
        try:
            return int(datetime.strptime(date_str, "%Y-%m-%d").timestamp())
        except ValueError as e:
            logger.exception(f"Error converting date {date_str} to timestamp: {e}")
            raise
    
    def add_document(self, news_id: str, embedding: List[float], metadata: Dict[str, Any]) -> bool:
        """Add a single document to ChromaDB"""
        try:
            self.collection.add(
                ids=[news_id],
                embeddings=[embedding],
                metadatas=[metadata]
            )
            logger.debug(f"Successfully added document {news_id} to ChromaDB")
            return True
            
        except ChromaError as e:
            logger.exception(f"ChromaDB error adding document {news_id}: {e}")
            return False
        except Exception as e:
            logger.exception(f"Unexpected error adding document {news_id}: {e}")
            return False
    
    def add_many(self, items: List[Dict[str, Any]]) -> int:
        """Add multiple documents to ChromaDB"""
        try:
            if not items:
                return 0
            
            ids = [item['id'] for item in items]
            embeddings = [item['embedding'] for item in items]
            metadatas = [item['metadata'] for item in items]
            
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas
            )
            
            logger.info(f"Successfully added {len(items)} documents to ChromaDB")
            return len(items)
            
        except ChromaError as e:
            logger.exception(f"ChromaDB error adding multiple documents: {e}")
            return 0
        except Exception as e:
            logger.exception(f"Unexpected error adding multiple documents: {e}")
            return 0
    
    def search_similar(self, query_embedding: List[float], n_results: int = 10, 
                      where: Optional[Dict[str, Any]] = None, 
                      include: Optional[List[str]] = None) -> Dict[str, Any]:
        """Search for similar documents"""
        try:
            if include is None:
                include = ["metadatas", "distances", "documents"]
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where,
                include=include
            )
            
            logger.debug(f"Found {len(results.get('ids', [[]])[0])} similar documents")
            return results
            
        except ChromaError as e:
            logger.exception(f"ChromaDB error searching similar documents: {e}")
            return {"ids": [[]], "distances": [[]], "metadatas": [[]], "documents": [[]]}
        except Exception as e:
            logger.exception(f"Unexpected error searching similar documents: {e}")
            return {"ids": [[]], "distances": [[]], "metadatas": [[]], "documents": [[]]}
    
    def search_duplicates(self, new_embedding: List[float], date_range: Tuple[str, str], 
                         distance_threshold: float = 0.1) -> List[Dict[str, Any]]:
        """Search for duplicate documents within a date range"""
        try:
            start_timestamp = self.convert_to_timestamp(date_range[0])
            end_timestamp = self.convert_to_timestamp(date_range[1])
            
            where_clause = {
                "$and": [
                    {"publish_date": {"$gte": start_timestamp}},
                    {"publish_date": {"$lte": end_timestamp}}
                ]
            }
            
            results = self.search_similar(
                query_embedding=new_embedding,
                n_results=10,
                where=where_clause,
                include=["metadatas", "distances"]
            )
            
            duplicates = []
            if results["distances"] and results["metadatas"]:
                for idx, distance in enumerate(results["distances"][0]):
                    if distance <= distance_threshold:
                        duplicates.append({
                            "metadata": results["metadatas"][0][idx],
                            "distance": distance
                        })
            
            logger.info(f"Found {len(duplicates)} potential duplicates")
            return duplicates
            
        except Exception as e:
            logger.exception(f"Error searching for duplicates: {e}")
            return []
    
    def get_by_ids(self, ids: List[str], include: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get documents by their IDs"""
        try:
            if include is None:
                include = ["metadatas", "documents", "embeddings"]
            
            results = self.collection.get(
                ids=ids,
                include=include
            )
            
            logger.debug(f"Retrieved {len(results.get('ids', []))} documents by IDs")
            return results
            
        except ChromaError as e:
            logger.exception(f"ChromaDB error getting documents by IDs: {e}")
            return {"ids": [], "metadatas": [], "documents": [], "embeddings": []}
        except Exception as e:
            logger.exception(f"Unexpected error getting documents by IDs: {e}")
            return {"ids": [], "metadatas": [], "documents": [], "embeddings": []}
    
    def update_document(self, news_id: str, embedding: Optional[List[float]] = None, 
                       metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Update a document in ChromaDB"""
        try:
            update_kwargs = {"ids": [news_id]}
            
            if embedding is not None:
                update_kwargs["embeddings"] = [embedding]
            
            if metadata is not None:
                update_kwargs["metadatas"] = [metadata]
            
            self.collection.update(**update_kwargs)
            
            logger.debug(f"Successfully updated document {news_id}")
            return True
            
        except ChromaError as e:
            logger.exception(f"ChromaDB error updating document {news_id}: {e}")
            return False
        except Exception as e:
            logger.exception(f"Unexpected error updating document {news_id}: {e}")
            return False
    
    def delete_documents(self, ids: List[str]) -> bool:
        """Delete documents by IDs"""
        try:
            self.collection.delete(ids=ids)
            logger.info(f"Successfully deleted {len(ids)} documents")
            return True
            
        except ChromaError as e:
            logger.exception(f"ChromaDB error deleting documents: {e}")
            return False
        except Exception as e:
            logger.exception(f"Unexpected error deleting documents: {e}")
            return False
    
    def delete_by_where(self, where: Dict[str, Any]) -> bool:
        """Delete documents matching where clause"""
        try:
            self.collection.delete(where=where)
            logger.info(f"Successfully deleted documents matching where clause")
            return True
            
        except ChromaError as e:
            logger.exception(f"ChromaDB error deleting documents by where clause: {e}")
            return False
        except Exception as e:
            logger.exception(f"Unexpected error deleting documents by where clause: {e}")
            return False
    
    def count_documents(self, where: Optional[Dict[str, Any]] = None) -> int:
        """Count documents in collection"""
        try:
            # ChromaDB doesn't have a direct count method, so we use get with limit
            if where:
                results = self.collection.get(where=where, include=[])
            else:
                results = self.collection.get(include=[])
            
            count = len(results.get('ids', []))
            logger.debug(f"Collection contains {count} documents")
            return count
            
        except ChromaError as e:
            logger.exception(f"ChromaDB error counting documents: {e}")
            return 0
        except Exception as e:
            logger.exception(f"Unexpected error counting documents: {e}")
            return 0
    
    def peek_collection(self, limit: int = 10) -> Dict[str, Any]:
        """Peek at collection contents"""
        try:
            results = self.collection.peek(limit=limit)
            logger.debug(f"Peeked at {len(results.get('ids', []))} documents")
            return results
            
        except ChromaError as e:
            logger.exception(f"ChromaDB error peeking collection: {e}")
            return {"ids": [], "metadatas": [], "documents": [], "embeddings": []}
        except Exception as e:
            logger.exception(f"Unexpected error peeking collection: {e}")
            return {"ids": [], "metadatas": [], "documents": [], "embeddings": []}
    
    def collection_exists(self, collection_name: str) -> bool:
        """Check if collection exists"""
        try:
            collections = self.client.list_collections()
            return any(col.name == collection_name for col in collections)
        except Exception as e:
            logger.exception(f"Error checking if collection exists: {e}")
            return False
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get collection information"""
        try:
            # Get basic collection info
            count = self.count_documents()
            peek_data = self.peek_collection(1)
            
            info = {
                "name": settings.CHROMA_COLLECTION,
                "count": count,
                "has_documents": count > 0,
                "sample_metadata": peek_data.get("metadatas", [[]])[0] if peek_data.get("metadatas") else None
            }
            
            return info
            
        except Exception as e:
            logger.exception(f"Error getting collection info: {e}")
            return {}
