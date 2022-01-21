from telethon import TelegramClient
import csv

api_id = ''
api_hash = ''
      
with TelegramClient('anon', api_id, api_hash) as client:
  with open('telegram.csv', 'w', encoding='UTF8', newline='') as f:
    writer = csv.writer(f)
    for dialog in client.iter_dialogs():
      if not dialog.is_group:
        continue
      if "yfi" not in dialog.name.lower() and "yearn" not in dialog.name.lower():
        continue
      if dialog.name == 'yearn.finance (YFI)' or dialog.name == 'yearn.social':
        continue
      row = [dialog.name]
      print(dialog.name, 'has ID', dialog.id)
      try:
        for user in client.iter_participants(dialog):
          username = ""
          try:
            if user.username:
              username = user.username
            else:
              if user.first_name:
                  username = user.first_name
              if user.last_name:
                  username = f'{username} {user.last_name}'
            print('\t',username)
            row.append(username)
          except:
            attrs = vars(user)
            print('error getting username')
            print(', '.join("%s: %s" % item for item in attrs.items()))
            raise
      except:
        attrs = vars(dialog)
        print('error iterating dialog participants')
        print(', '.join("%s: %s" % item for item in attrs.items()))
        raise
      if len(row) > 1:
        writer.writerow(row)