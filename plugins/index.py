import logging, re, asyncio, os, zipfile
from utils import temp
from info import ADMINS, is_admin
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait, MessageNotModified
from pyrogram.errors import ChannelInvalid, ChatAdminRequired, UsernameInvalid, UsernameNotModified
from info import LOG_CHANNEL
from database.ia_filterdb import save_file
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

@Client.on_callback_query(filters.regex(r'^index'))
async def index_files(bot, query):
    if not query.from_user or not is_admin(query.from_user.id):
        return await query.answer("ʏᴏᴜ ᴅᴏ ɴᴏᴛ ʜᴀᴠᴇ ꜱᴜꜰꜰɪᴄɪᴇɴᴛ ʀɪɢʜᴛꜱ ᴛᴏ ᴅᴏ ᴛʜɪꜱ!", show_alert=True)
    if query.data.startswith('index_cancel'):
        try:
            _, chat_id = query.data.split("#")
            chat_id = int(chat_id)
        except ValueError:
            return await query.answer("ɪɴᴠᴀʟɪᴅ ʀᴇǫᴜᴇꜱᴛ", show_alert=True)
        temp.CANCEL[chat_id] = True
        await query.answer("ᴄᴀɴᴄᴇʟʟɪɴɢ ɪɴᴅᴇxɪɴɢ...")
        try:
            await query.message.edit("<b>ɪɴᴅᴇxɪɴɢ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴄᴀɴᴄᴇʟʟᴇᴅ!</b>\n\nᴛʜᴇ ʙᴀᴄᴋɢʀᴏᴜɴᴅ ᴘʀᴏᴄᴇꜱꜱ ʜᴀꜱ ʙᴇᴇɴ ꜱᴀꜰᴇʟʏ ᴀʙᴏʀᴛᴇᴅ.")
        except Exception:
            pass
        return
    try:
        _, raju, chat, lst_msg_id, from_user = query.data.split("#")
    except ValueError:
        return await query.answer("ɪɴᴠᴀʟɪᴅ ʀᴇǫᴜᴇꜱᴛ", show_alert=True)

    msg = query.message
    await query.answer('ᴘʀᴏᴄᴇꜱꜱɪɴɢ...', show_alert=True)
    try:
        chat = int(chat)
    except Exception:
        chat = chat
    await msg.edit(
        "<b>ꜱᴛᴀʀᴛɪɴɢ ɪɴᴅᴇxɪɴɢ...</b>",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton('ᴄᴀɴᴄᴇʟ', callback_data=f'index_cancel#{chat}')]]
        )
    )
    await index_files_to_db(int(lst_msg_id), chat, msg, bot)


