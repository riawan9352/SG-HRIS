from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "Hospital HRIS API"
    secret_key: str = "change-this-secret-key"
    access_token_expire_minutes: int = 60 * 8
    algorithm: str = "HS256"
    database_url: str = "sqlite:///./hris.db"


settings = Settings()
