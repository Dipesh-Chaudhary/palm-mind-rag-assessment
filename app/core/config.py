from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GOOGLE_API_KEY: str
    DATABASE_URL: str
    REDIS_URL: str
    QDRANT_URL: str
    QDRANT_COLLECTION_NAME: str
    SMTP_SERVER: str
    SMTP_PORT: int
    SMTP_SENDER_EMAIL: str
    SMTP_SENDER_PASSWORD: str

    class Config:
        env_file = ".env"

settings = Settings()