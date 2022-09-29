import config
import logging
import re

import aiogram.utils.markdown as md
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.storage import FSMContextProxy
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils.exceptions import ChatNotFound

from forms import Vacancy, Service
from keyboards import (
    select_button, type_work_markup,
    salary_markup, contact_markup,
    inline_confirmation_vacancy,
    inline_confirmation_service,
)

# log level
logging.basicConfig(level=logging.INFO)

# bot init
storage = MemoryStorage()

bot = Bot(token=config.TOKEN)

dp = Dispatcher(bot, storage=storage)


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    mess = f'Привет, {message.from_user.first_name}\nЯ – бот Тусы для размещения вакансий/услуг'
    await message.answer(mess, parse_mode='html')
    question = 'Что вы хотите разместить?'
    await bot.send_message(message.chat.id, question, reply_markup=select_button)


@dp.message_handler()
async def job_posting(message: types.Message, state: FSMContext):

    if message.text == 'Разместить вакансию':
        await state.finish()
        await Vacancy.company_name.set()
        await message.reply('Введете названия компании ', reply_markup=types.ReplyKeyboardRemove())
    elif message.text == 'Разместить услугу':
        await state.finish()
        await Service.job_title.set()
        await message.reply('Введите вашу должность', reply_markup=types.ReplyKeyboardRemove())


# Vacancy
@dp.message_handler(state=Vacancy.company_name)
async def set_company_name(message: types.Message, state: FSMContext):
    if len(message.text) > config.COMPANY_NAME_CHARACTERS:
        await message.answer(f'Названия компании не должно превышать {config.COMPANY_NAME_CHARACTERS} символов')
        await Vacancy.company_name.set()
    else:
        async with state.proxy() as data:
            data['company_name'] = message.text

        await Vacancy.next()
        await message.answer("Введите должность кандидата")


@dp.message_handler(state=Vacancy.job_title)
async def set_job_title_vacancy(message: types.Message, state: FSMContext):
    if len(message.text) > config.JOB_TITLE_CHARACTERS:
        await message.answer(f'Должность кандидата не должно превышать {config.JOB_TITLE_CHARACTERS} символов')
        await Vacancy.job_title.set()
    else:
        async with state.proxy() as data:
            data['job_title'] = message.text

        await Vacancy.next()
        await message.answer("Укажите тип работы", reply_markup=type_work_markup)


@dp.message_handler(lambda message: message.text not in ["Работа в офисе", "Удаленно", "Проект(контракт)"],
                    state=Vacancy.type_of_work)
async def vacancy_type_of_work_invalid(message: types.Message):
    return await message.reply("Нет такого типа работы. Выберите один из типов работы на кнопке")


