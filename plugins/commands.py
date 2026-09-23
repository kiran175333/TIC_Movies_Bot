import os, logging, random, asyncio, time, datetime, re, sys, base64
from Script import script
from pyrogram import Client, filters, enums
from pyrogram.errors import ChatAdminRequired, FloodWait, MessageNotModified
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.ia_filterdb import col, sec_col, thi_col, db as fir_db, sec_db, thi_db, get_file_details, unpack_new_file_id, get_bad_files, get_trending_searches
from database.users_chats_db import db
from info import (SUPPORT_LINK, CHANNELS, ADMINS, is_admin, SHORTLINK_MODE, AUTH_CHANNEL, PAYMENT_TEXT, LOG_CHANNEL, PICS, CUSTOM_FILE_CAPTION, CHNL_LNK, GRP_LNK, PREMIUM_MODE, MAX_B_TN, VERIFY, SHORTLINK_API, SHORTLINK_URL, TUTORIAL)
from utils import (remove_junk, get_settings, pub_is_subscribed, get_size, is_subscribed, save_group_settings, temp, verify_user, check_token, check_verification, get_token, get_shortlink, get_seconds)
from database.connections_mdb import active_connection

logger = logging.getLogger(__name__)

BATCH_FILES = {}

def make_search_slug(title: str) -> str:
    import base64
    truncated = title[:45]
    encoded = base64.urlsafe_b64encode(truncated.encode()).decode().rstrip("=")
    return f"b64-{encoded}"

