import os, logging, random, uuid, asyncio, time, datetime, re, sys, base64, html
from Script import script
from pyrogram import Client, filters, enums
from pyrogram.errors import ChatAdminRequired, FloodWait, MessageNotModified
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.ia_filterdb import col, db as fir_db, get_file_details, unpack_new_file_id, get_bad_files
from database.users_chats_db import db
from info import (SUPPORT_LINK, CHANNELS, ADMINS, is_admin, SHORTLINK_MODE, AUTH_CHANNEL, AUTH_GROUP, PAYMENT_TEXT, LOG_CHANNEL, PICS, CUSTOM_FILE_CAPTION, CHNL_LNK, GRP_LNK, PREMIUM_MODE, MAX_B_TN, SHORTLINK_API, SHORTLINK_URL, TUTORIAL, REQ_TO_JOIN)
from utils import (remove_junk, get_settings, pub_is_subscribed, get_size, is_subscribed, save_group_settings, temp, get_shortlink, get_seconds, get_ist_now, IST)

logger = logging.getLogger(__name__)

BATCH_FILES = {}

DOWNTIME_TEXT = (
    "<b>⚠️ ᴛᴇᴍᴘᴏʀᴀʀʏ ꜱᴇʀᴠᴇʀ ɪꜱꜱᴜᴇ\n\n"
    "ᴏᴜʀ ʟɪɴᴋ-ɢᴇɴᴇʀᴀᴛɪɴɢ ᴡᴇʙsɪᴛᴇ ɪꜱ ᴄᴜʀʀᴇɴᴛʟʏ ᴇxᴘᴇʀɪᴇɴᴄɪɴɢ ᴅᴏᴡɴᴛɪᴍᴇ.\n\n"
    "ᴘʟᴇᴀꜱᴇ ᴛʀʏ ʀᴇǫᴜᴇꜱᴛɪɴɢ ᴛʜᴇ ꜰɪʟᴇ ᴀɢᴀɪɴ ɪɴ ᴀ ʙɪᴛ.\n\n"
    "ᴡᴀɴᴛ ᴛᴏ ꜱᴋɪᴘ ᴀʟʟ ʟɪɴᴋꜱ? ɢᴇᴛ ɪɴꜱᴛᴀɴᴛ, ᴀᴅ-ꜰʀᴇᴇ ꜰɪʟᴇꜱ ᴠɪᴀ ᴏᴜʀ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ.</b>"
)
DOWNTIME_BUTTONS = InlineKeyboardMarkup([
    [InlineKeyboardButton("★ ʙᴜʏ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ ★", callback_data="buy_premium")]
])

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
        try:
            await message.reply_text(
                text=f"<b>🎉 ᴛʜᴀɴᴋ ʏᴏᴜ ꜰᴏʀ ᴀᴅᴅɪɴɢ ᴍᴇ ɪɴ {html.escape(message.chat.title or '')}!</b>",
                reply_markup=reply_markup
            )
        except Exception:
            pass


