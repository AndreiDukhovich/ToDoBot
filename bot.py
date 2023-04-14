from aiogram import Bot, types, Dispatcher, executor
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import logging
from aiogram.dispatcher.filters.state import State, StatesGroup
import os
from services import *
from datetime import datetime, timedelta
from markups import cancel_buttom, remove_buttom, periodicity_buttom, task_type
import httpx
from dotenv import load_dotenv
from json import dumps

load_dotenv('.env')
logging.basicConfig(level=logging.INFO)

dp = Dispatcher(bot)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class TaskForm(StatesGroup):
    type = State()
    topic = State()
    title = State()
    discription = State()
    date = State()
    time = State()
    periodicity = State()
    important = State()
    task_id = State()

class GetDataState(StatesGroup):
    date = State()
    number = State()
    model = State()
    tasks_id = State()


class ActionWithTask(StatesGroup):
    action = State()


@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    async with httpx.AsyncClient() as client:
        response = await client.get(api+f'tele_user/{message.chat.id}')
        if response.status_code != 200:
            text = 'Ой, что-то пошло не так, повторите попытку позже.'
            await send_message_by_telegram(text, id, markup=remove_buttom)
            return
        tele_user = response.json().get('tele_id', None)
    if tele_user:
        await bot.send_message(message.chat.id, 'Привет. Я рад, что вы вернулись.')
        await send_general_message(message.chat.id)
    else:
        link_to_bind = types.InlineKeyboardMarkup()
        link = types.InlineKeyboardButton('Привязать Telegram', url=f'{host}accounts/telegram/{message.chat.id}')
        link_to_bind.add(link)
        await bot.send_message(message.chat.id, 'Привет. Я помогу вам выполнить то, что вы запланировали. Но для начала привяжите свой Telegram к основному аккуанту.',
                        reply_markup=link_to_bind)


@dp.message_handler(commands=["unlink"])
async def unlink_account(message: types.Message):
    async with httpx.AsyncClient() as client:
        response = await client.get(api+f'tele_user/{message.chat.id}')
        if response.status_code != 200:
            text = 'Ой, что-то пошло не так, повторите попытку позже.'
            await send_message_by_telegram(text, id, markup=remove_buttom)
            return
        is_delete = response.json().get('tele_id', None)
    if is_delete:
        async with httpx.AsyncClient() as client:
            await client.delete(api+f'tele_user/{message.chat.id}')
            if response.status_code not in [204, 200]:
                text = 'Ой, что-то пошло не так, повторите попытку позже.'
                await send_message_by_telegram(text, message.chat.id, markup=remove_buttom)
                return
        text = 'Ваш телеграм успешно отвязан. Что бы привязать телеграм к аккаунту выполните команду /start'
    else:
        text = 'Ваш телеграм не был привязан к аккаунту.'
    await bot.send_message(message.chat.id, text)


@dp.message_handler(commands=["createtask"])
async def start_create(message: types.Message, state: FSMContext):
    text = 'Вы перешли в создание задач. Выберете тип задачи из предложенного списка.'
    await bot.send_message(message.chat.id, text, reply_markup=task_type)
    await state.set_state(TaskForm.type.state)

@dp.message_handler(commands=["sendgenmess"])
async def start_create(message: types.Message):
    await send_general_message(message.chat.id)
    


@dp.message_handler(state=TaskForm.type)   
async def set_type(message: types.Message, state: FSMContext):
    if message.text == 'Отмена':
        text = 'Отмена создания задачи'
        await cancel_entre(text, message.chat.id, state)
        return 
    if not await correct_type(message.text):
        await bot.send_message(message.chat.id, 'Неверный ввод. Попробуйте снова')
        return 
    await state.update_data(type=message.text.split(' ')[-1])
    text = 'Выберете тему задачи из предложенного списка.'
    topic_buttom = types.ReplyKeyboardMarkup(resize_keyboard=True)
    topics = tuple((item['topic'] for item in httpx.get(api+'topic/').json()))
    topic_buttom.add(*(types.KeyboardButton(topic) for topic in topics))
    topic_buttom.add(types.KeyboardButton('Отмена'))
    await bot.send_message(message.chat.id, text, reply_markup=topic_buttom)
    await state.set_state(TaskForm.topic.state)

