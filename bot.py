#!/usr/bin/env python3
"""
☠️  Blighted Scroll Bot — single-message edition   (python-telegram-bot ≥ 22)

• One living scroll per chat (group or DM).
• Reply to it to append a bullet.
• /list  drags the scroll to the bottom (no duplicates).
• /clear erases every line.
"""

import json, os, sys
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters,
)
from telegram.error import BadRequest, TelegramError

# ─── config ──────────────────────────────────────────────────────────
DATA_FILE = Path("data.json")
load_dotenv()

TOKEN     = os.getenv("BOT_TOKEN") or sys.exit("❌  BOT_TOKEN missing")
AUTO_DEL  = os.getenv("DELETE_REPLIES", "true").lower() in {"true", "1", "yes"}

SKULL     = "💀"
EMPTY_MSG = f"{SKULL} *Blighted Scroll*\n"

# ─── persistence ────────────────────────────────────────────────────
def _load() -> Dict[str, Dict]:
    return json.loads(DATA_FILE.read_text()) if DATA_FILE.exists() else {}

def _save(db: Dict[str, Dict]): DATA_FILE.write_text(json.dumps(db, indent=2))

db = _load()            # {chat_id: {"items": [], "anchor": int|None}}

def bucket(cid: int) -> Dict:
    key = str(cid)
    if key not in db:
        db[key] = {"items": [], "anchor": None}
    # migrate legacy keys if needed
    row = db[key]
    if "anchor" not in row:
        row["anchor"] = row.pop("msg_id", None)
    if "items" not in row:
        row["items"] = []
    return row

# ─── rendering & anchor maintenance ─────────────────────────────────
def render(items: List[str]) -> str:
    if not items:
        return EMPTY_MSG
    body = "\n".join(f"• {t}" for t in items)
    return f"{SKULL} *Blighted Scroll*\n{body}"

async def replace_scroll(
    ctx: ContextTypes.DEFAULT_TYPE,
    cid: int,
    new_text: str,
) -> int:
    """
    Post new scroll, delete the previous one if it exists,
    return new message_id.
    """
    row = bucket(cid)
    try:
        if row["anchor"]:
            await ctx.bot.delete_message(cid, row["anchor"])
    except TelegramError:
        # can't delete (e.g. message already gone) — ignore
        pass

    msg = await ctx.bot.send_message(
        cid, new_text, parse_mode="Markdown", disable_notification=True
    )
    row["anchor"] = msg.message_id
    _save(db)
    return msg.message_id

# ─── command handlers ───────────────────────────────────────────────
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    await replace_scroll(ctx, cid, render(bucket(cid)["items"]))
    await update.effective_chat.send_message(
        "*Scroll awakened.*\n"
        "Reply to it to stain new words.\n"
        "`/list`  — drag scroll down\n"
        "`/clear` — purge ink",
        parse_mode="Markdown",
    )

async def cmd_list(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    row = bucket(cid)
    await replace_scroll(ctx, cid, render(row["items"]))

async def cmd_clear(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    row = bucket(cid)
    row["items"].clear()
    await replace_scroll(ctx, cid, render(row["items"]))
    await update.message.reply_text("Scroll wiped 🩸")

# ─── reply handler ──────────────────────────────────────────────────
async def on_reply(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    m = update.message
    if not (m and m.reply_to_message):
        return

    cid  = m.chat.id
    row  = bucket(cid)
    text = (m.text or "").strip()
    if not text:
        return

    # only accept replies to current anchor
    if m.reply_to_message.message_id != row["anchor"]:
        return

    row["items"].append(text[:120])
    await replace_scroll(ctx, cid, render(row["items"]))

    if AUTO_DEL:
        await m.delete()

# ─── bootstrap ──────────────────────────────────────────────────────
def main() -> None:
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("list",   cmd_list))
    app.add_handler(CommandHandler("clear",  cmd_clear))
    app.add_handler(MessageHandler(filters.TEXT & filters.REPLY, on_reply))

    app.run_polling(close_loop=True)

if __name__ == "__main__":
    main()