import motor.motor_asyncio
from info import DATABASE_URI, DATABASE_NAME
from pyrogram import enums
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

myclient = motor.motor_asyncio.AsyncIOMotorClient(DATABASE_URI)
mydb = myclient[DATABASE_NAME]

async def add_gfilter(gfilters, text, reply_text, btn, file, alert):
    mycol = mydb[str(gfilters)]
    # mycol.create_index([('text', 'text')])

    data = {
        'text':str(text),
        'reply':str(reply_text),
        'btn':str(btn),
        'file':str(file),
        'alert':str(alert)
    }

    try:
        await mycol.update_one({'text': str(text)},  {"$set": data}, upsert=True)
    except Exception:
        logger.exception('Some error occured!', exc_info=True)
             
     
async def find_gfilter(gfilters, name):
    mycol = mydb[str(gfilters)]
    
    query = mycol.find( {"text":name})
    reply_text, btn, alert, fileid = None, None, None, None
    try:
        async for file in query:
            reply_text = file['reply']
            btn = file['btn']
            fileid = file['file']
            try:
                alert = file['alert']
            except Exception:
                alert = None
        return reply_text, btn, alert, fileid
    except Exception:
        return None, None, None, None


async def get_gfilters(gfilters):
    mycol = mydb[str(gfilters)]

    texts = []
    query = mycol.find()
    try:
        async for file in query:
            text = file['text']
            texts.append(text)
    except Exception:
        pass
    return texts


async def delete_gfilter(message, text, gfilters):
    mycol = mydb[str(gfilters)]
    
    myquery = {'text':text }
    query = await mycol.count_documents(myquery)
    if query == 1:
        await mycol.delete_one(myquery)
        await message.reply_text(
            f"'{text}' ʜᴀs ʙᴇᴇɴ ᴅᴇʟᴇᴛᴇᴅ. ɪ ᴡɪʟʟ ɴᴏ ʟᴏɴɢᴇʀ ʀᴇsᴘᴏɴᴅ ᴛᴏ ᴛʜᴀᴛ ɢʟᴏʙᴀʟ ғɪʟᴛᴇʀ.",
            quote=True
        )
    else:
        await message.reply_text("ɪ ᴄᴏᴜʟᴅ ɴᴏᴛ ғɪɴᴅ ᴛʜᴀᴛ ɢʟᴏʙᴀʟ ғɪʟᴛᴇʀ!", quote=True)

async def del_allg(message, gfilters):
    if str(gfilters) not in await mydb.list_collection_names():
        await message.edit_text("ᴛʜᴇʀᴇ ɪs ɴᴏᴛʜɪɴɢ ᴛᴏ ʀᴇᴍᴏᴠᴇ!")
        return

    mycol = mydb[str(gfilters)]
    try:
        await mycol.drop()
        await message.edit_text(f"ᴀʟʟ ɢʟᴏʙᴀʟ ғɪʟᴛᴇʀs ʜᴀᴠᴇ ʙᴇᴇɴ ʀᴇᴍᴏᴠᴇᴅ!")
    except Exception:
        await message.edit_text("ɪ ᴄᴏᴜʟᴅ ɴᴏᴛ ʀᴇᴍᴏᴠᴇ ᴀʟʟ ɢʟᴏʙᴀʟ ғɪʟᴛᴇʀs!")
        return

async def count_gfilters(gfilters):
    mycol = mydb[str(gfilters)]

    count = await mycol.count_documents({})
    return False if count == 0 else count


async def gfilter_stats():
    collections = await mydb.list_collection_names()

    if "CONNECTION" in collections:
        collections.remove("CONNECTION")

    totalcount = 0
    for collection in collections:
        mycol = mydb[collection]
        count = await mycol.count_documents({})
        totalcount += count

    totalcollections = len(collections)

    return totalcollections, totalcount
