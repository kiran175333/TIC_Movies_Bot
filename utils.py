import logging, asyncio, os, re, random, pytz, aiohttp, string, time, uuid
from info import *
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram import enums
from pyrogram.errors import *
from typing import Union
from Script import script
from datetime import datetime, date
from typing import List
from database.users_chats_db import db
from shortzy import Shortzy
from cachetools import TTLCache

def remove_junk(file_name):
    file_name = str(file_name)
    file_name = re.sub(r"(?i)\b(1tamilmv|movierulz|tamilblasters|tamilmv|hdhub4u|vegamovies|bollyflix|katmoviehd|themoviesboss|moviesflix|moviesmod|dotmovies|uhdmovies|ibomma|filmyzilla|9xmovies|jalshamoviez|mkvcinemas|pahe)(?:\.[a-z]{2,4})?\b", "", file_name)
    file_name = re.sub(r"(?i)(www\.?|@\w+|t\.me/[^\s]+|https?://[^\s]+)", "", file_name)
    file_name = re.sub(r"\[\s*\]|\(\s*\)", "", file_name)
    return ' '.join(file_name.split())

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
BTN_URL_REGEX = re.compile(r"(\[([^\[]+?)\]\((buttonurl|buttonalert):(?:/{0,2})(.+?)(:same)?\))")

# Limits the dictionaries to a safe size and auto-deletes expired tokens
TOKENS = TTLCache(maxsize=10000, ttl=600)
VERIFIED = TTLCache(maxsize=50000, ttl=VERIFY_EXPIRE)
SMART_OPEN = '“'
SMART_CLOSE = '”'
START_CHAR = ('\'', '"', SMART_OPEN)

async def background_deleter(bot):
    while True:
        await asyncio.sleep(10) # check every 10 secs
        now = time.time()
        pending = await db.get_pending_deletes(now)
        for item in pending:
            try:
                await bot.delete_messages(item['chat_id'], item['message_id'])
            except Exception:
                pass
            await db.remove_delete(item['_id'])

def delayed_delete(messages, delay=900):
    now = time.time()
    for msg in messages:
        if getattr(msg, "chat", None) and getattr(msg, "id", None):
            asyncio.create_task(db.add_delete(msg.chat.id, msg.id, now + delay))

# temp db for banned 
class temp(object):
    BANNED_USERS = []
    BANNED_CHATS = []
    ME = None
    BOT = None
    CURRENT=int(os.environ.get("SKIP", 2))
    CANCEL = {}
    U_NAME = None
    B_NAME = None
    SHORT = TTLCache(maxsize=2000, ttl=3600)
    SETTINGS = TTLCache(maxsize=500, ttl=3600)
    ALERTS = TTLCache(maxsize=2000, ttl=3600)

def check_callback_owner(query) -> bool:
    """
    Validates that query.from_user is authorized to interact with query.message.
    In private chat: authorized if message is in user's private chat.
    In group chats: authorized ONLY if query.message.reply_to_message exists,
    has from_user, and query.from_user.id matches the original requester.
    Returns True if authorized, False otherwise (fail closed).
    """
    if not query or not getattr(query, "from_user", None) or not getattr(query, "message", None):
        return False
    chat_type = query.message.chat.type
    if chat_type == enums.ChatType.PRIVATE:
        return query.message.chat.id == query.from_user.id
    if chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        reply = getattr(query.message, "reply_to_message", None)
        if not reply or not getattr(reply, "from_user", None):
            return False
        return query.from_user.id == reply.from_user.id
    return False

async def pub_is_subscribed(bot, query, channel):
    btn = []
    for id in channel:
        chat = await bot.get_chat(int(id))
        try:
            await bot.get_chat_member(id, query.from_user.id)
        except UserNotParticipant:
            btn.append(
                [InlineKeyboardButton(f'ᴊᴏɪɴ {chat.title}', url=chat.invite_link)]
            )
        except Exception as e:
            pass
    return btn

async def is_subscribed(bot, query):
    if not AUTH_CHANNEL:
        return True
    try:
        user = await bot.get_chat_member(AUTH_CHANNEL, query.from_user.id)
    except UserNotParticipant:
        pass
    except Exception as e:
        logger.exception(e)
        return True
    else:
        if user.status != enums.ChatMemberStatus.BANNED:
            return True
    return False

