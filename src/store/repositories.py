from abc import ABC, abstractmethod
import shelve
from uuid import uuid4
import os
from store.default import default_users
from store.database import Database, UserOrm

from store.domains import Admin, Manager, User, Item, Cart, Order
from store.utils import SingletonMeta


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


class ShelveDatabase(metaclass=SingletonMeta):
    def __init__(self):
        self.path = os.getenv("DB_PATH", "db")
        self.ensure_path()

    def ensure_path(self):
        if not os.path.isdir(self.path):
            os.mkdir(self.path)

    def path_for(self, name):
        return os.path.join(self.path, name)


class OrmUsersRepository(UsersRepository):
    """
    Реализация пользовательского хранилища через SqlAlchemy orm.
    """

    def __init__(self):
        self.db = Database()

    def get_users(
        self, email: str | None = None, password: str | None = None
    ) -> list[User]:
        filtered_users = []

        with self.db.session() as s:
            if email is not None:
                users = s.query(UserOrm).filter(UserOrm.email == email)
            else:
                users = s.query(UserOrm).all()
            for user in map(UserOrm.to_object, users):
                if email is None:
                    filtered_users.append(user)
                    continue

                # не выполняем аутентификацию для пользователей ниже чем Менеджер
                if not isinstance(user, Manager):
                    continue
                if password is not None and not user.authenticate(password):
                    continue
                filtered_users.append(user)
                if password is not None or email is not None:
                    break
        return filtered_users


class ShelveItemsRepository(ItemsRepository):
    """Реализация хранилища товаров через shelve"""

    def __init__(self):
        self.db_name = ShelveDatabase().path_for("items")

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
        self.db_name = ShelveDatabase().path_for("carts")

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
        self.db_name = ShelveDatabase().path_for("orders")

    def place_order(self, order: Order):
        with shelve.open(self.db_name) as db:
            db[order.id] = order


class Repository(metaclass=SingletonMeta):
    """Настройки хранилищ"""

    users_repo = OrmUsersRepository
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
