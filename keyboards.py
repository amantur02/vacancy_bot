from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


select_button = ReplyKeyboardMarkup(resize_keyboard=True).add(
    KeyboardButton('Разместить вакансию')
).add(
    KeyboardButton('Разместить услугу')
)

type_work_markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
type_work_markup.add("Работа в офисе")
type_work_markup.add("Удаленно")
type_work_markup.add("Проект(контракт)")

salary_markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
salary_markup.add("Договорная")

contact_markup = ReplyKeyboardMarkup(resize_keyboard=True)
contact_markup.add(KeyboardButton('Отправить свой контакт ☎️', request_contact=True))

inline_confirmation_vacancy = InlineKeyboardMarkup()
inline_confirmation_vacancy.add(InlineKeyboardButton('Подтвердить', callback_data='confirm_vacancy'))
inline_confirmation_vacancy.add(InlineKeyboardButton('Отменить', callback_data='cancel_vacancy'))

inline_confirmation_service = InlineKeyboardMarkup()
inline_confirmation_service.add(InlineKeyboardButton('Подтвердить', callback_data='confirm_service'))
inline_confirmation_service.add(InlineKeyboardButton('Отменить', callback_data='cancel_service'))