@Client.on_message(filters.private & filters.command('index') & filters.user(ADMINS))
async def send_for_index(bot, message):
    ask_msg = await bot.ask(message.chat.id, "<b>ɴᴏᴡ, ꜱᴇɴᴅ ᴍᴇ ʏᴏᴜʀ ᴄʜᴀɴɴᴇʟ'ꜱ ʟᴀꜱᴛ ᴘᴏꜱᴛ ʟɪɴᴋ ᴏʀ ꜰᴏʀᴡᴀʀᴅ ᴛʜᴇ ʟᴀꜱᴛ ᴍᴇꜱꜱᴀɢᴇ ꜰʀᴏᴍ ʏᴏᴜʀ ɪɴᴅᴇx ᴄʜᴀɴɴᴇʟ.\n\nʏᴏᴜ ᴄᴀɴ ᴀʟꜱᴏ ꜱᴇᴛ ᴀ ꜱᴋɪᴘ ɴᴜᴍʙᴇʀ ᴜꜱɪɴɢ: /setskip ʏᴏᴜʀ_ꜱᴋɪᴘ_ɴᴜᴍʙᴇʀ</b>")
    if ask_msg.forward_from_chat and ask_msg.forward_from_chat.type == enums.ChatType.CHANNEL:
        last_msg_id = ask_msg.forward_from_message_id
        chat_id = ask_msg.forward_from_chat.username or ask_msg.forward_from_chat.id
    elif ask_msg.text:
        regex = re.compile(r"(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")
        match = regex.match(ask_msg.text)
        if not match:
            return await ask_msg.reply('ɪɴᴠᴀʟɪᴅ ʟɪɴᴋ.\n\nᴘʟᴇᴀꜱᴇ ᴛʀʏ ᴀɢᴀɪɴ ᴜꜱɪɴɢ /index')
        chat_id = match.group(4)
        last_msg_id = int(match.group(5))
        if chat_id.isnumeric():
            chat_id  = int(("-100" + chat_id))
    else:
        return
    try:
        await bot.get_chat(chat_id)
    except ChannelInvalid:
        return await ask_msg.reply('ᴛʜɪꜱ ᴍᴀʏ ʙᴇ ᴀ ᴘʀɪᴠᴀᴛᴇ ᴄʜᴀɴɴᴇʟ ᴏʀ ɢʀᴏᴜᴘ.\n\nᴘʟᴇᴀꜱᴇ ᴍᴀᴋᴇ ᴍᴇ ᴀɴ ᴀᴅᴍɪɴ ᴛʜᴇʀᴇ ᴛᴏ ɪɴᴅᴇx ᴛʜᴇ ꜰɪʟᴇꜱ.')
    except (UsernameInvalid, UsernameNotModified):
        return await ask_msg.reply('<b>ɪɴᴠᴀʟɪᴅ ʟɪɴᴋ ꜱᴘᴇᴄɪꜰɪᴇᴅ.</b>')
    except Exception as e:
        logger.exception(e)
        return await ask_msg.reply(f'ᴇʀʀᴏʀꜱ: {e}')
    try:
        k = await bot.get_messages(chat_id, last_msg_id)
    except Exception:
        return await message.reply('ᴘʟᴇᴀꜱᴇ ᴍᴀᴋᴇ ꜱᴜʀᴇ ɪ ᴀᴍ ᴀɴ ᴀᴅᴍɪɴ ɪɴ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ, ᴇꜱᴘᴇᴄɪᴀʟʟʏ ɪꜰ ɪᴛ ɪꜱ ᴘʀɪᴠᴀᴛᴇ.')
    if k.empty:
        return await message.reply('ᴛʜɪꜱ ᴍᴀʏ ʙᴇ ᴀ ɢʀᴏᴜᴘ, ᴀɴᴅ ɪ ᴀᴍ ɴᴏᴛ ᴀɴ ᴀᴅᴍɪɴ ᴛʜᴇʀᴇ.')

    buttons = [[
        InlineKeyboardButton('ʏᴇꜱ', callback_data=f'index#accept#{chat_id}#{last_msg_id}#{message.from_user.id}')
    ],[
        InlineKeyboardButton('ᴄᴀɴᴄᴇʟ', callback_data='close_data')
    ]]
    reply_markup = InlineKeyboardMarkup(buttons)
    return await message.reply(
        f'<b>ᴅᴏ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ɪɴᴅᴇx ᴛʜɪꜱ ᴄʜᴀɴɴᴇʟ/ɢʀᴏᴜᴘ?\n\nᴄʜᴀᴛ ɪᴅ/ᴜꜱᴇʀɴᴀᴍᴇ:</b> <code>{chat_id}</code>\n<b>ʟᴀꜱᴛ ᴍᴇꜱꜱᴀɢᴇ ɪᴅ:</b> <code>{last_msg_id}</code>',
        reply_markup=reply_markup
    )


@Client.on_message(filters.command('setskip') & filters.user(ADMINS))
async def set_skip_number(bot, message):
    if ' ' in message.text:
        _, skip = message.text.split(" ")
        try:
            skip = int(skip)
        except Exception:
            return await message.reply("ꜱᴋɪᴘ ɴᴜᴍʙᴇʀ ᴍᴜꜱᴛ ʙᴇ ᴀɴ ɪɴᴛᴇɢᴇʀ.")
        await message.reply(f"ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ꜱᴇᴛ ꜱᴋɪᴘ ɴᴜᴍʙᴇʀ ᴛᴏ <code>{skip}</code>.")
        temp.CURRENT = int(skip)
    else:
        await message.reply("<b>ᴘʟᴇᴀꜱᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ꜱᴋɪᴘ ɴᴜᴍʙᴇʀ.</b>")


