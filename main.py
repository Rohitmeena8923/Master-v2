
import os
import re
import sys
import shutil
import logging
import asyncio
import subprocess
from typing import List, Tuple, Optional

from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait, RPCError
from pyromod import listen
from aiohttp import ClientSession
from config import Config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logging.getLogger("pyrogram").setLevel(logging.WARNING)

# Initialize bot
bot = Client(
    "bot",
    bot_token=Config.BOT_TOKEN,
    api_id=Config.API_ID,
    api_hash=Config.API_HASH
)

# ========== HELPER FUNCTIONS ========== #
async def parse_input(message: Message) -> List[str]:
    """Extract links from a document or text."""
    if message.document:
        file_path = await message.download()
        with open(file_path, "r") as f:
            content = f.read().split("\n")
        os.remove(file_path)
    else:
        content = message.text.split("\n")
    return [link.strip() for link in content if link.strip()]

async def validate_channel(bot: Client, channel_id: str) -> bool:
    """Check if the bot is admin in the channel."""
    try:
        chat = await bot.get_chat(channel_id)
        if chat.type != "channel":
            return False
        me = await bot.get_chat_member(channel_id, "me")
        return me.can_post_messages
    except RPCError:
        return False

async def download_video(url: str, output_name: str, resolution: str) -> bool:
    """Download video using yt-dlp."""
    cmd = [
        "yt-dlp",
        "-f", f"bv[height<={resolution}]+ba/b[height<={resolution}]",
        "-o", f"{output_name}.mp4",
        url
    ]
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Download failed: {e}")
        return False

async def upload_video(bot: Client, channel_id: int, file_path: str, caption: str, thumb: Optional[str] = None):
    """Upload video to Telegram."""
    try:
        await bot.send_video(
            chat_id=channel_id,
            video=file_path,
            caption=caption,
            thumb=thumb,
            supports_streaming=True
        )
        os.remove(file_path)
    except FloodWait as e:
        await asyncio.sleep(e.x)
    except RPCError as e:
        logger.error(f"Upload failed: {e}")

# ========== BOT COMMANDS ========== #
@bot.on_message(filters.command(["start"]))
async def start(bot: Client, m: Message):
    await m.reply_text(
        "😈 **Hi bruh!**\n"
        "🟢 **I'm Alive! Use /master to start.**\n\n"
        "**Supported URLs:**\n"
        "- All Non-DRM + DRM Protected URLs\n"
        "- Mpeg Dash\n"
        "- Vision IAS\n"
        "- PhysicsWallah\n"
        "- ClassPlus\n"
        "- Allen Institute\n\n"
        "**Developer:** @St2Master"
    )

@bot.on_message(filters.command(["master"]))
async def master(bot: Client, m: Message):
    if m.chat.id not in Config.VIP_USERS:
        await m.reply_text(
            "**⚠️ Premium Required!**\n\n"
            "Upgrade with /upgrade\n"
            f"Your ID: `{m.chat.id}`"
        )
        return

    try:
        # Step 1: Get links
        editable = await m.reply_text("**Send Master TXT file or links:**")
        input_msg = await bot.listen(m.chat.id, timeout=300)
        links = await parse_input(input_msg)
        if not links:
            await m.reply_text("**No valid links found!**")
            return

        # Step 2: Get batch details
        await editable.edit("**Enter Batch Name (or /d for filename):**")
        batch_msg = await bot.listen(m.chat.id, timeout=300)
        batch_name = batch_msg.text if batch_msg.text != "/d" else os.path.splitext(input_msg.document.file_name)[0]

        await editable.edit("**Enter Resolution (e.g., 720):**")
        res_msg = await bot.listen(m.chat.id, timeout=300)
        resolution = res_msg.text

        await editable.edit("**Enter Channel ID (or /d for current chat):**")
        channel_msg = await bot.listen(m.chat.id, timeout=300)
        channel_id = m.chat.id if channel_msg.text == "/d" else int(channel_msg.text)

        if not await validate_channel(bot, channel_id):
            await m.reply_text("**❌ Bot must be admin in the channel!**")
            return

        # Step 3: Process downloads
        await editable.edit("**Starting downloads...**")
        for idx, url in enumerate(links, 1):
            try:
                output_name = f"{str(idx).zfill(3)}_video"
                success = await download_video(url, output_name, resolution)
                if success:
                    caption = (
                        f"**📹 Video {idx}**\n"
                        f"**Batch:** {batch_name}\n"
                        f"**Quality:** {resolution}p\n"
                        f"**By:** {Config.DEFAULT_CHANNEL_NAME}"
                    )
                    await upload_video(bot, channel_id, f"{output_name}.mp4", caption)
            except Exception as e:
                logger.error(f"Error processing {url}: {e}")
                continue

        await m.reply_text("**✅ All downloads completed!**")
    except Exception as e:
        logger.error(f"Master command failed: {e}")
        await m.reply_text(f"**❌ Error:** `{e}`")

# ========== RUN BOT ========== #
if __name__ == "__main__":
    logger.info("Starting bot...")
    bot.run()