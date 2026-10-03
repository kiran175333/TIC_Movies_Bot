import os, logging, string, asyncio, time, re, ast, random, math, pytz, pyrogram
from datetime import datetime, timedelta, date, time
from cachetools import TTLCache

SPAM_TRACKER = TTLCache(maxsize=10000, ttl=1.5)
from Script import script
from info import *
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto, ChatPermissions, WebAppInfo
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait, UserIsBlocked, MessageNotModified, PeerIdInvalid
from pyrogram.errors import MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty
from utils import remove_junk, get_size, is_subscribed, pub_is_subscribed, temp, get_settings, save_group_settings, get_cap, check_callback_owner
from database.users_chats_db import db
from database.ia_filterdb import col, sec_col, thi_col, db as fir_db, sec_db, thi_db, get_file_details, get_search_results, get_bad_files, add_search_query
from database.filters_mdb import del_all, find_filter, get_filters
from database.connections_mdb import mydb, active_connection, all_connections, delete_connection, if_active, make_active, make_inactive
from database.gfilters_mdb import find_gfilter, get_gfilters, del_allg
from urllib.parse import quote_plus
from cachetools import TTLCache
def clean_filename(name):
    return remove_junk(name)
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
lock = asyncio.Lock()
BUTTON = TTLCache(maxsize=2000, ttl=3600)
BUTTONS = TTLCache(maxsize=2000, ttl=3600)
FRESH = TTLCache(maxsize=2000, ttl=3600)
BUTTONS0 = TTLCache(maxsize=2000, ttl=3600)
BUTTONS1 = TTLCache(maxsize=2000, ttl=3600)
BUTTONS2 = TTLCache(maxsize=2000, ttl=3600)
def get_header_buttons(key):
    return [
        [
            InlineKeyboardButton("ᴡᴇʙ sᴇʀɪᴇs & ᴀɴɪᴍᴇ ʙᴏᴛ", url="https://t.me/TIC_Web_Series_Anime_Bot"),
            InlineKeyboardButton("ʟᴀᴛᴇsᴛ ᴍᴏᴠɪᴇꜱ ʙᴏᴛ", url="https://t.me/TIC_Latest_Movies_Bot")
        ],
        [
            InlineKeyboardButton("ʟᴀɴɢᴜᴀɢᴇꜱ", callback_data=f"languages#{key}"),
            InlineKeyboardButton("ǫᴜᴀʟɪᴛʏ", callback_data=f"qualities#{key}")
        ]
    ]
@Client.on_message(filters.group & filters.text & filters.incoming)
async def give_filter(client, message):
    settings = await get_settings(message.chat.id)
    chatid = message.chat.id 
    user_id = message.from_user.id if message.from_user else 0
    
    if settings.get('fsub'):
        try:
            btn = await pub_is_subscribed(client, message, settings['fsub'])
            if btn:
                btn.append([InlineKeyboardButton("ᴜɴᴍᴜᴛᴇ ᴍᴇ", callback_data=f"unmuteme#{int(user_id)}")])
                await client.restrict_chat_member(chatid, message.from_user.id, ChatPermissions(can_send_messages=False))
                await message.reply_photo(
                    photo=random.choice(PICS), 
                    caption=f"ʜᴇʟʟᴏ {message.from_user.mention},\n\nᴘʟᴇᴀꜱᴇ ᴊᴏɪɴ ᴏᴜʀ ᴄʜᴀɴɴᴇʟ, ᴛʜᴇɴ ᴄʟɪᴄᴋ ᴏɴ ᴛʜᴇ 'ᴜɴᴍᴜᴛᴇ ᴍᴇ' ʙᴜᴛᴛᴏɴ.", 
                    reply_markup=InlineKeyboardMarkup(btn), 
                    parse_mode=enums.ParseMode.HTML
                )
                return
        except Exception as e:
            print(e)
            
    manual = await manual_filters(client, message)
    if manual == False:
        if message.text.startswith("/") or message.text.startswith("#") or message.text.startswith("!"):
            return
        try:
            if settings['auto_ffilter']:
                ai_search = True
                await auto_filter(client, message.text, message, None, ai_search)
        except KeyError:
            grpid = await active_connection(str(message.from_user.id))
            await save_group_settings(grpid, 'auto_ffilter', True)
            settings = await get_settings(message.chat.id)
            if settings['auto_ffilter']:
                ai_search = True
                await auto_filter(client, message.text, message, None, ai_search)
                
@Client.on_message(filters.private & filters.text & filters.incoming)
async def pm_text(bot, message):
    content = message.text
    if not content:
        return
    # 1. Ignore commands, hashtags, and prefixes
    if content.startswith(("/", "#", "!")):
        return
    # 2. Ignore multi-line messages (broadcast drafts, recent lists, copied posts)
    if "\n" in content:
        return
    # 3. Ignore links or indexing URLs
    if any(x in content.lower() for x in ["http://", "https://", "t.me/"]):
        return
    # 4. Ignore long text (movie titles are short and concise)
    if len(content) > 80:
        return
        
    if PM_SEARCH:
        ai_search = True
        # Clamp button text to 25 chars to prevent Telegram 64-byte button limits
        btn_label = content if len(content) <= 25 else f"{content[:22]}..."
        reply_msg = await message.reply_sticker(
            "CAACAgQAAxkBAAEKeqNlIpmeUoOEsEWOWEiPxPi3hH5q-QACbg8AAuHqsVDaMQeY6CcRojAE", 
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f'sᴇᴀʀᴄʜɪɴɢ ғᴏʀ {btn_label}', url=CHNL_LNK)]])
        )
        await auto_filter(bot, content, message, reply_msg, ai_search)
    