@Client.on_message(filters.new_chat_members & filters.group)
async def save_group(bot, message):
    r_j_check = [u.id for u in message.new_chat_members]
    if temp.ME in r_j_check:
        if not await db.get_chat(message.chat.id):
            try:
                total = await bot.get_chat_members_count(message.chat.id)
            except Exception:
                total = 0
            r_j = message.from_user.mention if message.from_user else "Anonymous" 
            await bot.send_message(LOG_CHANNEL, script.LOG_TEXT_G.format(message.chat.title, message.chat.id, total, r_j))       
            await db.add_chat(message.chat.id, message.chat.title)
        
        buttons = [
            [
                InlineKeyboardButton("⌖ ᴏᴜʀ ᴄʜᴀɴɴᴇʟ ⌖", url=CHNL_LNK),
                InlineKeyboardButton("⌖ ᴏᴜʀ ɢʀᴏᴜᴘ ⌖", url=GRP_LNK)
            ]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply_text(
            text=f"<b>ᴛʜᴀɴᴋʏᴏᴜ ꜰᴏʀ ᴀᴅᴅɪɴɢ ᴍᴇ ɪɴ {message.chat.title}</b>",
            reply_markup=reply_markup
        )

@Client.on_message(filters.command("start") & filters.incoming)
async def start(client, message):
    if message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        buttons = [
            [
                InlineKeyboardButton("⌖ ᴏᴜʀ ᴄʜᴀɴɴᴇʟ ⌖", url=CHNL_LNK),
                InlineKeyboardButton("⌖ ᴏᴜʀ ɢʀᴏᴜᴘ ⌖", url=GRP_LNK)
            ],
            [InlineKeyboardButton("✉ ᴍᴇꜱꜱᴀɢᴇ ᴍᴇ ᴘʀɪᴠᴀᴛᴇʟʏ ✉", url=f"http://t.me/{temp.U_NAME}?start=start")]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        msg = await message.reply(
            script.GRP_START_TXT.format(message.from_user.mention if message.from_user else message.chat.title), 
            reply_markup=reply_markup, 
            disable_web_page_preview=True
        )
        
        if not await db.get_chat(message.chat.id):
            try:
                total = await client.get_chat_members_count(message.chat.id)
            except Exception:
                total = 0
            await client.send_message(LOG_CHANNEL, script.LOG_TEXT_G.format(message.chat.title, message.chat.id, total, "Unknown"))       
            await db.add_chat(message.chat.id, message.chat.title)
            
        await asyncio.sleep(60)
        try:
            await msg.delete()
            await message.delete()
        except Exception:
            pass
        return 
        
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)
        await client.send_message(LOG_CHANNEL, script.LOG_TEXT_P.format(message.from_user.id, message.from_user.mention))
    
    if len(message.command) != 2:
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
        m = await message.reply_sticker("CAACAgIAAxkBAAEKDU1k3hdblAMuXWkapN9YbcsWdhHKXAAC_g4AAudvIEnxNZjTX_WA2DAE") 
        await asyncio.sleep(1.5)
        try:
            await m.delete()
        except Exception:
            pass
        await message.reply_photo(
            photo=random.choice(PICS),
            caption=script.START_TXT.format(message.from_user.mention),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        return
    
    if AUTH_CHANNEL and not await is_subscribed(client, message):
        try:
            chat = await client.get_chat(int(AUTH_CHANNEL))
            invite_link = chat.invite_link or (await client.create_chat_invite_link(int(AUTH_CHANNEL))).invite_link
        except Exception as e:
            print(e)
            await message.reply_text("ᴘʟᴇᴀꜱᴇ ᴍᴀᴋᴇ ꜱᴜʀᴇ ᴛʜᴇ ʙᴏᴛ ɪꜱ ᴀɴ ᴀᴅᴍɪɴ ɪɴ ᴛʜᴇ ꜰᴏʀᴄᴇ-ꜱᴜʙ ᴄʜᴀɴɴᴇʟ.")
            return
        try:
            btn = [[InlineKeyboardButton("✪ ᴊᴏɪɴ ᴏᴜʀ ᴄʜᴀɴɴᴇʟ ✪", url=invite_link)]]
            if len(message.command) > 1 and message.command[1] != "subscribe":
                try:
                    kk, file_id = message.command[1].split("_", 1)
                    btn.append([InlineKeyboardButton("↻ ᴛʀʏ ᴀɢᴀɪɴ ↻", callback_data=f"checksub#{kk}#{file_id}")])
                except (IndexError, ValueError):
                    btn.append([InlineKeyboardButton("↻ ᴛʀʏ ᴀɢᴀɪɴ ↻", url=f"https://t.me/{temp.U_NAME}?start={message.command[1]}")])
            
            text = "<b>ʏᴏᴜ ʜᴀᴠᴇɴ'ᴛ ᴊᴏɪɴᴇᴅ ᴏᴜʀ ᴄʜᴀɴɴᴇʟ ʏᴇᴛ.\n\nᴘʟᴇᴀꜱᴇ ᴊᴏɪɴ ᴏᴜʀ ᴄʜᴀɴɴᴇʟ ꜰɪʀꜱᴛ, ᴛʜᴇɴ ᴛʀʏ ᴀɢᴀɪɴ.</b>"
            await client.send_message(
                chat_id=message.from_user.id,
                text=text,
                reply_markup=InlineKeyboardMarkup(btn),
                parse_mode=enums.ParseMode.HTML
            )
            return
        except Exception as e:
            print(e)
            return await message.reply_text("ꜱᴏᴍᴇᴛʜɪɴɢ ᴡᴇɴᴛ ᴡʀᴏɴɢ ᴡɪᴛʜ ᴛʜᴇ ꜰᴏʀᴄᴇ-ꜱᴜʙꜱᴄʀɪʙᴇ ꜰᴇᴀᴛᴜʀᴇ.")
            
    if len(message.command) == 2 and message.command[1] in ["subscribe", "error", "okay", "help", "start"]:
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
        await message.reply_photo(
            photo=random.choice(PICS),
            caption=script.START_TXT.format(message.from_user.mention),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        return 
    
    data = message.command[1]
    
    # --- NEW SEARCH TRIGGER BLOCK ---
    if data.startswith("getsrc-"):
        search_query = data.replace("getsrc-", "", 1).replace("-", " ").strip()
        message.text = search_query  # Overwrite text to bypass the "/" command block in auto_filter
        try:
            from plugins.pm_filter import auto_filter
        except ImportError:
            from pm_filter import auto_filter
        
        await auto_filter(client, search_query, message, None, True)
        return
    elif data.startswith("b64-"):
        import base64
        encoded = data.replace("b64-", "", 1)
        encoded += "=" * ((4 - len(encoded) % 4) % 4)
        search_query = base64.urlsafe_b64decode(encoded).decode()
        message.text = search_query
        try:
            from plugins.pm_filter import auto_filter
        except ImportError:
            from pm_filter import auto_filter
            
        await auto_filter(client, search_query, message, None, True)
        return
    # --------------------------------

    try:
        pre, file_id = data.split('_', 1)
    except Exception:
        file_id = data
        pre = ""

    if data.split("-", 1)[0] == "verify":
        try:
            _, userid, token = data.split("-", 2)
        except ValueError:
            return await message.reply_text(text="<b>ɪɴᴠᴀʟɪᴅ ᴏʀ ᴇxᴘɪʀᴇᴅ ʟɪɴᴋ.</b>")
            
        if str(message.from_user.id) != str(userid):
            return await message.reply_text(text="<b>ɪɴᴠᴀʟɪᴅ ᴏʀ ᴇxᴘɪʀᴇᴅ ʟɪɴᴋ.</b>")
        is_valid = await check_token(client, userid, token)
        if is_valid == True:
            text = "<b>ʜᴇʏ {},\n\nʏᴏᴜ ʜᴀᴠᴇ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴄᴏᴍᴘʟᴇᴛᴇᴅ ᴛʜᴇ ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ.\n\nʏᴏᴜ ɴᴏᴡ ʜᴀᴠᴇ ᴜɴʟɪᴍɪᴛᴇᴅ ᴀᴄᴄᴇꜱꜱ ꜰᴏʀ 10 ᴍɪɴᴜᴛᴇs.\n\n</b>"
            if PREMIUM_MODE == True:
                text += "<b>ɪꜰ ʏᴏᴜ ᴡᴀɴᴛ ᴅɪʀᴇᴄᴛ ꜰɪʟᴇꜱ ᴡɪᴛʜᴏᴜᴛ ᴏᴘᴇɴɪɴɢ ʟɪɴᴋꜱ ᴏʀ ᴡᴀᴛᴄʜɪɴɢ ᴀᴅs, ᴘʟᴇᴀꜱᴇ ʙᴜʏ ᴏᴜʀ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ.\n\nꜱᴇɴᴅ /plan ᴛᴏ ᴄʜᴇᴄᴋ ᴏᴜᴛ ᴏᴜʀ ᴘʟᴀɴꜱ.</b>"            
            await message.reply_text(text=text.format(message.from_user.mention))
            await verify_user(client, userid, token)
            return # <--- This stops the bot from crashing here
        else:
            return await message.reply_text(text="<b>ɪɴᴠᴀʟɪᴅ ᴏʀ ᴇxᴘɪʀᴇᴅ ʟɪɴᴋ.</b>")
            

        
    elif data.startswith("short"):
        user = message.from_user.id
        pre = 'file'
        g = await get_shortlink(f"https://telegram.me/{temp.U_NAME}?start={pre}_{file_id}")
        
        if not g:
            error_msg = "<b>⚠️ ᴛᴇᴍᴘᴏʀᴀʀʏ ꜱᴇʀᴠᴇʀ ɪꜱꜱᴜᴇ\n\nᴏᴜʀ ʟɪɴᴋ-ɢᴇɴᴇʀᴀᴛɪɴɢ ᴡᴇʙsɪᴛᴇ ɪꜱ ᴄᴜʀʀᴇɴᴛʟʏ ᴇxᴘᴇʀɪᴇɴᴄɪɴɢ ᴅᴏᴡɴᴛɪᴍᴇ, ᴡʜɪᴄʜ ᴍᴇᴀɴꜱ ᴡᴇ ᴄᴀɴɴᴏᴛ ɢᴇɴᴇʀᴀᴛᴇ ʏᴏᴜʀ ꜰʀᴇᴇ ʟɪɴᴋ ʀɪɢʜᴛ ɴᴏᴡ.\n\nᴘʟᴇᴀꜱᴇ ᴛʀʏ ʀᴇǫᴜᴇꜱᴛɪɴɢ ᴛʜᴇ ꜰɪʟᴇ ᴀɢᴀɪɴ ɪɴ ᴀ ʙɪᴛ.\n\nᴛɪʀᴇᴅ ᴏꜰ ʟɪɴᴋꜱ ᴀɴᴅ ᴡᴀɪᴛɪɴɢ? ᴡᴀɴᴛ ᴛᴏ ꜱᴋɪᴘ ᴛʜᴇꜱᴇ ʟɪɴᴋꜱ ᴄᴏᴍᴘʟᴇᴛᴇʟʏ?\n\nɢᴇᴛ ɪɴꜱᴛᴀɴᴛ, ᴀᴅ-ꜰʀᴇᴇ ꜰɪʟᴇꜱ ᴅɪʀᴇᴄᴛʟʏ ɪɴ ʏᴏᴜʀ ᴄʜᴀᴛ ᴠɪᴀ /plan.</b>"
            await client.send_message(chat_id=user, text=error_msg)
            return

        btn = [[
            InlineKeyboardButton('▼ ᴅᴏᴡɴʟᴏᴀᴅ ɴᴏᴡ ▼', url=g)
        ]]
        if TUTORIAL:
            btn.append([InlineKeyboardButton('? ʜᴏᴡ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ ?', url=TUTORIAL)])
        text = "<b>ʜᴇʏ {},\n\nʏᴏᴜʀ ꜰɪʟᴇ ɪꜱ ʀᴇᴀᴅʏ.\n\nᴄʟɪᴄᴋ ᴏɴ ᴛʜᴇ 'ᴅᴏᴡɴʟᴏᴀᴅ ɴᴏᴡ' ʙᴜᴛᴛᴏɴ ᴀɴᴅ ᴏᴘᴇɴ ᴛʜᴇ ʟɪɴᴋ ᴛᴏ ɢᴇᴛ ʏᴏᴜʀ ꜰɪʟᴇ.\n\n</b>"
        if PREMIUM_MODE == True:
            text += "<b>ɪꜰ ʏᴏᴜ ᴡᴀɴᴛ ᴅɪʀᴇᴄᴛ ꜰɪʟᴇꜱ ᴡɪᴛʜᴏᴜᴛ ᴏᴘᴇɴɪɴɢ ʟɪɴᴋꜱ ᴏʀ ᴡᴀᴛᴄʜɪɴɢ ᴀᴅs, ᴘʟᴇᴀꜱᴇ ʙᴜʏ ᴏᴜʀ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ.\n\nꜱᴇɴᴅ /plan ᴛᴏ ᴄʜᴇᴄᴋ ᴏᴜᴛ ᴏᴜʀ ᴘʟᴀɴꜱ.</b>"
        k = await client.send_message(chat_id=user, text=text.format(message.from_user.mention), reply_markup=InlineKeyboardMarkup(btn))
        from utils import delayed_delete
        delayed_delete([k], 900)
        return

        
    elif data.startswith("files"):
        user = message.from_user.id
        pre = 'file'
        if SHORTLINK_MODE and not await db.has_premium_access(user):
            g = await get_shortlink(f"https://telegram.me/{temp.U_NAME}?start={pre}_{file_id}")
            
            if not g:
                error_msg = "<b>⚠️ ᴛᴇᴍᴘᴏʀᴀʀʏ ꜱᴇʀᴠᴇʀ ɪꜱꜱᴜᴇ\n\nᴏᴜʀ ʟɪɴᴋ-ɢᴇɴᴇʀᴀᴛɪɴɢ ᴡᴇʙsɪᴛᴇ ɪꜱ ᴄᴜʀʀᴇɴᴛʟʏ ᴇxᴘᴇʀɪᴇɴᴄɪɴɢ ᴅᴏᴡɴᴛɪᴍᴇ, ᴡʜɪᴄʜ ᴍᴇᴀɴꜱ ᴡᴇ ᴄᴀɴɴᴏᴛ ɢᴇɴᴇʀᴀᴛᴇ ʏᴏᴜʀ ꜰʀᴇᴇ ʟɪɴᴋ ʀɪɢʜᴛ ɴᴏᴡ.\n\nᴘʟᴇᴀꜱᴇ ᴛʀʏ ʀᴇǫᴜᴇꜱᴛɪɴɢ ᴛʜᴇ ꜰɪʟᴇ ᴀɢᴀɪɴ ɪɴ ᴀ ʙɪᴛ.\n\nᴛɪʀᴇᴅ ᴏꜰ ʟɪɴᴋꜱ ᴀɴᴅ ᴡᴀɪᴛɪɴɢ? ᴡᴀɴᴛ ᴛᴏ ꜱᴋɪᴘ ᴛʜᴇꜱᴇ ʟɪɴᴋꜱ ᴄᴏᴍᴘʟᴇᴛᴇʟʏ?\n\nɢᴇᴛ ɪɴꜱᴛᴀɴᴛ, ᴀᴅ-ꜰʀᴇᴇ ꜰɪʟᴇꜱ ᴅɪʀᴇᴄᴛʟʏ ɪɴ ʏᴏᴜʀ ᴄʜᴀᴛ ᴠɪᴀ /plan.</b>"
                await client.send_message(chat_id=message.from_user.id, text=error_msg)
                return
                
            btn = [[
                InlineKeyboardButton('▼ ᴅᴏᴡɴʟᴏᴀᴅ ɴᴏᴡ ▼', url=g)
            ]]
            if TUTORIAL:
                btn.append([InlineKeyboardButton('? ʜᴏᴡ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ ?', url=TUTORIAL)])
            text = "<b>ʜᴇʏ {},\n\nʏᴏᴜʀ ꜰɪʟᴇ ɪꜱ ʀᴇᴀᴅʏ.\n\nᴄʟɪᴄᴋ ᴏɴ ᴛʜᴇ 'ᴅᴏᴡɴʟᴏᴀᴅ ɴᴏᴡ' ʙᴜᴛᴛᴏɴ ᴀɴᴅ ᴏᴘᴇɴ ᴛʜᴇ ʟɪɴᴋ ᴛᴏ ɢᴇᴛ ʏᴏᴜʀ ꜰɪʟᴇ.\n\n</b>"
            if PREMIUM_MODE == True:
                text += "<b>ɪꜰ ʏᴏᴜ ᴡᴀɴᴛ ᴅɪʀᴇᴄᴛ ꜰɪʟᴇꜱ ᴡɪᴛʜᴏᴜᴛ ᴏᴘᴇɴɪɴɢ ʟɪɴᴋꜱ ᴏʀ ᴡᴀᴛᴄʜɪɴɢ ᴀᴅs, ᴘʟᴇᴀꜱᴇ ʙᴜʏ ᴏᴜʀ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ.\n\nꜱᴇɴᴅ /plan ᴛᴏ ᴄʜᴇᴄᴋ ᴏᴜᴛ ᴏᴜʀ ᴘʟᴀɴꜱ.</b>"
            k = await client.send_message(chat_id=message.from_user.id, text=text.format(message.from_user.mention), reply_markup=InlineKeyboardMarkup(btn))
            from utils import delayed_delete
            delayed_delete([k], 900)
            return
            
    user = message.from_user.id
    files_ = await get_file_details(file_id)           
    if not files_:
        try:
            pre, file_id = ((base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))).decode("ascii")).split("_", 1)
            reply_markup = None
            if not await db.has_premium_access(message.from_user.id):
                if not await check_verification(client, message.from_user.id) and VERIFY in [True, "True", "true"]:
                    verify_link = await get_token(client, message.from_user.id, f"https://telegram.me/{temp.U_NAME}?start=")
                    if not verify_link:
                        await message.reply_text("<b>⚠️ ᴛᴇᴍᴘᴏʀᴀʀʏ ꜱᴇʀᴠᴇʀ ɪꜱꜱᴜᴇ\n\nᴏᴜʀ ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ ᴡᴇʙꜱɪᴛᴇ ɪꜱ ᴄᴜʀʀᴇɴᴛʟʏ ᴇxᴘᴇʀɪᴇɴᴄɪɴɢ ᴅᴏᴡɴᴛɪᴍᴇ.\n\nᴘʟᴇᴀꜱᴇ ᴛʀʏ ᴀɢᴀɪɴ ɪɴ ᴀ ʙɪᴛ.</b>")
                        return
                    btn = [[
                        InlineKeyboardButton("▲ ᴠᴇʀɪꜰʏ ▲", url=verify_link)
                    ],[
                        InlineKeyboardButton("? ʜᴏᴡ ᴛᴏ ᴠᴇʀɪꜰʏ ?", url=TUTORIAL)
                    ]]
                    text = "<b>ʜᴇʏ {},\n\nʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴠᴇʀɪꜰɪᴇᴅ ʏᴇᴛ.\n\nᴘʟᴇᴀꜱᴇ ᴄʟɪᴄᴋ ᴏɴ 'ᴠᴇʀɪꜰʏ' ᴛᴏ ɢᴇᴛ ᴜɴʟɪᴍɪᴛᴇᴅ ᴀᴄᴄᴇꜱꜱ ꜰᴏʀ 10 ᴍɪɴᴜᴛᴇs.\n\n</b>"
                    if PREMIUM_MODE == True:
                        text += "<b>ɪꜰ ʏᴏᴜ ᴡᴀɴᴛ ᴅɪʀᴇᴄᴛ ꜰɪʟᴇꜱ ᴡɪᴛʜᴏᴜᴛ ᴏᴘᴇɴɪɴɢ ʟɪɴᴋꜱ ᴏʀ ᴡᴀᴛᴄʜɪɴɢ ᴀᴅs, ᴘʟᴇᴀꜱᴇ ʙᴜʏ ᴏᴜʀ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ.\n\nꜱᴇɴᴅ /plan ᴛᴏ ᴄʜᴇᴄᴋ ᴏᴜᴛ ᴏᴜʀ ᴘʟᴀɴꜱ.</b>"
                    await message.reply_text(
                        text=text.format(message.from_user.mention),
                        reply_markup=InlineKeyboardMarkup(btn)
                    )
                    return
            msg = await client.send_cached_media(
                chat_id=message.from_user.id,
                file_id=file_id,
                reply_markup=reply_markup
            )
            filetype = msg.media
            file = getattr(msg, filetype.value)
            clean_name = remove_junk(file.file_name)
            title = clean_name
            size = get_size(file.file_size)
            f_caption = f"<code>{title}</code>"
            if CUSTOM_FILE_CAPTION:
                try:
                    f_caption = CUSTOM_FILE_CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='')
                except Exception:
                    return
            await msg.edit_caption(caption=f_caption)
            k = await msg.reply(text=f"<blockquote><b><u>❗️ ɪᴍᴘᴏʀᴛᴀɴᴛ ❗️</u>\n\nᴛʜɪꜱ ᴍᴇꜱꜱᴀɢᴇ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ ɪɴ <u>15 ᴍɪɴᴜᴛᴇꜱ</u>\n(ᴅᴜᴇ ᴛᴏ ᴄᴏᴘʏʀɪɢʜᴛ ɪꜱꜱᴜᴇꜱ)\n\nᴘʟᴇᴀꜱᴇ ꜰᴏʀᴡᴀʀᴅ ᴛʜɪꜱ ᴍᴇꜱꜱᴀɢᴇ ᴛᴏ ʏᴏᴜʀ ꜱᴀᴠᴇᴅ ᴍᴇꜱꜱᴀɢᴇꜱ ᴏʀ ᴀɴʏ ᴘʀɪᴠᴀᴛᴇ ᴄʜᴀᴛ ᴛᴏ ᴀᴠᴏɪᴅ ʟᴏꜱɪɴɢ ɪᴛ.</b></blockquote>")
            
            from utils import delayed_delete
            delayed_delete([msg, k], 900)
            return
        except Exception:
            pass
        return await message.reply('<b>ɴᴏ ꜱᴜᴄʜ ꜰɪʟᴇ ᴇxɪꜱᴛꜱ.</b>')
        
    files = files_
    clean_name = remove_junk(files["file_name"])
    title = clean_name
    size = get_size(files["file_size"])
    f_caption = files["caption"]
    if CUSTOM_FILE_CAPTION:
        try:
            f_caption = CUSTOM_FILE_CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption)
        except Exception:
            f_caption = f_caption
    if f_caption is None:
        f_caption = f"{clean_name}"
    reply_markup = None
    if not await db.has_premium_access(message.from_user.id):
        if not await check_verification(client, message.from_user.id) and VERIFY in [True, "True", "true"]:
            verify_link = await get_token(client, message.from_user.id, f"https://telegram.me/{temp.U_NAME}?start=")
            if not verify_link:
                await message.reply_text("<b>⚠️ ᴛᴇᴍᴘᴏʀᴀʀʏ ꜱᴇʀᴠᴇʀ ɪꜱꜱᴜᴇ\n\nᴏᴜʀ ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ ᴡᴇʙꜱɪᴛᴇ ɪꜱ ᴄᴜʀʀᴇɴᴛʟʏ ᴇxᴘᴇʀɪᴇɴᴄɪɴɢ ᴅᴏᴡɴᴛɪᴍᴇ.\n\nᴘʟᴇᴀꜱᴇ ᴛʀʏ ᴀɢᴀɪɴ ɪɴ ᴀ ʙɪᴛ.</b>")
                return
            btn = [[
                InlineKeyboardButton("▲ ᴠᴇʀɪꜰʏ ▲", url=verify_link)
            ],[
                InlineKeyboardButton("? ʜᴏᴡ ᴛᴏ ᴠᴇʀɪꜰʏ ?", url=TUTORIAL)
            ]]
            text = "<b>ʜᴇʏ {},\n\nʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴠᴇʀɪꜰɪᴇᴅ ʏᴇᴛ.\n\nᴘʟᴇᴀꜱᴇ ᴄʟɪᴄᴋ ᴏɴ 'ᴠᴇʀɪꜰʏ' ᴛᴏ ɢᴇᴛ ᴜɴʟɪᴍɪᴛᴇᴅ ᴀᴄᴄᴇꜱꜱ ꜰᴏʀ 10 ᴍɪɴᴜᴛᴇs.\n\n</b>"
            if PREMIUM_MODE == True:
                text += "<b>ɪꜰ ʏᴏᴜ ᴡᴀɴᴛ ᴅɪʀᴇᴄᴛ ꜰɪʟᴇꜱ ᴡɪᴛʜᴏᴜᴛ ᴏᴘᴇɴɪɴɢ ʟɪɴᴋꜱ ᴏʀ ᴡᴀᴛᴄʜɪɴɢ ᴀᴅs, ᴘʟᴇᴀꜱᴇ ʙᴜʏ ᴏᴜʀ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ.\n\nꜱᴇɴᴅ /plan ᴛᴏ ᴄʜᴇᴄᴋ ᴏᴜᴛ ᴏᴜʀ ᴘʟᴀɴꜱ.</b>"
            await message.reply_text(
                text=text.format(message.from_user.mention),
                reply_markup=InlineKeyboardMarkup(btn)
            )
            return
    msg = await client.send_cached_media(
        chat_id=message.from_user.id,
        file_id=file_id,
        caption=f_caption,
        reply_markup=reply_markup
    )
    k = await msg.reply(text=f"<blockquote><b><u>❗️ ɪᴍᴘᴏʀᴛᴀɴᴛ ❗️</u>\n\nᴛʜɪꜱ ᴍᴇꜱꜱᴀɢᴇ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ ɪɴ <u>15 ᴍɪɴᴜᴛᴇꜱ</u>\n(ᴅᴜᴇ ᴛᴏ ᴄᴏᴘʏʀɪɢʜᴛ ɪꜱꜱᴜᴇꜱ)\n\nᴘʟᴇᴀꜱᴇ ꜰᴏʀᴡᴀʀᴅ ᴛʜɪꜱ ᴍᴇꜱꜱᴀɢᴇ ᴛᴏ ʏᴏᴜʀ ꜱᴀᴠᴇᴅ ᴍᴇꜱꜱᴀɢᴇꜱ ᴏʀ ᴀɴʏ ᴘʀɪᴠᴀᴛᴇ ᴄʜᴀᴛ ᴛᴏ ᴀᴠᴏɪᴅ ʟᴏꜱɪɴɢ ɪᴛ.</b></blockquote>")
    
    from utils import delayed_delete
    delayed_delete([msg, k], 900)
    return   

