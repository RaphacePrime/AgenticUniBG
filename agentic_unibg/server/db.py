"""
MongoDB connection module
"""
import os
import motor.motor_asyncio

MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb+srv://agentic_unibg:agentic_unibg2026@mycluster.jgl4w15.mongodb.net/?appName=MyCluster"
)

DB_NAME = os.getenv("MONGODB_DB_NAME", "agentic_unibg")

client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
db = client[DB_NAME]

# Collections
students_collection = db["users"]
