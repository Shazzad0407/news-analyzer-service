from sentence_transformers import SentenceTransformer
from app.core.logger import logger

class BanglaSentenceTransformer:
    def __init__(self):
        self.model = SentenceTransformer("shihab17/bangla-sentence-transformer")
        logger.success("-----------sentence transformer model loaded successfully-------------")

    def encode(self, text: str):
        return self.model.encode(text).tolist()