async def broadcast_messages(user_id, message):
    for _ in range(3):
        try:
            await message.copy(chat_id=user_id)
            return True, "ꜱᴜᴄᴄᴇꜱꜱ"
        except FloodWait as e:
            await asyncio.sleep(e.value)
            continue
        except UserDeactivated:
            await db.delete_user(int(user_id))
            logging.info(f"{user_id} - ʀᴇᴍᴏᴠᴇᴅ ꜰʀᴏᴍ ᴅᴀᴛᴀʙᴀꜱᴇ ʙᴇᴄᴀᴜꜱᴇ ᴛʜᴇ ᴀᴄᴄᴏᴜɴᴛ ᴡᴀꜱ ᴅᴇʟᴇᴛᴇᴅ.")
            return False, "ᴅᴇʟᴇᴛᴇᴅ"
        except UserIsBlocked:
            await db.delete_user(int(user_id))
            logging.info(f"{user_id} - ʙʟᴏᴄᴋᴇᴅ ᴛʜᴇ ʙᴏᴛ.")
            return False, "ʙʟᴏᴄᴋᴇᴅ"
        except PeerIdInvalid:
            await db.delete_user(int(user_id))
            logging.info(f"{user_id} - PeerIdInvalid")
            return False, "ᴇʀʀᴏʀ"
        except Exception as e:
            return False, "ᴇʀʀᴏʀ"
    return False, "ᴇʀʀᴏʀ"

async def broadcast_messages_group(chat_id, message):
    for _ in range(3):
        try:
            kd = await message.copy(chat_id=chat_id)
            return True, "ꜱᴜᴄᴄᴇꜱꜱ"
        except FloodWait as e:
            await asyncio.sleep(e.value)
            continue
        except Exception as e:
            return False, "ᴇʀʀᴏʀ"
    return False, "ᴇʀʀᴏʀ"
    
async def get_settings(group_id):
    settings = await db.get_settings(group_id)
    return settings
    
async def save_group_settings(group_id, key, value):
    current = await get_settings(group_id)
    current.update({key: value})
    await db.update_settings(group_id, current)
    
def get_size(size):
    units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB"]
    size = float(size)
    i = 0
    while size >= 1024.0 and i < len(units):
        i += 1
        size /= 1024.0
    return "%.2f %s" % (size, units[i])

def split_list(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]  

def get_file_id(msg: Message):
    if msg.media:
        for message_type in (
            "photo",
            "animation",
            "audio",
            "document",
            "video",
            "video_note",
            "voice",
            "sticker"
        ):
            obj = getattr(msg, message_type)
            if obj:
                setattr(obj, "message_type", message_type)
                return obj

def extract_user(message: Message) -> Union[int, str]:
    user_id = None
    user_first_name = None
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        user_first_name = message.reply_to_message.from_user.first_name

    elif len(message.command) > 1:
        if (
            len(message.entities) > 1 and
            message.entities[1].type == enums.MessageEntityType.TEXT_MENTION
        ):
           
            required_entity = message.entities[1]
            user_id = required_entity.user.id
            user_first_name = required_entity.user.first_name
        else:
            user_id = message.command[1]
            # don't want to make a request -_-
            user_first_name = user_id
        try:
            user_id = int(user_id)
        except ValueError:
            pass
    else:
        user_id = message.from_user.id
        user_first_name = message.from_user.first_name
    return (user_id, user_first_name)

def last_online(from_user):
    time = ""
    if from_user.is_bot:
        time += "ʙᴏᴛ :("
    elif from_user.status == enums.UserStatus.RECENTLY:
        time += "ʀᴇᴄᴇɴᴛʟʏ"
    elif from_user.status == enums.UserStatus.LAST_WEEK:
        time += "ᴡɪᴛʜɪɴ ᴛʜᴇ ʟᴀꜱᴛ ᴡᴇᴇᴋ"
    elif from_user.status == enums.UserStatus.LAST_MONTH:
        time += "ᴡɪᴛʜɪɴ ᴛʜᴇ ʟᴀꜱᴛ ᴍᴏɴᴛʜ"
    elif from_user.status == enums.UserStatus.LONG_AGO:
        time += "ᴀ ʟᴏɴɢ ᴛɪᴍᴇ ᴀɢᴏ :("
    elif from_user.status == enums.UserStatus.ONLINE:
        time += "ᴄᴜʀʀᴇɴᴛʟʏ ᴏɴʟɪɴᴇ"
    elif from_user.status == enums.UserStatus.OFFLINE:
        if from_user.last_online_date:
            time += from_user.last_online_date.strftime("%a, %d %b %Y, %H:%M:%S")
        else:
            time += "ᴏꜰꜰʟɪɴᴇ"
    return time

def split_quotes(text: str) -> List:
    if not any(text.startswith(char) for char in START_CHAR):
        return text.split(None, 1)
    counter = 1  # ignore first char -> is some kind of quote
    while counter < len(text):
        if text[counter] == "\\":
            counter += 1
        elif text[counter] == text[0] or (text[0] == SMART_OPEN and text[counter] == SMART_CLOSE):
            break
        counter += 1
    else:
        return text.split(None, 1)

    # 1 to avoid starting quote, and counter is exclusive so avoids ending
    key = remove_escapes(text[1:counter].strip())
    # index will be in range, or `else` would have been executed and returned
    rest = text[counter + 1:].strip()
    if not key:
        key = text[0] + text[0]
    return list(filter(None, [key, rest]))

