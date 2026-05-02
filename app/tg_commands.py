##Telegram Command Interface & Security.
#Allows remote control of the bot directly from the Telegram app. It listens 
#for commands like `/scan` and `/state` and executes them. Crucially, it 
#includes an authentication layer to actively reject any unauthorized users 
#who discover the bot, ensuring only the owner can trigger actions.

import json
from telegram import Update
from telegram.ext import ContextTypes

from app.config import settings
from app.scanner import start_background_scan
from app.state import state

async def check_auth(update: Update) -> bool:
    # Security: Only allow commands from your configured Telegram chat ID
    if str(update.effective_chat.id) != settings.telegram_chat_id:
        return False
    return True

async def handle_ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    await update.message.reply_text("Pong! The AI News Bot is online and monitoring.")

async def handle_state(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    
    # Grab the exact same info the /state web endpoint provides
    data = {
        "last_scan_at": state.data.get("last_scan_at", "Never"),
        "seen_count": len(state.data.get("seen_items", [])),
        "rss_sources": len(settings.rss_sources),
        "scrape_targets": len(settings.scrape_targets),
        "scan_interval_minutes": settings.scan_interval_minutes,
    }
    
    text = json.dumps(data, indent=2)
    # Send it nicely formatted as code block
    await update.message.reply_text(f"<pre>{text}</pre>", parse_mode="HTML")

async def handle_scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    
    # Start in the background to prevent Telegram timeout errors
    res = start_background_scan(force=False)
    
    text = json.dumps(res, indent=2)
    message = (
        f"<b>Scan Triggered</b>\n"
        f"<pre>{text}</pre>\n\n"
        f"<i>Note: The scan is running in the background. Relevant alerts will be sent here automatically when found.</i>"
    )
    await update.message.reply_text(message, parse_mode="HTML")