@Client.on_message(filters.command('channel') & filters.user(ADMINS))
async def channel_info(bot, message):
    text = '<b>ɪɴᴅᴇxᴇᴅ ᴄʜᴀɴɴᴇʟꜱ/ɢʀᴏᴜᴘꜱ</b>\n'
    for channel in CHANNELS:
        chat = await bot.get_chat(channel)
        if chat.username:
            text += '\n@' + chat.username
        else:
            text += '\n' + chat.title or chat.first_name

    text += f'\n\n<b>ᴛᴏᴛᴀʟ:</b> {len(CHANNELS)}'

    if len(text) < 4096:
        await message.reply(text)
    else:
        file = 'Indexed channels.txt'
        with open(file, 'w', encoding='utf-8') as f:
            f.write(text)
        await message.reply_document(file)
        os.remove(file)

@Client.on_message(filters.command('delete') & filters.user(ADMINS))
async def delete(bot, message):
    if message.reply_to_message and message.reply_to_message.media:
        reply = message.reply_to_message
        msg = await message.reply("ᴘʀᴏᴄᴇꜱꜱɪɴɢ...", quote=True)
    else:
        reply = await bot.ask(message.from_user.id, "ɴᴏᴡ, ꜱᴇɴᴅ ᴍᴇ ᴛʜᴇ ᴍᴇᴅɪᴀ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴅᴇʟᴇᴛᴇ.")
        if reply.media:
            msg = await message.reply("ᴘʀᴏᴄᴇꜱꜱɪɴɢ...", quote=True)
        else:
            await message.reply('ᴘʟᴇᴀꜱᴇ ꜱᴇɴᴅ ᴍᴇ ᴀ ᴠɪᴅᴇᴏ, ꜰɪʟᴇ, ᴏʀ ᴅᴏᴄᴜᴍᴇɴᴛ.', quote=True)
            return

    for file_type in ("document", "video", "audio"):
        media = getattr(reply, file_type, None)
        if media is not None:
            break
    else:
        await msg.edit('ᴛʜɪꜱ ɪꜱ ɴᴏᴛ ᴀ ꜱᴜᴘᴘᴏʀᴛᴇᴅ ꜰɪʟᴇ ꜰᴏʀᴍᴀᴛ.')
        return
    
    file_id = unpack_new_file_id(media.file_id)

    result = await col.delete_one({
        'file_id': file_id,
    })
    if not result.deleted_count and sec_col is not None:
        result = await sec_col.delete_one({'file_id': file_id})
    if not result.deleted_count and thi_col is not None:
        result = await thi_col.delete_one({'file_id': file_id})
    if result.deleted_count:
        await msg.edit('ꜰɪʟᴇ ʜᴀꜱ ʙᴇᴇɴ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ ꜰʀᴏᴍ ᴛʜᴇ ᴅᴀᴛᴀʙᴀꜱᴇ.')
    else:
        from database.ia_filterdb import clean_file_name
        file_name = clean_file_name(media.file_name)
    
        result = await col.delete_many({
            'file_name': file_name,
            'file_size': media.file_size
        })
        if not result.deleted_count and sec_col is not None:
            result = await sec_col.delete_many({'file_name': file_name, 'file_size': media.file_size})
        if not result.deleted_count and thi_col is not None:
            result = await thi_col.delete_many({'file_name': file_name, 'file_size': media.file_size})
        if result.deleted_count:
            await msg.edit('ꜰɪʟᴇ ʜᴀꜱ ʙᴇᴇɴ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ ꜰʀᴏᴍ ᴛʜᴇ ᴅᴀᴛᴀʙᴀꜱᴇ.')
        else:
            result = await col.delete_many({
                'file_name': media.file_name,
                'file_size': media.file_size
            })
            if not result.deleted_count and sec_col is not None:
                result = await sec_col.delete_many({'file_name': media.file_name, 'file_size': media.file_size})
            if not result.deleted_count and thi_col is not None:
                result = await thi_col.delete_many({'file_name': media.file_name, 'file_size': media.file_size})
            if result.deleted_count:
                await msg.edit('ꜰɪʟᴇ ʜᴀꜱ ʙᴇᴇɴ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ ꜰʀᴏᴍ ᴛʜᴇ ᴅᴀᴛᴀʙᴀꜱᴇ.')
            else:
                await msg.edit('ꜰɪʟᴇ ɴᴏᴛ ꜰᴏᴜɴᴅ ɪɴ ᴛʜᴇ ᴅᴀᴛᴀʙᴀꜱᴇ.')

