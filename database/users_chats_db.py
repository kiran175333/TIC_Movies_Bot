import re
import logging
from pymongo.errors import DuplicateKeyError
import motor.motor_asyncio
import asyncio
from info import DATABASE_NAME, DATABASE_URI, CUSTOM_FILE_CAPTION, BUTTON_MODE, AUTO_DELETE, MAX_BTN, AUTO_FILTER
import time
import datetime
import pytz

IST = pytz.timezone('Asia/Kolkata')

def get_ist_now():
    return datetime.datetime.now(IST).replace(tzinfo=None)

logger = logging.getLogger(__name__)

default_setgs = {
    'button': BUTTON_MODE,
    'auto_delete': AUTO_DELETE,
    'auto_ffilter': AUTO_FILTER,
    'max_btn': MAX_BTN,
    'caption': CUSTOM_FILE_CAPTION,
    'fsub': None
}

class Database:
    
    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name or "Cluster0"]
        self.col = self.db.users
        self.grp = self.db.groups
        self.users = self.col  # Single user storage model; eliminate uersz typo collection
        self.delete_col = self.db.delayed_deletes
        self.bot_setgs = self.db.bot_settings  # New collection for global bot config
        self.tokens = self.db.tokens
        self.verified = self.db.verified_users
        self._pm_search_cache = None

    async def setup_indices(self):
        """Ensure required indexes exist for fast O(1) lookups."""
        try:
            await self.tokens.create_index('time', expireAfterSeconds=900)
        except Exception:
            pass
        try:
            await self.delete_col.create_index('time')
        except Exception:
            pass
        try:
            await self.col.create_index('id')
        except Exception:
            pass
        try:
            await self.grp.create_index('id')
        except Exception:
            pass

    def new_user(self, id, name):
        return dict(
            id = int(id),
            name = name,
            file_id=None,
            caption=None,
            message_command=None,
            save=False,
            ban_status=dict(
                is_banned=False,
                ban_reason="",
            ),
            expiry_time=None,
        )


    async def add_req_group(self, id):
        user = await self.col.find_one({'id': int(id)})
        if user:
            await self.col.update_one({'id': int(id)}, {'$set': {'req_group': True}})

    async def has_req_group(self, id):
        user = await self.col.find_one({'id': int(id)})
        return user.get('req_group', False) if user else False


    def new_group(self, id, title):
        return dict(
            id = id,
            title = title,
            chat_status=dict(
                is_disabled=False,
                reason="",
            ),
            settings=default_setgs
        )
    
    async def add_user(self, id, name):
        try:
            user = self.new_user(id, name)
            await self.col.insert_one(user)
        except DuplicateKeyError:
            pass  # User already exists — idempotent, safe to ignore
        except Exception as e:
            logger.error("add_user(%s): database error: %s", id, e, exc_info=True)
    
    async def is_user_exist(self, id):
        try:
            user = await self.col.find_one({'id': int(id)})
            return bool(user)
        except Exception as e:
            logger.error("is_user_exist(%s): database error: %s", id, e, exc_info=True)
            return False
    
    async def total_users_count(self):
        try:
            count = await self.col.count_documents({})
            return count
        except Exception as e:
            logger.error("total_users_count: database error: %s", e, exc_info=True)
            return 0
        
    async def remove_ban(self, id):
        try:
            ban_status = dict(
                is_banned=False,
                ban_reason=''
            )
            await self.col.update_one({'id': int(id)}, {'$set': {'ban_status': ban_status}})
        except Exception as e:
            logger.error("remove_ban(%s): database error: %s", id, e, exc_info=True)
    
    async def ban_user(self, user_id, ban_reason="ɴᴏ ʀᴇᴀꜱᴏɴ ᴘʀᴏᴠɪᴅᴇᴅ"):
        try:
            ban_status = dict(
                is_banned=True,
                ban_reason=ban_reason
            )
            await self.col.update_one({'id': int(user_id)}, {'$set': {'ban_status': ban_status}})
        except Exception as e:
            logger.error("ban_user(%s): database error: %s", user_id, e, exc_info=True)

    async def get_ban_status(self, id):
        default = dict(
            is_banned=False,
            ban_reason=''
        )
        try:
            user = await self.col.find_one({'id': int(id)})
            if not user:
                return default
            return user.get('ban_status', default)
        except Exception as e:
            logger.error("get_ban_status(%s): database error: %s", id, e, exc_info=True)
            return default

    async def get_all_users(self):
        return self.col.find({})
    

    async def delete_user(self, user_id):
        try:
            await self.col.delete_many({'id': {'$in': [int(user_id), str(user_id)]}})
        except Exception as e:
            logger.error("delete_user(%s): database error: %s", user_id, e, exc_info=True)


    async def delete_chat(self, chat_id):
        try:
            await self.grp.delete_many({'id': {'$in': [int(chat_id), str(chat_id)]}})
        except Exception as e:
            logger.error("delete_chat(%s): database error: %s", chat_id, e, exc_info=True)


    async def get_banned(self):
        users = self.col.find({'ban_status.is_banned': True})
        chats = self.grp.find({'chat_status.is_disabled': True})
        b_chats = [chat['id'] async for chat in chats]
        b_users = [user['id'] async for user in users]
        return b_users, b_chats
    
    async def add_chat(self, chat, title):
        try:
            chat = self.new_group(chat, title)
            await self.grp.insert_one(chat)
        except Exception as e:
            logger.error("add_chat(%s): database error: %s", chat, e, exc_info=True)
    

    async def get_chat(self, chat):
        chat = await self.grp.find_one({'id':int(chat)})
        return False if not chat else chat.get('chat_status')
    

    async def re_enable_chat(self, id):
        try:
            chat_status=dict(
                is_disabled=False,
                reason="",
                )
            await self.grp.update_one({'id': int(id)}, {'$set': {'chat_status': chat_status}})
        except Exception as e:
            logger.error("re_enable_chat(%s): database error: %s", id, e, exc_info=True)
        
    async def update_settings(self, id, settings):
        try:
            await self.grp.update_one({'id': int(id)}, {'$set': {'settings': settings}})
        except Exception as e:
            logger.error("update_settings(%s): database error: %s", id, e, exc_info=True)
        
    
    async def get_settings(self, id):
        chat = await self.grp.find_one({'id':int(id)})
        if chat:
            return chat.get('settings', default_setgs)
        return default_setgs
    

    async def disable_chat(self, chat, reason="ɴᴏ ʀᴇᴀꜱᴏɴ ᴘʀᴏᴠɪᴅᴇᴅ"):
        try:
            chat_status=dict(
                is_disabled=True,
                reason=reason,
                )
            await self.grp.update_one({'id': int(chat)}, {'$set': {'chat_status': chat_status}})
        except Exception as e:
            logger.error("disable_chat(%s): database error: %s", chat, e, exc_info=True)
    

    async def total_chat_count(self):
        count = await self.grp.count_documents({})
        return count
    

    async def get_all_chats(self):
        return self.grp.find({})


    async def get_db_size(self):
        return (await self.db.command("dbstats"))['dataSize']

    async def get_user(self, user_id):
        if not user_id:
            return None
        try:
            user_data = await self.col.find_one({"id": int(user_id)})
            return user_data
        except Exception as e:
            logger.error("get_user(%s): database error: %s", user_id, e, exc_info=True)
            return None
            
    async def update_user(self, user_data):
        if not user_data or "id" not in user_data:
            return
        try:
            user_id = int(user_data["id"])
            user_data["id"] = user_id
            await self.col.update_one({"id": user_id}, {"$set": user_data}, upsert=True)
        except Exception as e:
            logger.error("update_user(%s): database error: %s", user_data.get("id"), e, exc_info=True)

    async def remove_premium_access(self, user_id):
        if not user_id:
            return
        try:
            await self.col.update_one({"id": int(user_id)}, {"$set": {"expiry_time": None}})
        except Exception as e:
            logger.error("remove_premium_access(%s): database error: %s", user_id, e, exc_info=True)

    async def get_expiry_time(self, user_id):
        try:
            user_data = await self.get_user(user_id)
            if user_data:
                return user_data.get("expiry_time")
            return None
        except Exception as e:
            logger.error("get_expiry_time(%s): database error: %s", user_id, e, exc_info=True)
            return None

    async def has_premium_access(self, user_id):
        if not user_id:
            return False
        try:
            user_data = await self.get_user(user_id)
            if user_data:
                expiry_time = user_data.get("expiry_time")
                if expiry_time is None:
                    return False
                now = get_ist_now()
                if isinstance(expiry_time, datetime.datetime):
                    if expiry_time.tzinfo is not None:
                        expiry_time = expiry_time.astimezone(IST).replace(tzinfo=None)
                    if now <= expiry_time:
                        return True
                    else:
                        await self.col.update_one({"id": int(user_id)}, {"$set": {"expiry_time": None}})
            return False
        except Exception as e:
            logger.error("has_premium_access(%s): database error: %s", user_id, e, exc_info=True)
            return False
    
    async def check_remaining_uasge(self, userid):
        if not userid:
            return None
        try:
            user_data = await self.get_user(userid)
            if not user_data:
                return None
            expiry_time = user_data.get("expiry_time")
            if not expiry_time or not isinstance(expiry_time, datetime.datetime):
                return None
            if expiry_time.tzinfo is not None:
                expiry_time = expiry_time.astimezone(IST).replace(tzinfo=None)
            now = get_ist_now()
            if now >= expiry_time:
                await self.col.update_one({"id": int(userid)}, {"$set": {"expiry_time": None}})
                return None
            return expiry_time - now
        except Exception as e:
            logger.error("check_remaining_uasge(%s): database error: %s", userid, e, exc_info=True)
            return None

    check_remaining_usage = check_remaining_uasge
    
    async def all_premium_users(self):
        try:
            now = get_ist_now()
            count = await self.col.count_documents({
                "expiry_time": {"$gt": now}
            })
            return count
        except Exception as e:
            logger.error("all_premium_users: database error: %s", e, exc_info=True)
            return 0


    async def add_delete(self, chat_id, message_id, time):
        try:
            await self.delete_col.insert_one({'chat_id': chat_id, 'message_id': message_id, 'time': time})
        except Exception as e:
            logger.error("add_delete: database error: %s", e)

    async def get_pending_deletes(self, now):
        try:
            return await self.delete_col.find({"time": {"$lte": now}}).to_list(length=None)
        except Exception as e:
            logger.error("get_pending_deletes: database error: %s", e)
            return []

    async def remove_delete(self, doc_id):
        try:
            await self.delete_col.delete_one({'_id': doc_id})
        except Exception as e:
            logger.error("remove_delete: database error: %s", e)

    async def get_pm_search_status(self):
        if self._pm_search_cache is not None:
            return self._pm_search_cache
        config = await self.bot_setgs.find_one({'_id': 'bot_config'})
        if config:
            self._pm_search_cache = config.get('pm_search_enabled', True)
            return self._pm_search_cache
        self._pm_search_cache = True
        return True
        
    async def update_pm_search_status(self, status: bool):
        self._pm_search_cache = status
        await self.bot_setgs.update_one(
            {'_id': 'bot_config'}, 
            {'$set': {'pm_search_enabled': status}}, 
            upsert=True
        )

    async def create_verify_token(self, user_id, token, file_data=None):
        import time
        await self.tokens.update_one({"token": token}, {"$set": {"user_id": user_id, "used": False, "time": time.time(), "file_data": file_data}}, upsert=True)
        
    async def get_verify_token(self, token):
        return await self.tokens.find_one({"token": token})
        
    async def consume_verify_token(self, token: str, user_id: int, max_age: int = 900):
        if not token:
            return None
        import time
        min_time = time.time() - max_age
        user_id_int = int(user_id) if str(user_id).lstrip("-").isdigit() else user_id
        query = {
            "token": token,
            "used": False,
            "time": {"$gte": min_time},
            "$or": [{"user_id": user_id_int}, {"user_id": str(user_id)}]
        }
        doc = await self.tokens.find_one_and_update(
            query,
            {"$set": {"used": True}}
        )
        return doc

    async def update_verify_token(self, token, used=True):
        await self.tokens.update_one({"token": token}, {"$set": {"used": used}})
        
    async def add_verified_user(self, user_id):
        import time
        await self.verified.update_one({"user_id": user_id}, {"$set": {"time": time.time()}}, upsert=True)
        
    async def get_verified_user(self, user_id):
        return await self.verified.find_one({"user_id": user_id})

db = Database(DATABASE_URI, DATABASE_NAME)