@dp.message_handler(state=TaskForm.topic)   
async def set_topic(message: types.Message, state: FSMContext):
    if message.text == 'Отмена':
        text = 'Отмена создания задачи'
        await cancel_entre(text, message.chat.id, state)
        return 
    topics = tuple((item['topic'] for item in httpx.get(api+'topic/').json()))
    if message.text not in topics:
        text = 'Не верная тема задачи. Попробуйте занова'
        await bot.send_message(message.chat.id, text)
        return
    text = 'Введите название задачи'
    await state.update_data(topic=message.text)
    await bot.send_message(message.chat.id, text, reply_markup=cancel_buttom)
    await state.set_state(TaskForm.title.state)

@dp.message_handler(state=TaskForm.title) 
async def set_name(message: types.Message, state: FSMContext):
    if message.text == 'Отмена':
        text = 'Отмена создания задачи'
        await cancel_entre(text, message.chat.id, state)
        return
    text = 'Введите описание задачи'
    await state.update_data(title=message.text)
    await bot.send_message(message.chat.id, text, reply_markup=cancel_buttom)
    await state.set_state(TaskForm.discription.state)

@dp.message_handler(state=TaskForm.discription) 
async def set_disctiption(message: types.Message, state: FSMContext):
    if message.text == 'Отмена':
        text = 'Отмена создания задачи'
        await cancel_entre(text, message.chat.id, state)
        return
    data = await state.get_data()
    task_id = data.get('task_id', None)
    if task_id:
        async with httpx.AsyncClient() as client:
            response = await client.get(api+f'task/{task_id}')
            if response.status_code != 200:
                text = 'Ой, что-то пошло не так, повторите попытку позже.'
                await send_message_by_telegram(text, id, markup=remove_buttom)
                return
        task_data = response.json()
        await state.update_data(type=await get_task_type(task_data), **task_data)
    else:
        await state.update_data(discription=message.text)
    data = await state.get_data()
    if data['type'] in ['дате', 'времени']:
        text = 'Введите дату выполнения задачи. Пример: 01.01.2000'
        await bot.send_message(message.chat.id, text, reply_markup=cancel_buttom)
        await state.set_state(TaskForm.date.state)
        return
    text = 'Введите время выполнения задачи. Пример: 12:52'
    await bot.send_message(message.chat.id, text, reply_markup=cancel_buttom)
    await state.set_state(TaskForm.time.state)


@dp.message_handler(state=TaskForm.date) 
async def set_date(message: types.Message, state: FSMContext):
    if message.text == 'Отмена':
        text = 'Отмена создания задачи'
        await cancel_entre(text, message.chat.id, state)
        return
    if not await correct_date(message.text):
        await bot.send_message(message.chat.id, 'Неверный формат. Попробуйте снова')
        return 
    await state.update_data(date=datetime.strptime(message.text, "%d.%m.%Y").date())
    data = await state.get_data()
    if data['type'] == 'времени':
        text = 'Введите время выполнения задачи. Пример: 12:52'
        await bot.send_message(message.chat.id, text, reply_markup=cancel_buttom)
        await state.set_state(TaskForm.time.state)
        return
    text = 'Задача важная?'
    await bot.send_message(message.chat.id, text, reply_markup=important_buttom)
    await state.set_state(TaskForm.important.state)

@dp.message_handler(state=TaskForm.time) 
async def set_time(message: types.Message, state: FSMContext):
    if message.text == 'Отмена':
        text = 'Отмена создания задачи'
        await cancel_entre(text, message.chat.id, state)
        return
    if not await correct_time(message.text):
        bot.send_message(message.chat.id, 'Неверный формат. Попробуйте снова')
        return 
    await state.update_data(time=datetime.strptime(message.text, "%H:%M").time())
    data = await state.get_data()
    if data['type'] == 'периодом':
        text = 'Выберете периодичность'
        await bot.send_message(message.chat.id, text, reply_markup=periodicity_buttom)
        await state.set_state(TaskForm.periodicity.state)
        return
    text = 'Задача важная? Введите "Да" или "Нет"'
    await bot.send_message(message.chat.id, text, reply_markup=important_buttom)
    await state.set_state(TaskForm.important.state)