@Client.on_message(filters.command('deleteall') & filters.user(ADMINS))
async def delete_all_index(bot, message):
    await message.reply_text(
        'ᴛʜɪꜱ ᴡɪʟʟ ᴅᴇʟᴇᴛᴇ ᴀʟʟ ɪɴᴅᴇxᴇᴅ ꜰɪʟᴇꜱ.\nᴅᴏ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴄᴏɴᴛɪɴᴜᴇ?',
        reply_markup=InlineKeyboardMarkup(
            [[
                InlineKeyboardButton(text="ʏᴇꜱ", callback_data="autofilter_delete")
            ],[
                InlineKeyboardButton(text="ᴄᴀɴᴄᴇʟ", callback_data="close_data")
            ]]
        ),
        quote=True,
    )

@Client.on_callback_query(filters.regex(r'^autofilter_delete'))
async def delete_all_index_confirm(bot, query):
    if not query.from_user or not is_admin(query.from_user.id):
        return await query.answer("ʏᴏᴜ ᴅᴏ ɴᴏᴛ ʜᴀᴠᴇ ꜱᴜꜰꜰɪᴄɪᴇɴᴛ ʀɪɢʜᴛꜱ ᴛᴏ ᴅᴏ ᴛʜɪꜱ!", show_alert=True)
    await col.drop()
    if sec_col is not None:
        await sec_col.drop()
    if thi_col is not None:
        await thi_col.drop()
    await query.answer('ᴘɪʀᴀᴄʏ ɪꜱ ᴀ ᴄʀɪᴍᴇ.')
    await query.message.edit('ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ ᴀʟʟ ɪɴᴅᴇxᴇᴅ ꜰɪʟᴇꜱ.')

