from pydantic_settings import BaseSettings, SettingsConfigDict
from loguru import logger

# Loguru Configuration
logger.remove(0)
logger.add("logs/file.log", level= "INFO", rotation= "100 MB")

class Settings(BaseSettings):
    '''
    Description: Settings class, which is inherited from BaseSettings,
    BaseSettings allows the class to automatically pull in values from environment variables 
    (or from an .env file) and validate those settings.
    '''
    model_config = SettingsConfigDict(env_file= ".env", extra= "ignore")
    
    # Database settings
    db_url: str
    
    # JWT settings
    secret_key: str 
    algorithm: str 
    access_token_expire_minutes: int
    refresh_token_expire_minutes: int
    
settings = Settings()