import logging
from telethon import TelegramClient, events, Button
from telethon.tl.types import Document, DocumentAttributeFilename
import uuid
import re
import math
from datetime import datetime 
import base64
from dotenv import load_dotenv
import os
import asyncio
from django.conf import settings
from database import (
    init_db, store_file_metadata, store_token,
    get_file_by_id, get_file_by_token, search_files, count_search_results,
    AsyncPostgresConnection
)
from userdb import (
    init_user_db, add_user, get_all_users, 
    get_user_count, update_user_activity, get_active_users_count
)

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize client as None
client = None

def init_client(api_id, api_hash, bot_token):
    """Initialize the Telegram client with credentials"""
    global client
    if client is None:
        client = TelegramClient('bot', api_id, api_hash)
        client.start(bot_token=bot_token)
    return client

VIDEO_EXTENSIONS = ['.mp4', '.mkv', '.webm', '.ts', '.mov', '.avi', '.flv', '.wmv', '.m4v', '.mpeg', '.mpg', '.3gp', '.3g2']

# List of authorized user IDs
AUTHORIZED_USER_IDS = [7951420571, 1509468839]  # Replace with your user ID and future moderator IDs

def normalize_keyword(keyword):
    # Replace special characters with spaces, convert to lowercase, and trim whitespace
    keyword = re.sub(r'[\.\_\@\(\)\-]', ' ', keyword).lower()
    keyword = re.sub(r'\s+', ' ', keyword)  # Replace multiple spaces with a single space
    return keyword.strip()

def split_keywords(keyword):
    # Split the normalized keyword into individual words
    return keyword.split()

