import logging
import os
import asyncio
import pytz
from datetime import datetime
from pyrogram import Client, __version__, enums
from database.users_chats_db import db
from info import *
from utils import temp
from Script import script
from aiohttp import web

is_healthy = False

# Lightweight health server to satisfy PaaS port binding (Koyeb/Render)
async def health_check(request):
    if not is_healthy:
        return web.Response(text="ʙᴏᴛ ɪꜱ ɴᴏᴛ ʀᴇᴀᴅʏ ᴏʀ ɪɴɪᴛɪᴀʟɪᴢᴀᴛɪᴏɴ ꜰᴀɪʟᴇᴅ!", status=503)
    return web.Response(text="ʙᴏᴛ ɪꜱ ʀᴜɴɴɪɴɢ ꜱᴍᴏᴏᴛʜʟʏ!", status=200)

class Bot(Client):
    def __init__(self):
        super().__init__(
            name=SESSION,
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            workers=15,
            plugins={"root": "plugins"},
            sleep_threshold=5,
        )

    async def start(self):
        # Display logo from script.py
        if hasattr(script, 'LOGO'):
            try:
                print(script.LOGO, flush=True)
            except UnicodeEncodeError:
                pass

        # Start the minimal web server
        app = web.Application()
        app.router.add_get('/', health_check)
        app.router.add_get('/health', health_check)
        
        self.runner = web.AppRunner(app)
        await self.runner.setup()
        bind_address = "0.0.0.0"
        port = int(os.environ.get("PORT", 8080))
        await web.TCPSite(self.runner, bind_address, port).start()
        logging.info(f"ʜᴇᴀʟᴛʜ ꜱᴇʀᴠᴇʀ ꜱᴛᴀʀᴛᴇᴅ ᴏɴ ᴘᴏʀᴛ {port}")

        try:
            from database.ia_filterdb import setup_indices as setup_ia_indices
            await db.setup_indices()
            res = await setup_ia_indices()
            if res is False:
                logging.warning("Non-fatal: ia_filterdb indexes returned warning, continuing startup...")
            else:
                logging.info("Database indexes initialized successfully.")
        except Exception as e:
            logging.warning(f"Non-fatal: Database index initialization error: {e}, continuing startup...")

        from utils import background_deleter
        self.deleter_task = asyncio.create_task(background_deleter(self))
        from plugins.pm_filter import spell_trigger_listener
        self.trigger_task = asyncio.create_task(spell_trigger_listener(self))

        await super().start()
        global is_healthy
        is_healthy = True
        self.set_parse_mode(enums.ParseMode.HTML)
        me = await self.get_me()
        temp.ME = me.id
        temp.U_NAME = me.username
        temp.B_NAME = me.first_name
        self.username = "@" + me.username
        
        logging.info(f"{me.first_name} ᴡɪᴛʜ ᴘʏʀᴏɢʀᴀᴍ ᴠ{__version__} ꜱᴛᴀʀᴛᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ!")
        try:
            b_users, b_chats = await db.get_banned()
            temp.BANNED_USERS = b_users
            temp.BANNED_CHATS = b_chats
        except Exception as e:
            logging.error(f"Failed to load banned lists: {e}")

        try:
            curr_time = datetime.now(pytz.timezone('Asia/Kolkata'))
            date_str = curr_time.strftime('%Y-%m-%d')
            time_str = curr_time.strftime('%I:%M:%S %p')
            await self.send_message(
                chat_id=LOG_CHANNEL,
                text=script.RESTART_TXT.format(date_str, time_str)
            )
        except Exception as e:
            logging.error(f"Failed to send restart message to LOG_CHANNEL: {e}")

    async def stop(self, *args):
        global is_healthy
        is_healthy = False
        await super().stop()
        if hasattr(self, 'deleter_task'):
            self.deleter_task.cancel()
        if hasattr(self, 'trigger_task'):
            self.trigger_task.cancel()
        if hasattr(self, 'runner'):
            await self.runner.cleanup()
            logging.info("ʜᴇᴀʟᴛʜ ꜱᴇʀᴠᴇʀ ꜱᴛᴏᴘᴘᴇᴅ.")
        logging.info("ʙᴏᴛ ꜱᴛᴏᴘᴘᴇᴅ. ʙʏᴇ.")

app = Bot()
app.run()