@dp.message_handler(state=TaskForm.periodicity) 
async def set_periodicity(message: types.Message, state: FSMContext):
    if message.text == 'Отмена':
        text = 'Отмена создания задачи'
        await cancel_entre(text, message.chat.id, state)
        return
    if not await correct_anwer_about_periodicity(message.text):
        bot.send_message(message.chat.id, 'Неверный ввод. Попробуйте снова')
        return 
    period = {'каждый день': 'ever',
                'по будням': 'wd',
                'по выходным': 'we'}
    await state.update_data(period=period[message.text.lower()])
    data = await state.get_data()
    date = await datetime.now().date()
    now_time = await datetime.now().time()
    if now_time > data['time']:
        date += timedelta(days=1)
    await state.update_data(date=await get_next_valid_date(date, data['period']))
    text = 'Задача важная? Введите "Да" или "Нет"'
    await bot.send_message(message.chat.id, text, reply_markup=important_buttom)
    await state.set_state(TaskForm.important.state)

@dp.message_handler(state=TaskForm.important) 
async def create_task(message: types.Message, state: FSMContext):
    if message.text == 'Отмена':
        text = 'Отмена создания задачи'
        await cancel_entre(text, message.chat.id, state)
        return
    if not await correct_answer_about_important(message.text):
        await bot.send_message(message.chat.id, 'Неверный ответ. Попробуйте снова')
        return 
    data = await state.get_data()
    task_id = data.get('task_id', None)
    if not task_id:
        async with httpx.AsyncClient() as client:
            response = await client.get(api+f'tele_user/{message.chat.id}')
            if response.status_code != 200:
                text = 'Ой, что-то пошло не так, повторите попытку позже.'
                await send_message_by_telegram(text, id, markup=remove_buttom)
                return
            user = response.json().get('user', None)
        data['person'] = user
        text = 'Задча создана.'
    data['important'] = True if message.text.lower() == 'да' else False
    async with httpx.AsyncClient() as client:
            if task_id:
                response = await client.put(api+f'task/{task_id}', data=data)
                if response.status_code not in [200, 204]:
                    text = 'Ой, что-то пошло не так, повторите попытку позже.'
                    await send_message_by_telegram(text, message.chat.id, markup=remove_buttom)
                    return
                text = 'Задача перенесена'
            else:
                response = await client.post(api+f'tasks/', data=data)
                if response.status_code != 201:
                    text = 'Ой, что-то пошло не так, повторите попытку позже.'
                    await send_message_by_telegram(text, message.chat.id, markup=remove_buttom)
                    return
    await bot.send_message(message.chat.id, text, reply_markup=remove_buttom)
    await send_general_message(message.chat.id)
    await state.finish()


@dp.message_handler(content_types=['text'])
async def handle_text(message: types.Message):
    if message.text == 'Привязать Telegram к основному аккаунту.':
        await bot.send_message(message.chat.id, f'Перейдите, пожалуйста, по ссылке.')
    else:
        await bot.send_message(message.chat.id, f'Ничего не понял. Попробуйте снова')


