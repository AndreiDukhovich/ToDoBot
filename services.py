from typing import Union
import os
from aiogram import Bot
from aiogram import types
from datetime import datetime, timedelta 
from markups import *
from datetime import datetime as dt, date as dateClass, time as timeClass
from dotenv import load_dotenv
from aiogram.dispatcher.filters.state import State
import httpx 

load_dotenv('.env')

host = os.getenv("ALLOWED_HOSTS")
api = host + 'api/v1/'
bot = Bot(token=os.getenv('BOT_TOKEN'))


async def send_message_by_telegram(text:str, tele_id:int, markup=None) -> None:
    await bot.send_message(tele_id, text, parse_mode='HTML', reply_markup=markup)

async def send_general_message(id: int) -> None:
    text = 'Чем могу помочь?'
    await send_message_by_telegram(text, id, general_keybord)

async def cancel_entre(text: str, id: int, state: State):
    await bot.send_message(id, text, reply_markup=remove_buttom)
    await state.finish()
    await send_general_message(id)

async def correct_type(answer: str) -> bool:
    if answer.lower() in ['по дате и времени', 
                  'по времени с периодом',
                  'только по дате']:
        return True
    return False

async def get_task_type(task: dict) -> str:
    if task.get('date', None) and task.get('time', None) and not task.get('period', None):
        return 'времени'
    if task.get('date', None) and not task.get('time', None):
        return 'дате'
    return 'периодом'

async def correct_date(date: str) -> bool:
    date = date.split('.')
    if len(date) != 3:
        return False
    for i in range(3):
        if i == 0:
            if len(date[i]) != 2:
                return False
            if 1 > int(date[i]) or int(date[i]) > 31:
                return False
            continue
        if i == 1:
            if len(date[i]) != 2:
                return False
            if 1 > int(date[i]) or int(date[i]) > 12:
                return False
            continue
        if i == 2:
            if len(date[i]) != 4:
                return False
    return True

async def correct_time(time: str) -> bool: 
    time = time.split(':')
    if len(time) != 2:
        return False
    for i in range(3):
        if i == 0:
            if len(time[i]) != 2:
                return False
            if 0 > int(time[i]) or int(time[i]) > 24:
                return False
            continue
        if i == 1:
            if len(time[i]) != 2:
                return False
            if 0 > int(time[i]) or int(time[i]) > 60:
                return False
            continue
    return True


async def correct_answer_about_important(answer: str) -> bool:
    if answer.lower() == 'нет' or answer.lower() == 'да':
        return True
    return False

async def correct_anwer_about_periodicity(answer: str) -> bool:
    if answer.lower() in ['каждый день', 'по будням', 'по выходным']:
        return True
    return False

async def get_next_valid_date(date: dateClass, period: str) -> dateClass:
    weekday_and_per_ratio = {
            'ever': range(7),
            'wd': range(5),
            'we': [5, 6]
        }
    for i in range(1, 7):
        if date.weekday() in weekday_and_per_ratio[period]:
            return date
        date += timedelta(days=1)

async def get_data_keybord(model: str) -> ReplyKeyboardMarkup:
    if model == 'task':
        return date_action_keybord
    else:
        return date_archive_keybord


async def send_task_or_archive_data(message: types.Message, model: str) -> bool:
    date = await get_date_from_string(message.text)
    if date: 
        async with httpx.AsyncClient() as client:
            response = await client.get(api+f'tele_user/{message.chat.id}')
            if response.status_code != 200:
                text = 'Ой, что-то пошло не так, повторите попытку позже.'
                await send_message_by_telegram(text, id, markup=remove_buttom)
                return
            user_id = response.json().get('user')
        there_are_tasks = await send_message_by_telegram_with_tasks_by_date(user_id, message.chat.id, date, model=model)
        return there_are_tasks
    else:
        await send_message_by_telegram('Неверный формат, попробуйте снова', message.chat.id, await get_data_keybord(model))
    


async def get_date_from_string(date: str | dateClass) -> str|bool:
    today = datetime.now().date()
    if date == 'Сегодня':
        return today
    elif date == 'Завтра':
        return today + timedelta(days=1)
    elif date == 'Все даты':
        return 'all_date' 
    else:
        if await correct_date(date):
            return str(date)
        else: 
            return False