@Client.on_message(filters.command("start") & filters.incoming)
async def start(client, message):
    if not message.from_user:
        return
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
            disable_web_page_preview=True,
            quote=False
        )
        
        if not await db.get_chat(message.chat.id):
            try:
                total = await client.get_chat_members_count(message.chat.id)
            except Exception:
                total = 0
            await client.send_message(LOG_CHANNEL, script.LOG_TEXT_G.format(html.escape(message.chat.title or ""), message.chat.id, total, "ᴜɴᴋɴᴏᴡɴ"))       
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
    
    if (AUTH_CHANNEL or AUTH_GROUP) and not await is_subscribed(client, message):
        try:
            in_channel = True
            in_group = True
            if AUTH_CHANNEL:
                try:
                    member = await client.get_chat_member(AUTH_CHANNEL, message.from_user.id)
                    if member.status == enums.ChatMemberStatus.BANNED:
                        in_channel = False
                except Exception:
                    in_channel = False
            
            if AUTH_GROUP:
                if REQ_TO_JOIN and await db.has_req_group(message.from_user.id):
                    pass
                else:
                    try:
                        member = await client.get_chat_member(AUTH_GROUP, message.from_user.id)
                        if member.status == enums.ChatMemberStatus.BANNED:
                            in_group = False
                    except Exception:
                        in_group = False
            btn = []
            if AUTH_CHANNEL and not in_channel:
                chat = await client.get_chat(int(AUTH_CHANNEL))
                invite_link = chat.invite_link or (await client.create_chat_invite_link(int(AUTH_CHANNEL))).invite_link
                btn.append([InlineKeyboardButton("✪ ᴊᴏɪɴ ᴏᴜʀ ᴄʜᴀɴɴᴇʟ ✪", url=invite_link)])
            
            if AUTH_GROUP and not in_group:
                chat_grp = await client.get_chat(int(AUTH_GROUP))
                invite_link_grp = chat_grp.invite_link or (await client.create_chat_invite_link(int(AUTH_GROUP))).invite_link
                btn.append([InlineKeyboardButton("✪ ᴊᴏɪɴ ᴏᴜʀ ɢʀᴏᴜᴘ ✪", url=invite_link_grp)])
        except Exception as e:
            print(e)
            return
        try:
            if len(message.command) > 1 and message.command[1] != "subscribe":
                try:
                    kk, file_id = message.command[1].split("_", 1)
                    btn.append([InlineKeyboardButton("↻ ᴛʀʏ ᴀɢᴀɪɴ ↻", callback_data=f"checksub#{kk}#{file_id}")])
                except (IndexError, ValueError):
                    btn.append([InlineKeyboardButton("↻ ᴛʀʏ ᴀɢᴀɪɴ ↻", url=f"https://t.me/{temp.U_NAME}?start={message.command[1]}")])
            
            text = "<b>⚠️ ʏᴏᴜ ʜᴀᴠᴇɴ'ᴛ ᴊᴏɪɴᴇᴅ ᴏᴜʀ ᴄᴏᴍᴍᴜɴɪᴛʏ ʏᴇᴛ.\n\n📢 ᴘʟᴇᴀꜱᴇ ᴊᴏɪɴ ᴜꜱ ꜰɪʀꜱᴛ, ᴛʜᴇɴ ᴛʀʏ ᴀɢᴀɪɴ.</b>"
            await client.send_message(
                chat_id=message.from_user.id,
                text=text,
                reply_markup=InlineKeyboardMarkup(btn),
                parse_mode=enums.ParseMode.HTML
            )
            return
        except Exception as e:
            print(e)
            return await message.reply_text("<b>❌ ꜱᴏᴍᴇᴛʜɪɴɢ ᴡᴇɴᴛ ᴡʀᴏɴɢ ᴡɪᴛʜ ᴛʜᴇ ꜰᴏʀᴄᴇ-ꜱᴜʙꜱᴄʀɪʙᴇ ꜰᴇᴀᴛᴜʀᴇ.</b>")
            
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
    is_token_verified = False
    if data.startswith("t_"):
        token = data.split("_", 1)[1]
        t = await db.get_verify_token(token)
        if not t or t.get("used"):
            return await message.reply_text("<b>⚠️ ᴛʜɪꜱ ʟɪɴᴋ ʜᴀꜱ ᴇxᴘɪʀᴇᴅ ᴏʀ ᴀʟʀᴇᴀᴅʏ ʙᴇᴇɴ ᴜꜱᴇᴅ!\n\nᴘʟᴇᴀꜱᴇ ɢᴇɴᴇʀᴀᴛᴇ ᴀ ɴᴇᴡ ʟɪɴᴋ ꜰʀᴏᴍ ᴛʜᴇ ʙᴏᴛ.</b>")
        if str(t.get("user_id")) != str(message.from_user.id):
            return await message.reply_text("<b>⚠️ ᴛʜɪꜱ ʟɪɴᴋ ᴅᴏᴇꜱ ɴᴏᴛ ʙᴇʟᴏɴɢ ᴛᴏ ʏᴏᴜ!</b>")
        await db.update_verify_token(token, True)
        data = t.get("file_data")
        is_token_verified = True
        
    
    # --- NEW SEARCH TRIGGER BLOCK ---
    if data.startswith("getsrc-") or data.startswith("b64-"):
        pm_search_enabled = await db.get_pm_search_status()
        is_premium = await db.has_premium_access(message.from_user.id)
        if not pm_search_enabled and not is_premium:
            btn = [
                [InlineKeyboardButton("✪ ᴊᴏɪɴ ᴏᴜʀ ɢʀᴏᴜᴘ ✪", url=GRP_LNK)],
                [InlineKeyboardButton("★ ʙᴜʏ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ ★", callback_data="buy_premium")]
            ]
            return await message.reply_text(
                "<b>🚫 ᴘᴍ ꜱᴇᴀʀᴄʜ ɪꜱ ᴄᴜʀʀᴇɴᴛʟʏ ᴅɪꜱᴀʙʟᴇᴅ ғᴏʀ ɴᴏʀᴍᴀʟ ᴜꜱᴇʀꜱ.\n\nᴘʟᴇᴀꜱᴇ ᴊᴏɪɴ ᴏᴜʀ ɢʀᴏᴜᴘ ᴛᴏ ꜱᴇᴀʀᴄʜ ғᴏʀ ᴍᴏᴠɪᴇꜱ, ᴡᴇʙ sᴇʀɪᴇs & ᴀɴɪᴍᴇ ᴏʀ ɢᴇᴛ ᴏᴜʀ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ ᴛᴏ ꜱᴇᴀʀᴄʜ ᴅɪʀᴇᴄᴛʟʏ ɪɴ ʙᴏᴛ ᴘᴍ!</b>",
                reply_markup=InlineKeyboardMarkup(btn),
                parse_mode=enums.ParseMode.HTML
            )

        if data.startswith("getsrc-"):
            search_query = data.replace("getsrc-", "", 1).replace("-", " ").strip()
        else:
            try:
                import base64
                encoded = data.replace("b64-", "", 1)
                encoded += "=" * ((4 - len(encoded) % 4) % 4)
                search_query = base64.urlsafe_b64decode(encoded).decode()
            except Exception:
                return await message.reply_text("<b>⚠️ ɪɴᴠᴀʟɪᴅ ᴏʀ ᴇxᴘɪʀᴇᴅ ʟɪɴᴋ.\n\nᴘʟᴇᴀꜱᴇ ꜱᴇᴀʀᴄʜ ꜰᴏʀ ᴛʜᴇ ꜰɪʟᴇ ᴀɢᴀɪɴ ᴛᴏ ɢᴇᴛ ᴀ ꜰʀᴇꜱʜ ʟɪɴᴋ.</b>")

        message.text = search_query  # Overwrite text to bypass the "/" command block in auto_filter
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

    if data.startswith("getlink_"):
        user = message.from_user.id
        pre = 'file'
        try:
            _, file_id = data.split('_', 1)
        except Exception:
            return
        
        if SHORTLINK_MODE and not await db.has_premium_access(user):
            token = str(uuid.uuid4())
            await db.create_verify_token(user, token, file_data=f"{pre}_{file_id}")
            g = await get_shortlink(f"https://telegram.me/{temp.U_NAME}?start=t_{token}")
            if not g:
                return await message.reply_text(DOWNTIME_TEXT, reply_markup=DOWNTIME_BUTTONS)
            btn = [[InlineKeyboardButton('▼ ᴅᴏᴡɴʟᴏᴀᴅ ɴᴏᴡ ▼', url=g)]]
            if TUTORIAL:
                btn.append([InlineKeyboardButton('? ʜᴏᴡ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ ?', url=TUTORIAL)])
                
            text = "<b>ʜᴇʏ {},\n\n📦 ʏᴏᴜʀ ꜰɪʟᴇ ɪꜱ ʀᴇᴀᴅʏ!\n\nᴄʟɪᴄᴋ ᴏɴ ᴛʜᴇ 'ᴅᴏᴡɴʟᴏᴀᴅ ɴᴏᴡ' ʙᴜᴛᴛᴏɴ ᴀɴᴅ ᴏᴘᴇɴ ᴛʜᴇ ʟɪɴᴋ ᴛᴏ ɢᴇᴛ ʏᴏᴜʀ ꜰɪʟᴇ.\n\n</b>"
            if PREMIUM_MODE == True:
                text += "<b>💎 ᴡᴀɴᴛ ɪɴꜱᴛᴀɴᴛ ꜰɪʟᴇꜱ ᴡɪᴛʜᴏᴜᴛ ᴀᴅꜱ? ʙᴜʏ ᴏᴜʀ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ!\n\nꜱᴇɴᴅ /plan ᴛᴏ ᴄʜᴇᴄᴋ ᴏᴜᴛ ᴏᴜʀ ᴘʟᴀɴꜱ.</b>"
            
            return await message.reply_text(
                text.format(message.from_user.mention),
                reply_markup=InlineKeyboardMarkup(btn)
            )
        else:
            is_token_verified = True

    elif data.startswith("short"):
        user = message.from_user.id
        pre = 'file'
        token = str(uuid.uuid4())
        await db.create_verify_token(user, token, file_data=f"{pre}_{file_id}")
        g = await get_shortlink(f"https://telegram.me/{temp.U_NAME}?start=t_{token}")
        
        if not g:
            await client.send_message(chat_id=user, text=DOWNTIME_TEXT, reply_markup=DOWNTIME_BUTTONS)
            return

        btn = [[
            InlineKeyboardButton('▼ ᴅᴏᴡɴʟᴏᴀᴅ ɴᴏᴡ ▼', url=g)
        ]]
        if TUTORIAL:
            btn.append([InlineKeyboardButton('? ʜᴏᴡ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ ?', url=TUTORIAL)])
        text = "<b>ʜᴇʏ {},\n\n📦 ʏᴏᴜʀ ꜰɪʟᴇ ɪꜱ ʀᴇᴀᴅʏ!\n\nᴄʟɪᴄᴋ ᴏɴ ᴛʜᴇ 'ᴅᴏᴡɴʟᴏᴀᴅ ɴᴏᴡ' ʙᴜᴛᴛᴏɴ ᴀɴᴅ ᴏᴘᴇɴ ᴛʜᴇ ʟɪɴᴋ ᴛᴏ ɢᴇᴛ ʏᴏᴜʀ ꜰɪʟᴇ.\n\n</b>"
        if PREMIUM_MODE == True:
            text += "<b>💎 ᴡᴀɴᴛ ɪɴꜱᴛᴀɴᴛ ꜰɪʟᴇꜱ ᴡɪᴛʜᴏᴜᴛ ᴀᴅꜱ? ʙᴜʏ ᴏᴜʀ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ!\n\nꜱᴇɴᴅ /plan ᴛᴏ ᴄʜᴇᴄᴋ ᴏᴜᴛ ᴏᴜʀ ᴘʟᴀɴꜱ.</b>"
        k = await client.send_message(chat_id=user, text=text.format(message.from_user.mention), reply_markup=InlineKeyboardMarkup(btn))
        from utils import delayed_delete
        delayed_delete([k], 900)
        return

        
    elif data.startswith("files"):
        user = message.from_user.id
        pre = 'file'
        if SHORTLINK_MODE and not await db.has_premium_access(user):
            token = str(uuid.uuid4())
            await db.create_verify_token(user, token, file_data=f"{pre}_{file_id}")
            g = await get_shortlink(f"https://telegram.me/{temp.U_NAME}?start=t_{token}")
            
            if not g:
                await client.send_message(chat_id=message.from_user.id, text=DOWNTIME_TEXT, reply_markup=DOWNTIME_BUTTONS)
                return
                
            btn = [[
                InlineKeyboardButton('▼ ᴅᴏᴡɴʟᴏᴀᴅ ɴᴏᴡ ▼', url=g)
            ]]
            if TUTORIAL:
                btn.append([InlineKeyboardButton('? ʜᴏᴡ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ ?', url=TUTORIAL)])
            text = "<b>ʜᴇʏ {},\n\n📦 ʏᴏᴜʀ ꜰɪʟᴇ ɪꜱ ʀᴇᴀᴅʏ!\n\nᴄʟɪᴄᴋ ᴏɴ ᴛʜᴇ 'ᴅᴏᴡɴʟᴏᴀᴅ ɴᴏᴡ' ʙᴜᴛᴛᴏɴ ᴀɴᴅ ᴏᴘᴇɴ ᴛʜᴇ ʟɪɴᴋ ᴛᴏ ɢᴇᴛ ʏᴏᴜʀ ꜰɪʟᴇ.\n\n</b>"
            if PREMIUM_MODE == True:
                text += "<b>💎 ᴡᴀɴᴛ ɪɴꜱᴛᴀɴᴛ ꜰɪʟᴇꜱ ᴡɪᴛʜᴏᴜᴛ ᴀᴅꜱ? ʙᴜʏ ᴏᴜʀ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ!\n\nꜱᴇɴᴅ /plan ᴛᴏ ᴄʜᴇᴄᴋ ᴏᴜᴛ ᴏᴜʀ ᴘʟᴀɴꜱ.</b>"
            k = await client.send_message(chat_id=message.from_user.id, text=text.format(message.from_user.mention), reply_markup=InlineKeyboardMarkup(btn))
            from utils import delayed_delete
            delayed_delete([k], 900)
            return
            
    user = message.from_user.id
    if SHORTLINK_MODE and not await db.has_premium_access(user) and not is_token_verified:
        return await message.reply_text("<b>⚠️ ɪɴᴠᴀʟɪᴅ ᴏʀ ᴇxᴘɪʀᴇᴅ ʟɪɴᴋ.\n\nᴘʟᴇᴀꜱᴇ ꜱᴇᴀʀᴄʜ ꜰᴏʀ ᴛʜᴇ ꜰɪʟᴇ ᴀɢᴀɪɴ ᴛᴏ ɢᴇᴛ ᴀ ꜰʀᴇꜱʜ ʟɪɴᴋ.</b>")

    files_ = await get_file_details(file_id)           
    if not files_:
        try:
            pre, file_id = ((base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))).decode("ascii")).split("_", 1)
        except Exception:
            return await message.reply('<b>❌ ɴᴏ ꜱᴜᴄʜ ꜰɪʟᴇ ᴇxɪꜱᴛꜱ.</b>')

        reply_markup = None
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
        f_caption = f"<b><code>{html.escape(title)}</code></b>"
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
        f_caption = f"<b>{html.escape(clean_name)}</b>"
    reply_markup = None
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
    text = '<b>ɪɴᴅᴇxᴇᴅ ᴄʜᴀɴɴᴇʟꜱ/ɢʀᴏᴜᴘꜱ</b>\n\n'
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
        msg = await message.reply("<b>ᴘʀᴏᴄᴇꜱꜱɪɴɢ...</b>", quote=True)
    else:
        reply = await bot.ask(message.from_user.id, "<b>ɴᴏᴡ, ꜱᴇɴᴅ ᴍᴇ ᴛʜᴇ ᴍᴇᴅɪᴀ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴅᴇʟᴇᴛᴇ.</b>")
        if reply.media:
            msg = await message.reply("<b>ᴘʀᴏᴄᴇꜱꜱɪɴɢ...</b>", quote=True)
        else:
            await message.reply('<b>ᴘʟᴇᴀꜱᴇ ꜱᴇɴᴅ ᴍᴇ ᴀ ᴠɪᴅᴇᴏ, ꜰɪʟᴇ, ᴏʀ ᴅᴏᴄᴜᴍᴇɴᴛ.</b>', quote=True)
            return

    for file_type in ("document", "video", "audio"):
        media = getattr(reply, file_type, None)
        if media is not None:
            break
    else:
        await msg.edit('<b>ᴛʜɪꜱ ɪꜱ ɴᴏᴛ ᴀ ꜱᴜᴘᴘᴏʀᴛᴇᴅ ꜰɪʟᴇ ꜰᴏʀᴍᴀᴛ.</b>')
        return
    
    file_id = unpack_new_file_id(media.file_id)

    result = await col.delete_one({
        'file_id': file_id,
    })
    if result.deleted_count:
        await msg.edit('<b>ꜰɪʟᴇ ʜᴀꜱ ʙᴇᴇɴ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ ꜰʀᴏᴍ ᴛʜᴇ ᴅᴀᴛᴀʙᴀꜱᴇ.</b>')
    else:
        from database.ia_filterdb import clean_file_name
        file_name = clean_file_name(media.file_name)
    
        result = await col.delete_many({
            'file_name': file_name,
            'file_size': media.file_size
        })
        if result.deleted_count:
            await msg.edit('<b>ꜰɪʟᴇ ʜᴀꜱ ʙᴇᴇɴ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ ꜰʀᴏᴍ ᴛʜᴇ ᴅᴀᴛᴀʙᴀꜱᴇ.</b>')
        else:
            result = await col.delete_many({
                'file_name': media.file_name,
                'file_size': media.file_size
            })
            if result.deleted_count:
                await msg.edit('<b>ꜰɪʟᴇ ʜᴀꜱ ʙᴇᴇɴ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ ꜰʀᴏᴍ ᴛʜᴇ ᴅᴀᴛᴀʙᴀꜱᴇ.</b>')
            else:
                await msg.edit('<b>ꜰɪʟᴇ ɴᴏᴛ ꜰᴏᴜɴᴅ ɪɴ ᴛʜᴇ ᴅᴀᴛᴀʙᴀꜱᴇ.</b>')

