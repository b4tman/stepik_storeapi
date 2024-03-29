from typing import Annotated
from fastapi import APIRouter, Depends, status, HTTPException

from store import services
from store.repositories import Repository
from store.schemas import (
    CheckoutModel,
    ErrorModel,
    GetItemModel,
    GetOrderModel,
)

router = APIRouter(tags=["Заказ"])


@router.post(
    "/checkout",
    response_model=GetOrderModel,
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

    result = GetOrderModel(
        email=order.email,
        items=[*map(GetItemModel.from_item, order.items)],
    )
    return result
