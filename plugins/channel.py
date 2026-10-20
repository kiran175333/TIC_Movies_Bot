import html
from pyrogram import Client, filters
from info import CHANNELS, LOG_CHANNEL
from database.ia_filterdb import save_file
from utils import get_size

media_filter = filters.document | filters.video

@Client.on_message(filters.chat(CHANNELS) & media_filter)
async def media(bot, message):
    media = getattr(message, message.media.value, None)
    media.caption = message.caption.html if message.caption else None
    aynav, vnay = await save_file(media)
    if not aynav and vnay == 0:
        if LOG_CHANNEL:
            try:
                msg_link = message.link or f"https://t.me/c/{str(message.chat.id).replace('-100', '')}/{message.id}"
                raw_name = getattr(media, "file_name", "") or "Unknown"
                file_name = html.escape(raw_name)
                file_size = get_size(getattr(media, "file_size", 0))
                dup_text = (
                    f"<b>#ᴅᴜᴘʟɪᴄᴀᴛᴇ 1️⃣</b>\n"
                    f"<b>• ꜰɪʟᴇ:</b> <code>{file_name}</code> [{file_size}]\n"
                    f"<b>• ʟɪɴᴋ:</b> <a href=\"{html.escape(msg_link)}\"><b>ᴠɪᴇᴡ ᴍᴇꜱꜱᴀɢᴇ</b></a>"
                )
                await bot.send_message(LOG_CHANNEL, dup_text, disable_web_page_preview=True)
            except Exception:
                pass