@Client.on_message(filters.command('deleteall') & filters.user(ADMINS))
async def delete_all_index(bot, message):
    await message.reply_text(
        '<b>ᴛʜɪꜱ ᴡɪʟʟ ᴅᴇʟᴇᴛᴇ ᴀʟʟ ɪɴᴅᴇxᴇᴅ ꜰɪʟᴇꜱ.\n\nᴅᴏ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴄᴏɴᴛɪɴᴜᴇ?</b>',
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

    from database.ia_filterdb import reset_and_setup_indices
    indices_ok = await reset_and_setup_indices()
    if not indices_ok:
        await query.answer('ꜰɪʟᴇꜱ ᴅᴇʟᴇᴛᴇᴅ, ʙᴜᴛ ɪɴᴅᴇx ʀᴇᴄʀᴇᴀᴛɪᴏɴ ꜰᴀɪʟᴇᴅ!', show_alert=True)
        return await query.message.edit('<b>ꜰɪʟᴇꜱ ᴅᴇʟᴇᴛᴇᴅ, ʙᴜᴛ ꜰᴀɪʟᴇᴅ ᴛᴏ ʀᴇᴄʀᴇᴀᴛᴇ ᴅᴀᴛᴀʙᴀꜱᴇ ɪɴᴅᴇxᴇꜱ.\n\nᴄʜᴇᴄᴋ ꜱᴇʀᴠᴇʀ ʟᴏɢꜱ!</b>')

    await query.answer('ᴘɪʀᴀᴄʏ ɪꜱ ᴀ ᴄʀɪᴍᴇ.')
    await query.message.edit('<b>ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ ᴀʟʟ ɪɴᴅᴇxᴇᴅ ꜰɪʟᴇꜱ.</b>')

@Client.on_message(filters.command('settings'))
async def settings(client, message):
    userid = message.from_user.id if message.from_user else None
    if not userid:
        return await message.reply("<b>👤 ʏᴏᴜ ᴀʀᴇ ᴀɴ ᴀɴᴏɴʏᴍᴏᴜꜱ ᴀᴅᴍɪɴ.</b>")
    chat_type = message.chat.type

    if chat_type == enums.ChatType.PRIVATE:
        await message.reply_text("<b>⚙️ ᴘʟᴇᴀꜱᴇ ᴜꜱᴇ /settings ɪɴꜱɪᴅᴇ ʏᴏᴜʀ ɢʀᴏᴜᴘ ᴛᴏ ᴄʜᴀɴɢᴇ ꜱᴇᴛᴛɪɴɢꜱ.</b>", quote=True)
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

    msg = None
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
        reply_markup = InlineKeyboardMarkup(buttons)
        msg = await message.reply_text(
            text=f"<b>⚙️ ᴄʜᴀɴɢᴇ ʏᴏᴜʀ ꜱᴇᴛᴛɪɴɢꜱ ꜰᴏʀ {title}</b>",
            reply_markup=reply_markup,
            disable_web_page_preview=True,
            parse_mode=enums.ParseMode.HTML,
            reply_to_message_id=message.id
        )
            
    if message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        await asyncio.sleep(60)
        try:
            if msg:
                await msg.delete()
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
        return await message.reply_text("<b>⚠️ ʏᴏᴜ ᴍᴜꜱᴛ ᴛʏᴘᴇ ʏᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ (ᴍɪɴɪᴍᴜᴍ 3 ᴄʜᴀʀᴀᴄᴛᴇʀꜱ).\n\nʀᴇǫᴜᴇꜱᴛꜱ ᴄᴀɴɴᴏᴛ ʙᴇ ᴇᴍᴘᴛʏ.</b>")
    
    try:
        btn = [[
            InlineKeyboardButton('ꜱʜᴏᴡ ᴏᴘᴛɪᴏɴꜱ', callback_data=f'show_option#{reporter}')
        ]]
            
        for admin in ADMINS:
            try:
                await bot.send_message(
                    chat_id=admin, 
                    text=f"<b>ʀᴇᴘᴏʀᴛᴇʀ : {mention} ({reporter})\n\nᴍᴇꜱꜱᴀɢᴇ : {content.strip().replace('<', '&lt;').replace('>', '&gt;')}</b>", 
                    reply_markup=InlineKeyboardMarkup(btn)
                )
            except Exception:
                pass
        await message.reply_text("<b>✅ ʏᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ ʜᴀꜱ ʙᴇᴇɴ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ꜱᴜʙᴍɪᴛᴛᴇᴅ ᴛᴏ ᴛʜᴇ ᴀᴅᴍɪɴꜱ!\n\nᴘʟᴇᴀꜱᴇ ᴡᴀɪᴛ ꜰᴏʀ ɪᴛ ᴛᴏ ʙᴇ ᴘʀᴏᴄᴇꜱꜱᴇᴅ.</b>")
    except Exception as e:
        await message.reply_text(f"<b>❌ ᴇʀʀᴏʀ ꜱᴜʙᴍɪᴛᴛɪɴɢ ʀᴇǫᴜᴇꜱᴛ:</b> <code>{html.escape(str(e))}</code>")

@Client.on_message(filters.command("send") & filters.user(ADMINS))
async def send_msg(bot, message):
    parts = message.text.split(None, 1)
    if len(parts) < 2 or not parts[1].strip():
        return await message.reply_text(
            "<b>ᴜꜱᴀɢᴇ:</b>\n\n"
            "<b>1. ᴅɪʀᴇᴄᴛ ᴛᴇxᴛ:</b>\n"
            "<code>/send user_id your message text</code>\n"
            "<code>/send id1 id2 id3 your message text</code>\n\n"
            "<b>2. ʀᴇᴘʟʏ (ꜰᴏʀ ᴍᴇᴅɪᴀ / ꜰɪʟᴇꜱ / ᴛᴇxᴛ):</b>\n"
            "<b>ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇꜱꜱᴀɢᴇ ᴡɪᴛʜ</b> <code>/send id1 id2 ...</code>"
        )

    # Mode 1: Reply Mode (copies replied media, files, or styled text)
    if message.reply_to_message:
        targets = [t.strip() for t in re.split(r"[\s,]+", parts[1].strip()) if t.strip()]
        is_direct_text = False
        text_to_send = None
    else:
        # Mode 2: Direct Text Mode (leading integer tokens are IDs, remainder is text)
        raw_args = parts[1].strip()
        tokens = raw_args.split()
        targets = []
        text_start_index = -1
        
        for i, token in enumerate(tokens):
            clean_token = token.rstrip(",")
            if clean_token.lstrip("-").isdigit():
                targets.append(clean_token)
            else:
                text_start_index = i
                break
                
        if not targets:
            return await message.reply_text("<b>ɴᴏ ᴠᴀʟɪᴅ ᴜꜱᴇʀ ɪᴅ ꜰᴏᴜɴᴅ.</b>")
            
        if text_start_index == -1:
            return await message.reply_text(
                "<b>ɴᴏ ᴍᴇꜱꜱᴀɢᴇ ᴛᴇxᴛ ᴘʀᴏᴠɪᴅᴇᴅ!</b>\n\n"
                "<b>• ᴇɪᴛʜᴇʀ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇꜱꜱᴀɢᴇ:</b> <code>/send user_id</code>\n\n"
                "<b>• ᴏʀ ᴛʏᴘᴇ ʏᴏᴜʀ ᴛᴇxᴛ:</b> <code>/send user_id your message text</code>"
            )
            
        is_direct_text = True
        text_to_send = " ".join(tokens[text_start_index:])

    success, failed = 0, 0
    failed_reasons = []

    for target in targets:
        try:
            target_id = int(target) if target.lstrip("-").isdigit() else target
            user = await bot.get_users(target_id)
            if not await db.is_user_exist(user.id):
                failed += 1
                failed_reasons.append(f"<code>{target}</code>: ᴛʜɪꜱ ᴜꜱᴇʀ ʜᴀꜱ ɴᴏᴛ ꜱᴛᴀʀᴛᴇᴅ ᴛʜɪꜱ ʙᴏᴛ ʏᴇᴛ")
            else:
                if is_direct_text:
                    await bot.send_message(chat_id=user.id, text=text_to_send)
                else:
                    await message.reply_to_message.copy(chat_id=user.id)
                success += 1
        except FloodWait as e:
            await asyncio.sleep(e.value)
            try:
                if is_direct_text:
                    await bot.send_message(chat_id=user.id, text=text_to_send)
                else:
                    await message.reply_to_message.copy(chat_id=user.id)
                success += 1
            except Exception:
                failed += 1
                failed_reasons.append(f"<code>{target}</code>: ꜰʟᴏᴏᴅ ᴡᴀɪᴛ")
        except Exception as e:
            failed += 1
            failed_reasons.append(f"<code>{target}</code>: {html.escape(str(e)[:30])}")

    if len(targets) == 1:
        if success:
            await message.reply_text(f"<b>ʏᴏᴜʀ ᴍᴇꜱꜱᴀɢᴇ ʜᴀꜱ ʙᴇᴇɴ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ꜱᴇɴᴛ ᴛᴏ {user.mention}.</b>")
        else:
            await message.reply_text(f"<b>ꜰᴀɪʟᴇᴅ ᴛᴏ ꜱᴇɴᴅ:</b> {failed_reasons[0]}")
    else:
        report = (
            "<b><u>ᴅᴇʟɪᴠᴇʀʏ ʀᴇᴘᴏʀᴛ</u></b>\n\n"
            f"<b>• ᴛᴏᴛᴀʟ:</b> <code>{len(targets)}</code>\n"
            f"<b>• ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟ:</b> <code>{success}</code>\n"
            f"<b>• ꜰᴀɪʟᴇᴅ:</b> <code>{failed}</code>"
        )
        if failed_reasons:
            report += "\n\n<b><u>ꜰᴀɪʟᴜʀᴇꜱ:</u></b>\n\n" + "\n".join(f"• {r}" for r in failed_reasons[:10])
        await message.reply_text(report, quote=True, parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command("deletefiles") & filters.user(ADMINS))
async def deletemultiplefiles(bot, message):
    chat_type = message.chat.type
    if chat_type != enums.ChatType.PRIVATE:
        return await message.reply_text(f"<b>ʜᴇʏ {message.from_user.mention}, ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ᴡᴏɴ'ᴛ ᴡᴏʀᴋ ɪɴ ɢʀᴏᴜᴘꜱ.\n\nɪᴛ ᴏɴʟʏ ᴡᴏʀᴋꜱ ɪɴ ᴍʏ ᴘᴍ!</b>")
    else:
        pass
    try:
        keyword = message.text.split(" ", 1)[1]
    except Exception:
        return await message.reply_text(f"<b>ʜᴇʏ {message.from_user.mention}, ᴘʟᴇᴀꜱᴇ ɢɪᴠᴇ ᴍᴇ ᴀ ᴋᴇʏᴡᴏʀᴅ ᴀʟᴏɴɢ ᴡɪᴛʜ ᴛʜᴇ ᴄᴏᴍᴍᴀɴᴅ ᴛᴏ ᴅᴇʟᴇᴛᴇ ꜰɪʟᴇꜱ.</b>")
    safe_keyword = keyword.replace('<', '&lt;').replace('>', '&gt;')
    k = await bot.send_message(chat_id=message.chat.id, text=f"<b>ꜰᴇᴛᴄʜɪɴɢ ꜰɪʟᴇꜱ ꜰᴏʀ ʏᴏᴜʀ ǫᴜᴇʀʏ '{safe_keyword}' ɪɴ ᴛʜᴇ ᴅᴀᴛᴀʙᴀꜱᴇ...\n\nᴘʟᴇᴀꜱᴇ ᴡᴀɪᴛ...</b>")
    files, total = await get_bad_files(keyword)
    await k.delete()
    del_key = f"k_{uuid.uuid4().hex}"
    temp.DEL_KEYWORDS[del_key] = keyword
    btn = [[
       InlineKeyboardButton("ʏᴇꜱ, ᴄᴏɴᴛɪɴᴜᴇ!", callback_data=f"killfilesdq#{del_key}")
    ],[
       InlineKeyboardButton("ᴄᴀɴᴄᴇʟ", callback_data="close_data")
    ]]
    await message.reply_text(
        text=f"<b>ꜰᴏᴜɴᴅ {total} ꜰɪʟᴇꜱ ꜰᴏʀ ʏᴏᴜʀ ǫᴜᴇʀʏ '{safe_keyword}'!\n\nᴅᴏ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴅᴇʟᴇᴛᴇ ᴛʜᴇᴍ?</b>",
        reply_markup=InlineKeyboardMarkup(btn),
        parse_mode=enums.ParseMode.HTML
    )

@Client.on_message(filters.command("restart") & filters.user(ADMINS))
async def stop_button(bot, message):
    msg = await bot.send_message(text="<b>ᴘʀᴏᴄᴇꜱꜱᴇꜱ ꜱᴛᴏᴘᴘᴇᴅ.\n\nʙᴏᴛ ɪꜱ ʀᴇꜱᴛᴀʀᴛɪɴɢ...</b>", chat_id=message.chat.id)       
    await asyncio.sleep(3)
    await msg.edit("<b>ʙᴏᴛ ɪꜱ ʀᴇꜱᴛᴀʀᴛᴇᴅ.\n\nʏᴏᴜ ᴄᴀɴ ɴᴏᴡ ᴜꜱᴇ ᴍᴇ.</b>")
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
            return await message.reply_text("<b>ɪɴᴠᴀʟɪᴅ ᴜꜱᴇʀ ɪᴅ.\n\nᴍᴜꜱᴛ ʙᴇ ᴀɴ ɪɴᴛᴇɢᴇʀ.</b>")
        time_str = message.command[2]        
        seconds = await get_seconds(time_str)
        if seconds and seconds > 0:
            current_expiry = await db.get_expiry_time(user_id)
            now = get_ist_now()
            if current_expiry and isinstance(current_expiry, datetime.datetime):
                if current_expiry.tzinfo is not None:
                    current_expiry = current_expiry.astimezone(IST).replace(tzinfo=None)
            base_time = current_expiry if (current_expiry and isinstance(current_expiry, datetime.datetime) and current_expiry > now) else now
            expiry_time = base_time + datetime.timedelta(seconds=seconds)
            user_data = {"id": user_id, "expiry_time": expiry_time} 
            await db.update_user(user_data)
            await message.reply_text(f"<b>ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ ʜᴀꜱ ʙᴇᴇɴ ᴀᴅᴅᴇᴅ ᴛᴏ ᴛʜᴇ ᴜꜱᴇʀ (ɪᴅ: {user_id}).</b>")            
            display_time = time_str.replace("day", " Days").replace("month", " Months").replace("year", " Years")
            try:
                await client.send_message(
                    chat_id=user_id,
                    text=f"""<b><u>🎉 ʏᴏᴜʀ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ ɪꜱ ɴᴏᴡ ᴀᴄᴛɪᴠᴇ!</u></b>\n\nʏᴏᴜʀ ᴀᴄᴄᴏᴜɴᴛ ɪꜱ ᴜᴘɢʀᴀᴅᴇᴅ ꜰᴏʀ <b><u>{display_time}</u></b>. ʏᴏᴜ ɴᴏᴡ ʜᴀᴠᴇ ᴜɴʟɪᴍɪᴛᴇᴅ, ɪɴꜱᴛᴀɴᴛ, ᴀɴᴅ ᴀᴅ-ꜰʀᴇᴇ ᴀᴄᴄᴇꜱꜱ ᴛᴏ ᴀʟʟ ᴏᴜʀ ʙᴏᴛꜱ!\n\n🎬 ᴍᴏᴠɪᴇꜱ: @TIC_Movies_Bot\n📺 ᴡᴇʙ ꜱᴇʀɪᴇꜱ & ᴀɴɪᴍᴇ: @TIC_Web_Series_Anime_Bot\n\n💡 ᴛʏᴘᴇ /myplan ᴛᴏ ᴄʜᴇᴄᴋ ʏᴏᴜʀ ꜱᴛᴀᴛᴜꜱ.\n\n<blockquote><b>🍿🎬 ᴇɴᴊᴏʏ & ʜᴀᴘᴘʏ ʙɪɴɢɪɴɢ!</b></blockquote>""",
                    parse_mode=enums.ParseMode.HTML
                )
            except Exception:
                pass
        else:
            await message.reply_text("<b>ɪɴᴠᴀʟɪᴅ ᴛɪᴍᴇ ꜰᴏʀᴍᴀᴛ.\n\nᴘʟᴇᴀꜱᴇ ᴜꜱᴇ '1min', '1hour', '1day', '1week', '1month', ᴏʀ '1year'.</b>")
    else:
        await message.reply_text("<b>ᴜꜱᴀɢᴇ: /add_premium user_id time \n\nᴇxᴀᴍᴘʟᴇ: /add_premium 1252789 10day \n\n(E.g. '1min', '1hour', '1day', '1week', '1month', or '1year')</b>")
        
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
            return await message.reply_text("<b>ɪɴᴠᴀʟɪᴅ ᴜꜱᴇʀ ɪᴅ.\n\nᴍᴜꜱᴛ ʙᴇ ᴀɴ ɪɴᴛᴇɢᴇʀ.</b>")
        user_data = {"id": target_id, "expiry_time": None}
        await db.update_user(user_data) 
        await message.reply_text(f"<b>ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ ʜᴀꜱ ʙᴇᴇɴ ʀᴇᴍᴏᴠᴇᴅ ꜰᴏʀ ᴜꜱᴇʀ {target_id}.</b>")
        try:
            await client.send_message(
                chat_id=target_id,
                text="<b>⚠️ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ ʜᴀꜱ ʙᴇᴇɴ ʀᴇᴍᴏᴠᴇᴅ ʙʏ ᴀᴅᴍɪɴꜱ.\n\nᴄᴏɴᴛᴀᴄᴛ ᴜꜱ ɪꜰ ᴛʜɪꜱ ɪꜱ ᴀ ᴍɪꜱᴛᴀᴋᴇ.</b>",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ᴄᴏɴᴛᴀᴄᴛ ꜱᴜᴘᴘᴏʀᴛ", url=SUPPORT_LINK)]])
            )
        except Exception:
            pass
    else:
        await message.reply_text("<b>ᴜꜱᴀɢᴇ: /remove_premium user_id</b>")
        
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
            if isinstance(expiry_time, datetime.datetime) and expiry_time.tzinfo is not None:
                expiry_time = expiry_time.astimezone(IST).replace(tzinfo=None)
            clean_remaining = str(remaining_time).split('.')[0]
            clean_expiry = str(expiry_time).split('.')[0]
            
            text = f"<b>🌟 ʏᴏᴜʀ ᴘʟᴀɴ ᴅᴇᴛᴀɪʟꜱ:</b>\n\n<b>ʀᴇᴍᴀɪɴɪɴɢ ᴛɪᴍᴇ:</b> <code>{clean_remaining}</code>\n\n<b>ᴇxᴘɪʀʏ ᴛɪᴍᴇ:</b> <code>{clean_expiry}</code>"
            btn = [[InlineKeyboardButton("⤬ ᴄʟᴏꜱᴇ ⤬", callback_data="close_data")]]
            
            msg = await message.reply_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(btn),
                parse_mode=enums.ParseMode.HTML
            )
        else:
            btn = [
                [InlineKeyboardButton("★ ʙᴜʏ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ ★", callback_data="buy_premium_myplan")],
                [InlineKeyboardButton("⤬ ᴄʟᴏꜱᴇ ⤬", callback_data="close_data")]
            ]
            msg = await message.reply_text(
                text="<b>ℹ️ ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴀɴʏ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ.\n\nᴄʜᴇᴄᴋ ᴏᴜᴛ ᴏᴜʀ ᴘʟᴀɴꜱ: /plan</b>", 
                reply_markup=InlineKeyboardMarkup(btn),
                parse_mode=enums.ParseMode.HTML
            )
    else:
        btn = [
            [InlineKeyboardButton("★ ʙᴜʏ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ ★", callback_data="buy_premium_myplan")],
            [InlineKeyboardButton("⤬ ᴄʟᴏꜱᴇ ⤬", callback_data="close_data")]
        ]
        reply_markup = InlineKeyboardMarkup(btn)
        
        msg = await message.reply_text(
            text="<b>ℹ️ ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴀɴʏ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ.\n\nᴄʜᴇᴄᴋ ᴏᴜᴛ ᴏᴜʀ ᴘʟᴀɴꜱ: /plan</b>", 
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )

