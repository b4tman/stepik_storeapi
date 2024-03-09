from typing import Annotated
from fastapi import APIRouter, Depends, Path, status
from pydantic import UUID4

from store import services
from store.domains import Role
from store.repositories import Repository
from store.schemas import (
    ChangeItemModel,
    CreateItemModel,
    ErrorModel,
    GetItemModel,
    GetItemsModel,
    LoginModel,
)

router = APIRouter(prefix="/items", tags=["Товары"])


@router.get("", response_model=GetItemsModel)
def get_items() -> GetItemsModel:
    """Получение списка товаров

    Returns:
        GetItemsModel: список товаров
    """
    return services.get_items(Repository.items())


@router.post(
    "",
    response_model=GetItemModel,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"model": GetItemModel},
        401: {"model": ErrorModel},
        403: {"model": ErrorModel},
    },
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

    services.authorize(credentials, Role.ADMIN)
    return services.create_item(item, Repository.items())


@router.put(
    "/{item_id}",
    response_model=GetItemModel,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"model": GetItemModel},
        401: {"model": ErrorModel},
        403: {"model": ErrorModel},
        404: {"model": ErrorModel},
    },
)
def change_item(
    item_id: Annotated[UUID4, Path()],
    data: Annotated[ChangeItemModel, Depends()],
    credentials: Annotated[LoginModel, Depends()],
):  # credentials – тело с логином и паролем. Обычно аутентификация выглядит сложнее, но для нашего случая пойдет и так.
    """Изменение товара

    Args:
        item_id (str): id товара
        data (ChangeItemModel): данные товара
        credentials (LoginModel): учетные данные пользователя

    Raises:
        HTTPException: 401 если аутентификация не пройдена
        HTTPException: 403 если авторизация не пройдена
        HTTPException: 404 если не найден товар
    """

    services.authorize(credentials, Role.MANAGER)
    return services.change_item(item_id, data, Repository.items())
