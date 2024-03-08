from abc import ABC, abstractmethod
import shelve
from uuid import uuid4

from store.domains import Admin, Manager, User, Item, Cart, Order


class SingletonMeta(type):
    """Метакласс для Singleton классов"""

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonMeta, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class UsersRepository(ABC):
    """
    Абстрактный репозиторий для пользователей.
    От него нужно наследоваться в случае, когда нужно сделать другое хранилище, старое переписывать не нужно.
    """

    @abstractmethod
    def get_users(
        self, email: str | None = None, password: str | None = None
    ) -> list[User]:
        """Получение списка пользователей

        :param email: фильтр по email
        :param password: фильтр по паролю
        :return: отфильтрованные пользователи
        """
        pass


class ItemsRepository(ABC):
    """
    Абстрактный репозиторий для товаров.
    Он содержит методы, которые нужно реализовать в случае если захочется сделать новую реализацию репозитория.
    """

    @abstractmethod
    def get_items(self) -> list[Item]:
        """Получение списка товаров

        :return: список товаров
        """
        pass

    @abstractmethod
    def get_item(self, item_id: str) -> Item:
        """Получение товара по id

        :param item_id: id товара
        :return: список товаров
        """
        pass

    @abstractmethod
    def save_item(self, item: Item):
        """Сохранение товара

        :param item: товар
        """
        pass


class CartsRepository(ABC):
    """
    Абстрактный репозиторий для корзины.
    Он содержит методы, которые нужно реализовать в случае если захочется сделать новую реализацию репозитория.
    """

    @abstractmethod
    def get_cart(self, user: User | None = None, email: str | None = None) -> Cart:
        """Получение корзины по пользователю или email

        :param user: пользователь
        :param email: email
        :return: объект корзины
        """
        pass

    @abstractmethod
    def save_cart(self, cart: Cart):
        """Сохранение корзины

        :param cart: Корзина
        """
        pass


class OrdersRepository(ABC):
    """
    Абстрактный репозиторий для заказов.
    Он содержит методы, которые нужно реализовать в случае если захочется сделать новую реализацию репозитория.
    """

    @abstractmethod
    def place_order(self, order: Order):
        """Сохранение заказа

        :param order: заказ
        """
        pass


class MemoryUsersRepository(UsersRepository):
    """
    Реализация пользовательского хранилища в оперативной памяти.
    Пользователи инициализируются во время инициализации репозитория
    """

    def __init__(self):
        self.users = [
            User(
                id="2e6db091-cbbc-4b78-98b0-1ec90cd7daae",
                email="vasya@example.com",
            ),
            Manager(
                id="0bc224c6-f78e-4de9-a3de-fe17451e6d0d",
                email="ivan@example.com",
                password="test",
            ),
            Admin(
                id="c56013d7-f913-4b88-bc76-52bfe4a1791d",
                email="admin@example.com",
                password="god",
            ),
        ]

    def get_users(
        self, email: str | None = None, password: str | None = None
    ) -> list[User]:
        filtered_users = []  # тут собираются отфильтрованные пользователи
        for (
            user
        ) in (
            self.users
        ):  # перебираем всех пользователей и осталвяем только тех, кто прошел фильтры
            if email is not None and user.email != email:
                continue
            if not isinstance(user, Manager):
                continue
            if password is not None and not user.authenticate(password):
                continue
            filtered_users.append(user)
            if password is not None or email is not None:
                break  # только 1 пользователь по email или password
        return filtered_users


class ShelveItemsRepository(ItemsRepository):
    """Реализация хранилища товаров через shelve"""

    def __init__(self):
        self.db_name = "items"

    def get_items(self) -> list[Item]:
        with shelve.open(self.db_name) as db:
            return list(db.values())

    def get_item(self, item_id: str) -> Item:
        with shelve.open(self.db_name) as db:
            return db[item_id]

    def save_item(self, item: Item):
        with shelve.open(self.db_name) as db:
            db[item.id] = item


class ShelveCartsRepository(CartsRepository):
    """Реализация хранилища корзин через shelve"""

    def __init__(self):
        self.db_name = "carts"

    def get_cart(self, user: User | None = None, email: str | None = None) -> Cart:
        if user is None and email is None:
            raise ValueError("no email")
        email = email or user.email
        with shelve.open(self.db_name) as db:
            for cart in db.values():
                if cart.email == email:
                    return cart
            cart = Cart(str(uuid4()), email, [])
            return cart

    def save_cart(self, cart: Cart):
        with shelve.open(self.db_name) as db:
            db[cart.id] = cart


class ShelveOrdersRepository(OrdersRepository):
    """Реализация хранилища заказов через shelve"""

    def __init__(self):
        self.db_name = "carts"

    def place_order(self, order: Order):
        with shelve.open(self.db_name) as db:
            db[order.id] = order


class Repository(metaclass=SingletonMeta):
    """Настройки хранилищ"""

    users_repo = MemoryUsersRepository
    items_repo = ShelveItemsRepository
    carts_repo = ShelveCartsRepository
    orders_repo = ShelveOrdersRepository

    @classmethod
    def users(cls):
        """Используемое хранилище пользователей"""
        return cls.users_repo()

    @classmethod
    def items(cls):
        """Используемое хранилище товаров"""
        return cls.items_repo()

    @classmethod
    def carts(cls):
        """Используемое хранилище корзин"""
        return cls.carts_repo()

    @classmethod
    def orders(cls):
        """Используемое хранилище заказов"""
        return cls.orders_repo()