@Client.on_message(filters.command("stats") & filters.user(ADMINS))
async def get_bot_stats(bot, message):
    msg = await message.reply_text("<b>ꜰᴇᴛᴄʜɪɴɢ ʟɪᴠᴇ ꜱᴛᴀᴛɪꜱᴛɪᴄꜱ...</b>")
    
    total_users = await db.total_users_count()
    totl_chats = await db.total_chat_count()
    total_files = await col.count_documents({}) if col is not None else 0
    
    stats = await fir_db.command('dbStats')
    used_db = (stats['dataSize']/(1024*1024))+(stats['indexSize']/(1024*1024))
    free_db = 512 - used_db

    stats_text = (
        "<b><u>ᴅᴀᴛᴀʙᴀꜱᴇ ꜱᴛᴀᴛɪꜱᴛɪᴄꜱ</u></b>\n\n"
        f"<b>★ ᴛᴏᴛᴀʟ ꜰɪʟᴇꜱ:</b> <code>{total_files}</code>\n"
        f"<b>★ ᴛᴏᴛᴀʟ ᴜꜱᴇʀꜱ:</b> <code>{total_users}</code>\n"
        f"<b>★ ᴛᴏᴛᴀʟ ɢʀᴏᴜᴘꜱ:</b> <code>{totl_chats}</code>\n\n"
        f"<b>★ ᴜꜱᴇᴅ ꜱᴛᴏʀᴀɢᴇ:</b> <code>{round(used_db, 2)} MB</code>\n"
        f"<b>★ ꜰʀᴇᴇ ꜱᴛᴏʀᴀɢᴇ:</b> <code>{round(free_db, 2)} MB</code>"
    )
    
    try:
        await msg.edit_text(stats_text)
    except MessageNotModified:
        pass

