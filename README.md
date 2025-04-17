# Telegram Group Management Scripts

Utility scripts for managing Telegram groups using [Telethon](https://github.com/LonamiWebs/Telethon).

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/saltyfacu/tg-purgooor.git
cd tg-purgooor
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure .env

Create a .env file in the project root with:

```javascript
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_PHONE=+1234567890
TELEGRAM_USERNAME=your_telegram_username
```

Get your API_ID and API_HASH from https://my.telegram.org.

## Scripts

### leavooor.py

Leaves groups that match a name pattern.

```bash
python leavooor.py --prefix "Crypto" --match-mode contains --exclude "Crypto News" --dry-run
```

Arguments:

- --prefix: The name to match
- --match-mode: startswith (default) or contains
- --exclude: List of group names to skip
- --dry-run: Simulate leaving without taking action
- --case-sensitive: Optional, defaults to false
- --session: (optional) Defaults to TELEGRAM_USERNAME

---

### purgooor.py

Kicks inactive members from a specific group who haven’t sent a message in the last N days.

```bash
python purgooor.py --group-name "DAO Squad" --days 30 --dry-run
```

Arguments:

- --group-name: Exact group name
- --days: Number of days of inactivity to check (default: 60)
- --dry-run: Only simulate without kicking

---

### listooor.py

Lists all groups you’re currently in, with optional exclusions.

```bash
python listooor.py --exclude "Secret Group" "Test Chat"
```

Arguments:

- --exclude: List of group names to skip
- --session: (optional) Defaults to TELEGRAM_USERNAME

## Safety & Rate Limits

- The leave_groups.py script includes delay and FloodWaitError handling.
- purge_group.py is designed for manual group maintenance, not spamming.
- Always use --dry-run first to preview actions.

## 👥 Credits

Built with ❤️ using [Telethon](https://github.com/LonamiWebs/Telethon).
