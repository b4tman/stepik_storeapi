from dataclasses import asdict
import os
from typing import Annotated, TypeVar
from sqlalchemy import Column, ForeignKey, String, Table, create_engine, inspect
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    sessionmaker,
)
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy import Enum
from sqlalchemy.dialects.postgresql import UUID
import uuid
from store.default import default_users

from store.domains import Admin, Cart, Item, Manager, Order, Role, User

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
DATABASE_INIT_DATA = os.getenv("DATABASE_INIT_DATA", "yes").lower() == "yes"

engine = create_engine(DATABASE_URL, echo=True)
session_factory = sessionmaker(engine)


class GUID(TypeDecorator):
    """Platform-independent GUID type.

    Uses PostgreSQL's UUID type, otherwise uses
    CHAR(32), storing as stringified hex values.

    source: https://gist.github.com/gmolveau/7caeeefe637679005a7bb9ae1b5e421e
    """

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return "%.32x" % uuid.UUID(value).int
            else:
                # hexstring
                return "%.32x" % value.int

    def _uuid_value(self, value):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                value = uuid.UUID(value)
            return value

    def process_result_value(self, value, dialect):
        return self._uuid_value(value)

    def sort_key_function(self, value):
        return self._uuid_value(value)


class Base(DeclarativeBase): ...


guidpk = Annotated[
    str, mapped_column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
]
email_uniq = Annotated[str, mapped_column(unique=True, nullable=False, index=True)]
optional_str = Annotated[str | None, mapped_column(nullable=True, default=None)]

UserOrmT = TypeVar("UserOrmT", bound="UserOrm")


class UserOrm(Base):
    __tablename__ = "users"
    id: Mapped[guidpk]
    role: Mapped[Role] = mapped_column(
        Enum(Role), default=Role.USER, nullable=False, index=True
    )
    email: Mapped[email_uniq]
    salt: Mapped[optional_str]
    hash: Mapped[optional_str]

    def to_object(self) -> User:
        cls = {Role.MANAGER: Manager, Role.ADMIN: Admin, Role.USER: User}
        obj = cls.get(self.role, User)(self.id, self.email)
        if self.role >= Role.MANAGER:
            obj.salt, obj.hash = self.salt, self.hash
        return obj

    @classmethod
    def from_object(cls, user: User) -> UserOrmT:
        data = asdict(user)
        if "password" in data:
            del data["password"]
        if not data["id"]:
            del data["id"]
        return cls(**data, role=user.role())


ItemsOrmT = TypeVar("ItemsOrmT", bound="ItemsOrm")


class ItemsOrm(Base):
    __tablename__ = "items"
    id: Mapped[guidpk]
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[int] = mapped_column(nullable=False)
    description: Mapped[optional_str]

    def to_object(self) -> Item:
        return Item(self.id, self.name, self.price, self.description)

    @classmethod
    def from_object(cls, item: Item, session=None, update=False) -> ItemsOrmT:
        if session is not None:
            entity = session.get(ItemsOrm, item.id)
            if entity is not None:
                if update:
                    for attr in ("name", "price", "description"):
                        old = getattr(entity, attr)
                        new = getattr(item, attr)
                        if old != new:
                            setattr(entity, attr, new)
                return entity
        return cls(**asdict(item))


cart_items = Table(
    "cart_items",
    Base.metadata,
    Column("cart_id", ForeignKey("carts.id"), primary_key=True),
    Column("items_id", ForeignKey("items.id"), primary_key=True),
)

CartOrmT = TypeVar("CartOrmT", bound="CartOrm")


class CartOrm(Base):
    __tablename__ = "carts"
    id: Mapped[guidpk]
    email: Mapped[email_uniq]
    items: Mapped[list[ItemsOrm]] = relationship(secondary=cart_items)

    def to_object(self) -> Cart:
        return Cart(self.id, self.email, [*map(ItemsOrm.to_object, self.items)])

    @classmethod
    def from_object(cls, cart: Cart, /, session=None, *, update=False) -> CartOrmT:
        items_converter = lambda x: ItemsOrm.from_object(x, session)
        if session is not None:
            entity = session.get(CartOrm, cart.id)
            if entity is not None:
                if update:
                    if entity.email != cart.email:
                        entity.email = cart.email
                    item_ids = sorted(map(lambda x: x.id, entity.items))
                    other_item_ids = sorted(map(lambda x: x.id, cart.items))
                    if item_ids != other_item_ids:
                        entity.items = [*map(items_converter, cart.items)]
                return entity
        data = {
            "id": cart.id,
            "email": cart.email,
            "items": [*map(items_converter, cart.items)],
        }
        return cls(**data)


order_items = Table(
    "order_items",
    Base.metadata,
    Column("order_id", ForeignKey("orders.id"), primary_key=True),
    Column("items_id", ForeignKey("items.id"), primary_key=True),
)

OrderOrmT = TypeVar("OrderOrmT", bound="OrderOrm")


class OrderOrm(Base):
    __tablename__ = "orders"
    id: Mapped[guidpk]
    email: Mapped[email_uniq]
    items: Mapped[list[ItemsOrm]] = relationship(secondary=order_items)

    def to_object(self) -> Order:
        return Order(self.id, self.email, [*map(ItemsOrm.to_object, self.items)])

    @classmethod
    def from_object(cls, order: Order, session=None) -> OrderOrmT:
        if session is not None:
            entity = session.get(OrderOrm, order.id)
            if entity is not None:
                return entity
        data = {
            "id": order.id,
            "email": order.email,
            "items": [*map(lambda x: ItemsOrm.from_object(x, session), order.items)],
        }
        return cls(**data)


def create_default_users():
    with session_factory() as session:
        users = [*map(UserOrm.from_object, default_users())]
        session.add_all(users)
        session.commit()


def bootstrap():
    if not inspect(engine).has_table("users"):
        Base.metadata.create_all(engine)
        if DATABASE_INIT_DATA:
            create_default_users()


bootstrap()