def gfilterparser(text):
    if "buttonalert" in text:
        text = (text.replace("\n", "\\n").replace("\t", "\\t"))
    buttons = []
    note_data = ""
    prev = 0
    i = 0
    alerts = []
    alert_id = str(uuid.uuid4())[:8]
    for match in BTN_URL_REGEX.finditer(text):
        # Check if btnurl is escaped
        n_escapes = 0
        to_check = match.start(1) - 1
        while to_check > 0 and text[to_check] == "\\":
            n_escapes += 1
            to_check -= 1

        # if even, not escaped -> create button
        if n_escapes % 2 == 0:
            note_data += text[prev:match.start(1)]
            prev = match.end(1)
            if match.group(3) == "buttonalert":
                # create a thruple with button label, url, and newline status
                if bool(match.group(5)) and buttons:
                    buttons[-1].append(InlineKeyboardButton(
                        text=match.group(2),
                        callback_data=f"gfilteralert:{i}:{alert_id}"
                    ))
                else:
                    buttons.append([InlineKeyboardButton(
                        text=match.group(2),
                        callback_data=f"gfilteralert:{i}:{alert_id}"
                    )])
                i += 1
                alerts.append(match.group(4))
            elif bool(match.group(5)) and buttons:
                buttons[-1].append(InlineKeyboardButton(
                    text=match.group(2),
                    url=match.group(4).replace(" ", "")
                ))
            else:
                buttons.append([InlineKeyboardButton(
                    text=match.group(2),
                    url=match.group(4).replace(" ", "")
                )])

        else:
            note_data += text[prev:to_check]
            prev = match.start(1) - 1
    else:
        note_data += text[prev:]

    if alerts:
        temp.ALERTS[alert_id] = alerts

    try:
        return note_data, buttons, alerts
    except Exception:
        return note_data, buttons, None

def parser(text):
    if "buttonalert" in text:
        text = (text.replace("\n", "\\n").replace("\t", "\\t"))
    buttons = []
    note_data = ""
    prev = 0
    i = 0
    alerts = []
    alert_id = str(uuid.uuid4())[:8]
    for match in BTN_URL_REGEX.finditer(text):
        # Check if btnurl is escaped
        n_escapes = 0
        to_check = match.start(1) - 1
        while to_check > 0 and text[to_check] == "\\":
            n_escapes += 1
            to_check -= 1

        # if even, not escaped -> create button
        if n_escapes % 2 == 0:
            note_data += text[prev:match.start(1)]
            prev = match.end(1)
            if match.group(3) == "buttonalert":
                # create a thruple with button label, url, and newline status
                if bool(match.group(5)) and buttons:
                    buttons[-1].append(InlineKeyboardButton(
                        text=match.group(2),
                        callback_data=f"alertmessage:{i}:{alert_id}"
                    ))
                else:
                    buttons.append([InlineKeyboardButton(
                        text=match.group(2),
                        callback_data=f"alertmessage:{i}:{alert_id}"
                    )])
                i += 1
                alerts.append(match.group(4))
            elif bool(match.group(5)) and buttons:
                buttons[-1].append(InlineKeyboardButton(
                    text=match.group(2),
                    url=match.group(4).replace(" ", "")
                ))
            else:
                buttons.append([InlineKeyboardButton(
                    text=match.group(2),
                    url=match.group(4).replace(" ", "")
                )])

        else:
            note_data += text[prev:to_check]
            prev = match.start(1) - 1
    else:
        note_data += text[prev:]

    if alerts:
        temp.ALERTS[alert_id] = alerts

    try:
        return note_data, buttons, alerts
    except Exception:
        return note_data, buttons, None

def remove_escapes(text: str) -> str:
    res = ""
    is_escaped = False
    for counter in range(len(text)):
        if is_escaped:
            res += text[counter]
            is_escaped = False
        elif text[counter] == "\\":
            is_escaped = True
        else:
            res += text[counter]
    return res
                           
async def get_shortlink(link):
    URL = SHORTLINK_URL
    API = SHORTLINK_API
    if URL == "api.shareus.io":
        url = f'https://{URL}/easy_api'
        params = {
            "key": API,
            "link": link,
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, raise_for_status=True, ssl=False) as response:
                    data = await response.text()
                    return data
        except Exception as e:
            logger.error(e)
            return None
    else:
        try:
            shortzy = Shortzy(api_key=API, base_site=URL)
            link = await shortzy.convert(link)
            return link
        except Exception as e:
            logger.error(f"Shortener Down: {e}")
            return None
        
