"""Configuration and settings utilities."""

import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""
    
    # Database
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5433"))  # Default to 5433 to match docker-compose
    POSTGRES_USER = os.getenv("POSTGRES_USER", "personaforge_user")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "personaforge123password")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "personaforge")
    
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    # Support both NEO4J_USER and NEO4J_USERNAME (Neo4j Aura uses USERNAME)
    NEO4J_USER = os.getenv("NEO4J_USERNAME") or os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "personaforge123password")
    
    # Flask
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "1") == "1"
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    
    # API Keys (optional - free tiers available)
    BUILTWITH_API_KEY = os.getenv("BUILTWITH_API_KEY", "")
    IPLOCATE_API_KEY = os.getenv("IPLOCATE_API_KEY", "")
    SHODAN_API_KEY = os.getenv("SHODAN_API_KEY", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")
    SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY", "")  # SerpAPI for reliable search results  # For YouTube Data API v3
    
    # Rate Limiting
    ENRICHMENT_RATE_LIMIT = int(os.getenv("ENRICHMENT_RATE_LIMIT", "10"))  # per minute
    
    # Caching
    CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    CACHE_TTL_HOURS = int(os.getenv("CACHE_TTL_HOURS", "24"))
    
    # Request Timeouts
    API_TIMEOUT_SECONDS = int(os.getenv("API_TIMEOUT_SECONDS", "10"))
    DB_CONNECTION_TIMEOUT = int(os.getenv("DB_CONNECTION_TIMEOUT", "5"))
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "logs/personaforge.log")
    
    # Retry Configuration
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_BASE_DELAY = float(os.getenv("RETRY_BASE_DELAY", "1.0"))
    
    # Dark Web Access (OPTIONAL - Use with extreme caution)
    # ⚠️ WARNING: Dark web access has legal risks. Consult legal counsel.
    DARKWEB_ENABLED = os.getenv("DARKWEB_ENABLED", "false").lower() == "true"
    TOR_PROXY_HOST = os.getenv("TOR_PROXY_HOST", "127.0.0.1")
    TOR_PROXY_PORT = int(os.getenv("TOR_PROXY_PORT", "9050"))
    
    @classmethod
    def get_database_url(cls) -> str:
        """Get PostgreSQL connection URL."""
        return f"postgresql://{cls.POSTGRES_USER}:{cls.POSTGRES_PASSWORD}@{cls.POSTGRES_HOST}:{cls.POSTGRES_PORT}/{cls.POSTGRES_DB}"
    
    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production."""
        return cls.FLASK_ENV.lower() == "production"

