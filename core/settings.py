import os
from functools import lru_cache

class Settings:
    MONGO_HOST: str = os.getenv("MONGO_HOST", "localhost")
    MONGO_PORT: int = int(os.getenv("MONGO_PORT", 27017))
    MONGO_USER: str = os.getenv("MONGO_USER", "")
    MONGO_PASS: str = os.getenv("MONGO_PASS", "")
    MONGO_DB: str = os.getenv("MONGO_DB", "mydb")
    MONGO_AUTH_SOURCE: str = os.getenv("MONGO_AUTH_SOURCE", "admin")
    MONGO_AUTH_MECHANISM: str = os.getenv("MONGO_AUTH_MECHANISM", "SCRAM-SHA-256")

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