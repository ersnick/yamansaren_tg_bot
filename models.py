from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey


class Base(DeclarativeBase):
    pass


class Master(Base):
    __tablename__ = "Master"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    tickets = relationship("Ticket", back_populates="master")
    tg_id = Column(Integer, nullable=False)


class Ticket(Base):
    __tablename__ = "Ticket"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    problem = Column(String, nullable=False)
    price = Column(String, nullable=False)
    address = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    client_name = Column(String, nullable=True)
    time = Column(String, nullable=False)
    description = Column(String, nullable=True)
    in_process = Column(Boolean, nullable=False)
    master_id = Column(Integer, ForeignKey("Master.id"))
    master = relationship("Master", back_populates="tickets")
