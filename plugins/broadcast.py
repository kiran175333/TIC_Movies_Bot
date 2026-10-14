import datetime, time, asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from info import ADMINS, is_admin
from utils import broadcast_messages, broadcast_messages_group
from database.users_chats_db import db

# Global state tracker for broadcasts
BROADCAST_STATE = {"status": "stopped"} 
PENDING_BROADCASTS = {}

async def run_pm_broadcast(b_msg, sts):
    BROADCAST_STATE["status"] = "running"
    users = await db.get_all_users()
    total_users = await db.total_users_count()
    done, failed, success = 0, 0, 0
    start_time = time.time()
    
    btn = [[
        InlineKeyboardButton("ᴘᴀᴜꜱᴇ", callback_data="broadcast_pause"),
        InlineKeyboardButton("ᴄᴀɴᴄᴇʟ", callback_data="broadcast_cancel")
    ]]
    
    async for user in users:
        # Pause Loop Check
        while BROADCAST_STATE["status"] == "paused":
            await asyncio.sleep(1)
        
        # Cancel Loop Check
        if BROADCAST_STATE["status"] == "cancelled":
            break
        
        if 'id' in user:
            pti, sh = await broadcast_messages(int(user['id']), b_msg)
            if pti:
                success += 1
            elif pti == False:
                failed += 1
        done += 1
        
        if not done % 20:
            try:
                # Update UI only if running
                if BROADCAST_STATE["status"] == "running":
                    await sts.edit(
                        f"<b>ʙʀᴏᴀᴅᴄᴀꜱᴛ ɪɴ ᴘʀᴏɢʀᴇꜱꜱ:</b>\n\nᴛᴏᴛᴀʟ ᴜꜱᴇʀꜱ: {total_users}\nᴄᴏᴍᴘʟᴇᴛᴇᴅ: {done} / {total_users}\nꜱᴜᴄᴄᴇꜱꜱ: {success}\nꜰᴀɪʟᴇᴅ: {failed} (ᴡɪʟʟ ʙᴇ ᴀᴜᴛᴏ-ᴅᴇʟᴇᴛᴇᴅ)",
                        reply_markup=InlineKeyboardMarkup(btn)
                    )
            except Exception:
                pass 
                
    status_text = "ᴄᴀɴᴄᴇʟʟᴇᴅ" if BROADCAST_STATE["status"] == "cancelled" else "ᴄᴏᴍᴘʟᴇᴛᴇᴅ"
    BROADCAST_STATE["status"] = "stopped"
    time_taken = datetime.timedelta(seconds=int(time.time()-start_time))
    
    rem_users = await db.total_users_count()
    await sts.edit(f"<b>ʙʀᴏᴀᴅᴄᴀꜱᴛ {status_text}:</b>\nᴄᴏᴍᴘʟᴇᴛᴇᴅ ɪɴ {time_taken}\n\nᴛᴏᴛᴀʟ ᴜꜱᴇʀꜱ: {total_users}\nᴄᴏᴍᴘʟᴇᴛᴇᴅ: {done} / {total_users}\nꜱᴜᴄᴄᴇꜱꜱ: {success}\nꜰᴀɪʟᴇᴅ: {failed} (ᴀᴜᴛᴏ-ᴅᴇʟᴇᴛᴇᴅ)\nʀᴇᴍᴀɪɴɪɴɢ ᴀᴄᴛɪᴠᴇ: {rem_users}")