async def date_format(date: datetime | str) -> str:
    '''Date conversion from %y%m%d to %d%m%y'''
    if isinstance(date, dateClass):
        date = str(date)
    return ".".join(reversed(date.split("-")))

async def send_message_by_telegram_with_tasks_by_date(user_id: int, tele_id: int, date: datetime|str, model='task', is_auto_mess=False) -> bool:
    if model == 'archive':
        markup = choose_archive_keybord
    else:
        markup = choose_task_keybord
    date_tasks = await get_task_data_based_on_date(user_id=user_id, tele_id=tele_id, date=date, model=model)
    date_text, text, there_are_tasks = await get_message_text_for_base_on_date_message(tasks=date_tasks, date=date, model=model)
    if there_are_tasks:
        await send_message_by_telegram(date_text, tele_id, remove_buttom)
    else:
        if is_auto_mess:
            markup = None
        else:
            markup = await get_data_keybord(model)
    await send_message_by_telegram(text, tele_id, markup)
    return there_are_tasks

async def get_message_text_for_base_on_date_message(tasks: dict, date: datetime|str, model='task') -> tuple[str, str, bool]:
    '''Get date text, text about tasks and there are any tasks for this date'''
    today = datetime.now().date()
    link = f'{host}task/'
    tomorrow = today + timedelta(days=1)
    tasks_text = ''
    date_text = ''
    if date == today:
        date_str = "Сегодня"
    elif date == tomorrow:
        date_str = "Завтра"
    elif date == 'all_date':
        date_str = 'За все время'
    else:
        date_str = date
    if len(tasks):
        if model == 'task':
            date_text = date_str + ' вы хотели сделать:\n'
        else:
            date_text = date_str + ' вы сделали:\n'
        i = 1
        for task in tasks:
            tasks_text += f'{i}. <a href="{link}{task.get("id")}">{task.get("title")}</a>;\n'
            i += 1
        tasks_text = tasks_text[:-2]+'.'
        there_are_tasks = True
    else:
        tasks_text = f'На {date_str.lower()} ничего нет.'
        there_are_tasks = False
    return date_text, tasks_text, there_are_tasks

async def get_task_data_based_on_date(user_id: int, tele_id: int, date: dt|str, model='task') -> dict:
    model += 's/'
    if date == 'all_date':
        model += f'?id={user_id}'
    else:
        date = await date_format(date)
        model += f'?id={user_id}&date={date}'
    async with httpx.AsyncClient() as client:
        response = await client.get(api+f'{model}')
        if response.status_code != 200:
                text = 'Ой, что-то пошло не так, повторите попытку позже.'
                await send_message_by_telegram(text, tele_id, markup=remove_buttom)
                return
        task_data = response.json()
    return task_data
      
        
async def is_correct_num(num, task_list: list) -> bool:
    if num.isdigit() and int(num)  <= len(task_list):
        return True
    else: 
        return False  

                 
async def send_message_about_task(num: int | str, data: dict, id: int) -> dict:
    num = int(num)
    link = f'{host}task/'
    task_id = data.get('tasks_id')[num-1]
    model = data.get('model')
    if model == 'task':
        async with httpx.AsyncClient() as client:
            response = await client.get(api+f'task/{task_id}')
            if response.status_code != 200:
                text = 'Ой, что-то пошло не так, повторите попытку позже.'
                await send_message_by_telegram(text, id, markup=remove_buttom)
                return
            task_data = response.json()
        if task_data.get('period', None):
            markup = task_with_per_complete_buttom
        else:
            markup = task_no_per_complete_buttom
    else:
        async with httpx.AsyncClient() as client:
            response = await client.get(api+f'archive/{task_id}')
            if response.status_code != 200:
                text = 'Ой, что-то пошло не так, повторите попытку позже.'
                await send_message_by_telegram(text, id, markup=remove_buttom)
                return
            task_data = response.json()
        markup = archive_action_keybord
    text = f'{task_data["topic"]}\n<a href="{link}{task_id}">{task_data["title"]}</a>\n'
    text += task_data['discription'] + '\n' if task_data['discription'] else '\n'
    text += await date_format(task_data['date']) + ' ' if task_data['date'] else ""
    text += ':'.join(task_data['time'].split(':')[:2]) if task_data['time'] else ""
    await send_message_by_telegram(text, id, markup=markup)
    return task_data

