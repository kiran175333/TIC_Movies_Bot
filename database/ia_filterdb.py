import re, base64, json
from struct import pack
from pyrogram.file_id import FileId
import motor.motor_asyncio
from pymongo.errors import DuplicateKeyError, OperationFailure
from info import DATABASE_URI, DATABASE_URI2, DATABASE_URI3, DATABASE_NAME, COLLECTION_NAME, MULTIPLE_DATABASE, USE_CAPTION_FILTER, MAX_B_TN
from utils import remove_junk

# First Database For File Saving 
client = motor.motor_asyncio.AsyncIOMotorClient(DATABASE_URI)
db = client[DATABASE_NAME]
col = db[COLLECTION_NAME]
trending_col = db['TRENDING_UPLOADS']

# Second & Third Databases For File Saving
sec_col = None
thi_col = None
sec_db = None
thi_db = None

if MULTIPLE_DATABASE:
    if DATABASE_URI2:
        sec_client = motor.motor_asyncio.AsyncIOMotorClient(DATABASE_URI2)
        sec_db = sec_client[DATABASE_NAME]
        sec_col = sec_db[COLLECTION_NAME]
    if DATABASE_URI3:
        thi_client = motor.motor_asyncio.AsyncIOMotorClient(DATABASE_URI3)
        thi_db = thi_client[DATABASE_NAME]
        thi_col = thi_db[COLLECTION_NAME]

_indices_setup = False

async def setup_indices():
    global _indices_setup
    if _indices_setup:
        return
    for collection in [col, sec_col, thi_col]:
        if collection is not None:
            try:
                await collection.create_index("file_id", unique=True, sparse=True)
                await collection.create_index("file_name")
            except Exception as e:
                print(f"Error creating indices: {e}")
    _indices_setup = True

async def save_file(media):
    """Save file in the database."""
    await setup_indices()
    
    file_id = unpack_new_file_id(media.file_id)
    file_name = clean_file_name(media.file_name)
    
    file = {
        'file_id': file_id,
        'file_name': file_name,
        'file_size': media.file_size,
        'caption': getattr(media, 'caption', None),
    }

    if await is_file_already_saved(file_id, file_name):
        return False, 0

    try:
        await col.insert_one(file)
        print(f"{file_name} ɪꜱ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ꜱᴀᴠᴇᴅ.")
        return True, 1
    except DuplicateKeyError:
        print(f"{file_name} ɪꜱ ᴀʟʀᴇᴀᴅʏ ꜱᴀᴠᴇᴅ.")
        return False, 0
    except OperationFailure:
        if MULTIPLE_DATABASE and sec_col is not None:
            try:
                await sec_col.insert_one(file)
                print(f"{file_name} ɪꜱ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ꜱᴀᴠᴇᴅ.")
                return True, 1
            except DuplicateKeyError:
                print(f"{file_name} ɪꜱ ᴀʟʀᴇᴀᴅʏ ꜱᴀᴠᴇᴅ.")
                return False, 0
            except OperationFailure:
                if thi_col is not None:
                    try:
                        await thi_col.insert_one(file)
                        print(f"{file_name} ɪꜱ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ꜱᴀᴠᴇᴅ.")
                        return True, 1
                    except DuplicateKeyError:
                        print(f"{file_name} ɪꜱ ᴀʟʀᴇᴀᴅʏ ꜱᴀᴠᴇᴅ.")
                        return False, 0
                    except Exception as e:
                        print(f"Error saving to third DB: {e}")
                        return False, 2
            except Exception as e:
                print(f"Error saving to second DB: {e}")
                return False, 2
        print("ʏᴏᴜʀ ᴘʀɪᴍᴀʀʏ ᴅᴀᴛᴀʙᴀꜱᴇ ɪꜱ ꜰᴜʟʟ ᴏʀ ꜰᴀɪʟᴇᴅ, ᴀɴᴅ ɴᴏ ʙᴀᴄᴋᴜᴘ ᴅᴀᴛᴀʙᴀꜱᴇ ᴄᴏᴜʟᴅ ꜱᴛᴏʀᴇ ᴛʜᴇ ꜰɪʟᴇ.")
        return False, 0
    except Exception as e:
        print(f"Error saving to primary DB: {e}")
        return False, 2

def clean_file_name(file_name):
    """Clean and format the file name."""
    file_name = re.sub(r"(?i)(www\.?|1tamilmv|movierulz|tamilblasters|tamilmv|@\w+|\.com|\.net|\.in|\bvet\b|\bpl\b|t\.me[^\s]+|https?://[^\s]+)", "", str(file_name))
    file_name = re.sub(r"(_|\-|\.|\+)", " ", file_name)
    old_file_name = ' '.join(file_name.split())
    return old_file_name

    
async def is_file_already_saved(file_id, file_name):
    """Check if the file is already saved in any active collection."""
    found1 = {'file_name': file_name}
    found = {'file_id': file_id}

    active_collections = [c for c in [col, sec_col, thi_col] if c is not None]
    for collection in active_collections:
        if await collection.find_one(found1) or await collection.find_one(found):
            print(f"{file_name} ɪꜱ ᴀʟʀᴇᴀᴅʏ ꜱᴀᴠᴇᴅ.")
            return True
            
    return False

