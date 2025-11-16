#!/usr/bin/env python3
"""
Database initialization script for SecurityGuard AI
Creates tables, indexes, and seeds initial data
"""

import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from loguru import logger
from core.config import get_settings
from models.database import initialize_database
from scripts.seed_patterns import PatternSeeder


async def main():
    """Initialize SecurityGuard AI database"""
    logger.info("🚀 Initializing SecurityGuard AI database...")
    
    try:
        settings = get_settings()
        
        # Initialize database schema
        logger.info("📊 Creating database schema...")
        engine = initialize_database(settings.database_url)
        
        # Seed initial patterns
        logger.info("🌱 Seeding initial exploit patterns...")
        seeder = PatternSeeder(settings.database_url)
        await seeder.seed_database()
        
        logger.info("✅ Database initialization completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())