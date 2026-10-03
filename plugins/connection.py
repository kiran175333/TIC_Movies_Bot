import logging
from info import ADMINS, is_admin
from pyrogram import filters, Client, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database.connections_mdb import add_connection, all_connections, if_active, delete_connection
import asyncio

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

@Client.on_message((filters.private | filters.group) & filters.command('connect'))
async def addconnection(client, message):
    userid = message.from_user.id if message.from_user else None
    if not userid:
        return await message.reply(f"ʏᴏᴜ ᴀʀᴇ ᴀɴ ᴀɴᴏɴʏᴍᴏᴜꜱ ᴀᴅᴍɪɴ. ᴜꜱᴇ /connect {message.chat.id} ɪɴ ᴘᴍ.")
    chat_type = message.chat.type

    if chat_type == enums.ChatType.PRIVATE:
        try:
            cmd, group_id = message.text.split(" ", 1)
        except Exception:
            await message.reply_text(
                "<b>ᴘʟᴇᴀꜱᴇ ᴇɴᴛᴇʀ ᴛʜᴇ ᴄᴏᴍᴍᴀɴᴅ ɪɴ ᴛʜᴇ ᴄᴏʀʀᴇᴄᴛ ꜰᴏʀᴍᴀᴛ!</b>\n\n"
                "<code>/connect groupid</code>\n\n"
                "<b>ɢᴇᴛ ʏᴏᴜʀ ɢʀᴏᴜᴘ ɪᴅ ʙʏ ᴀᴅᴅɪɴɢ ᴛʜɪꜱ ʙᴏᴛ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ ᴀɴᴅ ꜱᴇɴᴅɪɴɢ <code>/id</code>.</b>",
                quote=True
            )
            return

    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        group_id = message.chat.id

    try:
        st = await client.get_chat_member(group_id, userid)
        is_chat_admin = st.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]
        if not is_chat_admin and not is_admin(userid):
            await message.reply_text("<b>ʏᴏᴜ ᴍᴜꜱᴛ ʙᴇ ᴀɴ ᴀᴅᴍɪɴ ɪɴ ᴛʜᴇ ꜱᴘᴇᴄɪꜰɪᴇᴅ ɢʀᴏᴜᴘ!</b>", quote=True)
            return
    except Exception as e:
        if not is_admin(userid):
            logger.exception(e)
            await message.reply_text("<b>ɪɴᴠᴀʟɪᴅ ɢʀᴏᴜᴘ ɪᴅ!\n\nɪꜰ ᴛʜᴇ ɪᴅ ɪꜱ ᴄᴏʀʀᴇᴄᴛ, ᴘʟᴇᴀꜱᴇ ᴇɴꜱᴜʀᴇ ɪ ᴀᴍ ᴘʀᴇꜱᴇɴᴛ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ.</b>",
                quote=True,
            )
            return
    try:
        st = await client.get_chat_member(group_id, "me")
        if st.status == enums.ChatMemberStatus.ADMINISTRATOR:
            ttl = await client.get_chat(group_id)
            title = ttl.title

            addcon = await add_connection(str(group_id), str(userid))
            if addcon:
                await message.reply_text(
                    f"ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴄᴏɴɴᴇᴄᴛᴇᴅ ᴛᴏ <b>{title}</b>!\nʏᴏᴜ ᴄᴀɴ ɴᴏᴡ ᴍᴀɴᴀɢᴇ ʏᴏᴜʀ ɢʀᴏᴜᴘ ꜰʀᴏᴍ ᴍʏ ᴘᴍ.",
                    quote=True
                )
                if chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
                    await client.send_message(
                        userid,
                        f"ᴄᴏɴɴᴇᴄᴛᴇᴅ ᴛᴏ <b>{title}</b>!"
                    )
            else:
                await message.reply_text("<b>ʏᴏᴜ ᴀʀᴇ ᴀʟʀᴇᴀᴅʏ ᴄᴏɴɴᴇᴄᴛᴇᴅ ᴛᴏ ᴛʜɪꜱ ᴄʜᴀᴛ!</b>",
                    quote=True
                )
        else:
            await message.reply_text("<b>ᴘʟᴇᴀꜱᴇ ᴀᴅᴅ ᴍᴇ ᴀꜱ ᴀɴ ᴀᴅᴍɪɴ ɪɴ ᴛʜᴇ ɢʀᴏᴜᴘ.</b>", quote=True)
    except Exception as e:
        logger.exception(e)
        await message.reply_text('<b>ᴀɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ! ᴘʟᴇᴀꜱᴇ ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ.</b>', quote=True)
        pass
        
    if message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        await asyncio.sleep(60)
        try:
            await message.delete()
        except Exception:
            pass

