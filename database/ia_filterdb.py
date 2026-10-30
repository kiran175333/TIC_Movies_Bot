import logging
import re, base64, json
from struct import pack
from pyrogram.file_id import FileId
import motor.motor_asyncio
from pymongo.errors import DuplicateKeyError
from info import DATABASE_URI, DATABASE_NAME, COLLECTION_NAME, USE_CAPTION_FILTER, MAX_B_TN
from utils import remove_junk

logger = logging.getLogger(__name__)

# Database For File Saving 
client = motor.motor_asyncio.AsyncIOMotorClient(DATABASE_URI)
db = client[DATABASE_NAME]
col = db[COLLECTION_NAME]

_indices_setup = False

async def setup_indices():
    global _indices_setup
    if _indices_setup:
        return True
    try:
        await col.create_index("file_id", unique=True, sparse=True)
        await col.create_index("file_name")
        _indices_setup = True
        return True
    except Exception as e:
        logger.error(f"Error creating indices on {col.name}: {e}")
        _indices_setup = False
        return False

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

    if await is_file_already_saved(file_id, file_name, media.file_size):
        return False, 0

    try:
        await col.insert_one(file)
        logger.info(f"{file_name} ɪꜱ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ꜱᴀᴠᴇᴅ.")
        return True, 1
    except DuplicateKeyError:
        logger.debug(f"{file_name} ɪꜱ ᴀʟʀᴇᴀᴅʏ ꜱᴀᴠᴇᴅ.")
        return False, 0
    except Exception as e:
        logger.error(f"Error saving to DB: {e}")
        return False, 2

def clean_file_name(file_name):
    """Clean and format the file name."""
    file_name = remove_junk(file_name)
    file_name = re.sub(r"(_|\-|\.|\+)", " ", file_name)
    old_file_name = ' '.join(file_name.split())
    return old_file_name

async def is_file_already_saved(file_id, file_name, file_size=0):
    """Check if the file is already saved in the collection."""
    if file_size:
        query = {'$or': [{'file_id': file_id}, {'file_name': file_name, 'file_size': file_size}]}
    else:
        query = {'$or': [{'file_id': file_id}, {'file_name': file_name}]}

    if await col.find_one(query):
        logger.debug(f"{file_name} ɪꜱ ᴀʟʀᴇᴀᴅʏ ꜱᴀᴠᴇᴅ.")
        return True
            
    return False

LANGUAGE_SYNONYMS = {
    "kannada": r"(?:\b|[\.\+\-_])(?:kannada|kan)(?:\b|[\.\+\-_])",
    "hindi": r"(?:\b|[\.\+\-_])(?:hindi|hin)(?:\b|[\.\+\-_])",
    "tamil": r"(?:\b|[\.\+\-_])(?:tamil|tam)(?:\b|[\.\+\-_])",
    "telugu": r"(?:\b|[\.\+\-_])(?:telugu|tel)(?:\b|[\.\+\-_])",
    "malayalam": r"(?:\b|[\.\+\-_])(?:malayalam|mal)(?:\b|[\.\+\-_])",
    "english": r"(?:\b|[\.\+\-_])(?:english|eng)(?:\b|[\.\+\-_])",
}

