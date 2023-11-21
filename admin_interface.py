import asyncio
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, KeyboardButton, \
    ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.filters import (
    Command
)

from sqlalchemy.orm import Session
from models import *
from sqlalchemy import create_engine

from States import States

from main import bot

from openpyxl import load_workbook
from datetime import datetime

loop = asyncio.get_event_loop()
admin_router = Router()

xlsx_path = './otchetnost.xlsx'

engine = create_engine("sqlite:///yamansaren.db")
Base.metadata.create_all(bind=engine)


async def send_to_admin(text: str):
    await bot.send_message(6932519708, text=text, reply_markup=ReplyKeyboardMarkup(
                             keyboard=[[KeyboardButton(text="/список_неразобранных_заявок"), ]], resize_keyboard=True, ),
                           )


async def send_to_master(text: str, master_id):
    await bot.send_message(master_id, text=text)


@admin_router.message(Command("menu"))
async def menu_message(message: Message):
    menu_text = ("Список команд:\n/add_ticket - вызывает скрипт добавления новой заявки\n" +
                 "/add_master - вызывает скрипт добавления нового мастера\n" +
                 "/del_master - вызывает скрипт удаления мастера\n" +
                 "/list_of_unassembled_tickets - вызывает скрипт закрепления заявки за мастером\n" +
                 "/ticket_done - вызывает скрипт заполнения данных для таблицы и открепления заявки от мастера\n" +
                 "/list_of_masters - ознакомительный, показывает всех мастеров и закрепленные за ними заявки\n"
                 "/cancel - останавливает все активные скрипты")

    await message.answer(menu_text, reply_markup=ReplyKeyboardMarkup(
                             keyboard=[[KeyboardButton(text="/add_ticket"),
                                        KeyboardButton(text="/add_master"), ],
                                       [KeyboardButton(text="/del_master"),
                                        KeyboardButton(text="/list_of_unassembled_tickets"), ],
                                       [KeyboardButton(text="/ticket_done"),
                                        KeyboardButton(text="/list_of_masters"), ],
                                       [KeyboardButton(text="/cancel"), ]], resize_keyboard=True, ),
                         )


@admin_router.message(Command("start"))
async def start_message(message: Message):
    await message.answer("шалом")
    await message.answer("вот твой id: " + str(message.chat.id))


