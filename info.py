import re
from os import environ
from Script import script 

def is_enabled(value, default):
    if isinstance(value, bool):
        return value
    if str(value).lower() in ["true", "yes", "1", "enable", "y"]:
        return True
    elif str(value).lower() in ["false", "no", "0", "disable", "n"]:
        return False
    else:
        return default

id_pattern = re.compile(r'(?i)^-?\d+$')

# Bot information
SESSION = environ.get('SESSION', 'TheInsomniacsClub')
api_id_raw = environ.get('API_ID', '').strip()
if not id_pattern.search(api_id_raw):
    raise ValueError(
        "API_ID is required and must be a valid integer. "
        "Set the API_ID environment variable before starting the bot."
    )
API_ID = int(api_id_raw)
_api_hash = environ.get('API_HASH', '').strip()
if not _api_hash:
    raise ValueError(
        "API_HASH is required. "
        "Set the API_HASH environment variable before starting the bot."
    )
API_HASH = _api_hash

_bot_token = environ.get('BOT_TOKEN', '').strip()
if not _bot_token:
    raise ValueError(
        "BOT_TOKEN is required. "
        "Set the BOT_TOKEN environment variable before starting the bot."
    )
BOT_TOKEN = _bot_token

# This Pictures Is For Start Message Picture, You Can Add Multiple By Giving One Space Between Each.
PICS = (environ.get('PICS', 'https://telegra.ph/file/3dfa7005df1d8bd279b07.jpg')).split()

# Admins & Users
ADMINS = []
for admin in environ.get('ADMINS', '').split():
    admin = admin.strip()
    if not admin:
        continue
    if id_pattern.search(admin):
        ADMINS.append(int(admin))
    else:
        ADMINS.append(admin)

def is_admin(user):
    if user is None:
        return False
    if isinstance(user, int):
        return user in ADMINS or str(user) in ADMINS
    if isinstance(user, str):
        user = user.strip()
        if id_pattern.search(user):
            return int(user) in ADMINS or user in ADMINS
        clean_uname = user.lstrip('@').lower()
        return any(
            str(a).lstrip('@').lower() == clean_uname
            for a in ADMINS
        )
    uid = getattr(user, 'id', None)
    if uid is not None and is_admin(uid):
        return True
    uname = getattr(user, 'username', None)
    if uname and is_admin(uname):
        return True
    return False

# This Channel Is For When User Start Your Bot Then Bot Send That User Name And Id In This Log Channel, Same For Group Also.
log_channel = environ.get('LOG_CHANNEL', '').strip()
if not id_pattern.search(log_channel):
    raise ValueError(
        "LOG_CHANNEL is required and must be a valid integer channel ID. "
        "Set the LOG_CHANNEL environment variable before starting the bot."
    )
LOG_CHANNEL = int(log_channel)

# This Is File Channel Where You Upload Your File Then Bot Automatically Save It In Database 
CHANNELS = [int(ch) if id_pattern.search(ch) else ch for ch in environ.get('CHANNELS', '').split()]  # For Multiple Id Use One Space Between Each.

# This Is Force Subscribe Channel, also known as Auth Channel 
auth_channel = environ.get('AUTH_CHANNEL', '').strip() # give your force subscribe channel id here else leave it blank
AUTH_CHANNEL = int(auth_channel) if auth_channel and id_pattern.search(auth_channel) else None

auth_group = environ.get('AUTH_GROUP', '').strip()
AUTH_GROUP = int(auth_group) if auth_group and id_pattern.search(auth_group) else None

req_to_join = environ.get('REQ_TO_JOIN', 'True').lower()
REQ_TO_JOIN = req_to_join == 'true'

# This Channel Is For Index Request 
idx_channel = environ.get('INDEX_REQ_CHANNEL', '').strip()
INDEX_REQ_CHANNEL = int(idx_channel) if id_pattern.search(idx_channel) else LOG_CHANNEL

# MongoDB Configuration
# DATABASE_URI is required. No localhost fallback — a missing URI must be caught at startup.
_database_uri = environ.get('DATABASE_URI', '').strip()
if not _database_uri:
    raise ValueError(
        "DATABASE_URI is required. "
        "Set the DATABASE_URI environment variable to your MongoDB connection string before starting the bot."
    )
DATABASE_URI = _database_uri
DATABASE_NAME = environ.get('DATABASE_NAME', "Cluster0").strip() or "Cluster0"
COLLECTION_NAME = environ.get('COLLECTION_NAME', 'Telegram_files').strip() or 'Telegram_files'
MULTIPLE_DATABASE = is_enabled(environ.get('MULTIPLE_DATABASE', False), False)

# Additional File Storage Clusters (Used if MULTIPLE_DATABASE is True)
DATABASE_URI2 = environ.get('DATABASE_URI2', "")
DATABASE_URI3 = environ.get('DATABASE_URI3', "")