@Client.on_message(filters.command('settings'))
async def settings(client, message):
    userid = message.from_user.id if message.from_user else None
    if not userid:
        return await message.reply(f"ʏᴏᴜ ᴀʀᴇ ᴀɴ ᴀɴᴏɴʏᴍᴏᴜꜱ ᴀᴅᴍɪɴ. ᴜꜱᴇ /connect {message.chat.id} ɪɴ ᴘᴍ.")
    chat_type = message.chat.type

    if chat_type == enums.ChatType.PRIVATE:
        grpid = await active_connection(str(userid))
        if grpid is not None:
            grp_id = grpid
            try:
                chat = await client.get_chat(grpid)
                title = chat.title
            except Exception:
                await message.reply_text("ᴍᴀᴋᴇ ꜱᴜʀᴇ ɪ ᴀᴍ ᴘʀᴇꜱᴇɴᴛ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ!", quote=True)
                return
        else:
            await message.reply_text("ɪ ᴀᴍ ɴᴏᴛ ᴄᴏɴɴᴇᴄᴛᴇᴅ ᴛᴏ ᴀɴʏ ɢʀᴏᴜᴘꜱ!", quote=True)
            return

    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        grp_id = message.chat.id
        title = message.chat.title

    else:
        return

    try:
        st = await client.get_chat_member(grp_id, userid)
        is_chat_admin = st.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]
    except Exception:
        is_chat_admin = False

    if not is_chat_admin and not is_admin(userid):
        return
    
    settings = await get_settings(grp_id)

    try:
        if settings['max_btn']:
            settings = await get_settings(grp_id)
    except KeyError:
        await save_group_settings(grp_id, 'max_btn', False)
        settings = await get_settings(grp_id)
    if 'no_result_msg' not in settings.keys():
        await save_group_settings(grp_id, 'no_result_msg', True)

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
                    '15 ᴍɪɴꜱ' if settings["auto_delete"] else 'ᴏꜰꜰ',
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
        btn = [[
            InlineKeyboardButton("ᴏᴘᴇɴ ʜᴇʀᴇ ↓", callback_data=f"opnsetgrp#{grp_id}"),
            InlineKeyboardButton("ᴏᴘᴇɴ ɪɴ ᴘᴍ ↑", callback_data=f"opnsetpm#{grp_id}")
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        if chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            await message.reply_text(
                text="<b>ᴅᴏ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴏᴘᴇɴ ꜱᴇᴛᴛɪɴɢꜱ ʜᴇʀᴇ?</b>",
                reply_markup=InlineKeyboardMarkup(btn),
                disable_web_page_preview=True,
                parse_mode=enums.ParseMode.HTML,
                reply_to_message_id=message.id
            )
        else:
            await message.reply_text(
                text=f"<b>ᴄʜᴀɴɢᴇ ʏᴏᴜʀ ꜱᴇᴛᴛɪɴɢꜱ ꜰᴏʀ {title} ᴀꜱ ʏᴏᴜ ᴡɪꜱʜ.</b>",
                reply_markup=reply_markup,
                disable_web_page_preview=True,
                parse_mode=enums.ParseMode.HTML,
                reply_to_message_id=message.id
            )
            
    if message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        await asyncio.sleep(60)
        try:
            await message.delete()
        except Exception:
            pass

@Client.on_message((filters.command(["request", "Request"]) | filters.regex("#request") | filters.regex("#Request")) & filters.private)
async def requests(bot, message):
    reporter = str(message.from_user.id)
    mention = message.from_user.mention
    success = False
    
    if message.reply_to_message and message.reply_to_message.text:
        content = message.reply_to_message.text
        if len(content) >= 3:
            success = True
    elif message.text:
        content = message.text
        for keyword in ["#request ", "/request ", "#Request ", "/Request ", "#request", "/request", "#Request", "/Request"]:
            if content.startswith(keyword):
                content = content.replace(keyword, "", 1)
                break
        if len(content.strip()) >= 3:
            success = True
    
    if not success:
        return await message.reply_text("<b>ʏᴏᴜ ᴍᴜꜱᴛ ᴛʏᴘᴇ ʏᴏᴜʀ ʀᴇQᴜᴇꜱᴛ (ᴍɪɴɪᴍᴜᴍ 3 ᴄʜᴀʀᴀᴄᴛᴇʀꜱ). ʀᴇQᴜᴇꜱᴛꜱ ᴄᴀɴɴᴏᴛ ʙᴇ ᴇᴍᴘᴛʏ.</b>")
    
    try:
        btn = [[
            InlineKeyboardButton('ꜱʜᴏᴡ ᴏᴘᴛɪᴏɴꜱ', callback_data=f'show_option#{reporter}')
        ]]
            
        await bot.send_message(
            chat_id=LOG_CHANNEL, 
            text=f"<b>ʀᴇᴘᴏʀᴛᴇʀ : {mention} ({reporter})\n\nᴍᴇꜱꜱᴀɢᴇ : {content.strip().replace('<', '&lt;').replace('>', '&gt;')}</b>", 
            reply_markup=InlineKeyboardMarkup(btn)
        )
        await message.reply_text("<b>ʏᴏᴜʀ ʀᴇQᴜᴇꜱᴛ ʜᴀꜱ ʙᴇᴇɴ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ꜱᴜʙᴍɪᴛᴛᴇᴅ ᴛᴏ ᴛʜᴇ ᴀᴅᴍɪɴꜱ! ᴘʟᴇᴀꜱᴇ ᴡᴀɪᴛ ꜰᴏʀ ɪᴛ ᴛᴏ ʙᴇ ᴘʀᴏᴄᴇꜱꜱᴇᴅ.</b>")
    except Exception as e:
        await message.reply_text(f"Error submitting request: {e}")
        
    if message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        await asyncio.sleep(60)
        try:
            await message.delete()
        except Exception:
            pass
    
@Client.on_message(filters.command("send") & filters.user(ADMINS))
async def send_msg(bot, message):
    if message.reply_to_message:
        target_id = message.text.split(" ", 1)[1]
        out = "ᴜꜱᴇʀꜱ ꜱᴀᴠᴇᴅ ɪɴ ᴛʜᴇ ᴅᴀᴛᴀʙᴀꜱᴇ ᴀʀᴇ:\n\n"
        success = False
        try:
            user = await bot.get_users(target_id)
            if await db.is_user_exist(user.id):
                await message.reply_to_message.copy(int(user.id))
                success = True
            else:
                success = False
            if success:
                await message.reply_text(f"<b>ʏᴏᴜʀ ᴍᴇꜱꜱᴀɢᴇ ʜᴀꜱ ʙᴇᴇɴ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ꜱᴇɴᴛ ᴛᴏ {user.mention}.</b>")
            else:
                await message.reply_text("<b>ᴛʜɪꜱ ᴜꜱᴇʀ ʜᴀꜱ ɴᴏᴛ ꜱᴛᴀʀᴛᴇᴅ ᴛʜɪꜱ ʙᴏᴛ ʏᴇᴛ!</b>")
        except Exception as e:
            await message.reply_text(f"<b>ᴇʀʀᴏʀ: {e}</b>")
    else:
        await message.reply_text("<b>ᴜꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ᴀꜱ ᴀ ʀᴇᴘʟʏ ᴛᴏ ᴀɴʏ ᴍᴇꜱꜱᴀɢᴇ ᴜꜱɪɴɢ ᴛʜᴇ ᴛᴀʀɢᴇᴛ ᴄʜᴀᴛ ɪᴅ. ꜰᴏʀ ᴇxᴀᴍᴘʟᴇ: /send userid</b>")

@Client.on_message(filters.command("deletefiles") & filters.user(ADMINS))
async def deletemultiplefiles(bot, message):
    chat_type = message.chat.type
    if chat_type != enums.ChatType.PRIVATE:
        return await message.reply_text(f"<b>ʜᴇʏ {message.from_user.mention}, ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ᴡᴏɴ'ᴛ ᴡᴏʀᴋ ɪɴ ɢʀᴏᴜᴘꜱ. ɪᴛ ᴏɴʟʏ ᴡᴏʀᴋꜱ ɪɴ ᴍʏ ᴘᴍ!</b>")
    else:
        pass
    try:
        keyword = message.text.split(" ", 1)[1]
    except Exception:
        return await message.reply_text(f"<b>ʜᴇʏ {message.from_user.mention}, ᴘʟᴇᴀꜱᴇ ɢɪᴠᴇ ᴍᴇ ᴀ ᴋᴇʏᴡᴏʀᴅ ᴀʟᴏɴɢ ᴡɪᴛʜ ᴛʜᴇ ᴄᴏᴍᴍᴀɴᴅ ᴛᴏ ᴅᴇʟᴇᴛᴇ ꜰɪʟᴇꜱ.</b>")
    safe_keyword = keyword.replace('<', '&lt;').replace('>', '&gt;')
    k = await bot.send_message(chat_id=message.chat.id, text=f"<b>ꜰᴇᴛᴄʜɪɴɢ ꜰɪʟᴇꜱ ꜰᴏʀ ʏᴏᴜʀ Qᴜᴇʀʏ '{safe_keyword}' ɪɴ ᴛʜᴇ ᴅᴀᴛᴀʙᴀꜱᴇ... ᴘʟᴇᴀꜱᴇ ᴡᴀɪᴛ...</b>")
    files, total = await get_bad_files(keyword)
    await k.delete()
    btn = [[
       InlineKeyboardButton("ʏᴇꜱ, ᴄᴏɴᴛɪɴᴜᴇ!", callback_data=f"killfilesdq#{keyword}")
    ],[
       InlineKeyboardButton("ᴄᴀɴᴄᴇʟ", callback_data="close_data")
    ]]
    await message.reply_text(
        text=f"<b>ꜰᴏᴜɴᴅ {total} ꜰɪʟᴇꜱ ꜰᴏʀ ʏᴏᴜʀ Qᴜᴇʀʏ '{safe_keyword}'!\n\nᴅᴏ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴅᴇʟᴇᴛᴇ ᴛʜᴇᴍ?</b>",
        reply_markup=InlineKeyboardMarkup(btn),
        parse_mode=enums.ParseMode.HTML
    )

@Client.on_message(filters.command("restart") & filters.user(ADMINS))
async def stop_button(bot, message):
    msg = await bot.send_message(text="<b>ᴘʀᴏᴄᴇꜱꜱᴇꜱ ꜱᴛᴏᴘᴘᴇᴅ. ʙᴏᴛ ɪꜱ ʀᴇꜱᴛᴀʀᴛɪɴɢ...</b>", chat_id=message.chat.id)       
    await asyncio.sleep(3)
    await msg.edit("<b>ʙᴏᴛ ɪꜱ ʀᴇꜱᴛᴀʀᴛᴇᴅ. ʏᴏᴜ ᴄᴀɴ ɴᴏᴡ ᴜꜱᴇ ᴍᴇ.</b>")
    sys.exit(0)

@Client.on_message(filters.command("add_premium"))
async def give_premium_cmd_handler(client, message):
    if PREMIUM_MODE == False:
        return 
    if not message.from_user or not is_admin(message.from_user.id):
        try:
            await message.delete()
        except Exception:
            pass
        return
    if len(message.command) == 3:
        try:
            user_id = int(message.command[1])
        except ValueError:
            return await message.reply_text("ɪɴᴠᴀʟɪᴅ ᴜꜱᴇʀ ɪᴅ. ᴍᴜꜱᴛ ʙᴇ ᴀɴ ɪɴᴛᴇɢᴇʀ.")
        time_str = message.command[2]        
        seconds = await get_seconds(time_str)
        if seconds and seconds > 0:
            current_expiry = await db.get_expiry_time(user_id)
            now = datetime.datetime.now()
            base_time = current_expiry if (current_expiry and isinstance(current_expiry, datetime.datetime) and current_expiry > now) else now
            expiry_time = base_time + datetime.timedelta(seconds=seconds)
            user_data = {"id": user_id, "expiry_time": expiry_time} 
            await db.update_user(user_data)
            await message.reply_text(f"ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ ʜᴀꜱ ʙᴇᴇɴ ᴀᴅᴅᴇᴅ ᴛᴏ ᴛʜᴇ ᴜꜱᴇʀ (ɪᴅ: {user_id}).")            
            display_time = time_str.replace("day", " Days").replace("month", " Months").replace("year", " Years")
            try:
                await client.send_message(
                    chat_id=user_id,
                    text=f"""<b><u>🎉 ʏᴏᴜʀ sᴜʙsᴄʀɪᴘᴛɪᴏɴ ɪꜱ ɴᴏᴡ ᴀᴄᴛɪᴠᴇ!</u></b>\n\nʏᴏᴜʀ ᴀᴄᴄᴏᴜɴᴛ ɪꜱ ᴜᴘɢʀᴀᴅᴇᴅ ꜰᴏʀ <b><u>{display_time}</u></b>. ʏᴏᴜ ɴᴏᴡ ʜᴀᴠᴇ ᴜɴʟɪᴍɪᴛᴇᴅ, ɪɴꜱᴛᴀɴᴛ, ᴀɴᴅ ᴀᴅ-ꜰʀᴇᴇ ᴀᴄᴄᴇꜱꜱ ᴛᴏ ᴀʟʟ ᴏᴜʀ ʙᴏᴛꜱ!\n\n🍿 ᴍᴏᴠɪᴇꜱ: @TIC_Movies_Bot\n📺 ᴡᴇʙ ꜱᴇʀɪᴇꜱ, ᴀɴɪᴍᴇ & ᴋᴅʀᴀᴍᴀ: @TIC_Web_Series_Anime_Bot\n🔥 ʟᴀᴛᴇꜱᴛ ᴍᴏᴠɪᴇꜱ: @TIC_Latest_Movies_Bot\n\n💡 ᴛʏᴘᴇ /myplan ᴛᴏ ᴄʜᴇᴄᴋ ʏᴏᴜʀ ꜱᴛᴀᴛᴜꜱ.\n\n<blockquote><b>🍿🎬 ᴇɴᴊᴏʏ & ʜᴀᴘᴘʏ ʙɪɴɢɪɴɢ!</b></blockquote>""",
                    parse_mode=enums.ParseMode.HTML
                )
            except Exception:
                pass
        else:
            await message.reply_text("ɪɴᴠᴀʟɪᴅ ᴛɪᴍᴇ ꜰᴏʀᴍᴀᴛ. ᴘʟᴇᴀꜱᴇ ᴜꜱᴇ '1day', '1hour', '1min', '1month', ᴏʀ '1year'.")
    else:
        await message.reply_text("<b>ᴜꜱᴀɢᴇ: /add_premium user_id time \n\nᴇxᴀᴍᴘʟᴇ: /add_premium 1252789 10day \n\n(ᴇ.ɢ. '1day', '1hour', '1min', '1month', ᴏʀ '1year')</b>")
        
@Client.on_message(filters.command("remove_premium"))
async def remove_premium_cmd_handler(client, message):
    if PREMIUM_MODE == False:
        return 
    if not message.from_user or not is_admin(message.from_user.id):
        try:
            await message.delete()
        except Exception:
            pass
        return
    if len(message.command) == 2:
        try:
            target_id = int(message.command[1]) 
        except ValueError:
            return await message.reply_text("ɪɴᴠᴀʟɪᴅ ᴜꜱᴇʀ ɪᴅ. ᴍᴜꜱᴛ ʙᴇ ᴀɴ ɪɴᴛᴇɢᴇʀ.")
        user_data = {"id": target_id, "expiry_time": None}
        await db.update_user(user_data) 
        await message.reply_text(f"ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ ʜᴀꜱ ʙᴇᴇɴ ʀᴇᴍᴏᴠᴇᴅ ꜰᴏʀ ᴜꜱᴇʀ {target_id}.")
        try:
            await client.send_message(
                chat_id=target_id,
                text="<b>ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ ʜᴀꜱ ʙᴇᴇɴ ʀᴇᴍᴏᴠᴇᴅ ʙʏ ᴀᴅᴍɪɴꜱ.\n\nᴄᴏɴᴛᴀᴄᴛ ᴜs ɪꜰ ᴛʜɪꜱ ɪꜱ ᴀ ᴍɪꜱᴛᴀᴋᴇ.\n</b>",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ᴄᴏɴᴛᴀᴄᴛ ꜱᴜᴘᴘᴏʀᴛ", url=SUPPORT_LINK)]])
            )
        except Exception:
            pass
    else:
        await message.reply_text("ᴜꜱᴀɢᴇ: /remove_premium user_id")
        
@Client.on_message(filters.command("plan") & filters.private)
async def plans_cmd_handler(client, message): 
    if PREMIUM_MODE == False:
        return 
    btn = [            
        [InlineKeyboardButton("ᴄᴏɴᴛᴀᴄᴛ ꜱᴜᴘᴘᴏʀᴛ", url=SUPPORT_LINK)],
        [InlineKeyboardButton("⤬ ᴄʟᴏꜱᴇ ⤬", callback_data="close_data")]
    ]
    reply_markup = InlineKeyboardMarkup(btn)
    msg = await message.reply_text(
        text=PAYMENT_TEXT,
        reply_markup=reply_markup,
        parse_mode=enums.ParseMode.HTML
    )
        
@Client.on_message(filters.command("myplan") & filters.private)
async def check_plans_cmd(client, message):
    if PREMIUM_MODE == False:
        return 
    if not message.from_user:
        return
    user_id = message.from_user.id
    
    if await db.has_premium_access(user_id):         
        remaining_time = await db.check_remaining_uasge(user_id)
        expiry_time = await db.get_expiry_time(user_id)
        
        if remaining_time and expiry_time:
            clean_remaining = str(remaining_time).split('.')[0]
            clean_expiry = str(expiry_time).split('.')[0]
            
            text = f"<b>🌟 ʏᴏᴜʀ ᴘʟᴀɴ ᴅᴇᴛᴀɪʟꜱ:</b>\n\n<b>⏳ ʀᴇᴍᴀɪɴɪɴɢ ᴛɪᴍᴇ:</b> <code>{clean_remaining}</code>\n\n<b>📅 ᴇxᴘɪʀʏ ᴛɪᴍᴇ:</b> <code>{clean_expiry}</code>"
            btn = [[InlineKeyboardButton("⤬ ᴄʟᴏꜱᴇ ⤬", callback_data="close_data")]]
            
            msg = await message.reply_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(btn),
                parse_mode=enums.ParseMode.HTML
            )
        else:
            btn = [
                [InlineKeyboardButton("ʙᴜʏ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ", callback_data="buy_premium_myplan")],
                [InlineKeyboardButton("⤬ ᴄʟᴏꜱᴇ ⤬", callback_data="close_data")]
            ]
            msg = await message.reply_text(
                text="<b>ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴀɴʏ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ.\n\nᴄʜᴇᴄᴋ ᴏᴜᴛ ᴏᴜʀ ᴘʟᴀɴꜱ /plan.</b>", 
                reply_markup=InlineKeyboardMarkup(btn),
                parse_mode=enums.ParseMode.HTML
            )
    else:
        btn = [
            [InlineKeyboardButton("ʙᴜʏ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ", callback_data="buy_premium_myplan")],
            [InlineKeyboardButton("⤬ ᴄʟᴏꜱᴇ ⤬", callback_data="close_data")]
        ]
        reply_markup = InlineKeyboardMarkup(btn)
        
        msg = await message.reply_text(
            text="<b>ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴀɴʏ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ.\n\nᴄʜᴇᴄᴋ ᴏᴜᴛ ᴏᴜʀ ᴘʟᴀɴꜱ /plan.</b>", 
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )

@Client.on_message(filters.command("stats") & filters.user(ADMINS))
async def get_bot_stats(bot, message):
    msg = await message.reply_text("<b>ꜰᴇᴛᴄʜɪɴɢ ʟɪᴠᴇ ꜱᴛᴀᴛɪꜱᴛɪᴄꜱ...</b>")
    
    total_users = await db.total_users_count()
    totl_chats = await db.total_chat_count()
    
    filesp = await col.count_documents({}) if col is not None else 0
    totalsec = await sec_col.count_documents({}) if sec_col is not None else 0
    totalthi = await thi_col.count_documents({}) if thi_col is not None else 0
    total_files = filesp + totalsec + totalthi
    
    stats1 = await fir_db.command('dbStats')
    used_db1 = (stats1['dataSize']/(1024*1024))+(stats1['indexSize']/(1024*1024))
    free_db1 = 512-used_db1
    
    if sec_db is not None:
        stats2 = await sec_db.command('dbStats')
        used_db2 = (stats2['dataSize']/(1024*1024))+(stats2['indexSize']/(1024*1024))
        free_db2 = 512-used_db2
    else:
        used_db2, free_db2 = 0, 0
        
    if thi_db is not None:
        stats3 = await thi_db.command('dbStats')
        used_db3 = (stats3['dataSize']/(1024*1024))+(stats3['indexSize']/(1024*1024))
        free_db3 = 512-used_db3
    else:
        used_db3, free_db3 = 0, 0

    stats_text = (
        "<b><u>ᴅᴀᴛᴀʙᴀꜱᴇ ꜱᴛᴀᴛɪꜱᴛɪᴄꜱ</u></b>\n\n"
        f"<b>★ ᴛᴏᴛᴀʟ ꜰɪʟᴇꜱ:</b> <code>{total_files}</code>\n"
        f"<b>★ ᴛᴏᴛᴀʟ ᴜꜱᴇʀꜱ:</b> <code>{total_users}</code>\n"
        f"<b>★ ᴛᴏᴛᴀʟ ɢʀᴏᴜᴘꜱ:</b> <code>{totl_chats}</code>\n\n"
        "<b>• ꜰɪʀꜱᴛ ᴅᴀᴛᴀʙᴀꜱᴇ:</b>\n"
        f"★ ꜰɪʟᴇꜱ: <code>{filesp}</code>\n"
        f"★ ᴜꜱᴇᴅ ꜱᴛᴏʀᴀɢᴇ: <code>{round(used_db1, 2)} MB</code>\n"
        f"★ ꜰʀᴇᴇ ꜱᴛᴏʀᴀɢᴇ: <code>{round(free_db1, 2)} MB</code>\n\n"
        "<b>• ꜱᴇᴄᴏɴᴅ ᴅᴀᴛᴀʙᴀꜱᴇ:</b>\n"
        f"★ ꜰɪʟᴇꜱ: <code>{totalsec}</code>\n"
        f"★ ᴜꜱᴇᴅ ꜱᴛᴏʀᴀɢᴇ: <code>{round(used_db2, 2)} MB</code>\n"
        f"★ ꜰʀᴇᴇ ꜱᴛᴏʀᴀɢᴇ: <code>{round(free_db2, 2)} MB</code>\n\n"
        "<b>• ᴛʜɪʀᴅ ᴅᴀᴛᴀʙᴀꜱᴇ:</b>\n"
        f"★ ꜰɪʟᴇꜱ: <code>{totalthi}</code>\n"
        f"★ ᴜꜱᴇᴅ ꜱᴛᴏʀᴀɢᴇ: <code>{round(used_db3, 2)} MB</code>\n"
        f"★ ꜰʀᴇᴇ ꜱᴛᴏʀᴀɢᴇ: <code>{round(free_db3, 2)} MB</code>"
    )
    
    try:
        await msg.edit_text(stats_text)
    except MessageNotModified:
        pass

@Client.on_message(filters.command("ban") & filters.user(ADMINS))
async def ban_a_user(bot, message):
    if len(message.command) < 2:
        return await message.reply("ᴘʟᴇᴀꜱᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴜꜱᴇʀ ɪᴅ.")
    user_id = int(message.command[1])
    await db.ban_user(user_id, "Banned by Admin")
    if user_id not in temp.BANNED_USERS:
        temp.BANNED_USERS.append(user_id)
    await message.reply(f"ᴜꜱᴇʀ {user_id} ʜᴀꜱ ʙᴇᴇɴ ʙᴀɴɴᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ.")

@Client.on_message(filters.command("unban") & filters.user(ADMINS))
async def unban_a_user(bot, message):
    if len(message.command) < 2:
        return await message.reply("ᴘʟᴇᴀꜱᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴜꜱᴇʀ ɪᴅ.")
    user_id = int(message.command[1])
    await db.remove_ban(user_id)
    if user_id in temp.BANNED_USERS:
        temp.BANNED_USERS.remove(user_id)
    await message.reply(f"ᴜꜱᴇʀ {user_id} ʜᴀꜱ ʙᴇᴇɴ ᴜɴʙᴀɴɴᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ.")

@Client.on_message(filters.command("disable") & filters.user(ADMINS))
async def disable_a_chat(bot, message):
    if len(message.command) < 2:
        return await message.reply("ᴘʟᴇᴀꜱᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴄʜᴀᴛ ɪᴅ.")
    chat_id = int(message.command[1])
    await db.disable_chat(chat_id, "Disabled by Admin")
    if chat_id not in temp.BANNED_CHATS:
        temp.BANNED_CHATS.append(chat_id)
    await message.reply(f"ᴄʜᴀᴛ {chat_id} ʜᴀꜱ ʙᴇᴇɴ ᴅɪꜱᴀʙʟᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ.")

@Client.on_message(filters.command("enable") & filters.user(ADMINS))
async def enable_a_chat(bot, message):
    if len(message.command) < 2:
        return await message.reply("ᴘʟᴇᴀꜱᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴄʜᴀᴛ ɪᴅ.")
    chat_id = int(message.command[1])
    await db.re_enable_chat(chat_id)
    if chat_id in temp.BANNED_CHATS:
        temp.BANNED_CHATS.remove(chat_id)
    await message.reply(f"ᴄʜᴀᴛ {chat_id} ʜᴀꜱ ʙᴇᴇɴ ᴇɴᴀʙʟᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ.")

@Client.on_message(filters.command("leave") & filters.user(ADMINS))
async def leave_a_chat(bot, message):
    if len(message.command) < 2:
        return await message.reply("ᴘʟᴇᴀꜱᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴄʜᴀᴛ ɪᴅ.")
    chat_id = int(message.command[1])
    try:
        await bot.leave_chat(chat_id)
        await message.reply(f"ʟᴇꜰᴛ ᴄʜᴀᴛ {chat_id} ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ.")
    except Exception as e:
        await message.reply(f"ᴇʀʀᴏʀ: {e}")

@Client.on_message(filters.command("users") & filters.user(ADMINS))
async def list_users(bot, message):
    total_users = await db.total_users_count()
    await message.reply(f"ᴛᴏᴛᴀʟ ᴜꜱᴇʀꜱ ɪɴ ᴅᴀᴛᴀʙᴀꜱᴇ: {total_users}")

@Client.on_message(filters.command("chats") & filters.user(ADMINS))
async def list_chats(bot, message):
    total_chats = await db.total_chat_count()
    await message.reply(f"ᴛᴏᴛᴀʟ ᴄʜᴀᴛꜱ ɪɴ ᴅᴀᴛᴀʙᴀꜱᴇ: {total_chats}")

@Client.on_message(filters.command("trending"))
async def trending(bot, message):
    trending_data = await get_trending_searches(limit=10)
    if not trending_data:
        return await message.reply_text("<b>ɴᴏ ᴛʀᴇɴᴅɪɴɢ ᴜᴘʟᴏᴀᴅꜱ ʀᴇᴄᴏʀᴅᴇᴅ ʏᴇᴛ!</b>")

    text = "<b>🔥 <u>ᴛʀᴇɴᴅɪɴɢ</u> 🔥</b>\n\n"
    for i, item in enumerate(trending_data, 1):
        query_title = item['query'].title()
        count = item['count']
        text += f"<b>{i}.</b> <code>{query_title}</code> — <i>{count} searches</i>\n"

    keyboard = [[InlineKeyboardButton("⤬ ᴄʟᴏꜱᴇ ⤬", callback_data="close_data")]]

    sent_message = await message.reply_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        disable_web_page_preview=True
    )
    
    if message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        await asyncio.sleep(60)
        try:
            await sent_message.delete()
            await message.delete()
        except Exception:
            pass

