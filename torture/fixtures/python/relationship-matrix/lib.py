def helper() -> str:
    return "help"


class Worker:
    def __init__(self) -> None:
        self.ready = True

    def process_item(self) -> str:
        return "processed"


class Base:
    def hook(self) -> str:
        return "base"


class Child(Base):
    def hook(self) -> str:
        return "child"


class Special:
    def special_action(self) -> str:
        return "special"


class First:
    def shared_action(self) -> str:
        return "first"


class Second:
    def shared_action(self) -> str:
        return "second"
