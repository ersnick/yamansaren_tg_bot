from aiogram.fsm.state import StatesGroup, State


class States(StatesGroup):
    # states for functional with master
    add_master = State()
    master_id = State()
    del_master = State()

    # states for add ticket
    client_problem = State()
    price = State()
    address = State()
    phone = State()
    client_name = State()
    time = State()
    description = State()
    add_ticket = State()

    # states for add ticket to master
    select_ticket = State()
    select_master = State()

    # states for done ticket
    done_ticket = State()
    money_from_ticket = State()
    money_for_materials = State()
    ticket_description = State()
