from uuid import uuid4

from fastapi import HTTPException, status
from pydantic import UUID4

from store.domains import Cart, Item, Role, User, Order
from store.repositories import (
    ItemsRepository,
    Repository,
    UsersRepository,
    CartsRepository,
    OrdersRepository,
)
from store.schemas import (
    ChangeItemModel,
    CreateItemModel,
    GetItemModel,
    GetItemsModel,
    LoginModel,
)


class CartIsEmptyException(Exception):
    """Ошибка пустой корзины (при оформлении заказа)"""

    def __init__(self, message="cart is empty"):
        self.message = message


def get_items(repository: ItemsRepository) -> GetItemsModel:
    """Получение списка товаров"""
    items = repository.get_items()
    return GetItemsModel(items=[*map(GetItemModel.from_item, items)])


def create_item(item: CreateItemModel, repository: ItemsRepository) -> GetItemModel:
    """Создание товара"""
    data = item.model_dump()
    data["price"] = int(data["price"] * 100)
    item = Item(id=str(uuid4()), **data)
    repository.save_item(item=item)

    return GetItemModel.from_item(item)


def change_item(
    item_id: UUID4, data: ChangeItemModel, repository: ItemsRepository
) -> GetItemModel:
    """Изменение товара

    Args:
        item_id (UUID4): id товара
        data (ChangeItemModel): измененные данные товара
        repository (ItemsRepository): хранилище товаров
    """

    try:
        item = repository.get_item(str(item_id))
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="item not found"
        )

    data = data.model_dump()
    price = data.get("price")
    if price is not None:
        data["price"] = int(price * 100)

    for k, v in data.items():
        if not hasattr(item, k) or v is None:
            continue
        setattr(item, k, v)
    repository.save_item(item=item)

    return GetItemModel.from_item(item)


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


def remove_from_cart(item_id: str, email: str, repository: CartsRepository):
    """Удаление товара из коризны

    Args:
        item_id (str): id товара
        email (str): email пользователя
        carts_repository (CartsRepository): хранилище корзин
    """

    cart = repository.get_cart(email=email)
    new_items = []
    has_item = False

    for item in cart.items:
        if str(item.id) != str(item_id):
            new_items.append(item)
        else:
            has_item = True

    if not has_item:
        raise KeyError("item not found in cart")

    cart.items = new_items
    repository.save_cart(cart)


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


def authorize(credentials: LoginModel, required_role: Role):
    """Проверка доступа пользователя к ресурсу по требуемой роли

    Выполняет аутентификацию и авторизацию

    Args:
        credentials (LoginModel): данные пользователя
        required_role (Role): необходимая роль пользователя (не ниже)

    Raises:
        HTTPException: 401 если пользователь не аутентифицирован
        HTTPException: 403 если доступ запрещён
    """

    current_user = login(
        credentials.email,
        credentials.password.get_secret_value(),
        Repository.users(),
    )

    # Это аутентификация
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized user"
        )
    # а это авторизация
    if current_user.role() < required_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden resource"
        )
