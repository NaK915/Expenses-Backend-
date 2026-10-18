from datetime import datetime
from typing import List, Optional

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ReturnDocument

from app.config import get_settings
from app.models import GroupRead, TransactionRead, UserInDB, UserRead

settings = get_settings()

mongo_client = AsyncIOMotorClient(
    settings.mongodb_uri,
    serverSelectionTimeoutMS=2000,
)
database = mongo_client[settings.mongodb_db_name]

users_collection = database["users"]
groups_collection = database["groups"]
transactions_collection = database["transactions"]


async def ping_db() -> bool:
    try:
        await database.command("ping")
        return True
    except Exception:
        return False


async def ensure_indexes() -> None:
    await users_collection.create_index("email", unique=True)
    await groups_collection.create_index("member_ids")
    await transactions_collection.create_index([("group_id", 1), ("created_at", -1)])


def _without_mongo_id(document: dict) -> dict:
    document.pop("_id", None)
    return document


async def get_user(user_id: str) -> Optional[UserInDB]:
    document = await users_collection.find_one({"id": user_id})
    return UserInDB(**_without_mongo_id(document)) if document else None


async def get_user_by_email(email: str) -> Optional[UserInDB]:
    document = await users_collection.find_one({"email": email.strip().lower()})
    return UserInDB(**_without_mongo_id(document)) if document else None


async def create_user(user: UserInDB) -> UserRead:
    await users_collection.insert_one(user.model_dump())
    return UserRead(**user.model_dump(exclude={"password_hash"}))


async def list_users() -> List[UserRead]:
    cursor = users_collection.find({}, {"password_hash": 0}).sort("created_at", 1)
    return [UserRead(**_without_mongo_id(document)) async for document in cursor]


async def update_user_preferences(user_id: str, preferred_currency: str) -> Optional[UserRead]:
    result = await users_collection.find_one_and_update(
        {"id": user_id},
        {"$set": {"preferred_currency": preferred_currency}},
        return_document=ReturnDocument.AFTER,
    )
    return UserRead(**_without_mongo_id(result)) if result else None


async def get_group(group_id: str) -> Optional[GroupRead]:
    document = await groups_collection.find_one({"id": group_id})
    return GroupRead(**_without_mongo_id(document)) if document else None


async def list_groups_for_user(user_id: str) -> List[GroupRead]:
    cursor = groups_collection.find({"member_ids": user_id}).sort("created_at", -1)
    return [GroupRead(**_without_mongo_id(document)) async for document in cursor]


async def create_group(group: GroupRead) -> GroupRead:
    await groups_collection.insert_one(group.model_dump())
    return group


async def update_group_members(group_id: str, member_ids: List[str]) -> Optional[GroupRead]:
    result = await groups_collection.find_one_and_update(
        {"id": group_id},
        {"$set": {"member_ids": member_ids}},
        return_document=ReturnDocument.AFTER,
    )
    return GroupRead(**_without_mongo_id(result)) if result else None


async def get_transaction(transaction_id: str) -> Optional[TransactionRead]:
    document = await transactions_collection.find_one({"id": transaction_id})
    return TransactionRead(**_without_mongo_id(document)) if document else None


async def list_transactions(group_id: str) -> List[TransactionRead]:
    cursor = transactions_collection.find({"group_id": group_id}).sort("created_at", 1)
    return [TransactionRead(**_without_mongo_id(document)) async for document in cursor]


async def create_transaction(transaction: TransactionRead) -> TransactionRead:
    await transactions_collection.insert_one(transaction.model_dump())
    return transaction


async def update_transaction(transaction_id: str, updates: dict) -> Optional[TransactionRead]:
    updates["updated_at"] = datetime.utcnow()
    result = await transactions_collection.find_one_and_update(
        {"id": transaction_id},
        {"$set": updates},
        return_document=ReturnDocument.AFTER,
    )
    return TransactionRead(**_without_mongo_id(result)) if result else None


async def delete_transaction(transaction_id: str) -> bool:
    result = await transactions_collection.delete_one({"id": transaction_id})
    return result.deleted_count == 1
