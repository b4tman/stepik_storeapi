from pydantic import BaseModel


class GetItemModel(BaseModel):
    """Данные товара

    Поля:

      - id (str): id товара
      - name (str): название товара
      - description (str): описание товара
      - price (float): цена
    """

    id: str
    name: str
    description: str
    price: float


class GetItemsModel(BaseModel):
    """Список товаров (ответ)

    Поля:

      - items (список: [GetItemModel]): список товаров
    """

    items: list[GetItemModel]


class CreateItemModel(BaseModel):
    """Данные товара для создания

    Поля:

      - name (str): название товара
      - description (str): описание товара
      - price (float): цена
    """

    name: str
    description: str
    price: float


class LoginModel(BaseModel):
    """Учетные данные пользователя

    Поля:

      - email (str): email пользователя
      - password (str): пароль пользователя
    """

    email: str
    password: str


class ErrorModel(BaseModel):
    """Информация об ошибке

    Поля:

      - detail (str): описание ошибки
    """

    detail: str


class GetCartModel(BaseModel):
    """Данные корзины

    Поля:

      - email (str): email пользователя
      - items (список: [GetItemModel]): список товаров
    """

    email: str
    items: list[GetItemModel]


class AddToCartModel(BaseModel):
    """Данные для добавления товара в корзину

    Поля:

      - email (str): email пользователя
      - item_id (str): id товара
    """

    email: str
    item_id: str


class CheckoutModel(BaseModel):
    """Данные для оформления заказа

    Поля:

      - email (str): email пользователя
    """

    email: str


class GetOrderModel(BaseModel):
    """Данные заказа

    Поля:

      - email (str): email пользователя
      - items (список: [GetItemModel]): список товаров
    """

    email: str
    items: list[GetItemModel]
