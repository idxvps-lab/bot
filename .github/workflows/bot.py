import os
import re
from collections import defaultdict, deque
from datetime import datetime, timedelta
import discord
from discord.ext import commands
from dotenv import load_dotenv

# -----------------------------
# Bot Info
# -----------------------------
BOT_DESCRIPTION = "🔥 Powered by HemantGamerzYT 🔥"

# -----------------------------
# Load .env config
# -----------------------------
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
SPAM_THRESHOLD = int(os.getenv("SPAM_THRESHOLD", 5))  # messages
SPAM_WINDOW = int(os.getenv("SPAM_WINDOW", 10))       # seconds
TIMEOUT_DURATION = 60                                 # 1 minute for everything

# -----------------------------
# Intents setup
# -----------------------------
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    description=BOT_DESCRIPTION
)

# -----------------------------
# Data storage
# -----------------------------
user_messages = defaultdict(lambda: deque())
link_pattern = re.compile(r"https?://|www\.", re.IGNORECASE)

# -----------------------------
# Expanded bad words list
# -----------------------------
bad_words = [
    "gand",
    "land",
    "teri maa ke gand",
    "teri maa ke land",
    "bc",
    "bhosdike",
    "mc",
    "chutiya",
    "madarchod",
    "harami",
    "randi",
    "bkl",
    "lund",
    "behenchod",
    "gandu",
    "randi ka baccha",
    "saala",
    "haramkhor",
    "bhanchod"
]

# -----------------------------
# Helpers
# -----------------------------
def is_exempt(member: discord.Member):
    return member.guild_permissions.administrator or member.guild_permissions.manage_messages

def contains_badword(text: str):
    text_lower = text.lower()
    return any(word in text_lower for word in bad_words)

async def notify_owner(guild: discord.Guild, member: discord.Member, reason: str):
    """DM the server owner when someone is timed out."""
    try:
        owner = guild.owner
        if owner:
            msg = (
                f"🚨 **Timeout Notification** 🚨\n"
                f"**User:** {member} ({member.id})\n"
                f"**Reason:** {reason}\n"
                f"**Duration:** 1 minute\n"
                f"**Server:** {guild.name}\n"
                f"👑 Powered by HemantGamerzYT"
            )
            await owner.send(msg)
    except Exception as e:
        print(f"⚠️ Could not notify owner: {e}")

# -----------------------------
# Events
# -----------------------------
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    print(f"📜 Description: {BOT_DESCRIPTION}")
    await bot.change_presence(
        activity=discord.Game(name="Moderating Server | Powered by HemantGamerzYT")
    )

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.guild:
        return

    member = message.author
    if is_exempt(member):
        return await bot.process_commands(message)

    guild = message.guild

    # 🚫 BAD WORD FILTER
    if contains_badword(message.content):
        try:
            await message.delete()
            await message.channel.send(
                f"{member.mention}, bad words are not allowed! 😡 (Timed out for 1 minute)",
                delete_after=6
            )
            await member.timeout(
                discord.utils.utcnow() + timedelta(seconds=TIMEOUT_DURATION),
                reason="Used bad words"
            )
            await notify_owner(guild, member, "Used bad words")
            print(f"Timed out {member} for bad words (1 min)")
        except Exception as e:
            print(f"Failed to timeout {member} for bad words: {e}")
        return

    # 🔗 ANTI-LINK FILTER
    if link_pattern.search(message.content):
        try:
            await message.delete()
            await message.channel.send(
                f"{member.mention}, links are not allowed! 🚫 (Timed out for 1 minute)",
                delete_after=6
            )
            await member.timeout(
                discord.utils.utcnow() + timedelta(seconds=TIMEOUT_DURATION),
                reason="Sent a link"
            )
            await notify_owner(guild, member, "Sent a link")
            print(f"Timed out {member} for link (1 min)")
        except Exception as e:
            print(f"Failed to timeout {member}: {e}")
        return

    # 💬 ANTI-SPAM DETECTION
    now = datetime.utcnow()
    msgs = user_messages[member.id]
    msgs.append(now)

    # Keep only messages within SPAM_WINDOW
    while msgs and (now - msgs[0]).total_seconds() > SPAM_WINDOW:
        msgs.popleft()

    if len(msgs) >= SPAM_THRESHOLD:
        try:
            await member.timeout(
                discord.utils.utcnow() + timedelta(seconds=TIMEOUT_DURATION),
                reason="Spamming messages"
            )
            await message.channel.send(
                f"⏰ {member.mention} has been timed out for 1 minute for spamming. 🔇",
                delete_after=8
            )
            await notify_owner(guild, member, "Spamming messages")
            print(f"Timed out {member} for spam (1 min)")
            msgs.clear()
        except Exception as e:
            print(f"Failed to timeout {member}: {e}")

    await bot.process_commands(message)

# -----------------------------
# Command Example
# -----------------------------
@bot.command(name="about")
async def about(ctx):
    """Show bot description"""
    await ctx.send(f"🤖 {BOT_DESCRIPTION}")

# -----------------------------
# Run bot
# -----------------------------
bot.run(TOKEN)