async def get_search_results(chat_id, query, file_type=None, max_results=10, offset=0, filter=False):
    """For given query return (results, next_offset)"""
    
    query = query.strip()
    query = re.sub(r"\s*&\s*", " & ", query)
    
    if not query:
        filter = {'file_name': re.compile('.', flags=re.IGNORECASE)}
    else:
        query_words = query.split()
        if len(query_words) == 1:
            # Single word search (strict matching)
            if query.lower() in LANGUAGE_SYNONYMS:
                raw_pattern = LANGUAGE_SYNONYMS[query.lower()]
            elif re.match(r"^s0*(\d+)$", query, re.IGNORECASE):
                s_num = re.match(r"^s0*(\d+)$", query, re.IGNORECASE).group(1)
                raw_pattern = rf'(?:\b|_)(?:s|season)[\s\.\+\-_]*0*{s_num}(?:\b|_|(?=[eE]))'
            elif query.lower() in ["and", "&"]:
                raw_pattern = r'(?:(?:\b|_)and(?:\b|_)|&)'
            else:
                if (1 <= len(query) <= 3 and query.isalnum()) or query.lower() in {"swat", "abcd"}:
                    escaped_word = r'[\s\.\+\-_]*'.join(re.escape(c) for c in query)
                else:
                    escaped_word = re.escape(query)
                escaped_word = re.sub(r"\\?['’‘]", "['’]", escaped_word)
                if escaped_word.endswith("['’]s") or escaped_word.endswith("s"):
                    escaped_word = re.sub(r"(\['’\]s|s)$", r"(?:['’]s|s)", escaped_word)
                raw_pattern = r'(?:\b|_)' + escaped_word + r'(?:\b|_)'
            try:
                regex = re.compile(raw_pattern, flags=re.IGNORECASE)
            except Exception:
                regex = re.compile(re.escape(query), flags=re.IGNORECASE)
            filter = {'file_name': regex}
        else:
            # Multi-word search (finds all words in ANY order)
            filter_and = []
            for word in query_words:
                if word.lower() in LANGUAGE_SYNONYMS:
                    filter_and.append({"file_name": {"$regex": LANGUAGE_SYNONYMS[word.lower()], "$options": "i"}})
                elif re.match(r"^s0*(\d+)$", word, re.IGNORECASE):
                    s_num = re.match(r"^s0*(\d+)$", word, re.IGNORECASE).group(1)
                    s_pat = rf'(?:\b|_)(?:s|season)[\s\.\+\-_]*0*{s_num}(?:\b|_|(?=[eE]))'
                    filter_and.append({"file_name": {"$regex": s_pat, "$options": "i"}})
                elif word.lower() in ["and", "&"]:
                    filter_and.append({"file_name": {"$regex": r'(?:(?:\b|_)and(?:\b|_)|&)', "$options": "i"}})
                else:
                    is_short = (len(word) <= 3 and word.isalnum()) or word.lower() in {"swat", "abcd"}
                    if is_short:
                        escaped_word = r'[\s\.\+\-_]*'.join(re.escape(c) for c in word)
                    else:
                        escaped_word = re.escape(word)
                    escaped_word = re.sub(r"\\?['’‘`]", "['’`]", escaped_word)
                    if escaped_word.endswith("['’`]s") or escaped_word.endswith("s"):
                        escaped_word = re.sub(r"(\['’`]s|s)$", r"(?:['’`]s|s)", escaped_word)
                    if is_short:
                        escaped_word = rf'(?:\b|_){escaped_word}(?:\b|_)'
                    filter_and.append({"file_name": {"$regex": escaped_word, "$options": "i"}})
            
            filter = {"$and": filter_and}
            
    total_results = await col.count_documents(filter)
    files = []
    
    if offset < total_results:
        cursor = col.find(filter).sort('$natural', -1).skip(offset).limit(max_results)
        async for file in cursor:
            file['file_id'] = file.get('file_id', file.get('_id'))
            files.append(file)
                
    next_offset = "" if (offset + max_results) >= total_results else (offset + max_results)
    return files, next_offset, total_results

async def get_bad_files(query, file_type=None, use_filter=False):
    """For given query return (results, next_offset)"""
    query = query.strip()
    query = re.sub(r"\s*&\s*", " & ", query)
    
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
                    {"file_name": {"$regex": (rf'(?:\b|_){re.escape(word)}(?:\b|_)' if (len(word) <= 3 and word.isalnum()) else re.escape(word)), "$options": "i"}} for word in query_words
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

    total_results = await col.count_documents(filter_criteria)
    docs = await col.find(filter_criteria).to_list(length=10000)
    files = []
    for doc in docs:
        doc['file_id'] = doc.get('file_id', doc.get('_id'))
    files.extend(docs)

    return files, total_results

async def get_file_details(query):
    filter_query = {'$or': [{'file_id': query}, {'_id': query}]}
    file = await col.find_one(filter_query)
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
    
async def reset_and_setup_indices():
    """Reset the index-setup flag and recreate all required indexes."""
    global _indices_setup
    _indices_setup = False
    return await setup_indices()
