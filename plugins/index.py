import logging, re, asyncio
from utils import temp
from info import ADMINS, is_admin
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait, MessageNotModified
from pyrogram.errors import ChannelInvalid, ChatAdminRequired, UsernameInvalid, UsernameNotModified
from info import INDEX_REQ_CHANNEL as LOG_CHANNEL
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
        return await query.answer("ᴄᴀɴᴄᴇʟʟɪɴɢ ɪɴᴅᴇxɪɴɢ...")
    try:
        _, raju, chat, lst_msg_id, from_user = query.data.split("#")
    except ValueError:
        return await query.answer("ɪɴᴠᴀʟɪᴅ ʀᴇǫᴜᴇꜱᴛ", show_alert=True)
    if raju == 'reject':
        await query.message.delete()
        try:
            await bot.send_message(
                int(from_user),
                f'ʏᴏᴜʀ ꜱᴜʙᴍɪꜱꜱɪᴏɴ ꜰᴏʀ ɪɴᴅᴇxɪɴɢ {chat} ʜᴀꜱ ʙᴇᴇɴ ᴅᴇᴄʟɪɴᴇᴅ ʙʏ ᴏᴜʀ ᴍᴏᴅᴇʀᴀᴛᴏʀꜱ.',
                reply_to_message_id=int(lst_msg_id)
            )
        except Exception:
            pass
        return

    msg = query.message

    await query.answer('ᴘʀᴏᴄᴇꜱꜱɪɴɢ...', show_alert=True)
    if not is_admin(from_user):
        try:
            await bot.send_message(
                int(from_user),
                f'ʏᴏᴜʀ ꜱᴜʙᴍɪꜱꜱɪᴏɴ ꜰᴏʀ ɪɴᴅᴇxɪɴɢ {chat} ʜᴀꜱ ʙᴇᴇɴ ᴀᴄᴄᴇᴘᴛᴇᴅ ʙʏ ᴏᴜʀ ᴍᴏᴅᴇʀᴀᴛᴏʀꜱ ᴀɴᴅ ᴡɪʟʟ ʙᴇ ᴀᴅᴅᴇᴅ ꜱᴏᴏɴ.',
                reply_to_message_id=int(lst_msg_id)
            )
        except Exception:
            pass
    try:
        chat = int(chat)
    except Exception:
        chat = chat
    await msg.edit(
        "ꜱᴛᴀʀᴛɪɴɢ ɪɴᴅᴇxɪɴɢ...",
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
        return await ask_msg.reply('ᴛʜɪꜱ ᴍᴀʏ ʙᴇ ᴀ ᴘʀɪᴠᴀᴛᴇ ᴄʜᴀɴɴᴇʟ ᴏʀ ɢʀᴏᴜᴘ. ᴘʟᴇᴀꜱᴇ ᴍᴀᴋᴇ ᴍᴇ ᴀɴ ᴀᴅᴍɪɴ ᴛʜᴇʀᴇ ᴛᴏ ɪɴᴅᴇx ᴛʜᴇ ꜰɪʟᴇꜱ.')
    except (UsernameInvalid, UsernameNotModified):
        return await ask_msg.reply('ɪɴᴠᴀʟɪᴅ ʟɪɴᴋ ꜱᴘᴇᴄɪꜰɪᴇᴅ.')
    except Exception as e:
        logger.exception(e)
        return await ask_msg.reply(f'ᴇʀʀᴏʀꜱ: {e}')
    try:
        k = await bot.get_messages(chat_id, last_msg_id)
    except Exception:
        return await message.reply('ᴘʟᴇᴀꜱᴇ ᴍᴀᴋᴇ ꜱᴜʀᴇ ɪ ᴀᴍ ᴀɴ ᴀᴅᴍɪɴ ɪɴ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ, ᴇꜱᴘᴇᴄɪᴀʟʟʏ ɪꜰ ɪᴛ ɪꜱ ᴘʀɪᴠᴀᴛᴇ.')
    if k.empty:
        return await message.reply('ᴛʜɪꜱ ᴍᴀʏ ʙᴇ ᴀ ɢʀᴏᴜᴘ, ᴀɴᴅ ɪ ᴀᴍ ɴᴏᴛ ᴀɴ ᴀᴅᴍɪɴ ᴛʜᴇʀᴇ.')

    if is_admin(message.from_user):
        buttons = [[
            InlineKeyboardButton('ʏᴇꜱ', callback_data=f'index#accept#{chat_id}#{last_msg_id}#{message.from_user.id}')
        ],[
            InlineKeyboardButton('ᴄᴀɴᴄᴇʟ', callback_data='close_data')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        return await message.reply(
            f'ᴅᴏ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ɪɴᴅᴇx ᴛʜɪꜱ ᴄʜᴀɴɴᴇʟ/ɢʀᴏᴜᴘ?\n\nᴄʜᴀᴛ ɪᴅ/ᴜꜱᴇʀɴᴀᴍᴇ: <code>{chat_id}</code>\nʟᴀꜱᴛ ᴍᴇꜱꜱᴀɢᴇ ɪᴅ: <code>{last_msg_id}</code>',
            reply_markup=reply_markup
        )

    if type(chat_id) is int:
        try:
            link = (await bot.create_chat_invite_link(chat_id)).invite_link
        except ChatAdminRequired:
            return await message.reply('ᴍᴀᴋᴇ ꜱᴜʀᴇ ɪ ᴀᴍ ᴀɴ ᴀᴅᴍɪɴ ɪɴ ᴛʜᴇ ᴄʜᴀᴛ ᴀɴᴅ ʜᴀᴠᴇ ᴘᴇʀᴍɪꜱꜱɪᴏɴ ᴛᴏ ɪɴᴠɪᴛᴇ ᴜꜱᴇʀꜱ.')
    else:
        link = f"@{chat_id}"
    buttons = [[
        InlineKeyboardButton('ᴀᴄᴄᴇᴘᴛ ɪɴᴅᴇx', callback_data=f'index#accept#{chat_id}#{last_msg_id}#{message.from_user.id}')
    ],[
        InlineKeyboardButton('ʀᴇᴊᴇᴄᴛ ɪɴᴅᴇx', callback_data=f'index#reject#{chat_id}#{message.id}#{message.from_user.id}'),
    ]]
    reply_markup = InlineKeyboardMarkup(buttons)
    await bot.send_message(
        LOG_CHANNEL,
        f'#IndexRequest\n\nʙʏ: {message.from_user.mention} (<code>{message.from_user.id}</code>)\nᴄʜᴀᴛ ɪᴅ/ᴜꜱᴇʀɴᴀᴍᴇ: <code> {chat_id}</code>\nʟᴀꜱᴛ ᴍᴇꜱꜱᴀɢᴇ ɪᴅ: <code>{last_msg_id}</code>\nɪɴᴠɪᴛᴇ ʟɪɴᴋ: {link}',
        reply_markup=reply_markup
    )
    await message.reply('ᴛʜᴀɴᴋ ʏᴏᴜ ꜰᴏʀ ʏᴏᴜʀ ᴄᴏɴᴛʀɪʙᴜᴛɪᴏɴ! ᴘʟᴇᴀꜱᴇ ᴡᴀɪᴛ ꜰᴏʀ ᴏᴜʀ ᴍᴏᴅᴇʀᴀᴛᴏʀꜱ ᴛᴏ ᴠᴇʀɪꜰʏ ᴛʜᴇ ꜰɪʟᴇꜱ.')


@Client.on_message(filters.command('setskip') & filters.user(ADMINS))
async def set_skip_number(bot, message):
    if ' ' in message.text:
        _, skip = message.text.split(" ")
        try:
            skip = int(skip)
        except Exception:
            return await message.reply("ꜱᴋɪᴘ ɴᴜᴍʙᴇʀ ᴍᴜꜱᴛ ʙᴇ ᴀɴ ɪɴᴛᴇɢᴇʀ.")
        await message.reply(f"ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ꜱᴇᴛ ꜱᴋɪᴘ ɴᴜᴍʙᴇʀ ᴛᴏ {skip}.")
        temp.CURRENT = int(skip)
    else:
        await message.reply("ᴘʟᴇᴀꜱᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ꜱᴋɪᴘ ɴᴜᴍʙᴇʀ.")


async def index_files_to_db(lst_msg_id, chat, msg, bot):
    total_files = 0
    duplicate = 0
    errors = 0
    deleted = 0
    no_media = 0
    unsupported = 0
    try:
        current = int(temp.CURRENT)
        lst_msg_id = int(lst_msg_id)
        temp.CANCEL[chat] = False
        
        while current <= lst_msg_id:
            if temp.CANCEL.get(chat):
                await msg.edit(f"ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴄᴀɴᴄᴇʟʟᴇᴅ!\n\nꜱᴀᴠᴇᴅ <code>{total_files}</code> ꜰɪʟᴇꜱ ᴛᴏ ᴛʜᴇ ᴅᴀᴛᴀʙᴀꜱᴇ.\nᴅᴜᴘʟɪᴄᴀᴛᴇ ꜰɪʟᴇꜱ ꜱᴋɪᴘᴘᴇᴅ: <code>{duplicate}</code>\nᴅᴇʟᴇᴛᴇᴅ ᴍᴇꜱꜱᴀɢᴇꜱ ꜱᴋɪᴘᴘᴇᴅ: <code>{deleted}</code>\nɴᴏɴ-ᴍᴇᴅɪᴀ ᴍᴇꜱꜱᴀɢᴇꜱ ꜱᴋɪᴘᴘᴇᴅ: <code>{no_media + unsupported}</code> (ᴜɴꜱᴜᴘᴘᴏʀᴛᴇᴅ ᴍᴇᴅɪᴀ: <code>{unsupported}</code>)\nᴇʀʀᴏʀꜱ ᴏᴄᴄᴜʀʀᴇᴅ: <code>{errors}</code>")
                break
                
            # Fetch messages in chunks of 200 (Telegram API limit for Bots)
            chunk = list(range(current, min(current + 200, lst_msg_id + 1)))
            messages = await bot.get_messages(chat, chunk)
            
            for message in messages:
                if temp.CANCEL.get(chat):
                    break
                    
                if current % 30 == 0:
                    can = [[InlineKeyboardButton('ᴄᴀɴᴄᴇʟ', callback_data=f'index_cancel#{chat}')]]
                    reply = InlineKeyboardMarkup(can)
                    try:
                        await msg.edit_text(
                            text=f"ᴛᴏᴛᴀʟ ᴍᴇꜱꜱᴀɢᴇꜱ ꜰᴇᴛᴄʜᴇᴅ: <code>{current}</code>\nᴛᴏᴛᴀʟ ᴍᴇꜱꜱᴀɢᴇꜱ ꜱᴀᴠᴇᴅ: <code>{total_files}</code>\nᴅᴜᴘʟɪᴄᴀᴛᴇ ꜰɪʟᴇꜱ ꜱᴋɪᴘᴘᴇᴅ: <code>{duplicate}</code>\nᴅᴇʟᴇᴛᴇᴅ ᴍᴇꜱꜱᴀɢᴇꜱ ꜱᴋɪᴘᴘᴇᴅ: <code>{deleted}</code>\nɴᴏɴ-ᴍᴇᴅɪᴀ ᴍᴇꜱꜱᴀɢᴇꜱ ꜱᴋɪᴘᴘᴇᴅ: <code>{no_media + unsupported}</code> (ᴜɴꜱᴜᴘᴘᴏʀᴛᴇᴅ ᴍᴇᴅɪᴀ: <code>{unsupported}</code>)\nᴇʀʀᴏʀꜱ ᴏᴄᴄᴜʀʀᴇᴅ: <code>{errors}</code>",
                            reply_markup=reply
                        )
                    except MessageNotModified:
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
                    
                media.caption = message.caption.html if message.caption else None
                aynav, vnay = await save_file(media)
                
                if aynav:
                    total_files += 1
                elif vnay == 0:
                    duplicate += 1
                elif vnay == 2:
                    errors += 1
                    
            if temp.CANCEL.get(chat):
                break
                
    except Exception as e:
        logger.exception(e)
        k = await msg.edit(f'ᴇʀʀᴏʀ: {e}')
        await k.reply_text(f'ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ꜱᴀᴠᴇᴅ <code>{total_files}</code> ꜰɪʟᴇꜱ ᴛᴏ ᴛʜᴇ ᴅᴀᴛᴀʙᴀꜱᴇ.\nᴅᴜᴘʟɪᴄᴀᴛᴇ ꜰɪʟᴇꜱ ꜱᴋɪᴘᴘᴇᴅ: <code>{duplicate}</code>\nᴅᴇʟᴇᴛᴇᴅ ᴍᴇꜱꜱᴀɢᴇꜱ ꜱᴋɪᴘᴘᴇᴅ: <code>{deleted}</code>\nɴᴏɴ-ᴍᴇᴅɪᴀ ᴍᴇꜱꜱᴀɢᴇꜱ ꜱᴋɪᴘᴘᴇᴅ: <code>{no_media + unsupported}</code> (ᴜɴꜱᴜᴘᴘᴏʀᴛᴇᴅ ᴍᴇᴅɪᴀ: <code>{unsupported}</code>)\nᴇʀʀᴏʀꜱ ᴏᴄᴄᴜʀʀᴇᴅ: <code>{errors}</code>')
        await k.reply_text("<b>ɪꜰ ʏᴏᴜ ɢᴇᴛ ᴀ 'ᴍᴇꜱꜱᴀɢᴇ ɴᴏᴛ ᴍᴏᴅɪꜰɪᴇᴅ' ᴇʀʀᴏʀ, ᴘʟᴇᴀꜱᴇ ꜱᴋɪᴘ ʏᴏᴜʀ ꜱᴀᴠᴇᴅ ꜰɪʟᴇꜱ ᴀɴᴅ ɪɴᴅᴇx ᴀɢᴀɪɴ.</b>")
    else:
        if not temp.CANCEL.get(chat):
            await msg.edit(f'ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ꜱᴀᴠᴇᴅ <code>{total_files}</code> ꜰɪʟᴇꜱ ᴛᴏ ᴛʜᴇ ᴅᴀᴛᴀʙᴀꜱᴇ.\nᴅᴜᴘʟɪᴄᴀᴛᴇ ꜰɪʟᴇꜱ ꜱᴋɪᴘᴘᴇᴅ: <code>{duplicate}</code>\nᴅᴇʟᴇᴛᴇᴅ ᴍᴇꜱꜱᴀɢᴇꜱ ꜱᴋɪᴘᴘᴇᴅ: <code>{deleted}</code>\nɴᴏɴ-ᴍᴇᴅɪᴀ ᴍᴇꜱꜱᴀɢᴇꜱ ꜱᴋɪᴘᴘᴇᴅ: <code>{no_media + unsupported}</code> (ᴜɴꜱᴜᴘᴘᴏʀᴛᴇᴅ ᴍᴇᴅɪᴀ: <code>{unsupported}</code>)\nᴇʀʀᴏʀꜱ ᴏᴄᴄᴜʀʀᴇᴅ: <code>{errors}</code>')
