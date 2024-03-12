import toml
from store.domains import Admin, Cart, Manager, User, Item
from store.utils import SingletonMeta


class Defaults(metaclass=SingletonMeta):
    DEFAULTS_PATH = "default.toml"

    def __init__(self):
        self.load()

    def load(self):
        with open(Defaults.DEFAULTS_PATH, "r", encoding="utf-8") as f:
            self.config = toml.load(f)
        self.load_users()
        self.load_items()
        self.load_carts()

    def load_users(self):
        users = []
        for user in self.config.get("users", []):
            cls = {"User": User, "Manager": Manager, "Admin": Admin}
            cls = cls.get(user["class"], User)
            del user["class"]
            users.append(cls(**user))
        self.__users = tuple(users)

    def load_items(self):
        items = []
        for item in self.config.get("items", []):
            items.append(Item(**item))
        self.__items = tuple(items)

    def load_carts(self):
        carts = []
        for cart in self.config.get("carts", []):
            carts.append(
                Cart(
                    id=cart["id"],
                    email=cart["email"],
                    items=[*map(lambda x: Item(**x), cart["items"])],
                )
            )
        self.__carts = tuple(carts)

    @property
    def users(self) -> tuple[User]:
        return self.__users

    @property
    def items(self) -> tuple[Item]:
        return self.__items

    @property
    def carts(self) -> tuple[Cart]:
        return self.__carts
