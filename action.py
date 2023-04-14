from services import send_message_by_telegram, send_message_by_telegram_with_tasks_by_date
from datetime import time as tm, datetime as dt, timedelta
from markups import task_no_per_complete_buttom, task_with_per_complete_buttom
import os
from dotenv import load_dotenv
import httpx 
from json import dumps

load_dotenv('.env')

host = os.getenv("ALLOWED_HOSTS")
api = host + 'api/v1/'


async def datetime_telegram_alert(task_id: str, user: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(api+f'task/{task_id}')
    if response.status_code == 200:
        task = response.json()
        text = await _get_text_for_message(task)
        await send_message_by_telegram(text=text, tele_id=user, markup=task_no_per_complete_buttom)

async def telegram_alert_with_periodicity(task_id: str, user: str, period: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(api+f'task/{task_id}')
    if response.status_code == 200:
        task = response.json()
        text = await _get_text_for_message(task)
        await send_message_by_telegram(text=text, tele_id=user, markup=task_with_per_complete_buttom)
        if period != 'once':
            async with httpx.AsyncClient() as client:
                await client.get(api+f'task/{task_id}?createnewdate=True')


async def telegram_daily_message(time: str, user_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(api+f'tele_user/?user_id={user_id}')
    if response.status_code == 200:
        person = response.json()
        time = tm.fromisoformat(time)
        await send_message_by_telegram_with_tasks_by_date(user_id=user_id,
                                                    tele_id=person.get('tele_id'), 
                                                    date=dt.now().date(),
                                                    is_auto_mess=True)
        await _create_daily_periodic_task(time=time, user_id=user_id)

async def daily_system_task():
    today = dt.now().date()
    async with httpx.AsyncClient() as client:
        response = await client.get(api+f'tasks/?date={today}')
    if response.status_code == 200:
        unfulfilled_task = response.json()
        for task in unfulfilled_task:
            if not task.get('period') in ['', None]:
                async with httpx.AsyncClient() as client:
                    await client.get(api+f'task/{task.get("id")}?createnewdate=True')
                    await client.delete(api+f'task/{task.get("id")}')

        async with httpx.AsyncClient() as client:
            await client.post(api+f'pertasks/', 
                            content={'name': 'daily_system_task',
                                'time': tm.fromisoformat('00:01'),
                                'date': today+timedelta(days=1),
                                'action': 'daily_system_task',
                                'kwargs': None})
    

async def _get_text_for_message(task: dict) -> str:
    link = f'https://todobydukhovich.fly.dev/task/{task.get("id")}'
    text = f'Вы хотели {task.get("title")}\n'
    text += f'<a href="{link}">Подробнее</a>'
    return text

async def _create_daily_periodic_task(time: tm, user_id: int) -> None: 
    date = dt.now().date()
    if dt.now().time() > time:
        date += timedelta(days=1)
    async with httpx.AsyncClient() as client:
        await client.post(api+f'pertasks/', 
                        data={'name': user_id,
                              'date': date,
                              'time': time,
                              'period': 'ever',
                              'action': 'telegram_daily_message',
                              'kwargs': dumps({"user_id": user_id,
                                               'time': str(time)})})
