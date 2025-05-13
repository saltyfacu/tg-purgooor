import os
import argparse
import asyncio
from dotenv import dotenv_values
from telethon.sync import TelegramClient
from telethon.tl.types import Channel, Chat
from telethon.errors import FloodWaitError

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
    parser = argparse.ArgumentParser(description='Leave Telegram groups by name filter.')
    parser.add_argument('--prefix', required=True, help='String to match in group name')
    parser.add_argument('--match-mode', choices=['startswith', 'contains'], default='startswith',
                        help='Match mode: "startswith" or "contains" (default: startswith)')
    parser.add_argument('--exclude', nargs='*', default=[], help='Group names to exclude (exact match)')
    parser.add_argument('--dry-run', action='store_true', help='Only show the groups that would be left')
    parser.add_argument('--case-sensitive', action='store_true', help='Use case-sensitive name matching')
    parser.add_argument('--session', default=default_session_name, help='Session file name (default: TELEGRAM_USERNAME)')
    return parser.parse_args()

def matches(name, pattern, mode, case_sensitive=False):
    if not case_sensitive:
        name = name.lower()
        pattern = pattern.lower()
    if mode == 'startswith':
        return name.startswith(pattern)
    elif mode == 'contains':
        return pattern in name
    return False

async def main(api_id, api_hash, prefix, match_mode, excludes, dry_run, session_name, case_sensitive):
    client = TelegramClient(session_name, api_id, api_hash)
    await client.start()
    print("Logged in successfully.\n")

    excludes_set = set(name if case_sensitive else name.lower() for name in excludes)
    count = 0
    scanned_dialogs = 0
    scanned_groups = 0

    offset_id = 0
    offset_date = None
    batch_limit = 20  # tighter pagination

    while True:
        dialogs = await client.get_dialogs(limit=batch_limit, offset_date=offset_date, offset_id=offset_id)
        if not dialogs:
            break

        scanned_dialogs += len(dialogs)

        for dialog in dialogs:
            entity = dialog.entity
            name = dialog.name or ""
            compare_name = name if case_sensitive else name.lower()

            if isinstance(entity, (Channel, Chat)) and dialog.is_group:
                scanned_groups += 1
                if matches(name, prefix, match_mode, case_sensitive) and compare_name not in excludes_set:
                    count += 1
                    if dry_run:
                        print(f"[DRY RUN] Would leave group: {name}")
                    else:
                        print(f"Leaving group: {name}")
                        try:
                            await client.delete_dialog(entity)
                            await asyncio.sleep(2)
                        except FloodWaitError as e:
                            print(f"Flood wait triggered. Sleeping for {e.seconds} seconds...")
                            await asyncio.sleep(e.seconds)
                        except Exception as e:
                            print(f"Failed to leave {name}: {e}")

        print(f"Scanned {scanned_dialogs} dialogs, checked {scanned_groups} groups so far...")

        last = dialogs[-1].message
        offset_id = last.id
        offset_date = last.date

    if count == 0:
        print("No matching groups found.")
    else:
        print(f"\nTotal groups {'matched' if dry_run else 'left'}: {count}")

    await client.disconnect()

if __name__ == '__main__':
    api_id = int(get_config_value('TELEGRAM_API_ID'))
    api_hash = get_config_value('TELEGRAM_API_HASH')
    default_session = get_config_value('TELEGRAM_USERNAME', required=False) or 'session_name'

    args = parse_args(default_session)

    asyncio.run(main(
        api_id=api_id,
        api_hash=api_hash,
        prefix=args.prefix,
        match_mode=args.match_mode,
        excludes=args.exclude,
        dry_run=args.dry_run,
        session_name=args.session,
        case_sensitive=args.case_sensitive
    ))