from app.models.bangla_sentence_transformer import BanglaSentenceTransformer
from app.core.logger import logger

class ModelRegistry:
    _instance = None

    @classmethod
    def get_instance(cls):
        """Gets the singleton instance, creating it if it doesn't exist."""
        if cls._instance is None:
            logger.info("Creating new ModelRegistry instance.")
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return
        logger.info("Initializing ModelRegistry... Models will be loaded on first use.")
        self._bangla_sentence_transformer = None
        self._initialized = True

    def get_bangla_sentence_transformer(self) -> BanglaSentenceTransformer:
        """Lazily loads and returns the sentence transformer model."""
        if self._bangla_sentence_transformer is None:
            logger.info("Loading BanglaSentenceTransformer model for the first time...")
            self._bangla_sentence_transformer = BanglaSentenceTransformer()
        return self._bangla_sentence_transformer