@dp.message_handler(state=Vacancy.type_of_work)
async def set_type_of_work_vacancy(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['type_of_work'] = message.text

    await Vacancy.next()
    await message.answer("Введите требования для соискателя", reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(lambda message: len(message.text) > config.REQUIREMENT_CHARACTERS, state=Vacancy.requirement)
async def requirements_invalid(message: types.Message):
    return await message.reply(f"Длинна требований работы не должна превышать {config.REQUIREMENT_CHARACTERS} символов")


@dp.message_handler(lambda message: len(message.text) < config.REQUIREMENT_CHARACTERS, state=Vacancy.requirement)
async def set_requirement(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['requirement'] = message.text

    await Vacancy.next()
    await message.answer("Введите условия работы для кандидата")


@dp.message_handler(lambda message: len(message.text) > config.TERM_CHARACTERS, state=Vacancy.term)
async def term_invalid(message: types.Message):
    return await message.reply(f"Длинна условия работы не должна превышать {config.TERM_CHARACTERS} символов")


@dp.message_handler(lambda message: len(message.text) < config.TERM_CHARACTERS, state=Vacancy.term)
async def set_term(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['term'] = message.text

    await Vacancy.next()
    await message.answer("Введите заработную плату кандидата", reply_markup=salary_markup)


@dp.message_handler(state=Vacancy.salary)
async def set_salary(message: types.Message, state: FSMContext):
    if len(message.text) > config.SALARY_CHARACTERS:
        await message.answer(f'Заработная плата не должно превышать {config.SALARY_CHARACTERS} символов.')
        await Vacancy.salary.set()
    else:
        async with state.proxy() as data:
            data['salary'] = message.text

        await Vacancy.next()
        await message.answer("Введите контакты", reply_markup=contact_markup)


async def create_hashtags(fields: []) -> str:

    # delete all symbols
    fields = ["".join(character for character in field if character.isalpha()) for field in fields]
    return ' '.join(f"#{field.replace(' ', '')}" for field in fields)


async def send_vacancy(
        chat_id: int,
        data: FSMContextProxy,
        reply_markup: types.InlineKeyboardMarkup
):
    hashtags = await create_hashtags([data[i] for i in data if i in config.VACANCY_HASHTAGS])

    await bot.send_message(
        chat_id,
        md.text(
            md.text(f"{md.bold(data['company_name'])}: ", md.bold(data['job_title'])),
            md.text(f"Тип: {data['type_of_work']}"),
            md.text(f"{md.bold('ЗП:')} {data['salary']}\n"),
            md.text(f"{md.bold('Требования:')} \n {data['requirement']}\n"),
            md.text(f"{md.bold('Условия:')} \n {data['term']}\n"),
            md.text(f"{md.bold('Контакты:')} {data['contact']}"),
            md.text(f"Тэги: {hashtags}"),
            sep='\n',
        ),
        reply_markup=reply_markup,
        parse_mode=types.ParseMode.MARKDOWN,
    )


async def send_service(
        chat_id: int,
        data: FSMContextProxy,
        reply_markup: types.InlineKeyboardMarkup
):
    hashtags = await create_hashtags([data[i] for i in data if i in config.SERVICE_HASHTAGS])

    await bot.send_message(
        chat_id,
        md.text(
            md.text(f"{md.bold(data['job_title'])}"),
            md.text(f"Тип: {data['type_of_work']}\n"),
            md.text(f"{md.bold('Услуги:')} \n {data['services']}\n"),
            md.text(f"{md.bold('Портфолио:')} \n {data['portfolio']}"),
            md.text(f"{md.bold('Стоимость услуг:')} {data['service_cost']}"),
            md.text(f"{md.bold('Контакты:')} {data['contact']}"),
            md.text(f"Тэги: {hashtags}"),
            sep='\n',
        ),
        reply_markup=reply_markup,
        parse_mode=types.ParseMode.MARKDOWN,

    )


async def set_contact(message: types.Message, state: FSMContext):
    if message.contact is None and len(message.text) > config.CONTACT_CHARACTERS:
        await message.answer(f'Контакты не должны превышать {config.CONTACT_CHARACTERS} символов.')
        if state == Vacancy.contact.state:
            await Vacancy.contact.set()
        elif state == Service.contact.state:
            await Service.contact.set()
    else:
        async with state.proxy() as data:
            if message.text:
                data['contact'] = message.text
            else:
                data['contact'] = message.contact.phone_number

            if data.state == Vacancy.contact.state:
                await send_vacancy(message.chat.id, data, inline_confirmation_vacancy)
                await Vacancy.next()
            elif data.state == Service.contact.state:
                await send_service(message.chat.id, data, inline_confirmation_service)
                await Service.next()


@dp.message_handler(content_types=types.ContentType.CONTACT, state=[Service.contact, Vacancy.contact])
async def set_contact_if_telegram_contact(message: types.Message, state: FSMContext):
    await set_contact(message, state)


@dp.message_handler(state=[Vacancy.contact, Service.contact])
async def set_contact_if_other_contact(message: types.Message, state: FSMContext):
    await set_contact(message, state)


@dp.callback_query_handler(
    text=['confirm_vacancy', 'cancel_vacancy', 'confirm_service', 'cancel_service'],
    state=[Service.hashtags, Vacancy.hashtags]
)
async def confirmation(call: types.CallbackQuery, state: FSMContext):
    try:
        async with state.proxy() as data:
            if call.data == 'confirm_vacancy':
                await send_vacancy(config.VACANCY_GROUP_ID, data, types.InlineKeyboardMarkup())
                await call.message.answer('ваша вакансия размещена на канале!', reply_markup=select_button)
            elif call.data == 'confirm_service':
                await send_service(config.SERVICE_GROUP_ID, data, types.InlineKeyboardMarkup())
                await call.message.answer('Ваша услуга размещена на канале!', reply_markup=select_button)
    except ChatNotFound:
        await call.message.answer('Что-то пошло не так', reply_markup=select_button)

    if call.data == 'cancel_vacancy':
        await call.message.answer('Вакансия удалена!', reply_markup=select_button)
    elif call.data == 'cancel_service':
        await call.message.answer('Услуга удалена!', reply_markup=select_button)

    await state.finish()


# Employee
@dp.message_handler(state=Service.job_title)
async def set_job_title_employee(message: types.Message, state: FSMContext):
    if len(message.text) > config.JOB_TITLE_CHARACTERS:
        await message.answer(f'Должность не должно превышать {config.JOB_TITLE_CHARACTERS} символов. ')
        await Service.job_title.set()
    else:
        async with state.proxy() as data:
            data['job_title'] = message.text

        type_work_markup.add('Не важно')

        await Service.next()
        await message.answer("Укажите тип работы", reply_markup=type_work_markup)


@dp.message_handler(lambda message: message.text not in ["Работа в офисе", "Удаленно", "Проект(контракт)", "Не важно"],
                    state=Service.type_of_work)
async def employee_type_of_work_invalid(message: types.Message):
    return await message.reply("Нет такого типа работы. Выберите один из типов работы на кнопке")


@dp.message_handler(state=Service.type_of_work)
async def set_type_of_work_employee(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['type_of_work'] = message.text

    await Service.next()
    await message.answer("Введите ваши услуги", reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(lambda message: len(message.text) > config.SERVICE_CHARACTERS, state=Service.services)
async def service_invalid(message: types.Message):
    return await message.reply(f"Длинна услуги не должна превышать {config.SERVICE_CHARACTERS} символов")


@dp.message_handler(lambda message: len(message.text) < config.SERVICE_CHARACTERS, state=Service.services)
async def set_term(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['services'] = message.text

    await Service.next()
    await message.answer("Введите ссылку(и) на портфолио")


@dp.message_handler(state=Service.portfolio)
async def set_services_employee(message: types.Message, state: FSMContext):
    if len(message.text) > config.PORTFOLIO_CHARACTERS:
        await message.answer(f'Длинна порфолио не должно превышать {config.PORTFOLIO_CHARACTERS} символов. ')
        await Service.portfolio.set()
    else:
        async with state.proxy() as data:
            data['portfolio'] = message.text

        await Service.next()
        await message.answer("Введите заработную плату ваших услуг", reply_markup=salary_markup)


@dp.message_handler(state=Service.service_cost)
async def set_services_employee(message: types.Message, state: FSMContext):
    if len(message.text) > config.SALARY_CHARACTERS:
        await message.answer(f'Данное сообщение не должно превышать {config.SALARY_CHARACTERS} символов. ')
        await Service.service_cost.set()
    else:
        async with state.proxy() as data:
            data['service_cost'] = message.text

        await Service.next()
        await message.answer("Введите контакты", reply_markup=contact_markup)


# run long polling
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
