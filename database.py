from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI, DATABASE_NAME

client = AsyncIOMotorClient(MONGO_URI)
db = client[DATABASE_NAME]

org_collection = db["organizations"]
admin_collection = db["admins"]

def get_org_collection_name(org_name: str) -> str:
    return f"org_{org_name.lower()}"
