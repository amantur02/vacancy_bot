from aiogram.dispatcher.filters.state import State, StatesGroup


class Vacancy(StatesGroup):
    company_name = State()
    job_title = State()
    type_of_work = State()
    requirement = State()
    term = State()
    salary = State()
    contact = State()
    hashtags = State()


class Service(StatesGroup):
    job_title = State()
    type_of_work = State()
    services = State()
    portfolio = State()
    service_cost = State()
    contact = State()
    hashtags = State()