async def main(api_id=None, api_hash=None, bot_token=None):
    """Main bot function that sets up event handlers and runs the bot"""
    global client
    if client is None:
        client = init_client(api_id, api_hash, bot_token)
    
    # Initialize database
    await init_db()
    await init_user_db()
    
    # Start bot if not already started
    if not client.is_connected():
        await client.start()
        
    logger.info("Main bot created")

    @client.on(events.NewMessage(pattern='/start'))
    async def start(event):
        user = event.sender
        await add_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        command_args = event.message.text.split()
        if len(command_args) > 1:
            token = command_args[1]
            try:
                decoded_token = base64.urlsafe_b64decode(token.encode()).decode()
                logger.debug(f"Decoded token: {decoded_token}")

                result = await get_file_by_token(token)
                logger.debug(f"Token verification result: {result}")

                if result:
                    file_id = result

                    file_info = await get_file_by_id(file_id)
                    logger.debug(f"File fetch result: {file_info}")

                    if file_info:
                        # Note: asyncpg returns Record object, access by key
                        id = file_info['id']
                        access_hash = file_info['access_hash']
                        file_reference = file_info['file_reference']
                        mime_type = file_info['mime_type']
                        file_name = file_info['file_name']

                        formatted_caption = file_name.replace(" ", ".").replace("@", "")

                        document = Document(
                            id=int(id),
                            access_hash=int(access_hash),
                            file_reference=bytes(file_reference),  # Convert memoryview to bytes
                            date=None,
                            mime_type=mime_type,
                            size=None,
                            dc_id=None,
                            attributes=[DocumentAttributeFilename(file_name=file_name)]
                        )

                        try:
                            await client.send_file(
                                event.sender_id,
                                file=document,
                                caption=formatted_caption
                            )
                            logger.info(f"File {file_name} sent successfully.")
                        except Exception as e:
                            logger.error(f"Error sending file: {e}")
                            await event.respond('Failed to send the file.')
                    else:
                        await event.respond('File not found in the database.')
                        logger.error("File not found in the database.")
                else:
                    await event.respond('Invalid token.')
                    logger.error("Invalid token.")
            except (ValueError, UnicodeDecodeError) as e:
                logger.error(f"Token decoding error: {e}")
                await event.respond('Failed to decode the token. Please try again.')
        else:
            await event.respond('Hantar movies apa yang anda mahu.')
            logger.warning("No token provided.")

    @client.on(events.NewMessage)
    async def handle_messages(event):
        await update_user_activity(event.sender_id)
        if event.is_private:
            if event.message.document:
                try:
                    user_id = event.message.sender_id
                    logger.debug(f"User ID: {user_id}")

                    if user_id not in AUTHORIZED_USER_IDS:
                        await event.reply("Maaf, anda tidak dibenarkan menghantar media kepada bot ini.")
                        return

                    document = event.message.document
                    file_name = None
                    for attr in event.message.document.attributes:
                        if isinstance(attr, DocumentAttributeFilename):
                            file_name = attr.file_name
                            break

                    caption = event.message.message or ""
                    keywords = normalize_keyword(caption) + " " + normalize_keyword(file_name)
                    keyword_list = split_keywords(keywords)

                    logger.debug(f"Received document message: {event.message}")
                    logger.debug(f"Caption: {caption}")
                    logger.debug(f"Keywords: {keywords}")
                    logger.debug(f"File Name: {file_name}")
                    logger.debug(f"Mime Type: {document.mime_type}")

                    # Convert id and access_hash to strings before storing
                    id = str(document.id)
                    access_hash = str(document.access_hash)
                    file_reference = document.file_reference
                    mime_type = document.mime_type

                    logger.debug(f"Inserting file metadata: id={id}, access_hash={access_hash}, file_reference={file_reference}, mime_type={mime_type}, caption={caption}, keywords={keywords}, file_name={file_name}")
                    await store_file_metadata(id, access_hash, file_reference, mime_type, caption, keywords, file_name)
                    await event.reply('File metadata stored.')
                except Exception as e:
                    logger.error(f"Error handling document message: {e}")
                    await event.reply('Failed to store file metadata.')

            elif event.message.text:
                try:
                    if event.message.text.startswith('/'):
                        logger.debug(f"Ignoring command: {event.message.text}")
                        return

                    text = normalize_keyword(event.message.text.lower().strip())
                    keyword_list = split_keywords(text)
                    logger.debug(f"Received text message: {text}")

                    page = 1  # Default to first page
                    page_size = 10  # Number of results per page
                    offset = (page - 1) * page_size

                    db_results = await search_files(keyword_list, page_size, offset)
                    logger.debug(f"Database search results for keywords '{keyword_list}': {db_results}")

                    total_results = await count_search_results(keyword_list)
                    total_pages = math.ceil(total_results / page_size)

                    video_results = [result for result in db_results if any(result[2].lower().endswith(ext) for ext in VIDEO_EXTENSIONS)]
                    logger.debug(f"Filtered video results: {video_results}")

                    if video_results:
                        header = f"{total_results} Results for '{text}'"
                        buttons = []
                        for id, caption, file_name in video_results:
                            token = await store_token(str(id))
                            if token:
                                import urllib.parse
                                safe_video_name = urllib.parse.quote(file_name, safe='')
                                safe_token = urllib.parse.quote(token, safe='')
                                website_link = f"{settings.SITE_URL}/?token={safe_token}&videoName={safe_video_name}"
                                buttons.append([Button.url(file_name or caption or "Unknown File", website_link)])
                        
                        logger.debug(f"Generated buttons: {buttons}")

                        # Pagination Buttons
                        pagination_buttons = []
                        start_page = max(1, page - 2)
                        end_page = min(total_pages, start_page + 4)

                        for p in range(start_page, end_page + 1):
                            if p == page:
                                pagination_buttons.append(Button.inline(f"[{p}]", f"ignore|{text}|{p}"))
                            else:
                                pagination_buttons.append(Button.inline(str(p), f"page|{text}|{p}"))

                        if page > 1:
                            pagination_buttons.insert(0, Button.inline("Prev", f"page|{text}|{page - 1}"))
                        if page < total_pages:
                            pagination_buttons.append(Button.inline("Next", f"page|{text}|{page + 1}"))

                        buttons.append(pagination_buttons)
                        buttons.append([Button.inline("First Page", f"page|{text}|1"), Button.inline("Last Page", f"page|{total_pages}")])

                        await event.respond(header, buttons=buttons)
                    else:
                        logger.debug(f"No matching video files found for keyword '{text}'.")
                        await event.reply('Movies yang anda cari belum ada boleh request di @Request67_bot.')
                except Exception as e:
                    logger.error(f"Error handling text message: {e}")
                    await event.reply('Failed to process your request.')

    @client.on(events.CallbackQuery)
    async def callback_query_handler(event):
        try:
            data = event.data.decode('utf-8')
            logger.debug(f"Callback query data: {data}")

            if data.startswith("page|"):
                parts = data.split("|")
                if len(parts) < 3:
                    await event.answer("Invalid page data")
                    return

                _, keyword, page = parts
                page = int(page)
                page_size = 10
                offset = (page - 1) * page_size

                keyword_list = split_keywords(keyword)

                db_results = await search_files(keyword_list, page_size, offset)
                logger.debug(f"Database search results for keywords '{keyword_list}': {db_results}")

                total_results = await count_search_results(keyword_list)
                total_pages = math.ceil(total_results / page_size)

                video_results = [result for result in db_results if any(result[2].lower().endswith(ext) for ext in VIDEO_EXTENSIONS)]
                logger.debug(f"Filtered video results: {video_results}")

                if video_results:
                    header = f"{total_results} Results for '{keyword}'"
                    buttons = [
                        [Button.inline(file_name or caption or "Unknown File", f"{id}|{page}")]
                        for id, caption, file_name in video_results
                    ]
                    logger.debug(f"Generated buttons: {buttons}")

                    # Pagination Buttons
                    pagination_buttons = []
                    start_page = max(1, page - 2)
                    end_page = min(total_pages, start_page + 4)

                    for p in range(start_page, end_page + 1):
                        if p == page:
                            pagination_buttons.append(Button.inline(f"[{p}]", f"ignore|{keyword}|{p}"))
                        else:
                            pagination_buttons.append(Button.inline(str(p), f"page|{keyword}|{p}"))

                    if page > 1:
                        pagination_buttons.insert(0, Button.inline("Prev", f"page|{keyword}|{page - 1}"))
                    if page < total_pages:
                        pagination_buttons.append(Button.inline("Next", f"page|{keyword}|{page + 1}"))

                    buttons.append(pagination_buttons)
                    buttons.append([Button.inline("First Page", f"page|{keyword}|1"), Button.inline("Last Page", f"page|{total_pages}")])

                    await event.edit(header, buttons=buttons)
                else:
                    await event.edit("No more results.")
            elif data.startswith("ignore|"):
                pass  # Do nothing if the user clicks on the current page
            else:
                id, current_page = data.split("|")
                token = await store_token(str(id))
                if token:
                    result = await get_file_by_id(str(id))
                    if result:
                        import urllib.parse
                        video_name = result['file_name']
                        safe_video_name = urllib.parse.quote(video_name, safe='')
                        safe_token = urllib.parse.quote(token, safe='')
                        website_link = f"{settings.SITE_URL}/?token={safe_token}&videoName={safe_video_name}"
                        await event.respond(f"Klik pautan ini untuk memuat turun fail anda: {website_link}")
                    else:
                        logger.error("Failed to fetch video name.")
                        await event.respond("Failed to fetch video name.")
                else:
                    logger.error("Failed to generate download link.")
                    await event.respond("Failed to generate download link.")
        except Exception as e:
            logger.error(f"Error handling callback query: {e}")
            await event.respond('Failed to process your request.')

    @client.on(events.NewMessage(pattern='/listdb'))
    async def list_db(event):
        logger.debug("Executing /listdb command")
        c.execute("SELECT * FROM files")
        results = c.fetchall()
        logger.debug(f"Database entries: {results}")
        await event.reply(f"Database entries: {results}")

    @client.on(events.NewMessage(pattern='/stats'))
    async def stats_command(event):
        if event.sender_id not in AUTHORIZED_USER_IDS:
            await event.reply("You are not authorized to use this command.")
            return
            
        user_count = await get_user_count()
        active_users = await get_active_users_count()  # Add this function to userdb.py
        
        stats_message = (
            "📊 Bot Statistics 📊\n\n"
            f"👥 Total Users: {user_count}\n"
            f"📱 Active Users (24h): {active_users}\n"
            f"🤖 Bot Status: Online\n"
            f"⏰ Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            "Admin Commands:\n"
            "• /broadcast - Send message to all users\n"
            "• /stats - Show these statistics"
        )
        
        await event.reply(stats_message)

    @client.on(events.NewMessage(pattern='/broadcast'))
    async def broadcast_command(event):
        if event.sender_id not in AUTHORIZED_USER_IDS:
            await event.reply("You are not authorized to use this command.")
            return
        
        # Get the message to broadcast
        reply = await event.get_reply_message()
        if not reply and not event.message.text.replace('/broadcast', '').strip():
            usage = (
                "Usage:\n"
                "1. Text broadcast: /broadcast your message\n"
                "2. Media broadcast: Reply to a photo/video with /broadcast [caption]\n"
                "3. Media without caption: Reply with '/broadcast none'\n"
                "\nNote: Broadcast will not be sent to admin users."
            )
            await event.reply(usage)
            return
            
        users = await get_all_users()
        sent = 0
        failed = 0
        skipped = 0
        
        # Show progress message
        progress = await event.reply("🚀 Broadcasting message...")
        
        try:
            for user in users:
                # Skip if user is an admin
                if user['user_id'] in AUTHORIZED_USER_IDS:
                    skipped += 1
                    continue
                    
                try:
                    if reply:
                        # If broadcasting a media message
                        if reply.media:
                            caption = None
                            if event.message.text.strip().lower() != '/broadcast none':
                                caption = event.message.text.replace('/broadcast', '').strip() or reply.text
                            
                            await client.send_file(
                                user['user_id'],
                                file=reply.media,
                                caption=caption
                            )
                        else:
                            await client.send_message(user['user_id'], reply.text)
                    else:
                        # If broadcasting text only
                        message = event.message.text.replace('/broadcast', '').strip()
                        await client.send_message(user['user_id'], message)
                    
                    sent += 1
                    if sent % 5 == 0:  # Update progress every 5 successful sends
                        await progress.edit(
                            f"🚀 Broadcasting...\n"
                            f"✅ Sent: {sent}\n"
                            f"❌ Failed: {failed}\n"
                            f"⏩ Skipped (admins): {skipped}"
                        )
                    await asyncio.sleep(0.1)  # Avoid flooding
                    
                except Exception as e:
                    logger.error(f"Failed to send to user {user['user_id']}: {e}")
                    failed += 1
                    
        finally:
            report = (
                "📬 Broadcast Completed\n\n"
                f"✅ Successfully sent: {sent}\n"
                f"❌ Failed: {failed}\n"
                f"⏩ Skipped (admins): {skipped}\n"
                f"👥 Total reach: {sent + failed}\n"
                f"📊 Success rate: {(sent/(sent+failed)*100 if sent+failed>0 else 0):.1f}%"
            )
            await progress.edit(report)

    await client.run_until_disconnected()

if __name__ == "__main__":
    with client:
        client.loop.run_until_complete(main(api_id=settings.TELEGRAM_API_ID, api_hash=settings.TELEGRAM_API_HASH, bot_token=settings.TELEGRAM_BOT_TOKEN))