async def run_grp_broadcast(b_msg, sts):
    BROADCAST_STATE["status"] = "running"
    groups = await db.get_all_chats()
    total_groups = await db.total_chat_count()
    done, failed, success = 0, 0, 0
    start_time = time.time()
    
    btn = [[
        InlineKeyboardButton("ᴘᴀᴜꜱᴇ", callback_data="broadcast_pause"),
        InlineKeyboardButton("ᴄᴀɴᴄᴇʟ", callback_data="broadcast_cancel")
    ]]

    async for group in groups:
        while BROADCAST_STATE["status"] == "paused":
            await asyncio.sleep(1)
            
        if BROADCAST_STATE["status"] == "cancelled":
            break
            
        pti, sh = await broadcast_messages_group(int(group['id']), b_msg)
        if pti:
            success += 1
        elif pti == False:
            failed += 1
        done += 1
        
        if not done % 20:
            try:
                if BROADCAST_STATE["status"] == "running":
                    await sts.edit(
                        f"<b>ʙʀᴏᴀᴅᴄᴀꜱᴛ ɪɴ ᴘʀᴏɢʀᴇꜱꜱ:</b>\n\nᴛᴏᴛᴀʟ ɢʀᴏᴜᴘꜱ: {total_groups}\nᴄᴏᴍᴘʟᴇᴛᴇᴅ: {done} / {total_groups}\nꜱᴜᴄᴄᴇꜱꜱ: {success}\nꜰᴀɪʟᴇᴅ: {failed} (ᴡɪʟʟ ʙᴇ ᴀᴜᴛᴏ-ᴅᴇʟᴇᴛᴇᴅ)",
                        reply_markup=InlineKeyboardMarkup(btn)
                    )
            except Exception:
                pass
                
    status_text = "ᴄᴀɴᴄᴇʟʟᴇᴅ" if BROADCAST_STATE["status"] == "cancelled" else "ᴄᴏᴍᴘʟᴇᴛᴇᴅ"
    BROADCAST_STATE["status"] = "stopped"
    time_taken = datetime.timedelta(seconds=int(time.time()-start_time))
    
    rem_groups = await db.total_chat_count()
    await sts.edit(f"<b>ʙʀᴏᴀᴅᴄᴀꜱᴛ {status_text}:</b>\nᴄᴏᴍᴘʟᴇᴛᴇᴅ ɪɴ {time_taken}\n\nᴛᴏᴛᴀʟ ɢʀᴏᴜᴘꜱ: {total_groups}\nᴄᴏᴍᴘʟᴇᴛᴇᴅ: {done} / {total_groups}\nꜱᴜᴄᴄᴇꜱꜱ: {success}\nꜰᴀɪʟᴇᴅ: {failed} (ᴀᴜᴛᴏ-ᴅᴇʟᴇᴛᴇᴅ)\nʀᴇᴍᴀɪɴɪɴɢ ᴀᴄᴛɪᴠᴇ: {rem_groups}")


@Client.on_message(filters.command("broadcast") & filters.user(ADMINS))
async def pm_broadcast(bot, message):
    if BROADCAST_STATE.get("status") in ["running", "paused"]:
        return await message.reply_text("<b>ᴀ ʙʀᴏᴀᴅᴄᴀꜱᴛ ɪꜱ ᴀʟʀᴇᴀᴅʏ ɪɴ ᴘʀᴏɢʀᴇꜱꜱ! ᴘʟᴇᴀꜱᴇ ᴄᴀɴᴄᴇʟ ɪᴛ ꜰɪʀꜱᴛ.</b>")

    if message.reply_to_message:
        b_msg = message.reply_to_message
    else:
        b_msg = await bot.ask(chat_id=message.from_user.id, text="<b>ɴᴏᴡ, ꜱᴇɴᴅ ᴍᴇ ʏᴏᴜʀ ʙʀᴏᴀᴅᴄᴀꜱᴛ ᴍᴇꜱꜱᴀɢᴇ.</b>")
    
    msg_key = f"{b_msg.chat.id}_{b_msg.id}"
    PENDING_BROADCASTS[msg_key] = b_msg

    btn = [[
        InlineKeyboardButton("ᴄᴏɴꜰɪʀᴍ", callback_data=f"bcast_confirm_pm_{msg_key}"),
        InlineKeyboardButton("ᴄᴀɴᴄᴇʟ", callback_data="bcast_cancel_preview")
    ]]
    
    await message.reply_text(
        "<b>ʙʀᴏᴀᴅᴄᴀꜱᴛ ᴘʀᴇᴠɪᴇᴡ\n\nᴘʟᴇᴀꜱᴇ ᴄʜᴇᴄᴋ ᴛʜᴇ ᴍᴇꜱꜱᴀɢᴇ ᴀʙᴏᴠᴇ. ᴅᴏ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ʙʀᴏᴀᴅᴄᴀꜱᴛ ɪᴛ ᴛᴏ ᴀʟʟ ᴜꜱᴇʀꜱ?</b>",
        reply_markup=InlineKeyboardMarkup(btn),
        reply_to_message_id=b_msg.id
    )


@Client.on_message(filters.command("grp_broadcast") & filters.user(ADMINS))
async def broadcast_group(bot, message):
    if BROADCAST_STATE.get("status") in ["running", "paused"]:
        return await message.reply_text("<b>ᴀ ʙʀᴏᴀᴅᴄᴀꜱᴛ ɪꜱ ᴀʟʀᴇᴀᴅʏ ɪɴ ᴘʀᴏɢʀᴇꜱꜱ! ᴘʟᴇᴀꜱᴇ ᴄᴀɴᴄᴇʟ ɪᴛ ꜰɪʀꜱᴛ.</b>")

    if message.reply_to_message:
        b_msg = message.reply_to_message
    else:
        b_msg = await bot.ask(chat_id=message.from_user.id, text="<b>ɴᴏᴡ, ꜱᴇɴᴅ ᴍᴇ ʏᴏᴜʀ ʙʀᴏᴀᴅᴄᴀꜱᴛ ᴍᴇꜱꜱᴀɢᴇ.</b>")
    
    msg_key = f"{b_msg.chat.id}_{b_msg.id}"
    PENDING_BROADCASTS[msg_key] = b_msg

    btn = [[
        InlineKeyboardButton("ᴄᴏɴꜰɪʀᴍ", callback_data=f"bcast_confirm_grp_{msg_key}"),
        InlineKeyboardButton("ᴄᴀɴᴄᴇʟ", callback_data="bcast_cancel_preview")
    ]]
    
    await message.reply_text(
        "<b>ʙʀᴏᴀᴅᴄᴀꜱᴛ ᴘʀᴇᴠɪᴇᴡ\n\nᴘʟᴇᴀꜱᴇ ᴄʜᴇᴄᴋ ᴛʜᴇ ᴍᴇꜱꜱᴀɢᴇ ᴀʙᴏᴠᴇ. ᴅᴏ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ʙʀᴏᴀᴅᴄᴀꜱᴛ ɪᴛ ᴛᴏ ᴀʟʟ ɢʀᴏᴜᴘꜱ?</b>",
        reply_markup=InlineKeyboardMarkup(btn),
        reply_to_message_id=b_msg.id
    )