@Client.on_message(filters.command("ban") & filters.user(ADMINS))
async def ban_a_user(bot, message):
    if len(message.command) < 2:
        return await message.reply("<b>ᴘʟᴇᴀꜱᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴜꜱᴇʀ ɪᴅ.</b>")
    user_id = int(message.command[1])
    await db.ban_user(user_id, "Banned by Admin")
    if user_id not in temp.BANNED_USERS:
        temp.BANNED_USERS.append(user_id)
    await message.reply(f"<b>ᴜꜱᴇʀ {user_id} ʜᴀꜱ ʙᴇᴇɴ ʙᴀɴɴᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ.</b>")

@Client.on_message(filters.command("unban") & filters.user(ADMINS))
async def unban_a_user(bot, message):
    if len(message.command) < 2:
        return await message.reply("<b>ᴘʟᴇᴀꜱᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴜꜱᴇʀ ɪᴅ.</b>")
    user_id = int(message.command[1])
    await db.remove_ban(user_id)
    if user_id in temp.BANNED_USERS:
        temp.BANNED_USERS.remove(user_id)
    await message.reply(f"<b>ᴜꜱᴇʀ {user_id} ʜᴀꜱ ʙᴇᴇɴ ᴜɴʙᴀɴɴᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ.</b>")

