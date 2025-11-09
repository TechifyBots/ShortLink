from typing import Any
from config import DB_URI, DB_NAME
from motor import motor_asyncio
from datetime import datetime, timedelta
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError
from bson import ObjectId

client = motor_asyncio.AsyncIOMotorClient(DB_URI)
db = client[DB_NAME]

class Techifybots:
    def __init__(self):
        self.users = db["users"]
        self.banned_users = db["banned_users"]
        self.cache: dict[int, dict[str, Any]] = {}

    async def add_user(self, user_id: int, name: str) -> dict[str, Any] | None:
        try:
            user_id = int(user_id)
            user = {"user_id": user_id, "name": name, "shortener": None, "api": None}
            saved = await self.users.find_one_and_update(
                {"user_id": user_id},
                {"$set": user},
                upsert=True,
                return_document=ReturnDocument.AFTER
            )
            if saved:
                self.cache[user_id] = saved
            return saved
        except DuplicateKeyError:
            existing = await self.users.find_one({"user_id": user_id})
            if existing:
                self.cache[user_id] = existing
            return existing
        except Exception as e:
            print("Error in add_user:", e)
            return None

    async def get_user(self, user_id: int) -> dict[str, Any] | None:
        try:
            if user_id in self.cache:
                return self.cache[user_id]
            user = await self.users.find_one({"user_id": int(user_id)})
            if user:
                self.cache[user_id] = user
            return user
        except Exception as e:
            print("Error in get_user:", e)
            return None

    async def get_all_users(self) -> list[dict[str, Any]]:
        try:
            users: list[dict[str, Any]] = []
            async for user in self.users.find():
                users.append(user)
            return users
        except Exception as e:
            print("Error in get_all_users:", e)
            return []

    async def delete_user(self, identifier: int | str | ObjectId) -> bool:
        try:
            query = {}
            if isinstance(identifier, int):
                query = {"user_id": identifier}
                self.cache.pop(identifier, None)
            elif isinstance(identifier, (str, ObjectId)):
                query = {"_id": ObjectId(identifier)} if isinstance(identifier, str) else {"_id": identifier}
                doc = await self.users.find_one(query)
                if doc and "user_id" in doc:
                    self.cache.pop(int(doc["user_id"]), None)
            else:
                return False
            result = await self.users.delete_one(query)
            return result.deleted_count > 0
        except Exception as e:
            print("Error in delete_user:", e)
            return False

    async def ban_user(self, user_id: int, reason: str = None) -> bool:
        try:
            ban = {"user_id": user_id, "reason": reason}
            await self.banned_users.insert_one(ban)
            return True
        except Exception as e:
            print("Error in banUser:", e)
            return False

    async def unban_user(self, user_id: int) -> bool:
        try:
            result = await self.banned_users.delete_one({"user_id": user_id})
            return result.deleted_count > 0
        except Exception as e:
            print("Error in unbanUser:", e)
            return False

    async def is_user_banned(self, user_id: int) -> bool:
        try:
            user = await self.banned_users.find_one({"user_id": user_id})
            return user is not None
        except Exception as e:
            print("Error in isUserBanned:", e)
            return False

    async def set_shortner(self, user_id: int, shortner: str, api: str):
        try:
            await self.users.update_one(
                {'user_id': user_id},
                {'$set': {'shortner': shortner, 'api': api}},
                upsert=True
            )
        except Exception as e:
            print("Error in set_shortner:", e)

    async def get_value(self, key: str, user_id: int):
        try:
            user = await self.users.find_one({'user_id': user_id})
            if user:
                return user.get(key)
        except Exception as e:
            print("Error in get_value:", e)
            return None

tb = Techifybots()
