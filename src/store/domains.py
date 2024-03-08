from dataclasses import dataclass, field
from enum import Enum
import hashlib
import hmac

from uuid import uuid4
from functools import total_ordering


@total_ordering
class Role(Enum):
    """Роль пользователя

    Значения:

      - **USER**: обычный пользователь
      - **MANAGER**: менеджер
      - **ADMIN**: админ
    """

    USER = 1
    MANAGER = 2
    ADMIN = 3

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.value.__eq__(other.value)

    def __lt__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.value.__lt__(other.value)


@dataclass
class Item:
    """Товар

    Поля:

      - id (str): id товара
      - name (str): название товара
      - description (str): описание товара
      - price (int): цена * 100 (чтобы небыло проблем с копейками в float)

    """

    id: str
    name: str
    description: str
    price: int


@dataclass
class Cart:
    """Корзина

    Поля:

      - id (str): id корзины
      - email (str): email корзины(пользователя)
      - items (list): список товаров
    """

    id: str
    email: str
    items: list[Item]


@dataclass
class User:
    """Обычный пользователь

    Поля:

      - id (str): id пользователя
      - email (str): email пользователя
    """

    id: str
    email: str

    def role(self) -> Role:
        """Роль пользователя"""
        return Role.USER


@dataclass
class Manager(User):
    """Пользователь, наделенный правами менеджера

    Доп.поля:

      - password (str) - пароль, используется для создания экземпляра, очищается после создания
      - salt (str): соль для хранения пароля
      - hash (str): хеш пароля
    """

    password: str
    salt: str = field(init=False)
    hash: str = field(init=False)

    def __post_init__(self):
        if self.password:
            self.set_password(self.password)
            self.password = ""
        else:
            self.salt = ""
            self.hash = ""

    def set_password(self, password):
        """Установка нового пароля (сохраняет хеш)"""
        self.salt = uuid4().hex
        self.hash = hashlib.sha512((password + self.salt).encode("utf-8")).hexdigest()

    def authenticate(self, password: str) -> bool:
        """Проверка пароля пользователя"""
        hash = hashlib.sha512((password + self.salt).encode("utf-8")).digest()
        return hmac.compare_digest(hash, bytes.fromhex(self.hash))

    def role(self) -> Role:
        return Role.MANAGER


@dataclass
class Admin(Manager):
    """Пользователь, наделенный правами администратора"""

    def role(self) -> Role:
        return Role.ADMIN


@dataclass
class Order:
    """Заказ

    Поля:

      - id (str): id заказа
      - email (str): email заказа(пользователя)
      - items (list): список товаров"""

    id: str
    email: str
    items: list[Item]

    @classmethod
    def from_cart(cls, cart: Cart, user: User | None = None, email: str | None = None):
        """Создание заказа из корзины"""

        if user is None and email is None:
            raise ValueError("no email")
        email = email or user.email
        return cls(str(uuid4()), email, cart.items.copy())
