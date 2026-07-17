import logging
import os
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

logger = logging.getLogger("backend.database")

from app.database.mongodb.collections.user import User
from app.database.mongodb.collections.lead import Lead
from app.database.mongodb.collections.job import ScrapeJob
from app.database.mongodb.collections.intelligence import CompanyIntelligence
from app.database.mongodb.collections.lead_score import LeadScore
from app.database.mongodb.collections.outreach import (
    EmailAccount,
    EmailTemplate,
    Campaign,
    CampaignStep,
    CampaignRecipient,
    EmailEvent,
    EmailAnalytics,
)

# List of documents mapping to Beanie ODM.
DOCUMENT_MODELS = [
    User,
    Lead,
    ScrapeJob,
    CompanyIntelligence,
    LeadScore,
    EmailAccount,
    EmailTemplate,
    Campaign,
    CampaignStep,
    CampaignRecipient,
    EmailEvent,
    EmailAnalytics,
]

from typing import Optional

class DatabaseManager:
    client: AsyncIOMotorClient = None
    db_name: Optional[str] = None

    @classmethod
    async def initialize(cls) -> None:
        """Initialize the MongoDB connection and Beanie ODM."""
        mongodb_url = os.getenv("MONGODB_URL", "mongodb://leadforge:leadforge_password@localhost:27017/leadforge_db?authSource=admin")
        cls.db_name = os.getenv("MONGODB_DB_NAME", "leadforge_db")
        
        logger.info(f"Connecting to MongoDB at {mongodb_url.split('@')[-1]}...")
        
        try:
            cls.client = AsyncIOMotorClient(mongodb_url)
            # Initialize Beanie with document models
            await init_beanie(
                database=cls.client[cls.db_name],
                document_models=DOCUMENT_MODELS
            )
            logger.info("Successfully connected to MongoDB and initialized Beanie ODM.")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise e

    @classmethod
    async def close(cls) -> None:
        """Close the MongoDB connection pool."""
        if cls.client is not None:
            cls.client.close()
            logger.info("MongoDB connection closed.")
        else:
            logger.warning("MongoDB client was not initialized when close requested.")

async def get_db_client() -> AsyncIOMotorClient:
    """Dependency injector for database client."""
    return DatabaseManager.client
