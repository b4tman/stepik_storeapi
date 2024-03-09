from typing import Annotated
from fastapi import APIRouter, Depends, Path, status, HTTPException
from pydantic import UUID4, EmailStr

from store import services
from store.repositories import Repository
from store.schemas import (
    AddToCartModel,
    ErrorModel,
    GetCartModel,
    GetItemModel,
)

router = APIRouter(prefix="/cart", tags=["Корзина"])


@router.get(
    "/{email}",
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
    "",
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
    "/{email}/{item_id}",
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
