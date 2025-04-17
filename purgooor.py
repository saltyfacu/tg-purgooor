import os
import argparse
from datetime import datetime, timedelta
from typing import Dict

import pytz
from dotenv import dotenv_values
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.types import ChatBannedRights, User

# --- Config Loading ---
config = {
    **dotenv_values(".env"),
    **os.environ,
}
api_id = int(config['TELEGRAM_API_ID'])
api_hash = config['TELEGRAM_API_HASH']
phone = config['TELEGRAM_PHONE']
username = config['TELEGRAM_USERNAME']

# --- CLI Parsing ---
parser = argparse.ArgumentParser(description='Purge inactive group members.')
parser.add_argument("--group-name", required=True, help="Exact name of the group to purge")
parser.add_argument("--days", default=60, type=int, help="Number of days of inactivity to consider")
parser.add_argument("--dry-run", action="store_true", help="Only simulate the purge without kicking users")
args = parser.parse_args()

# --- Telegram Client ---
client = TelegramClient(username, api_id, api_hash)

# --- Utility Functions ---
def get_readable_username(user: User) -> str:
    if user.username:
        return user.username
    name = user.first_name or ""
    if user.last_name:
        name += f" {user.last_name}"
    return name or f"[user_id:{user.id}]"

def is_recent_message(msg_date: datetime, cutoff: datetime) -> bool:
    return msg_date >= cutoff

async def ensure_logged_in():
    await client.connect()
    if not await client.is_user_authorized():
        await client.send_code_request(phone)
        try:
            await client.sign_in(phone, input("Enter the code: "))
        except SessionPasswordNeededError:
            await client.sign_in(password=input("Password: "))

async def process_group(dialog, days: int, dry_run: bool):
    cutoff_date = pytz.utc.localize(datetime.utcnow()) - timedelta(days=days)
    messages_by_user: Dict[int, int] = {}
    print(f"Scanning messages in the last {days} days...")

    async for msg in client.iter_messages(dialog):
        if not is_recent_message(msg.date, cutoff_date):
            continue
        sender = await msg.get_sender()
        if sender and isinstance(sender, User):
            messages_by_user[sender.id] = messages_by_user.get(sender.id, 0) + 1

    active_count = len(messages_by_user)
    total_users = 0
    inactive_users = 0

    print("\nChecking participants...")

    async for participant in client.iter_participants(dialog):
        total_users += 1
        if participant.id in messages_by_user:
            continue

        inactive_users += 1
        name = get_readable_username(participant)
        print(f"Kicking {name}... ", end='')

        if dry_run:
            print("DRY RUN")
        else:
            try:
                await client(EditBannedRequest(
                    channel=dialog,
                    participant=participant,
                    banned_rights=ChatBannedRights(
                        until_date=None,
                        view_messages=True
                    )
                ))
                print("KICKED")
            except Exception as err:
                print(f"FAILED: {err}")

    print(f"\nSummary for group: {dialog.name}")
    print(f"Total users: {total_users}")
    print(f"Active: {active_count} ({active_count / total_users:.0%})")
    print(f"Inactive: {inactive_users} ({inactive_users / total_users:.0%})")

# --- Main Entry ---
async def main():
    await ensure_logged_in()
    print("Connected to Telegram.\nSearching for group...")

    async for dialog in client.iter_dialogs():
        if dialog.is_group and dialog.name == args.group_name:
            print(f"✅ Found group: {dialog.name}")
            await process_group(dialog, days=args.days, dry_run=args.dry_run)
            break
    else:
        print(f"❌ Group '{args.group_name}' not found.")

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())