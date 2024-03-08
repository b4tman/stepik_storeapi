from typing import Annotated
from fastapi import APIRouter, Depends, Path, status, HTTPException
from pydantic import UUID4, EmailStr

from store import services
from store.domains import Role
from store.repositories import Repository
from store.schemas import (
    AddToCartModel,
    CheckoutModel,
    CreateItemModel,
    ErrorModel,
    GetCartModel,
    GetItemModel,
    GetItemsModel,
    GetOrderModel,
    LoginModel,
)

router = APIRouter()  # это роутер, он нужен для FastAPI, чтобы определять эндпоинты


@router.get("/items", response_model=GetItemsModel)
def get_items() -> GetItemsModel:
    """Получение списка пользователей

    Returns:
        GetItemsModel: список пользователей
    """
    items = services.get_items(Repository.items())
    return GetItemsModel(
        items=[
            GetItemModel(
                id=item.id,
                name=item.name,
                description=item.description,
                price=item.price / 100,
            )
            for item in items
        ]
    )


@router.post(
    "/items",
    response_model=GetItemModel,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"model": GetItemModel},
        401: {"model": ErrorModel},
        403: {"model": ErrorModel},
    },  # Это нужно для сваггера. Мы перечисляем ответы эндпоинта, чтобы получить четкую документацию.
)
def create_item(
    item: Annotated[CreateItemModel, Depends()],
    credentials: Annotated[LoginModel, Depends()],
) -> (
    GetItemModel
):  # credentials – тело с логином и паролем. Обычно аутентификация выглядит сложнее, но для нашего случая пойдет и так.
    """Создание товара

    Args:
        item (CreateItemModel): данные нового товара
        credentials (LoginModel): учетные данные пользователя

    Raises:
        HTTPException: 401 если аутентификация не пройдена
        HTTPException: 403 если авторизация не пройдена

    Returns:
        GetItemModel: товар
    """

    current_user = services.login(
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
    if current_user.role() != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden resource"
        )

    item = services.create_item(
        item.name,
        item.description,
        int(item.price * 100),
        Repository.items(),
    )
    return GetItemModel(
        id=item.id, name=item.name, description=item.description, price=item.price / 100
    )


@router.put(
    "/items/{item_id}",
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"model": None},
        401: {"model": ErrorModel},
        403: {"model": ErrorModel},
        404: {"model": ErrorModel},
    },  # Это нужно для сваггера. Мы перечисляем ответы эндпоинта, чтобы получить четкую документацию.
)
def change_item(
    item_id: Annotated[UUID4, Path()],
    data: Annotated[CreateItemModel, Depends()],
    credentials: Annotated[LoginModel, Depends()],
):  # credentials – тело с логином и паролем. Обычно аутентификация выглядит сложнее, но для нашего случая пойдет и так.
    """Изменение товара

    Args:
        item_id (str): id товара
        data (CreateItemModel): данные товара
        credentials (LoginModel): учетные данные пользователя

    Raises:
        HTTPException: 401 если аутентификация не пройдена
        HTTPException: 403 если авторизация не пройдена
        HTTPException: 404 если не найден товар
    """

    current_user = services.login(
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
    if current_user.role() < Role.MANAGER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden resource"
        )

    try:
        services.change_item(
            str(item_id),
            Repository.items(),
            name=data.name,
            description=data.description,
            price=int(data.price * 100),
        )
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="item not found"
        )


@router.get(
    "/cart/{email}",
    response_model=GetCartModel,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"model": GetCartModel},
    },
)
def get_cart(email: Annotated[EmailStr, Path()]) -> GetCartModel:
    """Получение корзины

    Args:
        email (str): email пользователя

    Returns:
        GetCartModel: данные корзины
    """
    cart = services.get_cart(
        email,
        Repository.carts(),
    )

    return GetCartModel(
        email=cart.email,
        items=[
            GetItemModel(
                id=item.id,
                name=item.name,
                description=item.description,
                price=item.price / 100,
            )
            for item in cart.items
        ],
    )


@router.post(
    "/cart",
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
    responses={204: {"model": None}, 404: {"model": ErrorModel}},
)
def add_to_cart(data: Annotated[AddToCartModel, Depends()]):
    """Добавление товара в корзину

    Args:
        data (AddToCartModel): данные запроса (email и item_id)

    Raises:
        HTTPException: 404 если товар не найден
    """

    try:
        services.add_to_cart(
            str(data.item_id), data.email, Repository.items(), Repository.carts()
        )
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="item not found"
        )


@router.delete(
    "/cart/{email}/{item_id}",
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
    responses={204: {"model": None}, 404: {"model": ErrorModel}},
)
def remove_from_cart(
    email: Annotated[EmailStr, Path()], item_id: Annotated[UUID4, Path()]
):
    """Удаление товара из корзины

    Args:
        email (str): email пользователя
        item_id (str): id товара

    Raises:
        HTTPException: 404 если товар не найден
    """
    try:
        services.remove_from_cart(str(item_id), email, Repository.carts())
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="item not found"
        )


@router.post(
    "/checkout",
    response_model=CheckoutModel,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"model": GetOrderModel},
        428: {"model": ErrorModel},
    },
)
def checkout(data: Annotated[CheckoutModel, Depends()]) -> GetOrderModel:
    """Оформление заказа

    Args:
        data (CheckoutModel): данные (email)

    Raises:
        HTTPException: 428 если корзина пустая

    Returns:
        GetOrderModel: данные заказа
    """
    try:
        order = services.checkout(
            data.email,
            Repository.carts(),
            Repository.orders(),
        )
    except services.CartIsEmptyException:
        raise HTTPException(
            status_code=status.HTTP_428_PRECONDITION_REQUIRED, detail="cart is empty"
        )

    return GetOrderModel(
        email=order.email,
        items=[
            GetItemModel(
                id=item.id,
                name=item.name,
                description=item.description,
                price=item.price / 100,
            )
            for item in order.items
        ],
    )
