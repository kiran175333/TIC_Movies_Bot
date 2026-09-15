from pyrogram import Client, filters
from utils import temp
from pyrogram.types import Message
from database.users_chats_db import db
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

async def banned_users(_, client, message: Message):
    return message.from_user is not None and message.from_user.id in temp.BANNED_USERS

banned_user = filters.create(banned_users)

async def disabled_chat(_, client, message: Message):
    return message.chat.id in temp.BANNED_CHATS

disabled_group=filters.create(disabled_chat)


@Client.on_message(filters.private & banned_user & filters.incoming)
async def ban_reply(bot, message):
    ban = await db.get_ban_status(message.from_user.id)
    await message.reply(f'ꜱᴏʀʀʏ, ʏᴏᴜ ᴀʀᴇ ʙᴀɴɴᴇᴅ ꜰʀᴏᴍ ᴜꜱɪɴɢ ᴍᴇ.\nʙᴀɴ ʀᴇᴀꜱᴏɴ: {ban["ban_reason"]}')

@Client.on_message(filters.group & disabled_group & filters.incoming)
async def grp_bd(bot, message):
    vazha = await db.get_chat(message.chat.id)
    k = await message.reply(
        text=f"ᴄʜᴀᴛ ɴᴏᴛ ᴀʟʟᴏᴡᴇᴅ\n\nᴍʏ ᴀᴅᴍɪɴꜱ ʜᴀᴠᴇ ʀᴇꜱᴛʀɪᴄᴛᴇᴅ ᴍᴇ ꜰʀᴏᴍ ᴡᴏʀᴋɪɴɢ ʜᴇʀᴇ!\nʀᴇᴀꜱᴏɴ: <code>{vazha['reason']}</code>."
    )
    try:
        await k.pin()
    except Exception:
        pass
    await bot.leave_chat(message.chat.id)
