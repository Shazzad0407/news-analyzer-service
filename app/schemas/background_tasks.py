from enum import Enum

class Backgroud_tasks(str, Enum):
    sentiment_task = "sentiment_classification_task_status"
    ner_task = "ner_task_status"
    vectorization_and_news_search_task = "vectorization&news_search_task_status"