async def get_search_results(chat_id, query, file_type=None, max_results=10, offset=0, filter=False):
    """For given query return (results, next_offset)"""
    
    query = query.strip()
    
    if not query:
        filter = {'file_name': re.compile('.', flags=re.IGNORECASE)}
    else:
        query_words = query.split()
        if len(query_words) == 1:
            # Single word search (strict matching)
            escaped_word = re.escape(query)
            escaped_word = re.sub(r"\\?['’‘]", "['’]", escaped_word)
            if escaped_word.endswith("['’]s") or escaped_word.endswith("s"):
                escaped_word = re.sub(r"(\['’\]s|s)$", r"(?:['’]s|s)", escaped_word)
                
            raw_pattern = r'(\b|[\.\+\-_])' + escaped_word + r'(\b|[\.\+\-_])'
            try:
                regex = re.compile(raw_pattern, flags=re.IGNORECASE)
            except Exception:
                regex = re.compile(escaped_word, flags=re.IGNORECASE)
            filter = {'file_name': regex}
        else:
            # Multi-word search (finds all words in ANY order)
            filter_and = []
            for word in query_words:
                escaped_word = re.escape(word)
                escaped_word = escaped_word.replace(r"\'", "['’]").replace("'", "['’]").replace("’", "['’]").replace("‘", "['’]")
                if escaped_word.endswith("['’]s") or escaped_word.endswith("s"):
                    escaped_word = re.sub(r"(\['’\]s|s)$", r"(?:['’]s|s)", escaped_word)
                filter_and.append({"file_name": {"$regex": escaped_word, "$options": "i"}})
            
            filter = {"$and": filter_and}
            
            
    active_collections = [c for c in [col, sec_col, thi_col] if c is not None] if MULTIPLE_DATABASE else [col]
    
    files = []
    total_results = 0
    remaining_offset = offset
    remaining_limit = max_results
    
    for collection in active_collections:
        c_count = await collection.count_documents(filter)
        total_results += c_count
        
        if remaining_limit > 0:
            if remaining_offset >= c_count:
                remaining_offset -= c_count
            else:
                cursor = collection.find(filter).sort('$natural', -1).skip(remaining_offset).limit(remaining_limit)
                async for file in cursor:
                    file['file_id'] = file.get('file_id', file.get('_id'))
                    files.append(file)
                
                fetched = len(files) - (max_results - remaining_limit)
                remaining_limit -= fetched
                remaining_offset = 0
                
    next_offset = "" if (offset + max_results) >= total_results else (offset + max_results)
    return files, next_offset, total_results

async def get_bad_files(query, file_type=None, use_filter=False):
    """For given query return (results, next_offset)"""
    query = query.strip()
    
    if not query:
        filter_criteria = {'file_name': re.compile('.', flags=re.IGNORECASE)}
    else:
        query_words = query.split()
        if len(query_words) == 1:
            raw_pattern = rf'(\b|[.+-_]){re.escape(query)}(\b|[.+-_])'
            try:
                regex = re.compile(raw_pattern, flags=re.IGNORECASE)
            except re.error:
                regex = re.compile(re.escape(query), flags=re.IGNORECASE)
            filter_criteria = {'file_name': regex}
        else:
            filter_criteria = {
                "$and": [
                    {"file_name": {"$regex": re.escape(word), "$options": "i"}} for word in query_words
                ]
            }

    if USE_CAPTION_FILTER:
        if len(query.split()) == 1:
            filter_criteria = {'$or': [filter_criteria, {'caption': filter_criteria['file_name']}]}
        else:
            caption_filter = {
                "$and": [
                    {"caption": {"$regex": re.escape(word), "$options": "i"}} for word in query.split()
                ]
            }
            filter_criteria = {'$or': [filter_criteria, caption_filter]}

    active_cols = [c for c in [col, sec_col, thi_col] if c is not None] if MULTIPLE_DATABASE else [col]

    async def count_documents(collection):
        return await collection.count_documents(filter_criteria)

    total_results = sum([await count_documents(c) for c in active_cols])

    async def find_documents(collection):
        return await collection.find(filter_criteria).to_list(length=10000)

    files = []
    for c in active_cols:
        docs = await find_documents(c)
        for doc in docs:
            doc['file_id'] = doc.get('file_id', doc.get('_id'))
        files.extend(docs)

    return files, total_results

async def get_file_details(query):
    filter_query = {'$or': [{'file_id': query}, {'_id': query}]}
    file = await col.find_one(filter_query)
    if not file and sec_col is not None:
        file = await sec_col.find_one(filter_query)
    if not file and thi_col is not None:
        file = await thi_col.find_one(filter_query)
    
    if file:
        file['file_id'] = file.get('file_id', file.get('_id'))
    return file

def encode_file_id(s: bytes) -> str:
    r = b""
    n = 0
    for i in s + bytes([22]) + bytes([4]):
        if i == 0:
            n += 1
        else:
            if n:
                r += b"\x00" + bytes([n])
                n = 0
            r += bytes([i])
    return base64.urlsafe_b64encode(r).decode().rstrip("=")
    
def unpack_new_file_id(new_file_id):
    """Return file_id"""
    decoded = FileId.decode(new_file_id)
    file_id = encode_file_id(
        pack(
            "<iiqq",
            int(decoded.file_type),
            decoded.dc_id,
            decoded.media_id,
            decoded.access_hash
        )
    )
    return file_id
    
async def add_search_query(search_query):
    search_query = search_query.strip().lower()
    if len(search_query) < 3:
        return
    try:
        await trending_col.update_one(
            {'query': search_query},
            {'$inc': {'count': 1}},
            upsert=True
        )
    except Exception as e:
        print(f"Error logging trending query: {e}")

async def get_trending_searches(limit=10):
    return await trending_col.find({}).sort('count', -1).limit(limit).to_list(length=limit)