@Client.on_message((filters.private | filters.group) & filters.command('disconnect'))
async def deleteconnection(client, message):
    userid = message.from_user.id if message.from_user else None
    if not userid:
        return await message.reply(f"ʏᴏᴜ ᴀʀᴇ ᴀɴ ᴀɴᴏɴʏᴍᴏᴜꜱ ᴀᴅᴍɪɴ. ᴜꜱᴇ /connect {message.chat.id} ɪɴ ᴘᴍ.")
    chat_type = message.chat.type

    if chat_type == enums.ChatType.PRIVATE:
        await message.reply_text("<b>ꜱᴇɴᴅ /connections ᴛᴏ ᴠɪᴇᴡ ᴏʀ ᴅɪꜱᴄᴏɴɴᴇᴄᴛ ꜰʀᴏᴍ ʏᴏᴜʀ ɢʀᴏᴜᴘꜱ!</b>", quote=True)

    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        group_id = message.chat.id

        try:
            st = await client.get_chat_member(group_id, userid)
            is_chat_admin = st.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]
        except Exception:
            is_chat_admin = False

        if not is_chat_admin and not is_admin(userid):
            return

        delcon = await delete_connection(str(userid), str(group_id))
        if delcon:
            await message.reply_text("<b>ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴅɪꜱᴄᴏɴɴᴇᴄᴛᴇᴅ ꜰʀᴏᴍ ᴛʜɪꜱ ᴄʜᴀᴛ.</b>", quote=True)
        else:
            await message.reply_text("<b>ᴛʜɪꜱ ᴄʜᴀᴛ ɪꜱ ɴᴏᴛ ᴄᴏɴɴᴇᴄᴛᴇᴅ ᴛᴏ ᴍᴇ!\nꜱᴇɴᴅ /connect ᴛᴏ ᴇꜱᴛᴀʙʟɪꜱʜ ᴀ ᴄᴏɴɴᴇᴄᴛɪᴏɴ.</b>", quote=True)

@Client.on_message(filters.private & filters.command(["connections"]))
async def connections(client, message):
    userid = message.from_user.id

    groupids = await all_connections(str(userid))
    if groupids is None:
        await message.reply_text("<b>ᴛʜᴇʀᴇ ᴀʀᴇ ɴᴏ ᴀᴄᴛɪᴠᴇ ᴄᴏɴɴᴇᴄᴛɪᴏɴꜱ! ᴘʟᴇᴀꜱᴇ ᴄᴏɴɴᴇᴄᴛ ᴛᴏ ꜱᴏᴍᴇ ɢʀᴏᴜᴘꜱ ꜰɪʀꜱᴛ.</b>",
            quote=True
        )
        return
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
        await message.reply_text("<b>ʏᴏᴜʀ ᴄᴏɴɴᴇᴄᴛᴇᴅ ɢʀᴏᴜᴘ ᴅᴇᴛᴀɪʟꜱ:\n\n</b>",
            reply_markup=InlineKeyboardMarkup(buttons),
            quote=True
        )
    else:
        await message.reply_text("<b>ᴛʜᴇʀᴇ ᴀʀᴇ ɴᴏ ᴀᴄᴛɪᴠᴇ ᴄᴏɴɴᴇᴄᴛɪᴏɴꜱ! ᴘʟᴇᴀꜱᴇ ᴄᴏɴɴᴇᴄᴛ ᴛᴏ ꜱᴏᴍᴇ ɢʀᴏᴜᴘꜱ ꜰɪʀꜱᴛ.</b>",
            quote=True
        )