@Client.on_message(filters.command("recent") & filters.user(ADMINS))
async def recent_uploads(client, message):
    HEADER_TEXT = "🔥 <u>ᴜᴘʟᴏᴀᴅᴇᴅ ᴍᴏᴠɪᴇꜱ</u> 🔥"

    try:
        limit = 100
        if len(message.command) > 1:
            limit = int(message.command[1])
            
        processing_msg = await message.reply(f"sᴄʀᴜʙʙɪɴɢ ᴛʜᴇ ʟᴀsᴛ {limit} ғɪʟᴇs ғʀᴏᴍ ᴅᴀᴛᴀʙᴀsᴇ")
        
        recent_files = col.find({}).sort('$natural', -1).limit(limit)
        
        unique_titles = []
        seen = set()
        
        async for file in recent_files:
            name = file.get('file_name', '')
            clean_name = re.sub(r"(_|\.)", " ", name)
            
            # 1. SERIES & ANIME LOGIC
            series_match = re.search(r"(?i)(.*?)\s*S(\d{1,2})(?:E\d{1,2})?\b", clean_name)
            if series_match:
                base_title = series_match.group(1).strip()
                season_num = series_match.group(2).zfill(2)
                raw_string = f"{base_title} S{season_num}"
                slug = make_search_slug(raw_string)
                safe_raw = raw_string.replace('<', '&lt;').replace('>', '&gt;')
                formatted_string = f"▪️ <a href='https://t.me/{temp.U_NAME}?start={slug}'>{safe_raw}</a>"
            
            # 2. MOVIE LOGIC
            else:
                movie_match = re.search(r"(.*?)\s*\(\d{4}\)", clean_name)
                if movie_match:
                    base_title = movie_match.group(1).strip()
                else:
                    base_title = re.split(r"(?i)(1080p|720p|576p|540p|480p|360p|PreDvd|WEB-DL|WEBRip|HDTVRip|HDRip|BluRay|x264|x265|HEVC|HQ|Audio|ESub)", clean_name)[0].strip()
                    base_title = re.sub(r"\s*(19|20)\d{2}$", "", base_title).strip()
                
                lang_bracket = re.search(r"\[(.*?)\]", name)
                if lang_bracket:
                    languages = f"[{lang_bracket.group(1)}]"
                else:
                    langs_found = re.findall(r"(?i)\b(Hindi|Tamil|Telugu|Malayalam|Kannada|English|Spanish|Punjabi|Bengali|Korean|Chinese|Japanese|French|German|Hin|Tam|Tel|Mal|Kan|Eng|Spa|Pun|Ben|Kor|Chi|Chin|Jap|Fre|Ger)\b", clean_name)
                    if langs_found:
                        langs_found = list(dict.fromkeys(l.capitalize() for l in langs_found))
                        languages = f"[{' '.join(langs_found)}]"
                    else:
                        languages = ""
                        
                raw_string = f"{base_title} {languages}".strip()
                slug = make_search_slug(base_title)
                safe_base = base_title.replace('<', '&lt;').replace('>', '&gt;')
                formatted_string = f"▪️ <a href='https://t.me/{temp.U_NAME}?start={slug}'>{safe_base}</a> {languages}".strip()

            if raw_string and raw_string.lower() not in seen:
                seen.add(raw_string.lower())
                unique_titles.append(formatted_string)

        if not unique_titles:
            return await processing_msg.edit("No files found in the requested range!")

        # Format final text using the universal template
        final_text = f"<b>{HEADER_TEXT}</b>\n\n"
        final_text += "<blockquote><b>👇 ᴊᴜsᴛ ᴛᴀᴘ ᴏɴ ᴀɴʏ ᴛɪᴛʟᴇ ʙᴇʟᴏᴡ ᴀɴᴅ ɢᴇᴛ ʏᴏᴜʀ ꜰɪʟᴇs ɪɴsᴛᴀɴᴛʟʏ!</b></blockquote>\n\n"
        
        for title in unique_titles:
            # 4096-Character Limit Safeguard
            if len(final_text) + len(title) + 150 > 4000:
                break
            # Added an extra \n here to create the empty line between titles
            final_text += f"{title}\n\n"
            
        # Removed the \n from the start of this line so the spacing stays perfectly balanced
        final_text += "<blockquote><b>🍿🎬 ɢʀᴀʙ ʏᴏᴜʀ ᴘᴏᴘᴄᴏʀɴ & ʜᴀᴘᴘʏ ʙɪɴɢɪɴɢ!</b></blockquote>"

        await processing_msg.edit_text(
            text=final_text, 
            disable_web_page_preview=True
        )
        
    except Exception as e:
        await message.reply(f"Error during extraction: {e}")