@dp.callback_query_handler(lambda call: True)
async def callback_function(call, state: FSMContext):
    callback = call.data.split('_')
    if callback[0] == 'show':
        model = callback[1]
        await start_set_date(model=model, state=state, call=call)
        return
    if callback[0] == 'choose':
        if callback[1] == 'date':
            model = callback[2]
            await start_set_date(model=model, state=state, call=call)
        else:
            model = callback[1]
            await bot.send_message(call.from_user.id, 'Введите номер задачи', reply_markup=cancel_buttom)
            task_id = [task['url'].split('/')[-1] for task in call['message']['entities']]
            await state.update_data(model=model, tasks_id=task_id)
            await state.set_state(GetDataState.number.state)
        return
    if callback[1] == 'task':
        task_id =call['message']['entities'][0]['url'].split('/')[-1]
        async with httpx.AsyncClient() as client:
            response = await client.get(api+f'task/{task_id}')
            if response.status_code != 200:
                text = 'Ой, что-то пошло не так, повторите попытку позже.'
                await send_message_by_telegram(text, id, markup=remove_buttom)
                return
            task_data = response.json()
        if not len(task_data):
            await bot.send_message(call.from_user.id, 'Данная задача была автоматически удалена. Проверьте другую дату', reply_markup=remove_buttom)
            await send_general_message(call.from_user.id)
            return
        else:
            if callback[0] == 'complete':
                async with httpx.AsyncClient() as client:
                    response = await client.get(api+f'task/{task_id}?complete=True')
                    if response.status_code != 200:
                        text = 'Ой, что-то пошло не так, повторите попытку позже.'
                        await send_message_by_telegram(text, id, markup=remove_buttom)
                        return
                    task_data = response.json()
                await bot.send_message(call.from_user.id, f'Задача {task_data["title"]} выполнена', reply_markup=remove_buttom)
                await send_general_message(call.from_user.id)
            elif callback[0] == 'delete':
                async with httpx.AsyncClient() as client:
                    response = await client.delete(api+f'task/{task_id}')
                    if response.status_code not in [204, 200]:
                        text = 'Ой, что-то пошло не так, повторите попытку позже.'
                        await send_message_by_telegram(text, call.from_user.id, markup=remove_buttom)
                        return
                await bot.send_message(call.from_user.id, f'Периодическая задача {task_data["title"]} удалена', reply_markup=remove_buttom)
                await send_general_message(call.from_user.id)
            elif callback[0] == 'reschedule':
                async with httpx.AsyncClient() as client:
                    response = await client.get(api+f'task/{task_id}')
                    if response.status_code != 200:
                        text = 'Ой, что-то пошло не так, повторите попытку позже.'
                        await send_message_by_telegram(text, id, markup=remove_buttom)
                        return
                task_data = response.json()
                await state.update_data(await state.update_data(task_id=task_id), 
                                        type=await get_task_type(task_data), 
                                        **task_data)
                data = await state.get_data()
                if data['type'] in ['дате', 'времени']:
                    text = 'Введите дату выполнения задачи. Пример: 01.01.2000'
                    await bot.send_message(call.from_user.id, text, reply_markup=cancel_buttom)
                    await state.set_state(TaskForm.date.state)
                    return
                else:
                    text = 'Введите время выполнения задачи. Пример: 12:52'
                    await bot.send_message(call.from_user.id, text, reply_markup=cancel_buttom)
                    await state.set_state(TaskForm.time.state)
                return
    if callback[1] == 'archive':
        task_id =call['message']['entities'][0]['url'].split('/')[-1]
        async with httpx.AsyncClient() as client:
            response = await client.get(api+f'archive/{task_id}')
            if response.status_code != 200:
                text = 'Ой, что-то пошло не так, повторите попытку позже.'
                await send_message_by_telegram(text, id, markup=remove_buttom)
                return
            task_data = response.json() 
        if not len(task_data):
            await bot.send_message(call.from_user.id, 'Данная задача была автоматически удалена.', reply_markup=remove_buttom)
            await send_general_message(call.from_user.id)
        else:
            if callback[0] == 'delete':
                async with httpx.AsyncClient() as client:
                    response = await client.delete(api+f'archive/{task_id}')
                    if response.status_code not in [204, 200]:
                        text = 'Ой, что-то пошло не так, повторите попытку позже.'
                        await send_message_by_telegram(text, call.from_user.id, markup=remove_buttom)
                        return
                await bot.send_message(call.from_user.id, f'Задача {task_data["title"]} из архива удалена', reply_markup=remove_buttom)
        return


@dp.message_handler(state=GetDataState.date)
async def send_tasks_or_archive(message: types.Message, state: FSMContext):
    if message.text == 'Отмена':
        text = 'Выбор даты отменен'
        await cancel_entre(text, message.chat.id, state)
        return 
    data = await state.get_data()
    model = data.get('model')
    there_are_tasks = await send_task_or_archive_data(message, model)
    if there_are_tasks:
        await state.finish()

@dp.message_handler(state=GetDataState.number)
async def send_task_or_archive_info(message: types.Message, state: FSMContext):
    if message.text == 'Отмена':
        text = 'Выбор задачи отменен'
        await cancel_entre(text, message.chat.id, state)
        return 
    num = message.text
    data = await state.get_data()
    if await is_correct_num(num, data.get('tasks_id')):
        await send_message_about_task(num, data, message.chat.id)
        await state.finish()         
    else:
        bot.send_message(message.chat.id, 'Некорректный номер, поробуйте снова.', reply_markup=remove_buttom)
        return 

async def start_set_date(model: str, state, call):
    await bot.send_message(call.from_user.id, 
                                'Введите или выберете дату. Пример: 01.01.2000',
                                    reply_markup=await get_data_keybord(model))
    await state.set_state(GetDataState.date.state)
    await state.set_data({'model': model})

if __name__ == '__main__':
    executor.start_polling(dp)
