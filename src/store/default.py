import toml
from store.domains import User, Admin, Manager

DEFAULTS_PATH = "default.toml"


def get_defaults():
    with open(DEFAULTS_PATH, "r", encoding="utf-8") as f:
        defaults = toml.load(f)
    return defaults


def default_users():
    defaults = get_defaults()
    result = []
    for user in defaults.get("users", []):
        cls = {"User": User, "Manager": Manager, "Admin": Admin}
        cls = cls.get(user["class"], User)
        del user["class"]
        result.append(cls(**user))
    return result