@Client.on_callback_query(filters.regex(r"^(broadcast_|bcast_)"))
async def broadcast_callbacks(bot, query):
    if not query.from_user or not is_admin(query.from_user):
        return await query.answer("ᴛʜɪꜱ ɪꜱ ᴀɴ ᴀᴅᴍɪɴ-ᴏɴʟʏ ꜰᴇᴀᴛᴜʀᴇ!", show_alert=True)
    
    data = query.data
    
    if data == "bcast_cancel_preview":
        return await query.message.edit_text("<b>ʙʀᴏᴀᴅᴄᴀꜱᴛ ᴄᴀɴᴄᴇʟʟᴇᴅ ʙᴇꜰᴏʀᴇ ꜱᴛᴀʀᴛɪɴɢ.</b>")
        
    if data.startswith("bcast_confirm_"):
        parts = data.split("_")
        b_type = parts[2]
        msg_key = f"{parts[3]}_{parts[4]}"
        
        b_msg = PENDING_BROADCASTS.get(msg_key)
        if not b_msg:
            return await query.answer("ᴇʀʀᴏʀ: ᴍᴇꜱꜱᴀɢᴇ ɴᴏᴛ ꜰᴏᴜɴᴅ. ᴘʟᴇᴀꜱᴇ ᴛʀʏ ᴀɢᴀɪɴ.", show_alert=True)
            
        btn = [[
            InlineKeyboardButton("ᴘᴀᴜꜱᴇ", callback_data="broadcast_pause"),
            InlineKeyboardButton("ᴄᴀɴᴄᴇʟ", callback_data="broadcast_cancel")
        ]]
        await query.message.edit_text(
            "<b>ʙʀᴏᴀᴅᴄᴀꜱᴛ ꜱᴛᴀʀᴛɪɴɢ...</b>", 
            reply_markup=InlineKeyboardMarkup(btn)
        )
        
        if b_type == "pm":
            asyncio.create_task(run_pm_broadcast(b_msg, query.message))
        else:
            asyncio.create_task(run_grp_broadcast(b_msg, query.message))
        return

    try:
        action = data.split("_")[1]
    except (IndexError, AttributeError):
        return await query.answer("ɪɴᴠᴀʟɪᴅ ᴀᴄᴛɪᴏɴ", show_alert=True)
    
    if action == "pause":
        BROADCAST_STATE["status"] = "paused"
        btn = [[
            InlineKeyboardButton("ʀᴇꜱᴜᴍᴇ", callback_data="broadcast_resume"),
            InlineKeyboardButton("ᴄᴀɴᴄᴇʟ", callback_data="broadcast_cancel")
        ]]
        await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(btn))
        await query.answer("ʙʀᴏᴀᴅᴄᴀꜱᴛ ᴘᴀᴜꜱᴇᴅ!")
        
    elif action == "resume":
        BROADCAST_STATE["status"] = "running"
        btn = [[
            InlineKeyboardButton("ᴘᴀᴜꜱᴇ", callback_data="broadcast_pause"),
            InlineKeyboardButton("ᴄᴀɴᴄᴇʟ", callback_data="broadcast_cancel")
        ]]
        await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(btn))
        await query.answer("ʙʀᴏᴀᴅᴄᴀꜱᴛ ʀᴇꜱᴜᴍᴇᴅ!")
        
    elif action == "cancel":
        BROADCAST_STATE["status"] = "cancelled"
        await query.answer("ᴄᴀɴᴄᴇʟʟɪɴɢ ʙʀᴏᴀᴅᴄᴀꜱᴛ... ᴘʟᴇᴀꜱᴇ ᴡᴀɪᴛ ꜰᴏʀ ᴛʜᴇ ꜰɪɴᴀʟ ʀᴇᴘᴏʀᴛ.", show_alert=True)