@Client.on_message(filters.command("disable") & filters.user(ADMINS))
async def disable_a_chat(bot, message):
    if len(message.command) < 2:
        return await message.reply("<b>ᴘʟᴇᴀꜱᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴄʜᴀᴛ ɪᴅ.</b>")
    chat_id = int(message.command[1])
    await db.disable_chat(chat_id, "Disabled by Admin")
    if chat_id not in temp.BANNED_CHATS:
        temp.BANNED_CHATS.append(chat_id)
    await message.reply(f"<b>ᴄʜᴀᴛ {chat_id} ʜᴀꜱ ʙᴇᴇɴ ᴅɪꜱᴀʙʟᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ.</b>")

@Client.on_message(filters.command("enable") & filters.user(ADMINS))
async def enable_a_chat(bot, message):
    if len(message.command) < 2:
        return await message.reply("<b>ᴘʟᴇᴀꜱᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴄʜᴀᴛ ɪᴅ.</b>")
    chat_id = int(message.command[1])
    await db.re_enable_chat(chat_id)
    if chat_id in temp.BANNED_CHATS:
        temp.BANNED_CHATS.remove(chat_id)
    await message.reply(f"<b>ᴄʜᴀᴛ {chat_id} ʜᴀꜱ ʙᴇᴇɴ ᴇɴᴀʙʟᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ.</b>")