SERIES_PATTERNS = [
    # Season & Episode combos: S01E01, S1E1, S01EP01, S01.E01, S01_E01, S01 - E01, Season 1 Episode 1
    re.compile(r"(?i)\bS(?:eason)?\s*\d{1,2}\s*[-._\s]?(?:E|EP|Episode)\s*\d{1,4}\b"),
    
    # Standalone Season: Season 1, Season 01, Seasons 1-3, S01-S03, Season Pack
    re.compile(r"(?i)\b(?:Season\s*\d{1,2}|Seasons\s*\d{1,2}|S\d{1,2}\s*[-to&]\s*S?\d{1,2})\b"),
    
    # Standalone 2-digit season tag like S01, S02, S09
    re.compile(r"(?i)\bS0[1-9]\b"),
    
    # Episode with number: Episode 1, Ep 01, Ep.01, Ep-01, Episodes 01-10
    re.compile(r"(?i)\b(?:Episode|Episodes|Ep|EP)\s*[-._#]?\s*\d{1,4}\b"),
    
    # Standalone E01 to E999 (requires at least 2 digits to prevent matching single letters)
    re.compile(r"(?i)\bE\d{2,4}\b"),
    
    # Anime episode style: " - 01 ", " - 105 ", " - 01 [720p]", " - 12 (1080p)"
    re.compile(r"(?i)\s+-\s+\d{1,4}(?:\s*v\d+)?\s*(?:\[|\(|\.|\s|$|480|720|1080|2160|mkv|mp4)"),
    
    # Anime bracket numbering e.g. [01], [02], [E01], [EP01]
    re.compile(r"(?i)\[(?:EP|E)?\s*\d{1,4}(?:\s*v\d+)?\]"),
    
    # TV / Drama / Webseries keywords
    re.compile(r"(?i)\b(?:webseries|web-series|tvseries|tv-series|kdrama|k-drama|cdrama|c-drama|jdrama|j-drama|dorama|docuseries|anime)\b"),
    
    # Complete series / Season packs
    re.compile(r"(?i)\b(?:complete\s*season|complete\s*series|full\s*season|all\s*episodes|season\s*pack|series\s*pack)\b"),
]

def is_series_or_anime(file_name: str, caption: str = "") -> bool:
    text = f"{file_name} {caption}".strip()
    if not text:
        return False
        
    # Star Wars movie exception: Star Wars Episode I to IX are movies
    if re.search(r"(?i)\bstar\s*wars\b", text):
        if re.search(r"(?i)\bS(?:eason)?\s*\d{1,2}", text):
            return True
        return False

    for pattern in SERIES_PATTERNS:
        if pattern.search(text):
            return True
            
    return False

async def send_index_logs(bot, msg, saved_path, skipped_path, dup_path, saved_count, skipped_count, dup_count):
    files_to_send = [
        (saved_path, f"<b>ꜱᴀᴠᴇᴅ ᴍᴏᴠɪᴇꜱ:</b> <code>{saved_count}</code>"),
        (skipped_path, f"<b>ꜱᴋɪᴘᴘᴇᴅ ꜱᴇʀɪᴇꜱ/ᴀɴɪᴍᴇ:</b> <code>{skipped_count}</code>"),
        (dup_path, f"<b>ᴅᴜᴘʟɪᴄᴀᴛᴇ ꜰɪʟᴇꜱ:</b> <code>{dup_count}</code>"),
    ]
    for file_path, cap in files_to_send:
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            try:
                size_mb = os.path.getsize(file_path) / (1024 * 1024)
                if size_mb < 45:
                    await msg.reply_document(document=file_path, caption=cap)
                else:
                    zip_path = f"{file_path}.zip"
                    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
                        z.write(file_path, os.path.basename(file_path))
                    await msg.reply_document(document=zip_path, caption=f"{cap} <b>(ᴄᴏᴍᴘʀᴇꜱꜱᴇᴅ ᴢɪᴘ)</b>")
                    try:
                        os.remove(zip_path)
                    except Exception:
                        pass
            except Exception as e:
                logger.error(f"Failed to send log file {file_path}: {e}")

