import asyncio
from datetime import datetime
from time import sleep
from json import dumps, loads
import httpx
from action import *
from dotenv import load_dotenv
import os 

load_dotenv('.env')

host = os.getenv("ALLOWED_HOSTS")
api = host + 'api/v1/'

print('Command startchek run successfully.')
dict_of_actions = {'datetime_telegram_alert': datetime_telegram_alert,
                    'telegram_alert_with_periodicity': telegram_alert_with_periodicity,
                    'telegram_daily_message': telegram_daily_message,
                    'daily_system_task': daily_system_task
                    }

async def check():
    while True:
        datetime_now = datetime.now()
        date = datetime_now.date()
        time = datetime_now.time()
        async with httpx.AsyncClient() as client:
            response = await client.get(api+f'pertasks/?date={date}&time={time}')
        if response.status_code == 200:
            tasks = response.json()
            if len(tasks):
                for task in tasks:
                    kwargs = task.get('kwargs')
                    kwargs = loads(kwargs) if kwargs else {}
                    await dict_of_actions[task.get('action')](**kwargs)
                    async with httpx.AsyncClient() as client:
                        response = await client.delete(api+f'del_pertask/{task.get("id")}')
        sleep(30)

if __name__ == '__main__':
  loop = asyncio.get_event_loop()
  loop.run_until_complete(check())
  loop.close()