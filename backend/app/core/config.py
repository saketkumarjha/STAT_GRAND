import os
from typing import List, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application configuration management using environment variables.
    Supports development, testing, and production environments.
    """
    
    # Application settings
    app_name: str = "NCO Semantic Search API"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"
    
    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"
    
    # Database settings
    database_url: str = "sqlite:///./nco_search.db"
    database_echo: bool = False
    
    # Vector database settings
    vector_dimension: int = 768
    vector_index_type: str = "faiss"
    
    # ML Model settings
    model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    model_cache_dir: str = "./models"
    embedding_batch_size: int = 32
    
    # Supported languages
    supported_languages: List[str] = ["en", "hi", "ta", "bn", "mr"]
    default_language: str = "en"
    
    # Search settings
    max_search_results: int = 10
    min_confidence_threshold: float = 0.3
    
    # Caching settings
    cache_ttl: int = 3600  # 1 hour in seconds
    cache_max_size: int = 1000
    
    # Logging settings
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # CORS settings
    cors_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["GET", "POST", "PUT", "DELETE"]
    cors_allow_headers: List[str] = ["*"]
    
    @field_validator('environment')
    @classmethod
    def validate_environment(cls, v):
        """Validate environment setting"""
        allowed_environments = ['development', 'testing', 'production']
        if v not in allowed_environments:
            raise ValueError(f'Environment must be one of: {allowed_environments}')
        return v
    
    @field_validator('supported_languages')
    @classmethod
    def validate_languages(cls, v):
        """Validate supported languages list"""
        if not v or len(v) == 0:
            raise ValueError('At least one language must be supported')
        return v
    
    @field_validator('min_confidence_threshold')
    @classmethod
    def validate_confidence_threshold(cls, v):
        """Validate confidence threshold is between 0 and 1"""
        if not 0 <= v <= 1:
            raise ValueError('Confidence threshold must be between 0 and 1')
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings instance"""
    return settings