# Premium Settings
PREMIUM_MODE = is_enabled(environ.get('PREMIUM_MODE', True), True)
PAYMENT_TEXT = environ.get('PAYMENT_TEXT', '<b>💎 ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ ᴘʟᴀɴꜱ\n✨ ɪɴᴄʟᴜᴅᴇꜱ ᴀᴄᴄᴇꜱꜱ ᴛᴏ ᴀʟʟ 𝟹 ʙᴏᴛꜱ ᴄᴏᴍʙɪɴᴇᴅ\n\n‣ ₹30 ➪ 1 ᴍᴏɴᴛʜ\n‣ ₹60 ➪ 2 ᴍᴏɴᴛʜꜱ\n‣ ₹90 ➪ 3 ᴍᴏɴᴛʜꜱ\n‣ ₹180 ➪ 6 ᴍᴏɴᴛʜꜱ\n\n🎁 ꜰᴇᴀᴛᴜʀᴇꜱ\n‣ ᴅɪʀᴇᴄᴛ &amp; ʜɪɢʜ-ꜱᴘᴇᴇᴅ ꜰɪʟᴇꜱ\n‣ ᴀᴅ-ꜰʀᴇᴇ ᴀᴄᴄᴇꜱꜱ\n‣ ᴜɴʟɪᴍɪᴛᴇᴅ ғɪʟᴇs ᴀᴄᴄᴇss\n\n👥 ɴᴀᴍᴇ: <code>DARSHAN C</code>\n💳 ᴜᴘɪ ɪᴅ: <code>darshancg175@okhdfcbank</code>\n\nᴘʟᴇᴀꜱᴇ ꜱᴇɴᴅ ʏᴏᴜʀ ᴘᴀʏᴍᴇɴᴛ ꜱᴄʀᴇᴇɴꜱʜᴏᴛ ᴀɴᴅ ᴛᴇʟᴇɢʀᴀᴍ ɪᴅ ᴛᴏ ᴏᴜʀ ꜱᴜᴘᴘᴏʀᴛ.\n\nᴄʜᴇᴄᴋ ʏᴏᴜʀ ɪᴅ: /id\nᴄʜᴇᴄᴋ ᴀᴄᴛɪᴠᴇ ᴘʟᴀɴ: /myplan\n\nꜰᴇᴇʟ ꜰʀᴇᴇ ᴛᴏ ᴄᴏɴᴛᴀᴄᴛ ᴜꜱ ɪꜰ ʏᴏᴜ ʜᴀᴠᴇ ᴀɴʏ ǫᴜᴇꜱᴛɪᴏɴꜱ!</b>')

# Links
GRP_LNK = environ.get('GRP_LNK', 'https://t.me/+F5kaO_-0cgswODE9')
CHNL_LNK = environ.get('CHNL_LNK', 'https://t.me/TheInsomniacsClub')
SUPPORT_LINK = environ.get('SUPPORT_LINK', 'https://t.me/TICSupportBot')

# True Or False
PM_SEARCH = is_enabled(environ.get('PM_SEARCH', True), True)
BUTTON_MODE = is_enabled(environ.get('BUTTON_MODE', True), True)
MAX_BTN = is_enabled(environ.get('MAX_BTN', True), True)
AUTO_FFILTER = is_enabled(environ.get('AUTO_FFILTER', True), True)
AUTO_DELETE = is_enabled(environ.get('AUTO_DELETE', True), True)
USE_CAPTION_FILTER = is_enabled(environ.get('USE_CAPTION_FILTER', True), True)

# Tutorial Link (Used for both Verification and Shortlinks)
TUTORIAL = environ.get('TUTORIAL', 'https://t.me/TheInsomniacsClub/459')

# Token Verification Info :
# VERIFY is auto-disabled when VERIFY_SHORTLINK_URL or VERIFY_SHORTLINK_API are empty,
# because an enabled VERIFY with no working shortlink backend is an unusable state.
VERIFY_SHORTLINK_URL = environ.get('VERIFY_SHORTLINK_URL', '').strip()
VERIFY_SHORTLINK_API = environ.get('VERIFY_SHORTLINK_API', '').strip()
VERIFY_EXPIRE = int(environ.get('VERIFY_EXPIRE', 900))
_verify_requested = is_enabled(environ.get('VERIFY', False), False)
if _verify_requested and (not VERIFY_SHORTLINK_URL or not VERIFY_SHORTLINK_API):
    import logging as _logging
    _logging.getLogger(__name__).warning(
        "VERIFY is enabled but VERIFY_SHORTLINK_URL or VERIFY_SHORTLINK_API is not set. "
        "VERIFY has been automatically disabled. Set both values to enable verification."
    )
    VERIFY = False
else:
    VERIFY = _verify_requested

# Shortlink Info
# SHORTLINK_MODE is auto-disabled when SHORTLINK_URL or SHORTLINK_API are empty,
# because shortlinking with no configured backend will fail every request.
SHORTLINK_URL = environ.get('SHORTLINK_URL', 'nowshort.com').strip()
SHORTLINK_API = environ.get('SHORTLINK_API', '86668b40e4986c631ca9a2a56a0d85c1d35e9c63').strip()
_shortlink_requested = is_enabled(environ.get('SHORTLINK_MODE', True), True)
if _shortlink_requested and (not SHORTLINK_URL or not SHORTLINK_API):
    import logging as _logging
    _logging.getLogger(__name__).warning(
        "SHORTLINK_MODE is enabled but SHORTLINK_URL or SHORTLINK_API is not set. "
        "SHORTLINK_MODE has been automatically disabled. Set both values to enable shortlinks."
    )
    SHORTLINK_MODE = False
else:
    SHORTLINK_MODE = _shortlink_requested

# Others
MAX_B_TN = environ.get("MAX_B_TN", "5")
PORT = environ.get("PORT", "8080")
MSG_ALRT = environ.get('MSG_ALRT', 'ᴡʜᴀᴛ ᴀʀᴇ ʏᴏᴜ ʟᴏᴏᴋɪɴɢ ғᴏʀ ?')
CUSTOM_FILE_CAPTION = environ.get("CUSTOM_FILE_CAPTION", f"{script.CAPTION}")

# Choose Option Settings 
LANGUAGES = ["kannada", "kan", "english", "eng", "hindi", "hin", "telugu", "tel", "malayalam", "mal", "tamil", "tam"]
QUALITIES = ["360p", "480p", "540p", "576p", "720p", "1080p", "1440p", "2160p"]
