from pydantic import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./data/egp.db"
    FEED_BASE_URL: str = "http://process3.gprocurement.go.th/EPROCRssFeedWeb/egpannouncerss.xml"
    
    class Config:
        case_sensitive = True

settings = Settings()
