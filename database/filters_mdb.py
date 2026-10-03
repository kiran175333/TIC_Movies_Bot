import motor.motor_asyncio
from info import DATABASE_URI, DATABASE_NAME
from pyrogram import enums
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

myclient = motor.motor_asyncio.AsyncIOMotorClient(DATABASE_URI)
mydb = myclient[DATABASE_NAME]

async def add_filter(grp_id, text, reply_text, btn, file, alert):
    mycol = mydb[str(grp_id)]
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
             
     
async def find_filter(group_id, name):
    mycol = mydb[str(group_id)]
    
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


async def get_filters(group_id):
    mycol = mydb[str(group_id)]

    texts = []
    query = mycol.find()
    try:
        async for file in query:
            text = file['text']
            texts.append(text)
    except Exception:
        pass
    return texts


async def delete_filter(message, text, group_id):
    mycol = mydb[str(group_id)]
    
    myquery = {'text':text }
    query = await mycol.count_documents(myquery)
    if query == 1:
        await mycol.delete_one(myquery)
        await message.reply_text(f"<b>'{text}' ʜᴀꜱ ʙᴇᴇɴ ᴅᴇʟᴇᴛᴇᴅ. ɪ ᴡɪʟʟ ɴᴏ ʟᴏɴɢᴇʀ ʀᴇꜱᴘᴏɴᴅ ᴛᴏ ᴛʜᴀᴛ ғɪʟᴛᴇʀ.</b>",
            quote=True
        )
    else:
        await message.reply_text("<b>ɪ ᴄᴏᴜʟᴅɴ'ᴛ ғɪɴᴅ ᴛʜᴀᴛ ғɪʟᴛᴇʀ!</b>", quote=True)


async def del_all(message, group_id, title):
    if str(group_id) not in await mydb.list_collection_names():
        await message.edit_text(f"<b>ᴛʜᴇʀᴇ ɪꜱ ɴᴏᴛʜɪɴɢ ᴛᴏ ʀᴇᴍᴏᴠᴇ ɪɴ {title}!</b>")
        return

    mycol = mydb[str(group_id)]
    try:
        await mycol.drop()
        await message.edit_text(f"<b>ᴀʟʟ ғɪʟᴛᴇʀꜱ ꜰʀᴏᴍ {title} ʜᴀᴠᴇ ʙᴇᴇɴ ʀᴇᴍᴏᴠᴇᴅ.</b>")
    except Exception:
        await message.edit_text("<b>ɪ ᴄᴏᴜʟᴅɴ'ᴛ ʀᴇᴍᴏᴠᴇ ᴀʟʟ ғɪʟᴛᴇʀꜱ ғʀᴏᴍ ᴛʜᴇ ɢʀᴏᴜᴘ!</b>")
        return


async def count_filters(group_id):
    mycol = mydb[str(group_id)]

    count = await mycol.count_documents({})
    return False if count == 0 else count


async def filter_stats():
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