@Client.on_message(filters.command("leave") & filters.user(ADMINS))
async def leave_a_chat(bot, message):
    if len(message.command) < 2:
        return await message.reply("<b>ᴘʟᴇᴀꜱᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴄʜᴀᴛ ɪᴅ.</b>")
    chat_id = int(message.command[1])
    try:
        await bot.leave_chat(chat_id)
        await message.reply(f"<b>ʟᴇꜰᴛ ᴄʜᴀᴛ {chat_id} ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ.</b>")
    except Exception as e:
        await message.reply(f"<b>ᴇʀʀᴏʀ:</b> <code>{html.escape(str(e))}</code>")

@Client.on_message(filters.command("users") & filters.user(ADMINS))
async def list_users(bot, message):
    total_users = await db.total_users_count()
    await message.reply(f"<b>ᴛᴏᴛᴀʟ ᴜꜱᴇʀꜱ ɪɴ ᴅᴀᴛᴀʙᴀꜱᴇ: {total_users}</b>")

@Client.on_message(filters.command("chats") & filters.user(ADMINS))
async def list_chats(bot, message):
    total_chats = await db.total_chat_count()
    await message.reply(f"<b>ᴛᴏᴛᴀʟ ᴄʜᴀᴛꜱ ɪɴ ᴅᴀᴛᴀʙᴀꜱᴇ: {total_chats}</b>")

@Client.on_message(filters.command("recent"))
async def recent_uploads(client, message):
    user_id = message.from_user.id if message.from_user else 0
    is_admin_user = is_admin(user_id)
    is_premium = await db.has_premium_access(user_id) if not is_admin_user else True

    if not is_admin_user and not is_premium:
        if message.chat.type != enums.ChatType.PRIVATE:
            return
        btn = [
            [InlineKeyboardButton("★ ʙᴜʏ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ ★", callback_data="buy_premium")]
        ]
        return await message.reply_text(
            "<b>🔒 ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ɪꜱ ᴇxᴄʟᴜꜱɪᴠᴇ ᴛᴏ ᴘʀᴇᴍɪᴜᴍ ᴜꜱᴇʀꜱ.\n\nꜱᴇɴᴅ /plan ᴏʀ ᴄʟɪᴄᴋ ʙᴇʟᴏᴡ ᴛᴏ ᴜᴘɢʀᴀᴅᴇ!</b>",
            reply_markup=InlineKeyboardMarkup(btn),
            quote=True
        )

    if not is_admin_user:
        if message.chat.type != enums.ChatType.PRIVATE:
            return
        limit = 15
    else:
        limit = 15
        if len(message.command) > 1:
            try:
                limit = int(message.command[1])
            except ValueError:
                pass
                
    HEADER_TEXT = "🔥 <u>ᴜᴘʟᴏᴀᴅᴇᴅ ᴍᴏᴠɪᴇꜱ</u> 🔥"

    try:
        processing_msg = await message.reply(f"<b>ꜱᴄʀᴜʙʙɪɴɢ ᴛʜᴇ ʟᴀꜱᴛ {limit} ᴛɪᴛʟᴇꜱ ғʀᴏᴍ ᴅᴀᴛᴀʙᴀꜱᴇ</b>")
        
        recent_files = col.find({}).sort('$natural', -1)
        
        merged_titles = {}
        ordered_keys = []
        
        async for file in recent_files:
            name = file.get('file_name') or ""
            clean_name = re.sub(r"(_|\.)", " ", name)
            
            langs_found = re.findall(r"(?i)\b(Hindi|Tamil|Telugu|Malayalam|Kannada|English|Spanish|Punjabi|Bengali|Korean|Chinese|Japanese|French|German|Hin|Tam|Tel|Mal|Kan|Eng|Spa|Pun|Ben|Kor|Chi|Chin|Jap|Fre|Ger)\b", clean_name)
            lang_set = set(l.capitalize() for l in langs_found)
            
            movie_match = re.search(r"(.*?)\s*\(\d{4}\)", clean_name)
            if movie_match:
                base_title = movie_match.group(1).strip()
            else:
                base_title = re.split(r"(?i)(1080p|720p|576p|540p|480p|360p|PreDvd|WEB-DL|WEBRip|HDTVRip|HDRip|BluRay|x264|x265|HEVC|HQ|Audio|ESub|mkv|mp4|avi|m4v|webm|flv)", clean_name)[0].strip()
                base_title = re.sub(r"\s*(19|20)\d{2}$", "", base_title).strip()
            
            base_title = re.sub(r"\s*\(\d*$", "", base_title).strip()
            # Strip trailing/leading symbols, dashes, and brackets
            base_title = base_title.strip(" -—–:|~•[]()")
            unique_key = base_title.lower()
                
            if not unique_key:
                continue
                
            if unique_key not in merged_titles:
                merged_titles[unique_key] = {
                    'title': base_title,
                    'langs': lang_set
                }
                ordered_keys.append(unique_key)
            else:
                merged_titles[unique_key]['langs'].update(lang_set)
                
            if len(ordered_keys) >= limit:
                break

        unique_titles = []
        for key in ordered_keys:
            data = merged_titles[key]
            lang_str = f" [{' '.join(sorted(data['langs']))}]" if data['langs'] else ""
            slug = make_search_slug(data['title'])
            safe_base = data['title'].replace('<', '&lt;').replace('>', '&gt;')
            
            formatted_string = f"▪️ <a href='https://t.me/{temp.U_NAME}?start={slug}'>{safe_base}</a>{lang_str}"
            unique_titles.append(formatted_string)

        if not unique_titles:
            return await processing_msg.edit("<b>🔍 ɴᴏ ᴛɪᴛʟᴇꜱ ꜰᴏᴜɴᴅ ɪɴ ᴛʜᴇ ʀᴇǫᴜᴇꜱᴛᴇᴅ ʀᴀɴɢᴇ!</b>")

        chunk_size = 15
        chunks = [unique_titles[i:i + chunk_size] for i in range(0, len(unique_titles), chunk_size)]
        
        for i, chunk in enumerate(chunks):
            final_text = f"<b>{HEADER_TEXT}</b>\n\n"
            if i == 0:
                final_text += "<blockquote><b>👇 ᴊᴜsᴛ ᴛᴀᴘ ᴏɴ ᴀɴʏ ᴛɪᴛʟᴇ ʙᴇʟᴏᴡ ᴀɴᴅ ɢᴇᴛ ʏᴏᴜʀ ꜰɪʟᴇs ɪɴsᴛᴀɴᴛʟʏ!</b></blockquote>\n\n"
            
            for title in chunk:
                final_text += f"{title}\n\n"
                
            if i == len(chunks) - 1:
                final_text += "<blockquote><b>🍿🎬 ɢʀᴀʙ ʏᴏᴜʀ ᴘᴏᴘᴄᴏʀɴ & ʜᴀᴘᴘʏ ʙɪɴɢɪɴɢ!</b></blockquote>"

            if i == 0:
                await processing_msg.edit_text(text=final_text, disable_web_page_preview=True)
            else:
                await message.reply_text(text=final_text, disable_web_page_preview=True)
                await asyncio.sleep(0.5)
        
    except Exception as e:
        await message.reply(f"<b>❌ ᴇʀʀᴏʀ ᴅᴜʀɪɴɢ ᴇxᴛʀᴀᴄᴛɪᴏɴ: {e}</b>")