@admin_router.message(Command("cancel"))
@admin_router.message(F.text.casefold() == "отмена")
async def cancel_handler(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        return

    await state.clear()
    await message.answer(
        "Отменено.",
        reply_markup=ReplyKeyboardRemove(),
    )


# функционал работы с мастером
@admin_router.message(Command("add_master"))
async def add_master(message: Message, state: FSMContext):
    await state.set_state(States.add_master)
    await message.answer("Как зовут нового мастера?",
                         reply_markup=ReplyKeyboardMarkup(
                             keyboard=[[KeyboardButton(text="/cancel")]], resize_keyboard=True, ),
                         )


@admin_router.message(States.add_master)
async def process_master_name(message: Message, state: FSMContext):
    await state.update_data(add_master=message.text)
    await state.set_state(States.master_id)
    await message.answer("Введите id мастера, чтобы узнать id, мастеру необходимо написать /start боту",
                         reply_markup=ReplyKeyboardRemove(), )


@admin_router.message(States.master_id)
async def process_master_id(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()

    with Session(autoflush=False, bind=engine) as db:
        master = Master(name=data["add_master"], tg_id=int(message.text))
        db.add(master)
        db.commit()

    await message.answer(data["add_master"] + " добавлен успешно",
                         reply_markup=ReplyKeyboardRemove(), )


@admin_router.message(Command("del_master"))
async def del_master(message: Message, state: FSMContext):
    await state.set_state(States.del_master)
    masters_list = "Выбирай номер, кого хочешь уволить\n"
    with Session(autoflush=False, bind=engine) as db:
        masters = db.query(Master).all()
        for master in masters:
            masters_list += str(master.id) + " " + master.name + "\n"

    await message.answer(masters_list,
                         reply_markup=ReplyKeyboardMarkup(
                             keyboard=[[KeyboardButton(text="/cancel")]], resize_keyboard=True, ),
                         )


@admin_router.message(States.del_master)
async def process_del_master(message: Message, state: FSMContext):
    number = int(message.text)
    await state.clear()

    with Session(autoflush=False, bind=engine) as db:
        master = db.query(Master).filter(Master.id == number).first()
        db.delete(master)
        db.commit()

    await message.answer(master.name + " был успешно увлоен))0)",
                         reply_markup=ReplyKeyboardRemove(), )


# присвоение заявки
@admin_router.message(Command("list_of_unassembled_tickets"))
async def ticket_list(message: Message, state: FSMContext):
    await state.set_state(States.select_ticket)
    ticket_list_text = "Список неразобранных заявок:\n"
    with Session(autoflush=False, bind=engine) as db:
        tickets = db.query(Ticket).filter(Ticket.in_process == False).all()
        for ticket in tickets:
            ticket_list_text += ("#" + str(ticket.id) + "\n" + str(ticket.problem) + "\n" + str(ticket.price) + "\n" +
                                 str(ticket.address) + "\n" + str(ticket.phone) + "\n" + str(ticket.client_name) + "\n"
                                 + str(ticket.time) + "\n" + str(ticket.description) + "\n\n")

    ticket_list_text += ("Выбирай номер заявки, чтобы присвоить ее мастеру")
    await message.answer(ticket_list_text,
                         reply_markup=ReplyKeyboardMarkup(
                             keyboard=[[KeyboardButton(text="/cancel")]], resize_keyboard=True, ),
                         )


@admin_router.message(States.select_ticket)
async def process_select_ticket(message: Message, state: FSMContext):
    await state.update_data(select_ticket=int(message.text))
    await state.set_state(States.select_master)
    masters_list = "Выбирай номер мастера, кому отдать заявку\n"
    ident = "\n           "
    with Session(autoflush=False, bind=engine) as db:
        masters = db.query(Master).all()
        for master in masters:
            masters_list += str(master.id) + " " + master.name + "\n"
            for ticket in master.tickets:
                masters_list += (ident + "#" + str(ticket.id) + ident + str(ticket.problem) + ident + str(ticket.price)
                                 + ident + str(ticket.address) + ident + str(ticket.phone) + ident +
                                 str(ticket.client_name) + ident + str(ticket.time) + ident + str(ticket.description)
                                 + "\n\n")

    await message.answer(masters_list,
                         reply_markup=ReplyKeyboardMarkup(
                             keyboard=[[KeyboardButton(text="/cancel")]], resize_keyboard=True, ),
                         )


@admin_router.message(States.select_master)
async def process_select_master(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    with (Session(autoflush=False, bind=engine) as db):
        master = db.query(Master).filter(Master.id == int(message.text)).first()
        ticket = db.query(Ticket).filter(Ticket.id == data["select_ticket"]).first()
        master.tickets.extend([ticket])
        ticket.in_process = True
        db.commit()
        message_text = "Заявка\n"
        ticket_text = ("#" + str(ticket.id) + "\n" + str(ticket.problem) + "\n" + str(ticket.price) + "\n" +
                       str(ticket.address) + "\n" + str(ticket.phone) + "\n" + str(ticket.client_name) + "\n" +
                       str(ticket.time) + "\n" + str(ticket.description) + "\n")
        message_text += ticket_text + ("Присвоена мастеру: " + master.name)

    await send_to_master(ticket_text, master.tg_id)
    await message.answer(message_text,
                         reply_markup=ReplyKeyboardRemove(), )


# заявка выполнена
@admin_router.message(Command("ticket_done"))
async def ticket_done(message: Message, state: FSMContext):
    await state.set_state(States.done_ticket)
    message_text = "Список мастеров и закрепленных за ними заявками:\n"
    ident = "\n           "
    with Session(autoflush=False, bind=engine) as db:
        masters = db.query(Master).all()
        for master in masters:
            message_text += str(master.id) + " " + master.name + "\n"
            for ticket in master.tickets:
                message_text += (ident + "#" + str(ticket.id) + ident + str(ticket.problem) + ident + str(ticket.price)
                                 + ident + str(ticket.address) + ident + str(ticket.phone) + ident +
                                 str(ticket.client_name) + ident + str(ticket.time) + ident + str(ticket.description)
                                 + "\n\n")

    message_text += "\nКакая заявка была выполнена?"
    await message.answer(message_text,
                         reply_markup=ReplyKeyboardMarkup(
                             keyboard=[[KeyboardButton(text="/cancel")]], resize_keyboard=True, ), )


@admin_router.message(States.done_ticket)
async def process_done_ticket(message: Message, state: FSMContext):
    await state.update_data(done_ticket=int(message.text))
    await state.set_state(States.money_from_ticket)
    await message.answer("Сколько забрали с заявки?",
                         reply_markup=ReplyKeyboardMarkup(
                             keyboard=[[KeyboardButton(text="/cancel")]], resize_keyboard=True, ), )


@admin_router.message(States.money_from_ticket)
async def process_money_from_ticket(message: Message, state: FSMContext):
    await state.update_data(money_from_ticket=int(message.text))
    await state.set_state(States.money_for_materials)
    await message.answer("Сколько потратили на материалы?",
                         reply_markup=ReplyKeyboardMarkup(
                             keyboard=[[KeyboardButton(text="/cancel")]], resize_keyboard=True, ), )


@admin_router.message(States.money_for_materials)
async def process_money_for_materials(message: Message, state: FSMContext):
    await state.update_data(money_for_materials=int(message.text))
    await state.set_state(States.ticket_description)
    await message.answer("Добавь описание к заявке",
                         reply_markup=ReplyKeyboardMarkup(
                             keyboard=[[KeyboardButton(text="/cancel")]], resize_keyboard=True, ), )


@admin_router.message(States.ticket_description)
async def process_ticket_description(message: Message, state: FSMContext):
    await state.update_data(ticket_description=message.text)
    data = await state.get_data()

    with Session(autoflush=False, bind=engine) as db:
        ticket = db.query(Ticket).filter(Ticket.id == data["done_ticket"]).first()
        master_name = ticket.master.name
        ticket.in_process = False
        master = db.query(Master).filter(Master.id == ticket.master.id).first()
        master.tickets.remove(ticket)
        db.commit()

    wb = load_workbook(xlsx_path)
    ws = wb['Sheet1']
    ws.append([data["done_ticket"], data["money_from_ticket"], data["money_for_materials"], str(datetime.now().date()),
               master_name, data["ticket_description"]])
    wb.save(xlsx_path)
    wb.close()

    await state.clear()
    await message.answer("Отчет по заявке записан в таблицу!",
                         reply_markup=ReplyKeyboardRemove(), )


# вывод списка мастеров и закрепленных заявок
@admin_router.message(Command("list_of_masters"))
async def masters_in_list(message: Message):
    message_text = "Список мастеров и закрепленных за ними заявками:\n"
    ident = "\n           "
    with Session(autoflush=False, bind=engine) as db:
        masters = db.query(Master).all()
        for master in masters:
            message_text += str(master.id) + " " + master.name + "\n"
            for ticket in master.tickets:
                message_text += (ident + "#" + str(ticket.id) + ident + str(ticket.problem) + ident + str(ticket.price)
                                 + ident + str(ticket.address) + ident + str(ticket.phone) + ident +
                                 str(ticket.client_name) + ident + str(ticket.time) + ident + str(ticket.description)
                                 + "\n\n")

    await message.answer(message_text,
                         reply_markup=ReplyKeyboardRemove(), )
