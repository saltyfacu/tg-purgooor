import os
import argparse
from dotenv import dotenv_values
from telethon.sync import TelegramClient
from telethon.tl.types import Channel, Chat
import asyncio

# Load config
config = {
    **dotenv_values(".env"),
    **os.environ,
}

def get_config_value(key, required=True):
    value = config.get(key)
    if required and not value:
        raise ValueError(f"Missing required config value: {key}")
    return value

def parse_args(default_session_name):
    parser = argparse.ArgumentParser(description='List Telegram groups for the logged-in user.')
    parser.add_argument('--exclude', nargs='*', default=[], help='Group names to exclude (exact match)')
    parser.add_argument('--session', default=default_session_name, help='Session file name (default: TELEGRAM_USERNAME)')
    return parser.parse_args()

async def list_groups(api_id, api_hash, excludes, session_name):
    client = TelegramClient(session_name, api_id, api_hash)
    await client.start()
    print("Logged in successfully.\n")

    excludes_lower = set(name.lower() for name in excludes)
    groups = []

    async for dialog in client.iter_dialogs():
        entity = dialog.entity
        name = dialog.name or ""

        if isinstance(entity, (Channel, Chat)) and dialog.is_group:
            if name.lower() not in excludes_lower:
                groups.append(name)

    if not groups:
        print("No groups found.")
    else:
        print(f"You are in the following groups:\n")
        for g in sorted(groups, key=str.lower):
            print(f"• {g}")

        print(f"\nTotal groups (after exclusions): {len(groups)}")

    await client.disconnect()

if __name__ == '__main__':
    api_id = int(get_config_value('TELEGRAM_API_ID'))
    api_hash = get_config_value('TELEGRAM_API_HASH')
    default_session = get_config_value('TELEGRAM_USERNAME', required=False) or 'session_name'

    args = parse_args(default_session)

    asyncio.run(list_groups(
        api_id=api_id,
        api_hash=api_hash,
        excludes=args.exclude,
        session_name=args.session
    ))