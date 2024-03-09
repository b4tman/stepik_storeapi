from pydantic import UUID4, BaseModel, EmailStr, PositiveFloat, SecretStr


class GetItemModel(BaseModel):
    """Данные товара

    Поля:

      - id (str): id товара
      - name (str): название товара
      - description (str): описание товара
      - price (float): цена
    """

    id: UUID4
    name: str
    description: str | None = None
    price: PositiveFloat


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
    description: str | None = None
    price: PositiveFloat


class ChangeItemModel(BaseModel):
    """Данные товара для изменения

    Поля:

      - name (str): название товара
      - description (str): описание товара
      - price (float): цена
    """

    name: str | None = None
    description: str | None = None
    price: PositiveFloat | None = None


class LoginModel(BaseModel):
    """Учетные данные пользователя

    Поля:

      - email (str): email пользователя
      - password (str): пароль пользователя
    """

    email: EmailStr
    password: SecretStr


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

    email: EmailStr
    items: list[GetItemModel]


class AddToCartModel(BaseModel):
    """Данные для добавления товара в корзину

    Поля:

      - email (str): email пользователя
      - item_id (str): id товара
    """

    email: EmailStr
    item_id: UUID4


class CheckoutModel(BaseModel):
    """Данные для оформления заказа

    Поля:

      - email (str): email пользователя
    """

    email: EmailStr


class GetOrderModel(BaseModel):
    """Данные заказа

    Поля:

      - email (str): email пользователя
      - items (список: [GetItemModel]): список товаров
    """

    email: EmailStr
    items: list[GetItemModel]
