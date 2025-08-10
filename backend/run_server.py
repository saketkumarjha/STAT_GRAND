#!/usr/bin/env python3
"""
Startup script for the NCO Semantic Search API server.
"""

import uvicorn
from app.core.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    
    print(f"Starting {settings.app_name} v{settings.app_version}")
    print(f"Environment: {settings.environment}")
    print(f"Server will be available at: http://{settings.api_host}:{settings.api_port}")
    print(f"API documentation: http://{settings.api_host}:{settings.api_port}/docs")
    print(f"API prefix: {settings.api_prefix}")
    
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )