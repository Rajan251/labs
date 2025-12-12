import os

class Config:
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    
    # Queue Names
    QUEUE_CRITICAL = "translation_critical"
    QUEUE_STANDARD = "translation_standard"
    
    # Worker Settings
    WORDS_PER_MINUTE = 1000
