from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove

cancel_buttom = ReplyKeyboardMarkup(resize_keyboard=True)
cancel = KeyboardButton('Отмена')
cancel_buttom.add(cancel)

remove_buttom = ReplyKeyboardRemove()

general_keybord = InlineKeyboardMarkup(resize_keyboard=True)

task_keybord = InlineKeyboardButton('Мои задачи', callback_data='show_task')
archive_keybord = InlineKeyboardButton('Архив', callback_data='show_archive')

general_keybord.add(task_keybord, archive_keybord)


date_archive_keybord = ReplyKeyboardMarkup(resize_keyboard=True)
date_archive_keybord.add(KeyboardButton('Сегодня'),
                        KeyboardButton('Все даты'),
                        cancel)
date_action_keybord = ReplyKeyboardMarkup(resize_keyboard=True)
date_action_keybord.add(KeyboardButton('Сегодня'),
                        KeyboardButton('Завтра'),
                        KeyboardButton('Все даты'),
                        cancel)



choose_task_keybord = InlineKeyboardMarkup(row_width=1, resize_keyboard=True)
choose_task_keybord.add(InlineKeyboardButton('Выбрать задачу', callback_data='choose_task'),
                        InlineKeyboardButton('Выбрать другую дату', callback_data='choose_date_task'))


choose_archive_keybord = InlineKeyboardMarkup(row_width=1, resize_keyboard=True)
choose_archive_keybord.add(InlineKeyboardButton('Выбрать задачу', callback_data='choose_archive'),
                           InlineKeyboardButton('Выбрать другую дату', callback_data='choose_date_archive'))



archive_action_keybord = InlineKeyboardMarkup(resize_keyboard=True)
archive_action_keybord.add(InlineKeyboardButton('Удалить', callback_data='delete_archive'))

task_no_per_action_keybord = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
task_no_per_action_keybord.add(KeyboardButton('Выполнить'), 
                                KeyboardButton('Перенести'),
                                cancel)

task_with_per_action_keybord = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
task_with_per_action_keybord.add(KeyboardButton('Выполнить'), KeyboardButton('Удалить'),
                                KeyboardButton('Перенести'),
                                cancel)

task_no_per_complete_buttom = InlineKeyboardMarkup(row_width=2, resize_keyboard=True)
task_no_per_complete_buttom.add(InlineKeyboardButton('Выполнить', callback_data='complete_task'),
                                InlineKeyboardButton('Перенести', callback_data='reschedule_task'))

task_with_per_complete_buttom = InlineKeyboardMarkup(row_width=2, resize_keyboard=True)
task_with_per_complete_buttom.add(InlineKeyboardButton('Выполнить', callback_data='complete_task'),
                                InlineKeyboardButton('Удалить', callback_data='delete_task'),
                                InlineKeyboardButton('Перенести', callback_data='reschedule_task'))


periodicity_buttom = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
periodicity_buttom.add(KeyboardButton('Каждый день'), 
                        KeyboardButton('По выходным'),
                        KeyboardButton('По будням'),
                        cancel)

task_type = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
task_type.add(KeyboardButton('По дате и времени'), 
                        KeyboardButton('По времени с периодом'),
                        KeyboardButton('Только по дате'),
                        cancel)


important_buttom = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
important_buttom.add(KeyboardButton('Да'), 
                        KeyboardButton('Нет'),
                        cancel)