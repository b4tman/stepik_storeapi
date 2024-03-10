from dataclasses import asdict
import os
from typing import Annotated
from sqlalchemy import create_engine
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

from store.domains import Admin, Manager, Role, User

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")

engine = create_engine(DATABASE_URL, echo=True)


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


class UserOrm(Base):
    __tablename__ = "users"
    id: Mapped[guidpk]
    role: Mapped[Role] = mapped_column(
        Enum(Role), default=Role.USER, nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(unique=True, nullable=False, index=True)
    salt: Mapped[str | None] = mapped_column(nullable=True, default=None)
    hash: Mapped[str | None] = mapped_column(nullable=True, default=None)

    def to_object(self) -> User:
        role = Role[self.role]
        cls = {Role.MANAGER: Manager, Role.ADMIN: Admin, Role.USER: User}
        obj = cls.get(role, User)(self.id, self.email)
        if role >= Role.MANAGER:
            obj.salt, obj.hash = self.salt, self.hash
        return obj

    @classmethod
    def from_object(cls, user: User):
        data = asdict(user)
        if "password" in data:
            del data["password"]
        if not data["id"]:
            del data["id"]
        return cls(**data, role=user.role())


session_factory = sessionmaker(engine)


def create_default_users():
    with session_factory() as session:
        users = [*map(UserOrm.from_object, default_users())]
        session.add_all(users)
        session.commit()


Base.metadata.create_all(engine)
create_default_users()
