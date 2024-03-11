from abc import ABC, abstractmethod
import shelve
from uuid import uuid4
import os
from store.default import default_users
from store.database import Database, ItemOrm, UserOrm, CartOrm, OrderOrm

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


class OrmUsersRepository(UsersRepository):
    """
    Реализация пользовательского хранилища через orm SqlAlchemy.
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


class OrmItemsRepository(ItemsRepository):
    """Реализация хранилища товаров через orm SqlAlchemy"""

    def __init__(self):
        self.db = Database()

    def get_items(self) -> list[Item]:
        with self.db.session() as session:
            return [*map(ItemOrm.to_object, session.query(ItemOrm).all())]

    def get_item(self, item_id: str) -> Item:
        with self.db.session() as session:
            item = session.get(ItemOrm, item_id)
            if item is None:
                raise KeyError("item not found")
            return item.to_object()

    def save_item(self, item: Item):
        with self.db.session() as session:
            obj = session.get(ItemOrm, item.id)
            if obj is None:
                session.add(ItemOrm.from_object(item))
            else:
                obj.name = item.name
                obj.description = item.description
                obj.price = item.price
            session.commit()


class OrmCartsRepository(CartsRepository):
    """Реализация хранилища корзин через orm SqlAlchemy"""

    def __init__(self):
        self.db = Database()

    def get_cart(self, user: User | None = None, email: str | None = None) -> Cart:
        if user is None and email is None:
            raise ValueError("no email")
        email = email or user.email
        with self.db.session() as session:
            cart = session.query(CartOrm).filter(CartOrm.email == email).scalar()
            if cart is None:
                return Cart(id=str(uuid4()), email=email, items=[])
            return cart.to_object()

    def save_cart(self, cart: Cart):
        with self.db.session() as session:
            is_new = session.get(ItemOrm, cart.id) is None
            obj = CartOrm.from_object(cart, session, update=True)
            if is_new:
                session.add(obj)
            session.commit()


class OrmOrdersRepository(OrdersRepository):
    """Реализация хранилища заказов через orm SqlAlchemy"""

    def __init__(self):
        self.db = Database()

    def place_order(self, order: Order):
        with self.db.session() as session:
            session.add(OrderOrm.from_object(order, session))
            session.commit()


class Repository(metaclass=SingletonMeta):
    """Настройки хранилищ"""

    users_repo = OrmUsersRepository
    items_repo = OrmItemsRepository
    carts_repo = OrmCartsRepository
    orders_repo = OrmOrdersRepository

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
