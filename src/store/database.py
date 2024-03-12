import os
import uuid
from dataclasses import asdict
from typing import Annotated, Callable

from sqlalchemy import Column, Enum, ForeignKey, String, Table, create_engine, inspect
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    sessionmaker,
)
from sqlalchemy.types import CHAR, TypeDecorator

from store.default import Defaults
from store.domains import Admin, Cart, Item, Manager, Order, Role, User
from store.utils import SingletonMeta


class Base(DeclarativeBase): ...


class Database(metaclass=SingletonMeta):
    _init_data_callbacks: list[Callable[["Database"], None]] = []

    def __init__(self):
        self.setup_url()
        self._engine = create_engine(self.url, echo=True)
        self._session = sessionmaker(self._engine)
        self._ready = False
        self._init_mode = False

    def setup_url(self):
        url = os.getenv("DATABASE_URL")
        if url is None:
            self.setup_url_from_path()
        else:
            self.url = url

    def setup_url_from_path(self):
        path = os.getenv("DB_PATH", "db")
        self.url = f"sqlite+pysqlite:///{path}/database.sqlite"
        if not os.path.isdir(path):
            os.mkdir(path)

    @property
    def engine(self):
        self.check_ready()
        return self._engine

    @property
    def session(self):
        self.check_ready()
        return self._session

    def check_ready(self):
        if self._ready or self._init_mode:
            return
        if not inspect(self._engine).has_table("users"):
            self.bootstrap()
        self._ready = True

    @classmethod
    def add_init_data_callback(cls, callback: Callable[["Database"], None]):
        cls._init_data_callbacks.append(callback)

    def bootstrap(self):
        Base.metadata.create_all(self._engine)
        if os.getenv("DATABASE_INIT_DATA", "yes").lower() == "yes":
            self._init_mode = True
            for callback in self._init_data_callbacks:
                callback(self)
            self._init_mode = False


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


guidpk = Annotated[
    str, mapped_column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
]
email = Annotated[str, mapped_column(nullable=False, index=True)]
email_uniq = Annotated[str, mapped_column(unique=True, nullable=False, index=True)]
optional_str = Annotated[str | None, mapped_column(nullable=True, default=None)]


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
    def from_object(cls, user: User) -> "UserOrm":
        data = asdict(user)
        if "password" in data:
            del data["password"]
        if not data["id"]:
            del data["id"]
        return cls(**data, role=user.role())


class ItemOrm(Base):
    __tablename__ = "items"
    id: Mapped[guidpk]
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[int] = mapped_column(nullable=False)
    description: Mapped[optional_str]

    def to_object(self) -> Item:
        return Item(str(self.id), self.name, self.price, self.description)

    @classmethod
    def from_object(cls, item: Item, /, session=None, *, update=False) -> "ItemOrm":
        if session is not None:
            entity = session.get(ItemOrm, item.id)
            if entity is not None:
                if update:
                    entity.name = item.name
                    entity.price = item.price
                    entity.description = item.description
                return entity
        return cls(**asdict(item))


cart_items = Table(
    "cart_items",
    Base.metadata,
    Column("cart_id", ForeignKey("carts.id", ondelete="CASCADE"), primary_key=True),
    Column("items_id", ForeignKey("items.id", ondelete="CASCADE"), primary_key=True),
)


class CartOrm(Base):
    __tablename__ = "carts"
    id: Mapped[guidpk]
    email: Mapped[email_uniq]
    items: Mapped[list[ItemOrm]] = relationship(secondary=cart_items, lazy="selectin")

    def to_object(self) -> Cart:
        return Cart(str(self.id), self.email, [*map(ItemOrm.to_object, self.items)])

    @classmethod
    def from_object(cls, cart: Cart, /, session=None, *, update=False) -> "CartOrm":
        items_converter = lambda x: ItemOrm.from_object(x, session)
        if session is not None:
            entity = session.get(CartOrm, cart.id)
            if entity is not None:
                if update:
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
    Column("order_id", ForeignKey("orders.id", ondelete="CASCADE"), primary_key=True),
    Column("items_id", ForeignKey("items.id", ondelete="CASCADE"), primary_key=True),
)


class OrderOrm(Base):
    __tablename__ = "orders"
    id: Mapped[guidpk]
    email: Mapped[email]
    items: Mapped[list[ItemOrm]] = relationship(secondary=order_items, lazy="selectin")

    def to_object(self) -> Order:
        return Order(str(self.id), self.email, [*map(ItemOrm.to_object, self.items)])

    @classmethod
    def from_object(cls, order: Order, session=None) -> "OrderOrm":
        if session is not None:
            entity = session.get(OrderOrm, order.id)
            if entity is not None:
                return entity
        data = {
            "id": order.id,
            "email": order.email,
            "items": [*map(lambda x: ItemOrm.from_object(x, session), order.items)],
        }
        return cls(**data)


def create_default_users(db: Database):
    with db.session() as session:
        session.add_all(map(UserOrm.from_object, Defaults().users))
        session.commit()


def create_default_items(db: Database):
    with db.session() as session:
        session.add_all(map(ItemOrm.from_object, Defaults().items))
        session.commit()


def create_default_carts(db: Database):
    with db.session() as session:
        session.add_all(
            map(lambda x: CartOrm.from_object(x, session), Defaults().carts)
        )
        session.commit()


Database.add_init_data_callback(create_default_users)
Database.add_init_data_callback(create_default_items)
Database.add_init_data_callback(create_default_carts)
