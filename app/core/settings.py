from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_WEBHOOK_URL: str
    HOST: str = "localhost"
    PORT: int = 8000

    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_API_KEY: str
    AZURE_OPENAI_DEPLOYMENT: str
    AZURE_OPENAI_API_VERSION: str

    MONGO_HOST: str
    MONGO_PORT: int
    MONGO_USER: str
    MONGO_PASS: str
    MONGO_DB: str
    MONGO_AUTH_SOURCE: str
    MONGO_AUTH_MECHANISM: str

    class Config:
        env_file = ".env"

    @property
    def MONGO_URI(self) -> str:
        if self.MONGO_USER and self.MONGO_PASS:
            return (
                f"mongodb://{self.MONGO_USER}:{self.MONGO_PASS}"
                f"@{self.MONGO_HOST}:{self.MONGO_PORT}/{self.MONGO_DB}"
                f"?authSource={self.MONGO_AUTH_SOURCE}&authMechanism={self.MONGO_AUTH_MECHANISM}"
            )
        else:
            return f"mongodb://{self.MONGO_HOST}:{self.MONGO_PORT}/{self.MONGO_DB}"


@lru_cache()
def get_settings():
    return Settings()
