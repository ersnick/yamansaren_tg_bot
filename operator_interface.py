import asyncio
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, KeyboardButton, \
    ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.filters import (
    Command
)

from sqlalchemy.orm import Session

import admin_interface
from models import *
from sqlalchemy import create_engine

from States import States

loop = asyncio.get_event_loop()
operator_router = Router()
engine = create_engine("sqlite:///yamansaren.db")
Base.metadata.create_all(bind=engine)


@operator_router.message(Command("add_ticket"))
async def add_ticket(message: Message, state: FSMContext):
    await state.set_state(States.client_problem)
    await message.answer("Какая проблема у клиента?",
                         reply_markup=ReplyKeyboardMarkup(
                             keyboard=[[KeyboardButton(text="/cancel")]], resize_keyboard=True, ),
                         )


@operator_router.message(Command("заново"))
async def add_ticket(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(States.client_problem)
    await message.answer("Какая проблема у клиента?",
                         reply_markup=ReplyKeyboardMarkup(
                             keyboard=[[KeyboardButton(text="/cancel")]], resize_keyboard=True, ),
                         )


@operator_router.message(States.client_problem)
async def process_client_problem(message: Message, state: FSMContext):
    await state.update_data(client_problem=message.text)
    await state.set_state(States.price)

    await message.answer("Какая цена была озвучена?",
                         reply_markup=ReplyKeyboardMarkup(
                             keyboard=[[KeyboardButton(text="/cancel")]], resize_keyboard=True, ),
                         )


@operator_router.message(States.price)
async def process_price(message: Message, state: FSMContext):
    await state.update_data(price=message.text)
    await state.set_state(States.address)

    await message.answer("Какой адрес у клиента?",
                         reply_markup=ReplyKeyboardMarkup(
                             keyboard=[[KeyboardButton(text="/cancel")]], resize_keyboard=True, ),
                         )


@operator_router.message(States.address)
async def process_address(message: Message, state: FSMContext):
    await state.update_data(address=message.text)
    await state.set_state(States.phone)

    await message.answer("Какой номер телефона у клиента?",
                         reply_markup=ReplyKeyboardMarkup(
                             keyboard=[[KeyboardButton(text="/cancel")]], resize_keyboard=True, ),
                         )


@operator_router.message(States.phone)
async def process_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await state.set_state(States.client_name)

    await message.answer("Как зовут клиента?",
                         reply_markup=ReplyKeyboardMarkup(
                             keyboard=[[KeyboardButton(text="/cancel")]], resize_keyboard=True, ),
                         )


@operator_router.message(States.client_name)
async def process_client_name(message: Message, state: FSMContext):
    await state.update_data(client_name=message.text)
    await state.set_state(States.time)

    await message.answer("На какое время вы договорились?",
                         reply_markup=ReplyKeyboardMarkup(
                             keyboard=[[KeyboardButton(text="/cancel")]], resize_keyboard=True, ),
                         )


@operator_router.message(States.time)
async def process_time(message: Message, state: FSMContext):
    await state.update_data(time=message.text)
    await state.set_state(States.description)

    await message.answer("Напишите комментарий к заявке",
                         reply_markup=ReplyKeyboardMarkup(
                             keyboard=[[KeyboardButton(text="/cancel")]], resize_keyboard=True, ),
                         )


@operator_router.message(States.description)
async def process_description(message: Message, state: FSMContext):
    data = await state.update_data(description=message.text)
    text = data["client_problem"] + "\n" + data["price"] + "\n" + data["address"] + "\n" + data["phone"] + "\n" + data[
        "client_name"] + "\n" + data["time"] + "\n" + data["description"]
    await state.set_state(States.add_ticket)

    await message.answer(text,
                         reply_markup=ReplyKeyboardMarkup(
                             keyboard=[[KeyboardButton(text="/cancel"),
                                        KeyboardButton(text="/заново"), ],
                                       [KeyboardButton(text="/все_правильно"), ]], resize_keyboard=True, ),
                         )


@operator_router.message(Command("все_правильно"))
async def cancel_handler(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    await state.clear()
    with Session(autoflush=False, bind=engine) as db:
        ticket = Ticket(problem=data["client_problem"],
                        price=data["price"], address=data["address"],
                        phone=data["phone"],
                        client_name=data["client_name"],
                        time=data["time"],
                        description=data["description"],
                        in_process=False)
        db.add(ticket)
        db.commit()
        ticket_text = ("#" + str(ticket.id) + "\n" + data["client_problem"] + "\n" + data["price"] + "\n" +
                       data["address"] + "\n" + data["phone"] + "\n" + data["client_name"] + "\n" + data[
                           "time"] + "\n" + data[
                           "description"])

    await message.answer("Заявка:\n" + ticket_text + "\n\nДобавлена успешно!",
                         reply_markup=ReplyKeyboardRemove(), )

    await admin_interface.send_to_admin(ticket_text)


@operator_router.message(Command("cancel"))
@operator_router.message(F.text.casefold() == "отмена")
async def cancel_handler(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        return

    await state.clear()
    await message.answer(
        "Отменено.",
        reply_markup=ReplyKeyboardRemove(), )