@Client.on_message(filters.command("premium_list") & filters.user(ADMINS))
async def premium_users_list(client, message):
    msg = await message.reply_text("<b>ꜰᴇᴛᴄʜɪɴɢ ᴘʀᴇᴍɪᴜᴍ ᴜꜱᴇʀꜱ...</b>")
    
    count = await db.users.count_documents({"expiry_time": {"$gt": datetime.datetime.now()}})
    
    if count == 0:
        return await msg.edit_text("<b>ᴛʜᴇʀᴇ ᴀʀᴇ ɴᴏ ᴀᴄᴛɪᴠᴇ sᴜʙsᴄʀɪᴘᴛɪᴏɴ ᴜꜱᴇʀꜱ ᴀᴛ ᴛʜᴇ ᴍᴏᴍᴇɴᴛ.</b>")
    
    premium_users = db.users.find({"expiry_time": {"$gt": datetime.datetime.now()}}).sort("expiry_time", 1)
    text = f"<b>🌟 <u>ᴀᴄᴛɪᴠᴇ sᴜʙsᴄʀɪᴘᴛɪᴏɴ ᴜꜱᴇʀꜱ</u></b>\n\n<b>ᴛᴏᴛᴀʟ ᴘʀᴇᴍɪᴜᴍ ᴜꜱᴇʀꜱ: {count}</b>\n\n"
    
    i = 0
    async for user in premium_users:
        i += 1
        user_id = user.get('id', 'Unknown')
        name = user.get('name', 'Unknown')
        exp_val = user.get('expiry_time')
        expiry = str(exp_val).split('.')[0] if exp_val else "Unknown"
        # Username is now wrapped in a clickable profile link:
        text += f"<b>{i}. ᴜsᴇʀɴᴀᴍᴇ: <a href='tg://user?id={user_id}'>{name}</a></b>\n<b>ɪᴅ:</b> <code>{user_id}</code>\n<b>ᴇxᴘɪʀᴇꜱ:</b> <code>{expiry}</code>\n\n"
        
    if True:
        
        # Telegram has a 4096 character limit per message, handle if list is too long
        if len(text) > 4000:
            with open("premium_users.txt", "w", encoding="utf-8") as f:
                f.write(text.replace("<b>", "").replace("</b>", "").replace("<code>", "").replace("</code>", "").replace("🌟", "").replace("<u>", "").replace("</u>", ""))
            await message.reply_document("premium_users.txt", caption="<b>🌟 sᴜʙsᴄʀɪᴘᴛɪᴏɴ ᴜꜱᴇʀꜱ ʟɪꜱᴛ</b>")
            try:
                os.remove("premium_users.txt")
            except Exception:
                pass
            await msg.delete()
        else:
            await msg.edit_text(text)