@Client.on_callback_query(filters.regex(r"^next"))
async def next_page(bot, query):
    try:
        ident, req, key, offset = query.data.split("_")
    except (ValueError, AttributeError):
        return await query.answer("ɪɴᴠᴀʟɪᴅ ʀᴇǫᴜᴇꜱᴛ", show_alert=True)
    
    if not query.from_user:
        return await query.answer("ᴜɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ", show_alert=True)
    curr_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
    
    try:
        req_id = int(req)
    except ValueError:
        req_id = 0
    
    if req_id not in [query.from_user.id, 0]:
        return await query.answer(
            f"ʜᴇʟʟᴏ {query.from_user.first_name},\n\nᴛʜɪꜱ ɪꜱ ɴᴏᴛ ʏᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ.\n\nᴘʟᴇᴀꜱᴇ ʀᴇǫᴜᴇꜱᴛ ʏᴏᴜʀ ᴏᴡɴ",
            show_alert=True
        )
        
    try:
        offset = int(offset)
    except Exception:
        offset = 0
        
    search = BUTTONS.get(key)
    if not search:
        search = FRESH.get(key)
    
    # Fix 2: Restored the safety check so it doesn't send 'None' to the database
    if not search:
        return await query.answer("ᴛʜɪꜱ ᴍᴇꜱꜱᴀɢᴇ ɪꜱ ᴛᴏᴏ ᴏʟᴅ.\n\nᴘʟᴇᴀꜱᴇ ꜱᴇᴀʀᴄʜ ᴀɢᴀɪɴ", show_alert=True)
    settings = await get_settings(query.message.chat.id)
    b_limit = 10 if settings.get('max_btn', True) else int(MAX_B_TN)
    
    files, n_offset, total = await get_search_results(query.message.chat.id, search, max_results=b_limit, offset=offset, filter=True)
    try:
        n_offset = int(n_offset)
    except Exception:
        n_offset = 0
    if not files:
        return
    temp.SHORT[query.from_user.id] = query.message.chat.id
    settings = await get_settings(query.message.chat.id)
    pre = 'file'
    if settings['button']:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"[{get_size(file['file_size'])}] {clean_filename(file['file_name'])}", callback_data=f'{pre}#{file["file_id"]}'
                ),
            ]
            for file in files
        ]
        btn = get_header_buttons(key) + btn
    else:
        btn = []
        btn = get_header_buttons(key) + btn
    try:
        if settings['max_btn']:
            if 0 < offset <= 10:
                off_set = 0
            elif offset == 0:
                off_set = None
            else:
                off_set = offset - 10
            if n_offset == 0:
                btn.append(
                    [InlineKeyboardButton("⟵ ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}"), InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages")]
                )
            elif off_set is None:
                btn.append([InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages"), InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages"), InlineKeyboardButton("ɴᴇxᴛ ⟶", callback_data=f"next_{req}_{key}_{n_offset}")])
            else:
                btn.append(
                    [
                        InlineKeyboardButton("⟵ ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}"),
                        InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages"),
                        InlineKeyboardButton("ɴᴇxᴛ ⟶", callback_data=f"next_{req}_{key}_{n_offset}")
                    ],
                )
        else:
            if 0 < offset <= int(MAX_B_TN):
                off_set = 0
            elif offset == 0:
                off_set = None
            else:
                off_set = offset - int(MAX_B_TN)
            if n_offset == 0:
                btn.append(
                    [InlineKeyboardButton("⟵ ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}"), InlineKeyboardButton(f"{math.ceil(int(offset)/int(MAX_B_TN))+1} / {math.ceil(total/int(MAX_B_TN))}", callback_data="pages")]
                )
            elif off_set is None:
                btn.append([InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages"), InlineKeyboardButton(f"{math.ceil(int(offset)/int(MAX_B_TN))+1} / {math.ceil(total/int(MAX_B_TN))}", callback_data="pages"), InlineKeyboardButton("ɴᴇxᴛ ⟶", callback_data=f"next_{req}_{key}_{n_offset}")])
            else:
                btn.append(
                    [
                        InlineKeyboardButton("⟵ ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}"),
                        InlineKeyboardButton(f"{math.ceil(int(offset)/int(MAX_B_TN))+1} / {math.ceil(total/int(MAX_B_TN))}", callback_data="pages"),
                        InlineKeyboardButton("ɴᴇxᴛ ⟶", callback_data=f"next_{req}_{key}_{n_offset}")
                    ],
                )
    except KeyError:
        await save_group_settings(query.message.chat.id, 'max_btn', True)
        if 0 < offset <= 10:
            off_set = 0
        elif offset == 0:
            off_set = None
        else:
            off_set = offset - 10
        if n_offset == 0:
            btn.append(
                [InlineKeyboardButton("⟵ ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}"), InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages")]
            )
        elif off_set is None:
            btn.append([InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages"), InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages"), InlineKeyboardButton("ɴᴇxᴛ ⟶", callback_data=f"next_{req}_{key}_{n_offset}")])
        else:
            btn.append(
                [
                    InlineKeyboardButton("⟵ ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}"),
                    InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages"),
                    InlineKeyboardButton("ɴᴇxᴛ ⟶", callback_data=f"next_{req}_{key}_{n_offset}")
                ],
            )
    if not settings["button"]:
        cur_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
        time_difference = timedelta(hours=cur_time.hour, minutes=cur_time.minute, seconds=(cur_time.second+(cur_time.microsecond/1000000))) - timedelta(hours=curr_time.hour, minutes=curr_time.minute, seconds=(curr_time.second+(curr_time.microsecond/1000000)))
        remaining_seconds = "{:.2f}".format(time_difference.total_seconds())
        cap = await get_cap(settings, remaining_seconds, files, query, total, search)
        try:
            await query.message.edit_text(text=cap, reply_markup=InlineKeyboardMarkup(btn), disable_web_page_preview=True)
        except MessageNotModified:
            pass
    else:
        try:
            await query.edit_message_reply_markup(
                reply_markup=InlineKeyboardMarkup(btn)
            )
        except MessageNotModified:
            pass
    await query.answer()
    
#languages
@Client.on_callback_query(filters.regex(r"^languages#"))
async def languages_cb_handler(client: Client, query: CallbackQuery):
    if not check_callback_owner(query):
        return await query.answer(
            f"ʜᴇʟʟᴏ {query.from_user.first_name if query.from_user else ''},\n\nᴛʜɪꜱ ɪꜱ ɴᴏᴛ ʏᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ.\n\nᴘʟᴇᴀꜱᴇ ʀᴇǫᴜᴇꜱᴛ ʏᴏᴜʀ ᴏᴡɴ",
            show_alert=True,
        )
    try:
        _, key = query.data.split("#")
    except (ValueError, AttributeError):
        return await query.answer("ɪɴᴠᴀʟɪᴅ ʀᴇǫᴜᴇꜱᴛ", show_alert=True)
    search = FRESH.get(key)
    if not search:
        return await query.answer("ᴛʜɪꜱ ᴍᴇꜱꜱᴀɢᴇ ɪꜱ ᴛᴏᴏ ᴏʟᴅ.\n\nᴘʟᴇᴀꜱᴇ ꜱᴇᴀʀᴄʜ ᴀɢᴀɪɴ", show_alert=True)
    try:
        search = search.replace(' ', '_')
    except Exception:
        pass
    btn = []
    for i in range(0, len(LANGUAGES)-1, 2):
        btn.append([
            InlineKeyboardButton(
                text=LANGUAGES[i].title(),
                callback_data=f"fl#{LANGUAGES[i].lower()}#{key}"
            ),
            InlineKeyboardButton(
                text=LANGUAGES[i+1].title(),
                callback_data=f"fl#{LANGUAGES[i+1].lower()}#{key}"
            ),
        ])
    btn.insert(
        0,
        [
            InlineKeyboardButton(
                text="ꜱᴇʟᴇᴄᴛ ʏᴏᴜʀ ʟᴀɴɢᴜᴀɢᴇꜱ", callback_data="ident"
            )
        ],
    )
    req = query.from_user.id
    offset = 0
    btn.append([InlineKeyboardButton(text="↭ ʙᴀᴄᴋ ᴛᴏ ʜᴏᴍᴇ ​↭", callback_data=f"fl#homepage#{key}")])
    try:
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(btn)
        )
    except MessageNotModified:
        pass
        
@Client.on_callback_query(filters.regex(r"^fl#"))
async def filter_languages_cb_handler(client: Client, query: CallbackQuery):
    try:
        _, lang, key = query.data.split("#")
    except (ValueError, AttributeError):
        return await query.answer("ɪɴᴠᴀʟɪᴅ ʀᴇǫᴜᴇꜱᴛ", show_alert=True)
    if not check_callback_owner(query):
        return await query.answer(
            f"ʜᴇʟʟᴏ {query.from_user.first_name if query.from_user else ''},\n\nᴛʜɪꜱ ɪꜱ ɴᴏᴛ ʏᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ.\n\nᴘʟᴇᴀꜱᴇ ʀᴇǫᴜᴇꜱᴛ ʏᴏᴜʀ ᴏᴡɴ",
            show_alert=True,
        )
    curr_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
    search = FRESH.get(key)
    if not search:
        return await query.answer("ᴛʜɪꜱ ᴍᴇꜱꜱᴀɢᴇ ɪꜱ ᴛᴏᴏ ᴏʟᴅ.\n\nᴘʟᴇᴀꜱᴇ ꜱᴇᴀʀᴄʜ ᴀɢᴀɪɴ", show_alert=True)
    baal = lang in search
    if baal:
        search = search.replace(lang, "")
    else:
        search = search
    req = query.from_user.id
    chat_id = query.message.chat.id
    message = query.message
    if lang != "homepage":
        search = f"{search} {lang}" 
    BUTTONS[key] = search
    settings = await get_settings(message.chat.id)
    b_limit = 10 if settings.get('max_btn', True) else int(MAX_B_TN)
    files, offset, total_results = await get_search_results(chat_id, search, max_results=b_limit, offset=0, filter=True)
    if not files:
        await query.answer("ɴᴏ ꜰɪʟᴇꜱ ᴡᴇʀᴇ ꜰᴏᴜɴᴅ", show_alert=1)
        return
    settings = await get_settings(message.chat.id)
    pre = 'file'
    if settings["button"]:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"[{get_size(file['file_size'])}] {clean_filename(file['file_name'])}", callback_data=f'{pre}#{file["file_id"]}'
                ),
            ]
            for file in files
        ]
        btn = get_header_buttons(key) + btn
    else:
        btn = []
        btn = get_header_buttons(key) + btn
    if offset != "":
        try:
            if settings['max_btn']:
                btn.append(
                    [InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages"), InlineKeyboardButton(text=f"1/{math.ceil(int(total_results)/10)}",callback_data="pages"), InlineKeyboardButton(text="ɴᴇxᴛ ⟶",callback_data=f"next_{req}_{key}_{offset}")]
                )
    
            else:
                btn.append(
                    [InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages"), InlineKeyboardButton(text=f"1/{math.ceil(int(total_results)/int(MAX_B_TN))}",callback_data="pages"), InlineKeyboardButton(text="ɴᴇxᴛ ⟶",callback_data=f"next_{req}_{key}_{offset}")]
                )
        except KeyError:
            await save_group_settings(query.message.chat.id, 'max_btn', True)
            btn.append(
                [InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages"), InlineKeyboardButton(text=f"1/{math.ceil(int(total_results)/10)}",callback_data="pages"), InlineKeyboardButton(text="ɴᴇxᴛ ⟶",callback_data=f"next_{req}_{key}_{offset}")]
            )
    else:
        btn.append(
            [InlineKeyboardButton(text="ɴᴏ ᴍᴏʀᴇ ᴘᴀɢᴇꜱ ᴀᴠᴀɪʟᴀʙʟᴇ",callback_data="pages")]
        )
    if lang != "homepage":
        req = query.from_user.id
        offset = 0
        btn.append([InlineKeyboardButton(text="↭ ʙᴀᴄᴋ ᴛᴏ ʜᴏᴍᴇ ↭", callback_data=f"fl#homepage#{key}")])
    
    if not settings["button"]:
        cur_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
        time_difference = timedelta(hours=cur_time.hour, minutes=cur_time.minute, seconds=(cur_time.second+(cur_time.microsecond/1000000))) - timedelta(hours=curr_time.hour, minutes=curr_time.minute, seconds=(curr_time.second+(curr_time.microsecond/1000000)))
        remaining_seconds = "{:.2f}".format(time_difference.total_seconds())
        cap = await get_cap(settings, remaining_seconds, files, query, total_results, search)
        try:
            await query.message.edit_text(text=cap, reply_markup=InlineKeyboardMarkup(btn), disable_web_page_preview=True)
        except MessageNotModified:
            pass
    else:
        try:
            await query.edit_message_reply_markup(
                reply_markup=InlineKeyboardMarkup(btn)
            )
        except MessageNotModified:
            pass
    await query.answer()
    
@Client.on_callback_query(filters.regex(r"^qualities#"))
async def qualities_cb_handler(client: Client, query: CallbackQuery):
    if not check_callback_owner(query):
        return await query.answer(
            f"ʜᴇʟʟᴏ {query.from_user.first_name if query.from_user else ''},\n\nᴛʜɪꜱ ɪꜱ ɴᴏᴛ ʏᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ.\n\nᴘʟᴇᴀꜱᴇ ʀᴇǫᴜᴇꜱᴛ ʏᴏᴜʀ ᴏᴡɴ",
            show_alert=True,
        )
    try:
        _, key = query.data.split("#")
    except (ValueError, AttributeError):
        return await query.answer("ɪɴᴠᴀʟɪᴅ ʀᴇǫᴜᴇꜱᴛ", show_alert=True)
    search = FRESH.get(key)
    if not search:
        return await query.answer("ᴛʜɪꜱ ᴍᴇꜱꜱᴀɢᴇ ɪꜱ ᴛᴏᴏ ᴏʟᴅ.\n\nᴘʟᴇᴀꜱᴇ ꜱᴇᴀʀᴄʜ ᴀɢᴀɪɴ", show_alert=True)
    try:
        search = search.replace(' ', '_')
    except Exception:
        pass
    btn = []
    for i in range(0, len(QUALITIES)-1, 2):
        btn.append([
            InlineKeyboardButton(
                text=QUALITIES[i].title(),
                callback_data=f"fq#{QUALITIES[i].lower()}#{key}"
            ),
            InlineKeyboardButton(
                text=QUALITIES[i+1].title(),
                callback_data=f"fq#{QUALITIES[i+1].lower()}#{key}"
            ),
        ])
    btn.insert(
        0,
        [
            InlineKeyboardButton(
                text="ꜱᴇʟᴇᴄᴛ ʏᴏᴜʀ ǫᴜᴀʟɪᴛʏ", callback_data="ident"
            )
        ],
    )
    req = query.from_user.id
    offset = 0
    btn.append([InlineKeyboardButton(text="↭ ʙᴀᴄᴋ ᴛᴏ ʜᴏᴍᴇ ↭", callback_data=f"fl#homepage#{key}")])
    await query.edit_message_reply_markup(InlineKeyboardMarkup(btn))
    
@Client.on_callback_query(filters.regex(r"^fq#"))
async def filter_qualities_cb_handler(client: Client, query: CallbackQuery):
    try:
        _, qual, key = query.data.split("#")
    except (ValueError, AttributeError):
        return await query.answer("ɪɴᴠᴀʟɪᴅ ʀᴇǫᴜᴇꜱᴛ", show_alert=True)
    if not check_callback_owner(query):
        return await query.answer(
            f"ʜᴇʟʟᴏ {query.from_user.first_name if query.from_user else ''},\n\nᴛʜɪꜱ ɪꜱ ɴᴏᴛ ʏᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ.\n\nᴘʟᴇᴀꜱᴇ ʀᴇǫᴜᴇꜱᴛ ʏᴏᴜʀ ᴏᴡɴ",
            show_alert=True,
        )
    search = FRESH.get(key)
    if not search:
        return await query.answer("ᴛʜɪꜱ ᴍᴇꜱꜱᴀɢᴇ ɪꜱ ᴛᴏᴏ ᴏʟᴅ.\n\nᴘʟᴇᴀꜱᴇ ꜱᴇᴀʀᴄʜ ᴀɢᴀɪɴ", show_alert=True)
    baal = qual in search
    if baal:
        search = search.replace(qual, "")
    else:
        search = search
    req = query.from_user.id
    chat_id = query.message.chat.id
    message = query.message
    searchagain = search
    if qual != "homepage":
        search = f"{search} {qual}" 
    BUTTONS[key] = search
    settings = await get_settings(message.chat.id)
    b_limit = 10 if settings.get('max_btn', True) else int(MAX_B_TN)
    files, offset, total_results = await get_search_results(chat_id, search, max_results=b_limit, offset=0, filter=True)
    # files = [file for file in files if re.search(lang, file["file_name"], re.IGNORECASE)]
    if not files:
        await query.answer("ɴᴏ ꜰɪʟᴇꜱ ᴡᴇʀᴇ ꜰᴏᴜɴᴅ", show_alert=1)
        return
    settings = await get_settings(message.chat.id)
    pre = 'file'
    if settings["button"]:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"[{get_size(file['file_size'])}] {clean_filename(file['file_name'])}", callback_data=f'{pre}#{file["file_id"]}'
                ),
            ]
            for file in files
        ]
        btn = get_header_buttons(key) + btn
    else:
        btn = []
        btn = get_header_buttons(key) + btn
    if offset != "":
        try:
            if settings['max_btn']:
                btn.append(
                    [InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages"), InlineKeyboardButton(text=f"1/{math.ceil(int(total_results)/10)}",callback_data="pages"), InlineKeyboardButton(text="ɴᴇxᴛ ⟶",callback_data=f"next_{req}_{key}_{offset}")]
                )
    
            else:
                btn.append(
                    [InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages"), InlineKeyboardButton(text=f"1/{math.ceil(int(total_results)/int(MAX_B_TN))}",callback_data="pages"), InlineKeyboardButton(text="ɴᴇxᴛ ⟶",callback_data=f"next_{req}_{key}_{offset}")]
                )
        except KeyError:
            await save_group_settings(query.message.chat.id, 'max_btn', True)
            btn.append(
                [InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages"), InlineKeyboardButton(text=f"1/{math.ceil(int(total_results)/10)}",callback_data="pages"), InlineKeyboardButton(text="ɴᴇxᴛ ⟶",callback_data=f"next_{req}_{key}_{offset}")]
            )
    else:
        btn.append(
            [InlineKeyboardButton(text="ɴᴏ ᴍᴏʀᴇ ᴘᴀɢᴇꜱ ᴀᴠᴀɪʟᴀʙʟᴇ",callback_data="pages")]
        )
    if qual != "homepage":
        req = query.from_user.id
        offset = 0
        btn.append([InlineKeyboardButton(text="↭ ʙᴀᴄᴋ ᴛᴏ ʜᴏᴍᴇ ↭", callback_data=f"next_{req}_{key}_{offset}")])
    
    if not settings["button"]:
        cur_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
        time_difference = timedelta(hours=cur_time.hour, minutes=cur_time.minute, seconds=(cur_time.second+(cur_time.microsecond/1000000))) - timedelta(hours=curr_time.hour, minutes=curr_time.minute, seconds=(curr_time.second+(curr_time.microsecond/1000000)))
        remaining_seconds = "{:.2f}".format(time_difference.total_seconds())
        cap = await get_cap(settings, remaining_seconds, files, query, total_results, search)
        try:
            await query.message.edit_text(text=cap, reply_markup=InlineKeyboardMarkup(btn), disable_web_page_preview=True)
        except MessageNotModified:
            pass
    else:
        try:
            await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(btn))
        except MessageNotModified:
            pass
                
@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    user_id = query.from_user.id if query.from_user else 0
    if user_id and user_id not in ADMINS:
        if user_id in SPAM_TRACKER:
            return await query.answer("⏳ ʏᴏᴜ ᴀʀᴇ ᴄʟɪᴄᴋɪɴɢ ᴛᴏᴏ ғᴀsᴛ!\n\nᴘʟᴇᴀsᴇ ᴡᴀɪᴛ ᴀ sᴇᴄᴏɴᴅ.", show_alert=True)
        SPAM_TRACKER[user_id] = True

    if query.data == "close_data":
        if query.message.chat.type == enums.ChatType.PRIVATE:
            if query.from_user and query.message.chat.id == query.from_user.id:
                try:
                    await query.message.delete()
                except Exception:
                    pass
            else:
                await query.answer("ʏᴏᴜ ᴄᴀɴ'ᴛ ᴅᴏ ᴛʜᴀᴛ!", show_alert=True)
        elif check_callback_owner(query) or (query.from_user and is_admin(query.from_user.id)):
            try:
                await query.message.delete()
            except Exception:
                pass
        else:
            await query.answer("ᴛʜɪꜱ ɪꜱ ɴᴏᴛ ʏᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ!", show_alert=True)           
    elif query.data.startswith("spcheck#"):
        try:
            _, correction = query.data.split("#", 1)
        except ValueError:
            return await query.answer("ɪɴᴠᴀʟɪᴅ ʀᴇǫᴜᴇꜱᴛ.", show_alert=True)
            
        await query.answer()
        # We must NOT use the user's original message, because if they deleted it, the bot will crash!
        # Instead, we pass the "Did you mean" message itself to auto_filter so it can safely reply to it.
        await auto_filter(client, correction, query.message, None, False, is_spell_check=True)
        
        # After the search is safely delivered, we delete the "Did you mean" buttons to keep the chat clean!
        try:
            await query.message.delete()
        except Exception:
            pass
        
    elif query.data.startswith("buy_premium"):
        # Check if the user came from the text-only /myplan command
        is_myplan = query.data == "buy_premium_myplan"
        back_callback = "myplan_back" if is_myplan else "start"
        
        buttons = [
            [InlineKeyboardButton("ᴄᴏɴᴛᴀᴄᴛ ꜱᴜᴘᴘᴏʀᴛ", url=SUPPORT_LINK)],
            [InlineKeyboardButton("⇋ ʙᴀᴄᴋ ⇋", callback_data=back_callback)]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        
        if query.message.media:
            # Came from /start (has photo), animate caption and swap media
            await query.message.edit_caption(caption="● ◌ ◌")
            await asyncio.sleep(0.2)
            await query.message.edit_caption(caption="● ● ◌")
            await asyncio.sleep(0.2)
            await query.message.edit_caption(caption="● ● ●")
            await asyncio.sleep(0.2)
            await query.message.edit_media(
                media=InputMediaPhoto(random.choice(PICS), caption=PAYMENT_TEXT),
                reply_markup=reply_markup
            )
        else:
            # Came from /myplan (text only), animate text
            await query.message.edit_text(text="● ◌ ◌")
            await asyncio.sleep(0.2)
            await query.message.edit_text(text="● ● ◌")
            await asyncio.sleep(0.2)
            await query.message.edit_text(text="● ● ●")
            await asyncio.sleep(0.2)
            await query.message.edit_text(
                text=PAYMENT_TEXT,
                reply_markup=reply_markup,
                parse_mode=enums.ParseMode.HTML
            )
        return 
    elif query.data == "myplan_back":
        btn = [
            [InlineKeyboardButton("ʙᴜʏ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ", callback_data="buy_premium_myplan")],
            [InlineKeyboardButton("⤬ ᴄʟᴏꜱᴇ ⤬", callback_data="close_data")]
        ]
        
        await query.message.edit_text(text="● ◌ ◌")
        await asyncio.sleep(0.2)
        await query.message.edit_text(text="● ● ◌")
        await asyncio.sleep(0.2)
        await query.message.edit_text(text="● ● ●")
        await asyncio.sleep(0.2)
        
        await query.message.edit_text(
            text="<b>ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴀɴʏ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ.\n\nᴄʜᴇᴄᴋ ᴏᴜᴛ ᴏᴜʀ ᴘʟᴀɴꜱ /plan</b>", 
            reply_markup=InlineKeyboardMarkup(btn),
            parse_mode=enums.ParseMode.HTML
        )
        return 
    elif query.data == "gfiltersdeleteallconfirm":
        if not query.from_user or not is_admin(query.from_user.id):
            return await query.answer("ʏᴏᴜ ᴅᴏ ɴᴏᴛ ʜᴀᴠᴇ ꜱᴜꜰꜰɪᴄɪᴇɴᴛ ʀɪɢʜᴛꜱ ᴛᴏ ᴅᴏ ᴛʜɪꜱ!", show_alert=True)
        await del_allg(query.message, 'gfilters')
        await query.answer("ᴅᴏɴᴇ!")
        return
    elif query.data == "gfiltersdeleteallcancel": 
        if not query.from_user or not is_admin(query.from_user.id):
            return await query.answer("ʏᴏᴜ ᴅᴏ ɴᴏᴛ ʜᴀᴠᴇ ꜱᴜꜰꜰɪᴄɪᴇɴᴛ ʀɪɢʜᴛꜱ ᴛᴏ ᴅᴏ ᴛʜɪꜱ!", show_alert=True)
        await query.answer("ᴘʀᴏᴄᴇꜱꜱ ᴄᴀɴᴄᴇʟʟᴇᴅ!")
        try:
            await query.message.reply_to_message.delete()
        except Exception:
            pass
        try:
            await query.message.delete()
        except Exception:
            pass
        return
    elif query.data == "delallconfirm":
        userid = query.from_user.id
        chat_type = query.message.chat.type
        if chat_type == enums.ChatType.PRIVATE:
            grpid = await active_connection(str(userid))
            if grpid is not None:
                grp_id = grpid
                try:
                    chat = await client.get_chat(grpid)
                    title = chat.title
                except Exception:
                    await query.message.edit_text("<b>ᴘʟᴇᴀꜱᴇ ᴍᴀᴋᴇ ꜱᴜʀᴇ ɪ ᴀᴍ ᴘʀᴇꜱᴇɴᴛ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ</b>", quote=True)
                    return await query.answer(MSG_ALRT)
            else:
                await query.message.edit_text("<b>ɪ ᴀᴍ ɴᴏᴛ ᴄᴏɴɴᴇᴄᴛᴇᴅ ᴛᴏ ᴀɴʏ ɢʀᴏᴜᴘꜱ!\nᴄʜᴇᴄᴋ /connections ᴏʀ ᴄᴏɴɴᴇᴄᴛ ᴛᴏ ᴀ ɢʀᴏᴜᴘ.</b>",
                    quote=True
                )
                return await query.answer(MSG_ALRT)
        elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            grp_id = query.message.chat.id
            title = query.message.chat.title
        else:
            return await query.answer(MSG_ALRT)
        is_owner = False
        try:
            st = await client.get_chat_member(grp_id, userid)
            is_owner = (st.status == enums.ChatMemberStatus.OWNER)
        except Exception:
            pass
        if is_owner or is_admin(userid):
            await del_all(query.message, grp_id, title)
        else:
            await query.answer("ʏᴏᴜ ɴᴇᴇᴅ ᴛᴏ ʙᴇ ᴛʜᴇ ɢʀᴏᴜᴘ ᴏᴡɴᴇʀ ᴏʀ ᴀɴ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴜꜱᴇʀ ᴛᴏ ᴅᴏ ᴛʜᴀᴛ", show_alert=True)
    elif query.data == "delallcancel":
        await query.answer("ᴘʀᴏᴄᴇꜱꜱ ᴄᴀɴᴄᴇʟʟᴇᴅ!")
        userid = query.from_user.id
        chat_type = query.message.chat.type
        if chat_type == enums.ChatType.PRIVATE:
            try:
                await query.message.reply_to_message.delete()
            except Exception:
                pass
            try:
                await query.message.delete()
            except Exception:
                pass
        elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            grp_id = query.message.chat.id
            is_owner = False
            try:
                st = await client.get_chat_member(grp_id, userid)
                is_owner = (st.status == enums.ChatMemberStatus.OWNER)
            except Exception:
                pass
            if is_owner or is_admin(userid):
                try:
                    await query.message.delete()
                except Exception:
                    pass
                try:
                    await query.message.reply_to_message.delete()
                except Exception:
                    pass
            else:
                await query.answer("ᴛʜᴀᴛ ɪꜱ ɴᴏᴛ ꜰᴏʀ ʏᴏᴜ!", show_alert=True)
    elif "groupcb" in query.data:
        await query.answer()
        try:
            group_id = query.data.split(":")[1]
            act = query.data.split(":")[2]
        except (ValueError, IndexError):
            return await query.answer("ɪɴᴠᴀʟɪᴅ ʀᴇǫᴜᴇꜱᴛ", show_alert=True)
        hr = await client.get_chat(int(group_id))
        title = hr.title
        user_id = query.from_user.id
        if act == "":
            stat = "ᴄᴏɴɴᴇᴄᴛ"
            cb = "connectcb"
        else:
            stat = "ᴅɪꜱᴄᴏɴɴᴇᴄᴛ"
            cb = "disconnect"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{stat}", callback_data=f"{cb}:{group_id}"),
             InlineKeyboardButton("ᴅᴇʟᴇᴛᴇ", callback_data=f"deletecb:{group_id}")],
            [InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="backcb")]
        ])
        await query.message.edit_text(
            f"ɢʀᴏᴜᴘ ɴᴀᴍᴇ: <b>{title}</b>\nɢʀᴏᴜᴘ ɪᴅ: <code>{group_id}</code>",
            reply_markup=keyboard
        )
        return await query.answer(MSG_ALRT)
    elif "connectcb" in query.data:
        await query.answer()
        try:
            group_id = query.data.split(":")[1]
        except (ValueError, IndexError):
            return await query.answer("ɪɴᴠᴀʟɪᴅ ʀᴇǫᴜᴇꜱᴛ", show_alert=True)
        hr = await client.get_chat(int(group_id))
        title = hr.title
        user_id = query.from_user.id
        mkact = await make_active(str(user_id), str(group_id))
        if mkact:
            await query.message.edit_text(
                f"ᴄᴏɴɴᴇᴄᴛᴇᴅ ᴛᴏ <b>{title}</b>"
            )
        else:
            await query.message.edit_text('<b>ᴀɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ!</b>', parse_mode=enums.ParseMode.MARKDOWN)
        return await query.answer(MSG_ALRT)
    
    elif "disconnect" in query.data:
        await query.answer()
        try:
            group_id = query.data.split(":")[1]
        except (ValueError, IndexError):
            return await query.answer("ɪɴᴠᴀʟɪᴅ ʀᴇǫᴜᴇꜱᴛ", show_alert=True)
        hr = await client.get_chat(int(group_id))
        title = hr.title
        user_id = query.from_user.id
        mkinact = await make_inactive(str(user_id))
        if mkinact:
            await query.message.edit_text(
                f"ᴅɪꜱᴄᴏɴɴᴇᴄᴛᴇᴅ ꜰʀᴏᴍ <b>{title}</b>"
            )
        else:
            await query.message.edit_text(f"<b>ᴀɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ!</b>",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        return await query.answer(MSG_ALRT)
    
    elif "deletecb" in query.data:
        await query.answer()
        user_id = query.from_user.id
        try:
            group_id = query.data.split(":")[1]
        except (ValueError, IndexError):
            return await query.answer("ɪɴᴠᴀʟɪᴅ ʀᴇǫᴜᴇꜱᴛ", show_alert=True)
        delcon = await delete_connection(str(user_id), str(group_id))
        if delcon:
            await query.message.edit_text("<b>ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ ᴛʜᴇ ᴄᴏɴɴᴇᴄᴛɪᴏɴ!</b>"
            )
        else:
            await query.message.edit_text(f"<b>ᴀɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ!</b>",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        return await query.answer(MSG_ALRT)
    elif query.data == "backcb":
        await query.answer()
        userid = query.from_user.id
        groupids = await all_connections(str(userid))
        if groupids is None:
            await query.message.edit_text("<b>ᴛʜᴇʀᴇ ᴀʀᴇ ɴᴏ ᴀᴄᴛɪᴠᴇ ᴄᴏɴɴᴇᴄᴛɪᴏɴꜱ! ᴘʟᴇᴀꜱᴇ ᴄᴏɴɴᴇᴄᴛ ᴛᴏ ꜱᴏᴍᴇ ɢʀᴏᴜᴘꜱ ꜰɪʀꜱᴛ.</b>",
            )
            return await query.answer(MSG_ALRT)
        buttons = []
        for groupid in groupids:
            try:
                ttl = await client.get_chat(int(groupid))
                title = ttl.title
                active = await if_active(str(userid), str(groupid))
                act = " - ᴀᴄᴛɪᴠᴇ" if active else ""
                buttons.append(
                    [
                        InlineKeyboardButton(
                            text=f"{title}{act}", callback_data=f"groupcb:{groupid}:{act}"
                        )
                    ]
                )
            except Exception:
                pass
        if buttons:
            await query.message.edit_text("<b>ʏᴏᴜʀ ᴄᴏɴɴᴇᴄᴛᴇᴅ ɢʀᴏᴜᴘ ᴅᴇᴛᴀɪʟꜱ:\n\n</b>",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
    elif "gfilteralert" in query.data:
        try:
            i = int(query.data.split(":")[1])
            alert_id = query.data.split(":")[2]
        except (ValueError, IndexError):
            return await query.answer("ɪɴᴠᴀʟɪᴅ ʀᴇǫᴜᴇꜱᴛ", show_alert=True)
            
        alerts = temp.ALERTS.get(alert_id)
        if alerts is not None:
            try:
                alert = alerts[i]
                alert = alert.replace("\\n", "\n").replace("\\t", "\t")
                await query.answer(alert, show_alert=True)
            except IndexError:
                await query.answer("ɪɴᴠᴀʟɪᴅ ᴀʟᴇʀᴛ", show_alert=True)
        else:
            await query.answer("ᴛʜɪꜱ ᴍᴇꜱꜱᴀɢᴇ ɪꜱ ᴛᴏᴏ ᴏʟᴅ.\n\nᴘʟᴇᴀꜱᴇ ʀᴇǫᴜᴇꜱᴛ ᴀɢᴀɪɴ", show_alert=True)
    
    elif "alertmessage" in query.data:
        try:
            i = int(query.data.split(":")[1])
            alert_id = query.data.split(":")[2]
        except (ValueError, IndexError):
            return await query.answer("ɪɴᴠᴀʟɪᴅ ʀᴇǫᴜᴇꜱᴛ", show_alert=True)
            
        alerts = temp.ALERTS.get(alert_id)
        if alerts is not None:
            try:
                alert = alerts[i]
                alert = alert.replace("\\n", "\n").replace("\\t", "\t")
                await query.answer(alert, show_alert=True)
            except IndexError:
                await query.answer("ɪɴᴠᴀʟɪᴅ ᴀʟᴇʀᴛ", show_alert=True)
        else:
            await query.answer("ᴛʜɪꜱ ᴍᴇꜱꜱᴀɢᴇ ɪꜱ ᴛᴏᴏ ᴏʟᴅ.\n\nᴘʟᴇᴀꜱᴇ ʀᴇǫᴜᴇꜱᴛ ᴀɢᴀɪɴ", show_alert=True)
        
    if query.data.startswith("file"):
        if not check_callback_owner(query):
            return await query.answer(
                f"ʜᴇʏ {query.from_user.first_name if query.from_user else ''},\n\nᴛʜɪꜱ ɪꜱ ɴᴏᴛ ʏᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ.\n\nᴘʟᴇᴀꜱᴇ ʀᴇǫᴜᴇꜱᴛ ʏᴏᴜʀ ᴏᴡɴ",
                show_alert=True
            )
        try:
            ident, file_id = query.data.split("#")
        except (ValueError, AttributeError):
            return await query.answer("ɪɴᴠᴀʟɪᴅ ʀᴇǫᴜᴇꜱᴛ", show_alert=True)
        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer('ɴᴏ ꜱᴜᴄʜ ꜰɪʟᴇ ᴇxɪꜱᴛꜱ.')
        files = files_
        clean_name = remove_junk(files["file_name"])
        title = clean_name
        size = get_size(files["file_size"])
        f_caption = files["caption"]
        settings = await get_settings(query.message.chat.id)
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(file_name='' if title is None else title,
                                                       file_size='' if size is None else size,
                                                       file_caption='' if f_caption is None else f_caption)
            except Exception as e:
                logger.exception(e)
            f_caption = f_caption
        if f_caption is None:
            f_caption = f"{clean_name}"
        try:
            if SHORTLINK_MODE and not await db.has_premium_access(query.from_user.id):
                temp.SHORT[query.from_user.id] = query.message.chat.id
                await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start=short_{file_id}")
                return
            elif SHORTLINK_MODE and await db.has_premium_access(query.from_user.id):
                await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start={ident}_{file_id}")
                return
            else:
                await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start={ident}_{file_id}")
                return
        except UserIsBlocked:
            await query.answer('ᴘʟᴇᴀꜱᴇ ᴜɴʙʟᴏᴄᴋ ᴛʜᴇ ʙᴏᴛ', show_alert=True)
        except PeerIdInvalid:
            try:
                await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start={ident}_{file_id}")
            except Exception:
                pass
        except Exception as e:
            try:
                await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start={ident}_{file_id}")
            except Exception:
                pass
            
    elif query.data.startswith("unmuteme"):
        try:
            ident, userid = query.data.split("#")
        except (ValueError, AttributeError):
            return await query.answer("ɪɴᴠᴀʟɪᴅ ʀᴇǫᴜᴇꜱᴛ", show_alert=True)
        if not query.from_user:
            return await query.answer("ᴜɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ", show_alert=True)
        try:
            target_user_id = int(userid)
        except ValueError:
            return await query.answer("ɪɴᴠᴀʟɪᴅ ᴜꜱᴇʀ", show_alert=True)
        if target_user_id == 0:
            await query.answer("ʏᴏᴜ ᴀʀᴇ ᴀɴ ᴀɴᴏɴʏᴍᴏᴜꜱ ᴀᴅᴍɪɴ", show_alert=True)
            return
        if query.from_user.id != target_user_id:
            await query.answer("ᴛʜɪꜱ ʙᴜᴛᴛᴏɴ ɪꜱ ɴᴏᴛ ꜰᴏʀ ʏᴏᴜ!", show_alert=True)
            return
        user_id = query.from_user.id
        settings = await get_settings(int(query.message.chat.id))
        try:
            btn = await pub_is_subscribed(client, query, settings['fsub'])
            if btn:
                await query.answer("ᴘʟᴇᴀꜱᴇ ᴊᴏɪɴ ᴛʜᴇ ᴏᴜʀ ᴄʜᴀɴɴᴇʟ, ᴛʜᴇɴ ᴄʟɪᴄᴋ ᴏɴ ᴛʜᴇ 'ᴜɴᴍᴜᴛᴇ' ʙᴜᴛᴛᴏɴ.", show_alert=True)
            else:
                await client.unban_chat_member(query.message.chat.id, user_id)
                await query.answer("ᴜɴᴍᴜᴛᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ", show_alert=True)
                try:
                    await query.message.delete()
                except Exception:
                    return
        except Exception:
            await query.answer("ᴛʜɪꜱ ɪꜱ ɴᴏᴛ ꜰᴏʀ ʏᴏᴜ", show_alert=True)
   
    elif query.data.startswith("del#"):
        try:
            ident, file_id = query.data.split("#")
        except (ValueError, AttributeError):
            return await query.answer("ɪɴᴠᴀʟɪᴅ ʀᴇǫᴜᴇꜱᴛ", show_alert=True)
        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer('ɴᴏ ꜱᴜᴄʜ ꜰɪʟᴇ ᴇxɪꜱᴛꜱ')
        files = files_
        clean_name = remove_junk(files["file_name"])
        title = clean_name
        size = get_size(files['file_size'])
        f_caption = files['caption']
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(file_name='' if title is None else title,
                                                       file_size='' if size is None else size,
                                                       file_caption='' if f_caption is None else f_caption)
            except Exception as e:
                logger.exception(e)
            f_caption = f_caption
        if f_caption is None:
            f_caption = f"{clean_name}"
        await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start=file_{file_id}")
    
    elif query.data.startswith("checksub"):
        if AUTH_CHANNEL and not await is_subscribed(client, query):
            await query.answer("ᴘʟᴇᴀꜱᴇ ᴊᴏɪɴ ᴏᴜʀ ᴄʜᴀɴɴᴇʟ", show_alert=True)
            return
        try:
            ident, kk, file_id = query.data.split("#")
        except (ValueError, AttributeError):
            return await query.answer("ɪɴᴠᴀʟɪᴅ ʀᴇǫᴜᴇꜱᴛ", show_alert=True)
        await query.answer(url=f"https://t.me/{temp.U_NAME}?start={kk}_{file_id}")
    
    elif query.data == "pages":
        await query.answer()
    
    elif query.data.startswith("killfilesdq"):
        if not query.from_user or not is_admin(query.from_user.id):
            return await query.answer("ʏᴏᴜ ᴅᴏ ɴᴏᴛ ʜᴀᴠᴇ ꜱᴜꜰꜰɪᴄɪᴇɴᴛ ʀɪɢʜᴛꜱ ᴛᴏ ᴅᴏ ᴛʜɪꜱ!", show_alert=True)
            
        await query.answer("ꜱᴛᴀʀᴛɪɴɢ ᴅᴇʟᴇᴛɪᴏɴ...", show_alert=True)
        
        try:
            ident, keyword = query.data.split("#")
        except (ValueError, AttributeError):
            return await query.message.edit_text("<b>ɪɴᴠᴀʟɪᴅ ʀᴇǫᴜᴇꜱᴛ</b>")
            
        files, total = await get_bad_files(keyword)
        await query.message.edit_text("<b>ꜰɪʟᴇ ᴅᴇʟᴇᴛɪᴏɴ ᴘʀᴏᴄᴇꜱꜱ ᴡɪʟʟ ꜱᴛᴀʀᴛ ɪɴ 5 ꜱᴇᴄᴏɴᴅꜱ</b>")
        await asyncio.sleep(5)
        
        deleted = 0
        async with lock:
            try:
                for file in files:
                    file_name = file.get("file_name", "Unknown")
                    
                    result = await col.delete_one({'_id': file['_id']})
                    if not result.deleted_count and sec_col is not None:
                        result = await sec_col.delete_one({'_id': file['_id']})
                    if not result.deleted_count and thi_col is not None:
                        result = await thi_col.delete_one({'_id': file['_id']})
                        
                    if result.deleted_count:
                        logger.info(f"File Found for your query {keyword}! Successfully deleted {file_name} from database.")
                        deleted += 1
                        
                    if deleted > 0 and deleted % 50 == 0:
                        await query.message.edit_text(f"<b>ᴘʀᴏᴄᴇꜱꜱ ꜱᴛᴀʀᴛᴇᴅ ꜰᴏʀ ᴅᴇʟᴇᴛɪɴɢ ꜰɪʟᴇꜱ ꜰʀᴏᴍ ᴛʜᴇ ᴅᴀᴛᴀʙᴀꜱᴇ. ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ {str(deleted)} ꜰɪʟᴇꜱ ꜰᴏʀ ʏᴏᴜʀ ǫᴜᴇʀʏ '{keyword}'!\n\nᴘʟᴇᴀꜱᴇ ᴡᴀɪᴛ...</b>")
            except Exception as e:
                logger.exception(e)
                await query.message.edit_text(f'<b>ᴇʀʀᴏʀ: {e}</b>')
            else:
                await query.message.edit_text(f"<b>ꜰɪʟᴇ ᴅᴇʟᴇᴛɪᴏɴ ᴘʀᴏᴄᴇꜱꜱ ᴄᴏᴍᴘʟᴇᴛᴇᴅ!\n\nꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ {str(deleted)} ꜰɪʟᴇꜱ ꜰʀᴏᴍ ᴛʜᴇ ᴅᴀᴛᴀʙᴀꜱᴇ ꜰᴏʀ ʏᴏᴜʀ ǫᴜᴇʀʏ '{keyword}'.</b>")
        return
    
    elif query.data.startswith("opnsetgrp"):
        try:
            ident, grp_id = query.data.split("#")
        except (ValueError, AttributeError):
            return await query.answer("ɪɴᴠᴀʟɪᴅ ʀᴇǫᴜᴇꜱᴛ", show_alert=True)
        userid = query.from_user.id if query.from_user else None
        if not userid:
            return await query.answer("ᴜɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ", show_alert=True)
        is_chat_admin = False
        try:
            st = await client.get_chat_member(grp_id, userid)
            is_chat_admin = st.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]
        except Exception:
            pass
        if not is_chat_admin and not is_admin(userid):
            await query.answer("ʏᴏᴜ ᴅᴏ ɴᴏᴛ ʜᴀᴠᴇ ᴛʜᴇ ʀɪɢʜᴛꜱ ᴛᴏ ᴅᴏ ᴛʜɪꜱ", show_alert=True)
            return
        title = query.message.chat.title
        settings = await get_settings(grp_id)
        if settings is not None:
            buttons = [
            [
                InlineKeyboardButton(
                    'ʀᴇꜱᴜʟᴛ ᴘᴀɢᴇ',
                    callback_data=f'setgs#button#{settings["button"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    'ʙᴜᴛᴛᴏɴ' if settings["button"] else 'ᴛᴇxᴛ',
                    callback_data=f'setgs#button#{settings["button"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'ᴀᴜᴛᴏ-ᴅᴇʟᴇᴛᴇ',
                    callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    '1𝟻 ᴍɪɴꜱ' if settings["auto_delete"] else 'ᴏꜰꜰ',
                    callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'ᴀᴜᴛᴏ-ꜰɪʟᴛᴇʀ',
                    callback_data=f'setgs#auto_ffilter#{settings["auto_ffilter"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    'ᴏɴ' if settings["auto_ffilter"] else 'ᴏꜰꜰ',
                    callback_data=f'setgs#auto_ffilter#{settings["auto_ffilter"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'ᴍᴀx ʙᴜᴛᴛᴏɴꜱ',
                    callback_data=f'setgs#max_btn#{settings["max_btn"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    '10' if settings["max_btn"] else f'{MAX_B_TN}',
                    callback_data=f'setgs#max_btn#{settings["max_btn"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'ɴᴏ-ʀᴇꜱᴜʟᴛ ᴍꜱɢ',
                    callback_data=f'setgs#no_result_msg#{settings.get("no_result_msg", True)}#{grp_id}',
                ),
                InlineKeyboardButton(
                    'ᴏɴ' if settings.get("no_result_msg", True) else 'ᴏꜰꜰ',
                    callback_data=f'setgs#no_result_msg#{settings.get("no_result_msg", True)}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton('⤬ ᴄʟᴏꜱᴇ ⤬', callback_data='close_data')
            ]
        ]
            reply_markup = InlineKeyboardMarkup(buttons)
            await query.message.edit_text(
                text=f"<b>ᴄʜᴀɴɢᴇ ʏᴏᴜʀ ꜱᴇᴛᴛɪɴɢꜱ ꜰᴏʀ {title} ᴀꜱ ʏᴏᴜ ᴡɪꜱʜ</b>",
                disable_web_page_preview=True,
                parse_mode=enums.ParseMode.HTML
            )
            await query.message.edit_reply_markup(reply_markup)
        
    elif query.data.startswith("opnsetpm"):
        try:
            ident, grp_id = query.data.split("#")
        except (ValueError, AttributeError):
            return await query.answer("ɪɴᴠᴀʟɪᴅ ʀᴇǫᴜᴇꜱᴛ", show_alert=True)
        userid = query.from_user.id if query.from_user else None
        if not userid:
            return await query.answer("ᴜɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ", show_alert=True)
        is_chat_admin = False
        try:
            st = await client.get_chat_member(grp_id, userid)
            is_chat_admin = st.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]
        except Exception:
            pass
        if not is_chat_admin and not is_admin(userid):
            await query.answer("ʏᴏᴜ ᴅᴏ ɴᴏᴛ ʜᴀᴠᴇ ᴛʜᴇ ʀɪɢʜᴛꜱ ᴛᴏ ᴅᴏ ᴛʜɪꜱ", show_alert=True)
            return
        title = query.message.chat.title
        settings = await get_settings(grp_id)
        btn2 = [[
                 InlineKeyboardButton("ᴄʜᴇᴄᴋ ᴘᴍ", url=f"telegram.me/{temp.U_NAME}")
               ]]
        reply_markup = InlineKeyboardMarkup(btn2)
        await query.message.edit_text(f"<b>ʏᴏᴜʀ ꜱᴇᴛᴛɪɴɢꜱ ᴍᴇɴᴜ ꜰᴏʀ {title} ʜᴀꜱ ʙᴇᴇɴ ꜱᴇɴᴛ ᴛᴏ ʏᴏᴜʀ ᴘᴍ.</b>")
        await query.message.edit_reply_markup(reply_markup)
        if settings is not None:
            buttons = [
            [
                InlineKeyboardButton(
                    'ʀᴇꜱᴜʟᴛ ᴘᴀɢᴇ',
                    callback_data=f'setgs#button#{settings["button"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    'ʙᴜᴛᴛᴏɴ' if settings["button"] else 'ᴛᴇxᴛ',
                    callback_data=f'setgs#button#{settings["button"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'ᴀᴜᴛᴏ-ᴅᴇʟᴇᴛᴇ',
                    callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    '1𝟻 ᴍɪɴꜱ' if settings["auto_delete"] else 'ᴏꜰꜰ',
                    callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'ᴀᴜᴛᴏ-ꜰɪʟᴛᴇʀ',
                    callback_data=f'setgs#auto_ffilter#{settings["auto_ffilter"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    'ᴏɴ' if settings["auto_ffilter"] else 'ᴏꜰꜰ',
                    callback_data=f'setgs#auto_ffilter#{settings["auto_ffilter"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'ᴍᴀx ʙᴜᴛᴛᴏɴꜱ',
                    callback_data=f'setgs#max_btn#{settings["max_btn"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    '10' if settings["max_btn"] else f'{MAX_B_TN}',
                    callback_data=f'setgs#max_btn#{settings["max_btn"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'ɴᴏ-ʀᴇꜱᴜʟᴛ ᴍꜱɢ',
                    callback_data=f'setgs#no_result_msg#{settings.get("no_result_msg", True)}#{grp_id}',
                ),
                InlineKeyboardButton(
                    'ᴏɴ' if settings.get("no_result_msg", True) else 'ᴏꜰꜰ',
                    callback_data=f'setgs#no_result_msg#{settings.get("no_result_msg", True)}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton('⤬ ᴄʟᴏꜱᴇ ⤬', callback_data='close_data')
            ]
        ]
            reply_markup = InlineKeyboardMarkup(buttons)
            await client.send_message(
                chat_id=userid,
                text=f"<b>ᴄʜᴀɴɢᴇ ʏᴏᴜʀ ꜱᴇᴛᴛɪɴɢꜱ ꜰᴏʀ {title} ᴀꜱ ʏᴏᴜ ᴡɪꜱʜ</b>",
                reply_markup=reply_markup,
                disable_web_page_preview=True,
                parse_mode=enums.ParseMode.HTML,
                reply_to_message_id=query.message.id
            )
    elif query.data.startswith("show_option"):
        try:
            ident, from_user = query.data.split("#")
        except (ValueError, AttributeError):
            return await query.answer("ɪɴᴠᴀʟɪᴅ ʀᴇǫᴜᴇꜱᴛ", show_alert=True)
        btn = [[
                InlineKeyboardButton("ᴜɴᴀᴠᴀɪʟᴀʙʟᴇ", callback_data=f"unavailable#{from_user}"),
                InlineKeyboardButton("ᴜᴘʟᴏᴀᴅᴇᴅ", callback_data=f"uploaded#{from_user}")
             ],[
                InlineKeyboardButton("ᴀʟʀᴇᴀᴅʏ ᴀᴠᴀɪʟᴀʙʟᴇ", callback_data=f"already_available#{from_user}")
              ]]
        if query.from_user and is_admin(query.from_user):
            reply_markup = InlineKeyboardMarkup(btn)
            await query.message.edit_reply_markup(reply_markup)
            await query.answer("ʜᴇʀᴇ ᴀʀᴇ ᴛʜᴇ ᴏᴘᴛɪᴏɴꜱ!")
        else:
            await query.answer("ʏᴏᴜ ᴅᴏ ɴᴏᴛ ʜᴀᴠᴇ ꜱᴜꜰꜰɪᴄɪᴇɴᴛ ʀɪɢʜᴛꜱ ᴛᴏ ᴅᴏ ᴛʜɪꜱ!", show_alert=True)
            
    elif query.data.startswith("unavailable"):
        try:
            ident, from_user = query.data.split("#")
        except (ValueError, AttributeError):
            return await query.answer("ɪɴᴠᴀʟɪᴅ ʀᴇǫᴜᴇꜱᴛ", show_alert=True)
        btn = [[InlineKeyboardButton("ᴜɴᴀᴠᴀɪʟᴀʙʟᴇ", callback_data=f"unalert#{from_user}")]]
        if query.from_user and is_admin(query.from_user):
            user_mention = "User"
            try:
                user = await client.get_users(int(from_user))
                user_mention = user.mention
            except Exception:
                pass
            reply_markup = InlineKeyboardMarkup(btn)
            content = query.message.text or ""
            movie_name = content.split("ᴍᴇꜱꜱᴀɢᴇ : ")[1] if "ᴍᴇꜱꜱᴀɢᴇ : " in content else content
            safe_content = content.replace('<', '&lt;').replace('>', '&gt;')
            safe_movie = movie_name.replace('<', '&lt;').replace('>', '&gt;')
            await query.message.edit_text(f"<b><strike>{safe_content}</strike></b>")
            await query.message.edit_reply_markup(reply_markup)
            await query.answer("ꜱᴇᴛ ᴛᴏ ᴜɴᴀᴠᴀɪʟᴀʙʟᴇ!")
            try:
                await client.send_message(chat_id=int(from_user), text=f"<b>ʜᴇʏ {user_mention},\n\n❌ ꜱᴏʀʀʏ, \"{safe_movie}\" ɪꜱ ᴜɴᴀᴠᴀɪʟᴀʙʟᴇ (ɴᴏᴛ ʀᴇʟᴇᴀꜱᴇᴅ ᴏʀ ɴᴏ ꜰɪʟᴇꜱ).\n\n⚠️ ɪꜰ ɪᴛ ɪꜱ ᴀɴ ᴜᴘᴄᴏᴍɪɴɢ ʀᴇʟᴇᴀꜱᴇ, ɪᴛ ᴡɪʟʟ ʙᴇ ᴜᴘʟᴏᴀᴅᴇᴅ ʜᴇʀᴇ ᴀꜱ ꜱᴏᴏɴ ᴀꜱ ɪᴛ ᴅʀᴏᴘꜱ:\n\n🎬 ᴍᴏᴠɪᴇꜱ ➔ @TIC_Movies_Bot\n📺 ᴡᴇʙ ꜱᴇʀɪᴇꜱ & ᴀɴɪᴍᴇ ➔ @TIC_Web_Series_Anime_Bot\n🔥 ʟᴀᴛᴇꜱᴛ ᴍᴏᴠɪᴇꜱ [ᴄᴀᴍ ᴘʀɪɴᴛ] ➔ @TIC_Latest_Movies_Bot</b>")
            except Exception:
                pass
        else:
            await query.answer("ʏᴏᴜ ᴅᴏ ɴᴏᴛ ʜᴀᴠᴇ ꜱᴜꜰꜰɪᴄɪᴇɴᴛ ʀɪɢʜᴛꜱ ᴛᴏ ᴅᴏ ᴛʜɪꜱ!", show_alert=True)
    elif query.data.startswith("uploaded"):
        try:
            ident, from_user = query.data.split("#")
        except (ValueError, AttributeError):
            return await query.answer("ɪɴᴠᴀʟɪᴅ ʀᴇǫᴜᴇꜱᴛ", show_alert=True)
        btn = [[InlineKeyboardButton("ᴜᴘʟᴏᴀᴅᴇᴅ", callback_data=f"upalert#{from_user}")]]
        if query.from_user and is_admin(query.from_user):
            user_mention = "User"
            try:
                user = await client.get_users(int(from_user))
                user_mention = user.mention
            except Exception:
                pass
            reply_markup = InlineKeyboardMarkup(btn)
            content = query.message.text or ""
            movie_name = content.split("ᴍᴇꜱꜱᴀɢᴇ : ")[1] if "ᴍᴇꜱꜱᴀɢᴇ : " in content else content
            safe_content = content.replace('<', '&lt;').replace('>', '&gt;')
            safe_movie = movie_name.replace('<', '&lt;').replace('>', '&gt;')
            await query.message.edit_text(f"<b><strike>{safe_content}</strike></b>")
            await query.message.edit_reply_markup(reply_markup)
            await query.answer("ꜱᴇᴛ ᴛᴏ ᴜᴘʟᴏᴀᴅᴇᴅ!")
            try:
                await client.send_message(chat_id=int(from_user), text=f"<b>ʜᴇʏ {user_mention},\n\n✅ ʏᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ ꜰᴏʀ \"{safe_movie}\" ʜᴀꜱ ʙᴇᴇɴ ᴜᴘʟᴏᴀᴅᴇᴅ!\n\n⚠️ ꜰɪʟᴇꜱ ᴀʀᴇ ꜱᴇᴘᴀʀᴀᴛᴇᴅ ʙʏ ᴄᴀᴛᴇɢᴏʀʏ. ᴘʟᴇᴀꜱᴇ ꜱᴇᴀʀᴄʜ ɪɴ ᴛʜᴇ ᴄᴏʀʀᴇᴄᴛ ʙᴏᴛ:\n\n🎬 ᴍᴏᴠɪᴇꜱ ➔ @TIC_Movies_Bot\n📺 ᴡᴇʙ ꜱᴇʀɪᴇꜱ & ᴀɴɪᴍᴇ ➔ @TIC_Web_Series_Anime_Bot\n🔥 ʟᴀᴛᴇꜱᴛ ᴍᴏᴠɪᴇꜱ [ᴄᴀᴍ ᴘʀɪɴᴛ] ➔ @TIC_Latest_Movies_Bot</b>")
            except Exception:
                pass
        else:
            await query.answer("ʏᴏᴜ ᴅᴏ ɴᴏᴛ ʜᴀᴠᴇ ꜱᴜꜰꜰɪᴄɪᴇɴᴛ ʀɪɢʜᴛꜱ ᴛᴏ ᴅᴏ ᴛʜɪꜱ", show_alert=True)
    elif query.data.startswith("already_available"):
        try:
            ident, from_user = query.data.split("#")
        except (ValueError, AttributeError):
            return await query.answer("ɪɴᴠᴀʟɪᴅ ʀᴇǫᴜᴇꜱᴛ", show_alert=True)
        btn = [[InlineKeyboardButton("ᴀʟʀᴇᴀᴅʏ ᴀᴠᴀɪʟᴀʙʟᴇ", callback_data=f"alalert#{from_user}")]]
        if query.from_user and is_admin(query.from_user):
            user_mention = "User"
            try:
                user = await client.get_users(int(from_user))
                user_mention = user.mention
            except Exception:
                pass
            reply_markup = InlineKeyboardMarkup(btn)
            content = query.message.text or ""
            movie_name = content.split("ᴍᴇꜱꜱᴀɢᴇ : ")[1] if "ᴍᴇꜱꜱᴀɢᴇ : " in content else content
            safe_content = content.replace('<', '&lt;').replace('>', '&gt;')
            safe_movie = movie_name.replace('<', '&lt;').replace('>', '&gt;')
            await query.message.edit_text(f"<b><strike>{safe_content}</strike></b>")
            await query.message.edit_reply_markup(reply_markup)
            await query.answer("ꜱᴇᴛ ᴛᴏ ᴀʟʀᴇᴀᴅʏ ᴀᴠᴀɪʟᴀʙʟᴇ!")
            try:
                await client.send_message(chat_id=int(from_user), text=f"<b>ʜᴇʏ {user_mention},\n\n🔄 ᴡᴇ ᴀʟʀᴇᴀᴅʏ ʜᴀᴠᴇ \"{safe_movie}\" ɪɴ ᴏᴜʀ ᴄᴏʟʟᴇᴄᴛɪᴏɴ!\n\n⚠️ ɪꜰ ʏᴏᴜ ᴄᴀɴ'ᴛ ꜰɪɴᴅ ɪᴛ, ʏᴏᴜ ᴍɪɢʜᴛ ʙᴇ ɪɴ ᴛʜᴇ ᴡʀᴏɴɢ ʙᴏᴛ. ᴘʟᴇᴀꜱᴇ ꜱᴇᴀʀᴄʜ ʜᴇʀᴇ:\n\n🎬 ᴍᴏᴠɪᴇꜱ ➔ @TIC_Movies_Bot\n📺 ᴡᴇʙ ꜱᴇʀɪᴇꜱ & ᴀɴɪᴍᴇ ➔ @TIC_Web_Series_Anime_Bot\n🔥 ʟᴀᴛᴇꜱᴛ ᴍᴏᴠɪᴇꜱ [ᴄᴀᴍ ᴘʀɪɴᴛ] ➔ @TIC_Latest_Movies_Bot</b>")
            except Exception:
                pass
        else:
            await query.answer("ʏᴏᴜ ᴅᴏ ɴᴏᴛ ʜᴀᴠᴇ ꜱᴜꜰꜰɪᴄɪᴇɴᴛ ʀɪɢʜᴛꜱ ᴛᴏ ᴅᴏ ᴛʜɪꜱ!", show_alert=True)
    elif query.data.startswith("alalert") or query.data.startswith("upalert") or query.data.startswith("unalert"):
        if query.from_user and is_admin(query.from_user):
            await query.answer("ꜱᴛᴀᴛᴜꜱ ᴜᴘᴅᴀᴛᴇᴅ", show_alert=True)
        else:
            await query.answer("ʏᴏᴜ ᴅᴏ ɴᴏᴛ ʜᴀᴠᴇ ꜱᴜꜰꜰɪᴄɪᴇɴᴛ ʀɪɢʜᴛꜱ ᴛᴏ ᴅᴏ ᴛʜɪꜱ", show_alert=True)
    
    elif query.data == "reqinfo":
        await query.answer(text=script.REQINFO, show_alert=True)
    elif query.data == "select":
        await query.answer(text=script.SELECT, show_alert=True)
    elif query.data == "sinfo":
        await query.answer(text=script.SINFO, show_alert=True)
    elif query.data == "start":
        buttons = [
            [InlineKeyboardButton("⍟ ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ ⍟", url=f"http://t.me/{temp.U_NAME}?startgroup=true")],
            [InlineKeyboardButton("⍰ ʜᴏᴡ ᴛᴏ ᴜꜱᴇ ᴛʜᴇ ʙᴏᴛ ⍰", callback_data="users")],
            [InlineKeyboardButton("★ ʙᴜʏ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ ★", callback_data="buy_premium")],
            [
                InlineKeyboardButton("⌖ ᴏᴜʀ ᴄʜᴀɴɴᴇʟ ⌖", url=CHNL_LNK),
                InlineKeyboardButton("⌖ ᴏᴜʀ ɢʀᴏᴜᴘ ⌖", url=GRP_LNK)
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(text="● ◌ ◌")
        await asyncio.sleep(0.2)
        await query.message.edit_text(text="● ● ◌")
        await asyncio.sleep(0.2)
        await query.message.edit_text(text="● ● ●")
        await asyncio.sleep(0.2)
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        await query.message.edit_text(
            text=script.START_TXT.format(query.from_user.mention, temp.U_NAME, temp.B_NAME),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        try:
            await query.answer(MSG_ALRT)
        except Exception:
            pass
        
    elif query.data == "users":
        buttons = [
            [InlineKeyboardButton('ᴛᴜᴛᴏʀɪᴀʟ ᴠɪᴅᴇᴏ', url="https://t.me/TheInsomniacsClub/461")],
            [
                InlineKeyboardButton('ʀᴜʟᴇꜱ', callback_data='rules'),
                InlineKeyboardButton('ᴄᴏᴍᴍᴀɴᴅꜱ', callback_data='commands')
            ],
            [InlineKeyboardButton('ʜᴏᴡ ᴛᴏ ʀᴇǫᴜᴇꜱᴛ', callback_data='request_help')],
            [InlineKeyboardButton('⇋ ʙᴀᴄᴋ ⇋', callback_data='start')]
        ]
        
        # Loading Animation
        await query.message.edit_text(text="● ◌ ◌")
        await asyncio.sleep(0.2)
        await query.message.edit_text(text="● ● ◌")
        await asyncio.sleep(0.2)
        await query.message.edit_text(text="● ● ●")
        await asyncio.sleep(0.2)
        
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        await query.message.edit_text(
            text=script.HOW_TO_USE_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "rules":
        buttons = [[InlineKeyboardButton('⇋ ʙᴀᴄᴋ ⇋', callback_data='users')]]
        
        await query.message.edit_text(text="● ◌ ◌")
        await asyncio.sleep(0.2)
        await query.message.edit_text(text="● ● ◌")
        await asyncio.sleep(0.2)
        await query.message.edit_text(text="● ● ●")
        await asyncio.sleep(0.2)
        
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        await query.message.edit_text(
            text=script.RULES_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "commands":
        buttons = [[InlineKeyboardButton('⇋ ʙᴀᴄᴋ ⇋', callback_data='users')]]
        
        await query.message.edit_text(text="● ◌ ◌")
        await asyncio.sleep(0.2)
        await query.message.edit_text(text="● ● ◌")
        await asyncio.sleep(0.2)
        await query.message.edit_text(text="● ● ●")
        await asyncio.sleep(0.2)
        
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        await query.message.edit_text(
            text=script.COMMANDS_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "request_help":
        buttons = [
            [InlineKeyboardButton("⇋ ʙᴀᴄᴋ ⇋", callback_data="users")]
        ]
        await query.message.edit_text(text="● ◌ ◌")
        await asyncio.sleep(0.2)
        await query.message.edit_text(text="● ● ◌")
        await asyncio.sleep(0.2)
        await query.message.edit_text(text="● ● ●")
        await asyncio.sleep(0.2)
        
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        await query.message.edit_text(
            text=script.REQUEST_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        ) 
                
    elif query.data.startswith("setgs"):
        try:
            ident, set_type, status, grp_id = query.data.split("#")
        except (ValueError, AttributeError):
            return await query.answer("ɪɴᴠᴀʟɪᴅ ʀᴇǫᴜᴇꜱᴛ", show_alert=True)
        if not query.from_user:
            return await query.answer("ᴜɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ", show_alert=True)
        grpid = await active_connection(str(query.from_user.id))
        if str(grp_id) != str(grpid):
            await query.message.edit("ʏᴏᴜʀ ᴀᴄᴛɪᴠᴇ ᴄᴏɴɴᴇᴄᴛɪᴏɴ ʜᴀꜱ ʙᴇᴇɴ ᴄʜᴀɴɢᴇᴅ. ɢᴏ ᴛᴏ /connections ᴀɴᴅ ᴄʜᴀɴɢᴇ ʏᴏᴜʀ ᴀᴄᴛɪᴠᴇ ᴄᴏɴɴᴇᴄᴛɪᴏɴ.")
            return await query.answer(MSG_ALRT)
            
        userid = query.from_user.id
        is_chat_admin = False
        try:
            st = await client.get_chat_member(grpid, userid)
            is_chat_admin = st.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]
        except Exception:
            pass
        if not is_chat_admin and not is_admin(userid):
            await query.answer("ʏᴏᴜ ᴅᴏ ɴᴏᴛ ʜᴀᴠᴇ ᴛʜᴇ ʀɪɢʜᴛꜱ ᴛᴏ ᴅᴏ ᴛʜɪꜱ", show_alert=True)
            return
        if status == "True":
            await save_group_settings(grpid, set_type, False)
        else:
            settings = await get_settings(grpid)
            await save_group_settings(grpid, set_type, True)
        settings = await get_settings(grpid)
        if settings is not None:
            buttons = [
            [
                InlineKeyboardButton(
                    'ʀᴇꜱᴜʟᴛ ᴘᴀɢᴇ',
                    callback_data=f'setgs#button#{settings["button"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    'ʙᴜᴛᴛᴏɴ' if settings["button"] else 'ᴛᴇxᴛ',
                    callback_data=f'setgs#button#{settings["button"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'ᴀᴜᴛᴏ-ᴅᴇʟᴇᴛᴇ',
                    callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    '1𝟻 ᴍɪɴꜱ' if settings["auto_delete"] else 'ᴏꜰꜰ',
                    callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'ᴀᴜᴛᴏ-ꜰɪʟᴛᴇʀ',
                    callback_data=f'setgs#auto_ffilter#{settings["auto_ffilter"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    'ᴏɴ' if settings["auto_ffilter"] else 'ᴏꜰꜰ',
                    callback_data=f'setgs#auto_ffilter#{settings["auto_ffilter"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'ᴍᴀx ʙᴜᴛᴛᴏɴꜱ',
                    callback_data=f'setgs#max_btn#{settings["max_btn"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    '10' if settings["max_btn"] else f'{MAX_B_TN}',
                    callback_data=f'setgs#max_btn#{settings["max_btn"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'ɴᴏ-ʀᴇꜱᴜʟᴛ ᴍꜱɢ',
                    callback_data=f'setgs#no_result_msg#{settings.get("no_result_msg", True)}#{grp_id}',
                ),
                InlineKeyboardButton(
                    'ᴏɴ' if settings.get("no_result_msg", True) else 'ᴏꜰꜰ',
                    callback_data=f'setgs#no_result_msg#{settings.get("no_result_msg", True)}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton('⤬ ᴄʟᴏꜱᴇ ⤬', callback_data='close_data')
            ]
        ]
            reply_markup = InlineKeyboardMarkup(buttons)
            await query.message.edit_reply_markup(reply_markup)
    try:
        await query.answer(MSG_ALRT)
    except Exception:
        pass
async def auto_filter(client, name, msg, reply_msg, ai_search, spoll=False, is_spell_check=False):
    user_id = msg.from_user.id if msg.from_user else 0
    if not spoll and user_id and user_id not in ADMINS:
        if user_id in SPAM_TRACKER:
            if reply_msg:
                try:
                    await reply_msg.delete()
                except Exception:
                    pass
            warning = await msg.reply_text("<b>⏳ ʏᴏᴜ ᴀʀᴇ sᴇᴀʀᴄʜɪɴɢ ᴛᴏᴏ ғᴀsᴛ!\n\nᴘʟᴇᴀsᴇ ᴡᴀɪᴛ ᴀ ᴍᴏᴍᴇɴᴛ ʙᴇғᴏʀᴇ sᴇɴᴅɪɴɢ ᴀɴᴏᴛʜᴇʀ ʀᴇǫᴜᴇsᴛ.</b>")
            async def auto_delete():
                await asyncio.sleep(10)
                try:
                    await warning.delete()
                except Exception:
                    pass
            asyncio.create_task(auto_delete())
            return
        SPAM_TRACKER[user_id] = True

    curr_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
    if not spoll:
        message = msg
        if message.text.startswith("/"): return  # ignore commands
        if re.findall(r"((^\/|^,|^!|^\.|^[\U0001F600-\U000E007F]).*)", message.text):
            return
        if len(message.text) < 100:
            search = name
            search = search.lower()
            find = search.split(" ")
            search = ""
            removes = ["in","upload", "series", "full", "horror", "thriller", "mystery", "print", "file"]
            for x in find:
                if x in removes:
                    continue
                else:
                    search = search + x + " "
            search = re.sub(r"\b(pl(i|e)*?(s|z+|ease|se|ese|(e+)s(e)?)|((send|snd|giv(e)?|gib)(\sme)?)|movie(s)?|film(s)?|new|latest|bro(o+)?|bruh|helo|hello|hey|hi|sir|admin|that|find|dubbed|link|any(one)|with\ssubtitle(s)?|want|need|available|upload(ed)?|watch|download)", "", search, flags=re.IGNORECASE)
            search = re.sub(r"\s+", " ", search).strip()
            search = search.replace("’", "'").replace("‘", "'")
            search = search.replace("-", " ")
            search = search.replace(":", "")
            search = search.replace(".", "")
            settings = await get_settings(message.chat.id)
            b_limit = 10 if settings.get('max_btn', True) else int(MAX_B_TN)
            
            files, offset, total_results = await get_search_results(message.chat.id, search, max_results=b_limit, offset=0, filter=True)
            if files and total_results > 0:
                await add_search_query(search)
            if not files:
                if settings.get('no_result_msg', True):
                    if reply_msg:
                        try:
                            await reply_msg.delete()
                        except Exception:
                            pass
                    
                    from utils import get_spell_check
                    
                    btn = []
                    text = f"<b>ɪ ᴄᴏᴜʟᴅɴ'ᴛ ꜰɪɴᴅ ᴀɴʏ ꜰɪʟᴇ ʀᴇʟᴀᴛᴇᴅ ᴛᴏ {name.replace('<', '&lt;').replace('>', '&gt;')}.\n\nᴘʟᴇᴀꜱᴇ ᴄʜᴇᴄᴋ ᴛʜᴇ ꜱᴘᴇʟʟɪɴɢ ɪɴ ɢᴏᴏɢʟᴇ ᴏʀ ɪᴍᴅʙ</b>"
                    
                    # 🪄 PM-ONLY SPELL CHECK LOGIC
                    if message.chat.type == enums.ChatType.PRIVATE:
                        if is_spell_check:
                            text = f"<b>ɪ ᴄᴏᴜʟᴅɴ'ᴛ ꜰɪɴᴅ ᴀɴʏ ꜰɪʟᴇ ꜰᴏʀ {name.replace('<', '&lt;').replace('>', '&gt;')}.\n\nᴘʟᴇᴀꜱᴇ ᴍᴀᴋᴇ ꜱᴜʀᴇ ʏᴏᴜ ᴀʀᴇ ꜱᴇᴀʀᴄʜɪɴɢ ɪɴ ᴛʜᴇ ᴄᴏʀʀᴇᴄᴛ ʙᴏᴛ:\n\n🎬 ᴍᴏᴠɪᴇꜱ ➔ @TIC_Movies_Bot\n📺 ᴡᴇʙ ꜱᴇʀɪᴇꜱ & ᴀɴɪᴍᴇ ➔ @TIC_Web_Series_Anime_Bot\n🔥 ʟᴀᴛᴇꜱᴛ ᴍᴏᴠɪᴇꜱ [ᴄᴀᴍ ᴘʀɪɴᴛ] ➔ @TIC_Latest_Movies_Bot\n\nɪꜰ ʏᴏᴜ ᴀʀᴇ ɪɴ ᴛʜᴇ ᴄᴏʀʀᴇᴄᴛ ʙᴏᴛ, ɪᴛ ᴍᴇᴀɴꜱ ɪᴛ ɪꜱ ɴᴏᴛ ᴜᴘʟᴏᴀᴅᴇᴅ ʏᴇᴛ!\n\nᴛᴀᴘ ᴛᴏ ᴄᴏᴘʏ ᴛʜɪꜱ ➔ <code>/request {name.replace('<', '&lt;').replace('>', '&gt;')}</code> ➔ ꜱᴇɴᴅ ɪᴛ ʜᴇʀᴇ 👇</b>"
                        else:
                            suggestions = await get_spell_check(name)
                            if suggestions:
                                text = f"<b>ɪ ᴄᴏᴜʟᴅɴ'ᴛ ꜰɪɴᴅ ᴀɴʏ ꜰɪʟᴇ ʀᴇʟᴀᴛᴇᴅ ᴛᴏ {name.replace('<', '&lt;').replace('>', '&gt;')}.\n\nᴅɪᴅ ʏᴏᴜ ᴍᴇᴀɴ ᴀɴʏ ᴏꜰ ᴛʜᴇꜱᴇ ʙᴇʟᴏᴡ ᴏɴᴇꜱ:</b>"
                                for title in suggestions:
                                    btn.append([InlineKeyboardButton(f"{title}", callback_data=f"spcheck#{title[:50]}")])

                                btn.append([InlineKeyboardButton("❌ ɴᴏɴᴇ ᴏғ ᴛʜᴇsᴇ? ʀᴇǫᴜᴇsᴛ ɪᴛ 📬", callback_data=f"spcheck#{name[:50]}")])
                    
                    spell_check_msg = await message.reply_text(
                        text=text,
                        reply_markup=InlineKeyboardMarkup(btn) if btn else None
                    )
                    
                    from utils import delayed_delete
                    delayed_delete([spell_check_msg, message], 60)
                    return
                else:
                    if reply_msg:
                        try:
                            await reply_msg.delete()
                        except Exception:
                            pass
                    return
        else:
            return
    else:
        message = msg.message.reply_to_message  # msg will be callback query
        search, files, offset, total_results = spoll
        settings = await get_settings(message.chat.id)
        await msg.message.delete()
    pre = 'file'
    key = f"{message.chat.id}-{message.id}"
    user_id = message.chat.id if message.chat.type == enums.ChatType.PRIVATE else (message.from_user.id if message.from_user else 0)
    req = user_id
    FRESH[key] = search
    if user_id:
        temp.SHORT[user_id] = message.chat.id
    if settings["button"]:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"[{get_size(file['file_size'])}] {clean_filename(file['file_name'])}", callback_data=f'{pre}#{file["file_id"]}'
                ),
            ]
            for file in files
        ]
        btn = get_header_buttons(key) + btn
    else:
        btn = []
        btn = get_header_buttons(key) + btn
    if offset != "":
        try:
            if settings['max_btn']:
                btn.append(
                    [InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages"), InlineKeyboardButton(text=f"1/{math.ceil(int(total_results)/10)}",callback_data="pages"), InlineKeyboardButton(text="ɴᴇxᴛ ⟶",callback_data=f"next_{req}_{key}_{offset}")]
                )
            else:
                btn.append(
                    [InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages"), InlineKeyboardButton(text=f"1/{math.ceil(int(total_results)/int(MAX_B_TN))}",callback_data="pages"), InlineKeyboardButton(text="ɴᴇxᴛ ⟶",callback_data=f"next_{req}_{key}_{offset}")]
                )
        except KeyError:
            await save_group_settings(message.chat.id, 'max_btn', True)
            btn.append(
                [InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages"), InlineKeyboardButton(text=f"1/{math.ceil(int(total_results)/10)}",callback_data="pages"), InlineKeyboardButton(text="ɴᴇxᴛ ⟶",callback_data=f"next_{req}_{key}_{offset}")]
            )
    else:
        btn.append(
            [InlineKeyboardButton(text="ɴᴏ ᴍᴏʀᴇ ᴘᴀɢᴇꜱ ᴀᴠᴀɪʟᴀʙʟᴇ",callback_data="pages")]
        )
    cur_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
    time_difference = timedelta(hours=cur_time.hour, minutes=cur_time.minute, seconds=(cur_time.second+(cur_time.microsecond/1000000))) - timedelta(hours=curr_time.hour, minutes=curr_time.minute, seconds=(curr_time.second+(curr_time.microsecond/1000000)))
    remaining_seconds = "{:.2f}".format(time_difference.total_seconds())
    
    warn_text = "\n\n<b>⚠️ ᴀꜰᴛᴇʀ 15 ᴍɪɴᴜᴛᴇꜱ ᴛʜɪꜱ ᴍᴇꜱꜱᴀɢᴇ ᴡɪʟʟ ʙᴇ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ᴅᴇʟᴇᴛᴇᴅ.</b>" if settings.get('auto_delete', True) else ""
    user_mention = message.from_user.mention if message.from_user else (message.chat.title or "User")
    cap = f"<b>🫡 ʜᴇʏ {user_mention},\n\n📬 ʜᴇʀᴇ ɪꜱ ᴡʜᴀᴛ ɪ ꜰᴏᴜɴᴅ ɪɴ ᴍʏ ᴅᴀᴛᴀʙᴀꜱᴇ ꜰᴏʀ ʏᴏᴜʀ ǫᴜᴇʀʏ {search.replace('<', '&lt;').replace('>', '&gt;')}.</b>"
    
    # Attach the warning immediately after the header
    cap += warn_text
    if not settings.get("button", True):
        cap += "\n\n"
        for file in files:
            safe_name = clean_filename(file['file_name']).replace('<', '&lt;').replace('>', '&gt;')
            cap += f"📂 <a href='https://telegram.me/{temp.U_NAME}?start=file_{file['file_id']}'>"
            cap += f"[{get_size(file['file_size'])}] {safe_name}</a>\n\n"
            
    # Make sure you DELETE the old `cap += warn_text` that was underneath this block!
    try:
        if reply_msg:
            await reply_msg.delete()
    except Exception:
        pass
        
    fuk = await message.reply_text(text=cap, reply_markup=InlineKeyboardMarkup(btn), disable_web_page_preview=True)
        
    try:
        if settings.get('auto_delete', True):
            from utils import delayed_delete
            delayed_delete([fuk, message], 900)
    except Exception as e:
        logger.error(f"Auto-delete error: {e}")
async def manual_filters(client, message, text=False):
    settings = await get_settings(message.chat.id)
    group_id = message.chat.id
    name = text or message.text
    reply_id = message.reply_to_message.id if message.reply_to_message else message.id
    keywords = await get_filters(group_id)
    for keyword in reversed(sorted(keywords, key=len)):
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, name, flags=re.IGNORECASE):
            reply_text, btn, alert, fileid = await find_filter(group_id, keyword)
            if reply_text:
                reply_text = reply_text.replace("\\n", "\n").replace("\\t", "\t")
            if btn is not None:
                try:
                    if fileid == "None":
                        if btn == "[]":
                            joelkb = await client.send_message(
                                group_id, 
                                reply_text, 
                                disable_web_page_preview=True,
                                reply_to_message_id=reply_id
                            )
                            await process_auto_settings(client, message, joelkb, settings)
                        else:
                            button = eval(btn)
                            joelkb = await client.send_message(
                                group_id,
                                reply_text,
                                disable_web_page_preview=True,
                                reply_markup=InlineKeyboardMarkup(button),
                                reply_to_message_id=reply_id
                            )
                            await process_auto_settings(client, message, joelkb, settings)
                    elif btn == "[]":
                        joelkb = await client.send_cached_media(
                            group_id,
                            fileid,
                            caption=reply_text or "",
                            reply_to_message_id=reply_id
                        )
                        await process_auto_settings(client, message, joelkb, settings)
                    else:
                        button = eval(btn)
                        joelkb = await message.reply_cached_media(
                            fileid,
                            caption=reply_text or "",
                            reply_markup=InlineKeyboardMarkup(button),
                            reply_to_message_id=reply_id
                        )
                        await process_auto_settings(client, message, joelkb, settings)
                except Exception as e:
                    logger.exception(e)
                break
    else:
        return False
async def global_filters(client, message, text=False):
    settings = await get_settings(message.chat.id)
    group_id = message.chat.id
    name = text or message.text
    reply_id = message.reply_to_message.id if message.reply_to_message else message.id
    keywords = await get_gfilters('gfilters')
    for keyword in reversed(sorted(keywords, key=len)):
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, name, flags=re.IGNORECASE):
            reply_text, btn, alert, fileid = await find_gfilter('gfilters', keyword)
            if reply_text:
                reply_text = reply_text.replace("\\n", "\n").replace("\\t", "\t")
            if btn is not None:
                try:
                    if fileid == "None":
                        if btn == "[]":
                            joelkb = await client.send_message(
                                group_id, 
                                reply_text, 
                                disable_web_page_preview=True,
                                reply_to_message_id=reply_id
                            )
                            manual = await manual_filters(client, message)
                            if manual == False:
                                settings = await get_settings(message.chat.id)
                                await process_auto_settings(client, message, joelkb, settings)
                            else:
                                try:
                                    if settings['auto_delete']:
                                        await joelkb.delete()
                                except KeyError:
                                    grpid = await active_connection(str(message.from_user.id))
                                    await save_group_settings(grpid, 'auto_delete', True)
                                    settings = await get_settings(message.chat.id)
                                    if settings['auto_delete']:
                                        await joelkb.delete()
                            
                        else:
                            button = eval(btn)
                            joelkb = await client.send_message(
                                group_id,
                                reply_text,
                                disable_web_page_preview=True,
                                reply_markup=InlineKeyboardMarkup(button),
                                reply_to_message_id=reply_id
                            )
                            manual = await manual_filters(client, message)
                            if manual == False:
                                settings = await get_settings(message.chat.id)
                                await process_auto_settings(client, message, joelkb, settings)
                            else:
                                try:
                                    if settings['auto_delete']:
                                        await joelkb.delete()
                                except KeyError:
                                    grpid = await active_connection(str(message.from_user.id))
                                    await save_group_settings(grpid, 'auto_delete', True)
                                    settings = await get_settings(message.chat.id)
                                    if settings['auto_delete']:
                                        await joelkb.delete()
                    elif btn == "[]":
                        joelkb = await client.send_cached_media(
                            group_id,
                            fileid,
                            caption=reply_text or "",
                            reply_to_message_id=reply_id
                        )
                        manual = await manual_filters(client, message)
                        if manual == False:
                            settings = await get_settings(message.chat.id)
                            await process_auto_settings(client, message, joelkb, settings) 
                        else:
                            try:
                                if settings['auto_delete']:
                                    await joelkb.delete()
                            except KeyError:
                                grpid = await active_connection(str(message.from_user.id))
                                await save_group_settings(grpid, 'auto_delete', True)
                                settings = await get_settings(message.chat.id)
                                if settings['auto_delete']:
                                    await joelkb.delete()
                    else:
                        button = eval(btn)
                        joelkb = await message.reply_cached_media(
                            fileid,
                            caption=reply_text or "",
                            reply_markup=InlineKeyboardMarkup(button),
                            reply_to_message_id=reply_id
                        )
                        manual = await manual_filters(client, message)
                        if manual == False:
                            settings = await get_settings(message.chat.id)
                            await process_auto_settings(client, message, joelkb, settings)
                        else:
                            try:
                                if settings['auto_delete']:
                                    await joelkb.delete()
                            except KeyError:
                                grpid = await active_connection(str(message.from_user.id))
                                await save_group_settings(grpid, 'auto_delete', True)
                                settings = await get_settings(message.chat.id)
                                if settings['auto_delete']:
                                    await joelkb.delete()
                                
                except Exception as e:
                    logger.exception(e)
                break
    else:
        return False
async def process_auto_settings(client, message, joelkb, settings):
    try:
        if settings.get('auto_ffilter', False):
            if message.text.startswith("/") or message.text.startswith("#") or message.text.startswith("!"):
                return
            ai_search = True
            reply_msg = await message.reply_sticker("CAACAgQAAxkBAAEKeqNlIpmeUoOEsEWOWEiPxPi3hH5q-QACbg8AAuHqsVDaMQeY6CcRojAE", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f'sᴇᴀᴄʜɪɴɢ ғᴏʀ {message.text}', url=CHNL_LNK)]]))
            await auto_filter(client, message.text, message, reply_msg, ai_search)
        
        if settings.get('auto_delete', False):
            if not settings.get('auto_ffilter', False):
                from utils import delayed_delete
                delayed_delete([joelkb], 900)
            else:
                await joelkb.delete()
    except Exception as e:
        logger.error(f"Error in process_auto_settings: {e}")