@Client.on_message(filters.command("premium_list") & filters.user(ADMINS))
async def premium_users_list(client, message):
    msg = await message.reply_text("<b>ꜰᴇᴛᴄʜɪɴɢ ᴘʀᴇᴍɪᴜᴍ ᴜꜱᴇʀꜱ...</b>")
    
    now = get_ist_now()
    count = await db.users.count_documents({"expiry_time": {"$gt": now}})
    
    if count == 0:
        return await msg.edit_text("<b>ᴛʜᴇʀᴇ ᴀʀᴇ ɴᴏ ᴀᴄᴛɪᴠᴇ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ ᴜꜱᴇʀꜱ ᴀᴛ ᴛʜᴇ ᴍᴏᴍᴇɴᴛ.</b>")
    
    premium_users = db.users.find({"expiry_time": {"$gt": now}}).sort("expiry_time", 1)
    text = f"<b><u>ᴀᴄᴛɪᴠᴇ sᴜʙsᴄʀɪᴘᴛɪᴏɴ ᴜꜱᴇʀꜱ</u></b>\n\n<b>ᴛᴏᴛᴀʟ ᴘʀᴇᴍɪᴜᴍ ᴜꜱᴇʀꜱ: {count}</b>\n\n"
    
    i = 0
    messages = []
    async for user in premium_users:
        i += 1
        user_id = user.get('id', 'Unknown')
        name = user.get('name', 'Unknown')
        exp_val = user.get('expiry_time')
        if isinstance(exp_val, datetime.datetime) and exp_val.tzinfo is not None:
            exp_val = exp_val.astimezone(IST).replace(tzinfo=None)
        expiry = str(exp_val).split('.')[0] if exp_val else "Unknown"
        # Username is now wrapped in a clickable profile link:
        text += f"<b>{i}. ᴜsᴇʀɴᴀᴍᴇ: <a href='tg://user?id={user_id}'>{name}</a></b>\n<b>ɪᴅ:</b> <code>{user_id}</code>\n<b>ᴇxᴘɪʀᴇꜱ:</b> <code>{expiry}</code>\n\n"
        
        if i % 15 == 0:
            messages.append(text)
            text = ""
    
    if text:
        messages.append(text)
    
    await msg.delete()
    for chunk in messages:
        await message.reply_text(chunk)


@Client.on_chat_join_request()
async def join_reqs(client, message):
    if AUTH_GROUP and message.chat.id == AUTH_GROUP and REQ_TO_JOIN:
        if not await db.is_user_exist(message.from_user.id):
            await db.add_user(message.from_user.id, message.from_user.first_name)
        await db.add_req_group(message.from_user.id)


@Client.on_message(filters.command("id") & filters.private)
async def showid(client: Client, message):
    rep = message.reply_to_message

    # 1. Privacy-hidden user forward
    if rep and rep.forward_sender_name:
        name = f"<code>{html.escape(rep.forward_sender_name)}</code>"
        text = f"<b>• ɴᴀᴍᴇ:</b> {name}\n<b>• ᴛᴇʟᴇɢʀᴀᴍ ɪᴅ:</b> <code>ʜɪᴅᴅᴇɴ ʙʏ ᴜꜱᴇʀ ᴘʀɪᴠᴀᴄʏ</code>"

    # 2. Channel / Group (forwarded or anonymous post)
    elif rep and (rep.forward_from_chat or rep.sender_chat):
        c = rep.forward_from_chat or rep.sender_chat
        title = f"<code>{html.escape(c.title or '')}</code>" if getattr(c, "title", None) else ""
        ctype = f"<code>{str(c.type).split('.')[-1].upper()}</code>" if getattr(c, "type", None) else ""
        uname = f"@{c.username}" if getattr(c, "username", None) else ""
        msg_id = f"\n<b>• ᴍᴇꜱꜱᴀɢᴇ ɪᴅ:</b> <code>{rep.forward_from_message_id}</code>" if getattr(rep, "forward_from_message_id", None) else ""
        text = f"<b>• ᴛɪᴛʟᴇ:</b> {title}\n<b>• ᴜꜱᴇʀɴᴀᴍᴇ:</b> {uname}\n<b>• ᴛᴇʟᴇɢʀᴀᴍ ɪᴅ:</b> <code>{c.id}</code>\n<b>• ᴄʜᴀᴛ ᴛʏᴘᴇ:</b> {ctype}{msg_id}"

    # 3. User (forwarded user, replied user, or sender themselves)
    else:
        u = (rep.forward_from or rep.from_user) if rep else message.from_user
        uid = u.id if u else message.chat.id
        first = f"<code>{html.escape(u.first_name or '')}</code>" if u and u.first_name else ""
        last = f"<code>{html.escape(u.last_name or '')}</code>" if u and u.last_name else ""
        uname = f"@{u.username}" if u and u.username else ""
        dc = f"<code>{u.dc_id}</code>" if u and getattr(u, "dc_id", None) else ""
        text = f"<b>• ꜰɪʀꜱᴛ ɴᴀᴍᴇ:</b> {first}\n<b>• ʟᴀꜱᴛ ɴᴀᴍᴇ:</b> {last}\n<b>• ᴜꜱᴇʀɴᴀᴍᴇ:</b> {uname}\n<b>• ᴛᴇʟᴇɢʀᴀᴍ ɪᴅ:</b> <code>{uid}</code>\n<b>• ᴅᴀᴛᴀ ᴄᴇɴᴛʀᴇ:</b> {dc}"

    await message.reply_text(text, quote=True, parse_mode=enums.ParseMode.HTML)
