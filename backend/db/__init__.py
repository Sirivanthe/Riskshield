# Database initialization and connection management
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]


async def init_indexes():
    """Create database indexes for performance"""
    try:
        await db.assessments.create_index("created_by")
        await db.assessments.create_index("status")
        await db.assessments.create_index("business_unit")
        await db.assessments.create_index([("created_at", -1)])
        await db.users.create_index("email", unique=True)
        await db.workflows.create_index("trigger")
        await db.workflows.create_index("active")
        
        # Indexes for advanced features
        await db.agent_activities.create_index("session_id")
        await db.agent_activities.create_index([("started_at", -1)])
        await db.model_metrics.create_index("session_id")
        await db.model_metrics.create_index([("timestamp", -1)])
        await db.explanations.create_index("session_id")
        await db.knowledge_entities.create_index("entity_type")
        await db.knowledge_entities.create_index("name")
        await db.knowledge_relations.create_index("source_entity_id")
        await db.knowledge_relations.create_index("target_entity_id")
        await db.issues.create_index("status")
        await db.issues.create_index("priority")
        await db.issues.create_index([("created_at", -1)])
        
        # Indexes for custom controls and testing
        await db.custom_controls.create_index("status")
        await db.custom_controls.create_index("category")
        await db.custom_controls.create_index("frameworks")
        await db.custom_controls.create_index("is_ai_control")
        await db.custom_controls.create_index([("created_at", -1)])
        await db.control_tests.create_index("control_id")
        await db.control_tests.create_index("status")
        await db.control_tests.create_index("tester")
        await db.control_tests.create_index([("test_date", -1)])
        await db.control_gaps.create_index("framework")
        await db.control_gaps.create_index("status")
        
        # Indexes for AI systems and assessments
        await db.ai_systems.create_index("risk_category")
        await db.ai_systems.create_index("deployment_status")
        await db.ai_systems.create_index("business_unit")
        await db.ai_control_assessments.create_index("ai_system_id")
        await db.ai_control_assessments.create_index("framework")
        await db.ai_control_assessments.create_index("status")
        
        return True
    except Exception as e:
        print(f"Index creation warning: {e}")
        return False


async def close_connection():
    """Close database connection"""
    client.close()