async def index_files_to_db(lst_msg_id, chat, msg, bot):
    total_files = 0
    skipped_series = 0
    duplicate = 0
    errors = 0
    deleted = 0
    no_media = 0
    unsupported = 0
    
    log_dir = "index_logs"
    os.makedirs(log_dir, exist_ok=True)
    clean_chat = str(chat).replace("-100", "").replace("-", "")
    saved_log_path = os.path.join(log_dir, f"saved_movies_ch{clean_chat}.txt")
    skipped_log_path = os.path.join(log_dir, f"skipped_series_ch{clean_chat}.txt")
    dup_log_path = os.path.join(log_dir, f"duplicates_ch{clean_chat}.txt")

    try:
        current = int(temp.CURRENT)
        lst_msg_id = int(lst_msg_id)
        temp.CANCEL[chat] = False
        
        with open(saved_log_path, "w", encoding="utf-8") as saved_file, \
             open(skipped_log_path, "w", encoding="utf-8") as skipped_file, \
             open(dup_log_path, "w", encoding="utf-8") as dup_file:
             
            while current <= lst_msg_id:
                if temp.CANCEL.get(chat):
                    break
                    
                # Fetch messages in chunks of 200 (Telegram API limit for Bots)
                chunk = list(range(current, min(current + 200, lst_msg_id + 1)))
                try:
                    messages = await bot.get_messages(chat, chunk)
                except FloodWait as e:
                    await asyncio.sleep(e.value)
                    continue
                
                for message in messages:
                    if temp.CANCEL.get(chat):
                        break
                        
                    if current % 50 == 0:
                        saved_file.flush()
                        skipped_file.flush()
                        dup_file.flush()
                        can = [[InlineKeyboardButton('ᴄᴀɴᴄᴇʟ', callback_data=f'index_cancel#{chat}')]]
                        reply = InlineKeyboardMarkup(can)
                        try:
                            await msg.edit_text(
                                text=f"<b><u>ɪɴᴅᴇxɪɴɢ ɪɴ ᴘʀᴏɢʀᴇꜱꜱ</u></b>\n\n"
                                     f"<b>• ᴛᴏᴛᴀʟ ᴍᴇꜱꜱᴀɢᴇꜱ ꜰᴇᴛᴄʜᴇᴅ:</b> <code>{current}</code>\n"
                                     f"<b>• ᴍᴏᴠɪᴇꜱ ꜱᴀᴠᴇᴅ ᴛᴏ ᴅʙ:</b> <code>{total_files}</code>\n"
                                     f"<b>• ꜱᴇʀɪᴇꜱ/ᴀɴɪᴍᴇ ꜱᴋɪᴘᴘᴇᴅ:</b> <code>{skipped_series}</code>\n"
                                     f"<b>• ᴅᴜᴘʟɪᴄᴀᴛᴇꜱ ꜱᴋɪᴘᴘᴇᴅ:</b> <code>{duplicate}</code>\n"
                                     f"<b>• ᴅᴇʟᴇᴛᴇᴅ ꜱᴋɪᴘᴘᴇᴅ:</b> <code>{deleted}</code>\n"
                                     f"<b>• ɴᴏɴ-ᴍᴇᴅɪᴀ ꜱᴋɪᴘᴘᴇᴅ:</b> <code>{no_media + unsupported}</code>\n"
                                     f"<b>• ᴇʀʀᴏʀꜱ:</b> <code>{errors}</code>",
                                reply_markup=reply
                            )
                        except MessageNotModified:
                            pass
                        except FloodWait as e:
                            await asyncio.sleep(e.value)
                        except Exception:
                            pass
                            
                    current += 1
                    
                    if message.empty:
                        deleted += 1
                        continue
                    elif not message.media:
                        no_media += 1
                        continue
                    elif message.media not in [enums.MessageMediaType.VIDEO, enums.MessageMediaType.AUDIO, enums.MessageMediaType.DOCUMENT]:
                        unsupported += 1
                        continue
                    
                    media = getattr(message, message.media.value, None)
                    if not media:
                        unsupported += 1
                        continue
                        
                    media_name = getattr(media, "file_name", "") or ""
                    plain_caption = message.caption or ""
                    log_entry = media_name or plain_caption.split("\n")[0] or f"msg_{message.id}"
                    
                    if is_series_or_anime(media_name, plain_caption):
                        skipped_series += 1
                        skipped_file.write(f"{log_entry}\n")
                        continue
                        
                    media.caption = message.caption.html if message.caption else None
                    aynav, vnay = await save_file(media)
                    
                    if aynav:
                        total_files += 1
                        saved_file.write(f"{log_entry}\n")
                    elif vnay == 0:
                        duplicate += 1
                        dup_file.write(f"{log_entry}\n")
                    elif vnay == 2:
                        errors += 1
                        
                if temp.CANCEL.get(chat):
                    break

        if temp.CANCEL.get(chat):
            try:
                await msg.edit_text(
                    f"<b><u>ɪɴᴅᴇxɪɴɢ ᴄᴀɴᴄᴇʟʟᴇᴅ</u></b>\n\n"
                    f"<b>• ᴛᴏᴛᴀʟ ᴍᴇꜱꜱᴀɢᴇꜱ ꜰᴇᴛᴄʜᴇᴅ:</b> <code>{current}</code>\n"
                    f"<b>• ᴍᴏᴠɪᴇꜱ ꜱᴀᴠᴇᴅ ᴛᴏ ᴅʙ:</b> <code>{total_files}</code>\n"
                    f"<b>• ꜱᴇʀɪᴇꜱ/ᴀɴɪᴍᴇ ꜱᴋɪᴘᴘᴇᴅ:</b> <code>{skipped_series}</code>\n"
                    f"<b>• ᴅᴜᴘʟɪᴄᴀᴛᴇꜱ ꜱᴋɪᴘᴘᴇᴅ:</b> <code>{duplicate}</code>\n"
                    f"<b>• ᴅᴇʟᴇᴛᴇᴅ ꜱᴋɪᴘᴘᴇᴅ:</b> <code>{deleted}</code>\n"
                    f"<b>• ɴᴏɴ-ᴍᴇᴅɪᴀ ꜱᴋɪᴘᴘᴇᴅ:</b> <code>{no_media + unsupported}</code>\n"
                    f"<b>• ᴇʀʀᴏʀꜱ:</b> <code>{errors}</code>"
                )
            except Exception:
                pass
            await send_index_logs(bot, msg, saved_log_path, skipped_log_path, dup_log_path, total_files, skipped_series, duplicate)
            return
            
        try:
            await msg.edit_text(
                f"<b><u>ɪɴᴅᴇxɪɴɢ ᴄᴏᴍᴘʟᴇᴛᴇᴅ</u></b>\n\n"
                f"<b>• ᴛᴏᴛᴀʟ ᴍᴇꜱꜱᴀɢᴇꜱ ꜰᴇᴛᴄʜᴇᴅ:</b> <code>{current}</code>\n"
                f"<b>• ᴍᴏᴠɪᴇꜱ ꜱᴀᴠᴇᴅ ᴛᴏ ᴅʙ:</b> <code>{total_files}</code>\n"
                f"<b>• ꜱᴇʀɪᴇꜱ/ᴀɴɪᴍᴇ ꜱᴋɪᴘᴘᴇᴅ:</b> <code>{skipped_series}</code>\n"
                f"<b>• ᴅᴜᴘʟɪᴄᴀᴛᴇꜱ ꜱᴋɪᴘᴘᴇᴅ:</b> <code>{duplicate}</code>\n"
                f"<b>• ᴅᴇʟᴇᴛᴇᴅ ꜱᴋɪᴘᴘᴇᴅ:</b> <code>{deleted}</code>\n"
                f"<b>• ɴᴏɴ-ᴍᴇᴅɪᴀ ꜱᴋɪᴘᴘᴇᴅ:</b> <code>{no_media + unsupported}</code>\n"
                f"<b>• ᴇʀʀᴏʀꜱ:</b> <code>{errors}</code>"
            )
        except Exception:
            pass
        await send_index_logs(bot, msg, saved_log_path, skipped_log_path, dup_log_path, total_files, skipped_series, duplicate)

    except Exception as e:
        logger.exception(e)
        try:
            await msg.edit_text(
                f"<b><u>ɪɴᴅᴇxɪɴɢ ꜱᴛᴏᴘᴘᴇᴅ ᴅᴜᴇ ᴛᴏ ᴇʀʀᴏʀ</u></b>\n\n"
                f"<b>• ᴇʀʀᴏʀ:</b> <code>{e}</code>\n\n"
                f"<b>• ᴛᴏᴛᴀʟ ᴍᴇꜱꜱᴀɢᴇꜱ ꜰᴇᴛᴄʜᴇᴅ:</b> <code>{current}</code>\n"
                f"<b>• ᴍᴏᴠɪᴇꜱ ꜱᴀᴠᴇᴅ ᴛᴏ ᴅʙ:</b> <code>{total_files}</code>\n"
                f"<b>• ꜱᴇʀɪᴇꜱ/ᴀɴɪᴍᴇ ꜱᴋɪᴘᴘᴇᴅ:</b> <code>{skipped_series}</code>\n"
                f"<b>• ᴅᴜᴘʟɪᴄᴀᴛᴇꜱ ꜱᴋɪᴘᴘᴇᴅ:</b> <code>{duplicate}</code>\n"
                f"<b>• ᴅᴇʟᴇᴛᴇᴅ ꜱᴋɪᴘᴘᴇᴅ:</b> <code>{deleted}</code>\n"
                f"<b>• ɴᴏɴ-ᴍᴇᴅɪᴀ ꜱᴋɪᴘᴘᴇᴅ:</b> <code>{no_media + unsupported}</code>\n"
                f"<b>• ᴇʀʀᴏʀꜱ:</b> <code>{errors}</code>"
            )
        except Exception:
            pass
        await send_index_logs(bot, msg, saved_log_path, skipped_log_path, dup_log_path, total_files, skipped_series, duplicate)

