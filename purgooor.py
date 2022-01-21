from datetime import *
import pytz
import argparse
import os
from dotenv import dotenv_values
from telethon import TelegramClient
from telethon import errors
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.types import ChatBannedRights

parser = argparse.ArgumentParser(description='The purgooooor!')
parser.add_argument("--group", required=True, type=str, help="The name of the group you want to purge")
parser.add_argument("--days", default=60 , type=int, help="Number of days to consider")
parser.add_argument("--dryrun", action="store_true", help="Do a dry run. No kicking will be done")

args = parser.parse_args()

# Load config
config = {
    **dotenv_values(".env"),  # load .env vars
    **os.environ,  # override loaded values with environment variables
}

api_id = config['TELEGRAM_API_ID']
api_hash = config['TELEGRAM_API_HASH']
phone = config['TELEGRAM_PHONE']
username = config['TELEGRAM_USERNAME']

group = args.group
dry_run = args.dryrun
delta_in_days = args.days

client = TelegramClient(username, api_id, api_hash)

def get_username(user):
  username = ""

  if user.username:
    username = user.username
  else:
    if user.first_name:
        username = user.first_name
    if user.last_name:
        username = f'{username} {user.last_name}'
  
  return username

async def main(): 
  await client.connect()

  # I make sure I'm authorized
  if not await client.is_user_authorized():
      client.send_code_request(phone)
      try:
          client.sign_in(phone, input('Enter the code: '))
      except SessionPasswordNeededError:
          client.sign_in(password=input('Password: '))
  
  print('Connected to Telegram')
  print(f'Looking for {group}... ', end = '')
  messages = {}
  message_count = {}
  
  total_users = 0
  inactive_users = 0
  active_users = 0

  async for dialog in client.iter_dialogs():
    if dialog.is_group and dialog.name == group:

      group_participants = await client.get_participants(dialog)

      # For some reason there are clones with 0 participants, idk
      if group_participants == 0:
        continue

      print('FOUND')
      print('Checking messages...')

      async for msg in client.iter_messages(dialog):
        # if it's an old message, ignore it
        oldest = pytz.utc.localize(datetime.now()) - timedelta(days = delta_in_days)
        if msg.date < oldest:
          continue

        username = ""
        user = await msg.get_sender()

        try:
          if user:
            username = user.username
          else:
            if user.first_name:
                username = user.first_name
            if user.last_name:
                username = f'{username} {user.last_name}'
          
          messages[username] = messages.get(username, 0) + 1
          message_count[user.id] = message_count.get(user.id, 0) + 1

        except BaseException as err:
          print(f"I was not expecting this {err=}, {type(err)=}")

      active_users = len(message_count)

      async for participant in client.iter_participants(dialog):
        total_users += 1

        if message_count.get(participant.id):
          continue
        else:
          inactive_users += 1
          print(f'Kicking {get_username(participant)}... ', end = '')
          
          if dry_run:
            print('DRY')
          else:
            try:
              await client(EditBannedRequest(dialog, participant, ChatBannedRights(
                until_date=None,
                view_messages=True
              )))
            except BaseException as err:
              print(f'FAILED {err=}')
            else:
              print("KICKED")
    
      active_perc = active_users / total_users
      inactive_perc = inactive_users / total_users

      print(f'\nTotal: {total_users}')
      print(f'Active: {active_users} ({active_perc:.0%})')
      print(f'Inactive: {inactive_users} ({inactive_perc:.0%})')

      break # only run for 1 group
      
with client:
    client.loop.run_until_complete(main())