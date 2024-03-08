from uuid import uuid4

from store.domains import Cart, Item, User, Order
from store.repositories import (
    ItemsRepository,
    UsersRepository,
    CartsRepository,
    OrdersRepository,
)


class CartIsEmptyException(Exception):
    """Ошибка пустой корзины (при оформлении заказа)"""

    def __init__(self, message="cart is empty"):
        self.message = message


def get_items(repository: ItemsRepository) -> list[Item]:
    """Получение списка товаров"""
    return repository.get_items()


def create_item(
    name: str, description: str, price: int, repository: ItemsRepository
) -> Item:
    """Создание товара"""
    item = Item(id=str(uuid4()), name=name, description=description, price=price)
    repository.save_item(item=item)
    return item


def change_item(item_id: str, repository: ItemsRepository, **kwargs):
    """Изменение товара

    Args:
        item_id (str): id товара
        repository (ItemsRepository): хранилище товаров
    Keyword args:
        name (str): имя
        description (str): описание
        price (int): цена * 100
    """
    item = repository.get_item(item_id)
    for k, v in kwargs.items():
        if not hasattr(item, k):
            continue
        setattr(item, k, v)
    repository.save_item(item=item)


def get_cart(
    email: str,
    repository: CartsRepository,
) -> Cart:
    """_summary_

    Args:
        email (str): email пользователя
        repository (CartsRepository): хранилище корзин

    Returns:
        Cart: объект корзины
    """
    return repository.get_cart(email=email)


def add_to_cart(
    item_id: str,
    email: str,
    items_repository: ItemsRepository,
    carts_repository: CartsRepository,
):
    """Добавление товара в корзину

    Args:
        item_id (str): id товара
        email (str): email пользователя
        items_repository (ItemsRepository): хранилище товаров
        carts_repository (CartsRepository): хранилище корзин
    """
    item = items_repository.get_item(item_id)
    cart = carts_repository.get_cart(email=email)
    cart.items.append(item)
    carts_repository.save_cart(cart)


def remove_from_cart(item_id: str, email: str, carts_repository: CartsRepository):
    """Удаление товара из коризны

    Args:
        item_id (str): id товара
        email (str): email пользователя
        carts_repository (CartsRepository): хранилище корзин
    """

    cart = carts_repository.get_cart(email=email)
    cart.items = [item for item in cart.items if item.id != item_id]
    carts_repository.save_cart(cart)


def checkout(
    email: str, carts_repository: CartsRepository, orders_repository: OrdersRepository
) -> Order:
    """Оформление заказа

    Args:
        email (str): email пользователя
        carts_repository (CartsRepository): хранилище корзин
        orders_repository (OrdersRepository): хранилище заказов

    Raises:
        CartIsEmptyException: ошибка если корзина пуста

    Returns:
        Order: объект заказа
    """

    cart = carts_repository.get_cart(email=email)
    if not cart.items:
        raise CartIsEmptyException()
    order = Order.from_cart(cart)
    orders_repository.place_order(order)
    cart.items.clear()
    carts_repository.save_cart(cart)
    return order


def login(email: str, password: str, repository: UsersRepository) -> User | None:
    """Аутентификация пользователя

    Args:
        email (str): email пользователя
        password (str): пароль пользователя
        repository (UsersRepository): хранилище пользователей

    Returns:
        User | None: пользователь если аутентификация успешна
    """
    users = repository.get_users(email=email, password=password)
    if users:
        return users[0]