async def get_verify_shorted_link(link, url, api):
    API = api
    URL = url
    if URL == "api.shareus.io":
        url = f'https://{URL}/easy_api'
        params = {
            "key": API,
            "link": link,
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, raise_for_status=True, ssl=False) as response:
                    data = await response.text()
                    return data
        except Exception as e:
            logger.error(e)
            return None
    else:
        try:
            shortzy = Shortzy(api_key=API, base_site=URL)
            link = await shortzy.convert(link)
            return link
        except Exception as e:
            logger.error(f"Shortener Down: {e}")
            return None
        
async def check_token(bot, userid, token):
    user = await bot.get_users(userid)
    if not await db.is_user_exist(user.id):
        await db.add_user(user.id, user.first_name)
        await bot.send_message(LOG_CHANNEL, script.LOG_TEXT_P.format(user.id, user.mention))
    if user.id in TOKENS.keys():
        TKN = TOKENS[user.id]
        if token in TKN.keys():
            is_used = TKN[token]
            if is_used == True:
                return False
            else:
                return True
        else:
            return False
    else:
        return False

async def get_token(bot, userid, link):
    user = await bot.get_users(userid)
    if not await db.is_user_exist(user.id):
        await db.add_user(user.id, user.first_name)
        await bot.send_message(LOG_CHANNEL, script.LOG_TEXT_P.format(user.id, user.mention))
    token = ''.join(random.choices(string.ascii_letters + string.digits, k=7))
    TOKENS[user.id] = {token: False}
    link = f"{link}verify-{user.id}-{token}"
    shortened_verify_url = await get_verify_shorted_link(link, VERIFY_SHORTLINK_URL, VERIFY_SHORTLINK_API)
    return shortened_verify_url

async def verify_user(bot, userid, token):
    user = await bot.get_users(userid)
    if not await db.is_user_exist(user.id):
        await db.add_user(user.id, user.first_name)
        await bot.send_message(LOG_CHANNEL, script.LOG_TEXT_P.format(user.id, user.mention))
    TOKENS[user.id] = {token: True}
    VERIFIED[user.id] = time.time()

async def check_verification(bot, userid):
    user = await bot.get_users(userid)
    if not await db.is_user_exist(user.id):
        await db.add_user(user.id, user.first_name)
        await bot.send_message(LOG_CHANNEL, script.LOG_TEXT_P.format(user.id, user.mention))
    if user.id in VERIFIED.keys():
        verified_time = VERIFIED[user.id]
        if (time.time() - verified_time) > VERIFY_EXPIRE:
            return False
        else:
            return True
    else:
        return False  
    

async def get_cap(settings, remaining_seconds, files, query, total_results, search):
    warn_text = "\n\n<b>⚠️ ᴀꜰᴛᴇʀ 15 ᴍɪɴᴜᴛᴇꜱ ᴛʜɪꜱ ᴍᴇꜱꜱᴀɢᴇ ᴡɪʟʟ ʙᴇ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ᴅᴇʟᴇᴛᴇᴅ.</b>" if settings.get('auto_delete', True) else ""
    user_mention = query.from_user.mention if getattr(query, "from_user", None) else "User"
    cap = f"<b>🫡 ʜᴇʏ {user_mention},\n\n📬 ʜᴇʀᴇ ɪꜱ ᴡʜᴀᴛ ɪ ꜰᴏᴜɴᴅ ɪɴ ᴍʏ ᴅᴀᴛᴀʙᴀꜱᴇ ꜰᴏʀ ʏᴏᴜʀ Qᴜᴇʀʏ {search.replace('<', '&lt;').replace('>', '&gt;')}.</b>"

    # The warning is now appended directly after the header
    cap += warn_text + "\n\n"

    # The file loop executes after the warning
    if not settings.get("button", True):
        for file in files:
            safe_name = file['file_name'].replace('<', '&lt;').replace('>', '&gt;')
            cap += f"📂 <a href='https://telegram.me/{temp.U_NAME}?start=file_{file['file_id']}'>[{get_size(file['file_size'])}] {safe_name}</a>\n\n"

    return cap


async def get_seconds(time_string):
    def extract_value_and_unit(ts):
        value = ""
        unit = ""
        index = 0
        while index < len(ts) and ts[index].isdigit():
            value += ts[index]
            index += 1
        unit = ts[index:]
        if value:
            value = int(value)
        return value, unit
    value, unit = extract_value_and_unit(time_string)
    if unit == 's':
        return value
    elif unit == 'min':
        return value * 60
    elif unit == 'hour':
        return value * 3600
    elif unit == 'day':
        return value * 86400
    elif unit == 'month':
        return value * 86400 * 30
    elif unit == 'year':
        return value * 86400 * 365
    else:
        return 0
