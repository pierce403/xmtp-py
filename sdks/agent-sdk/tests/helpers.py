class DummyMessage:
    def __init__(self, content: str) -> None:
        self.content = content


class DummyContext:
    def __init__(self, content: str) -> None:
        self.message = DummyMessage(content)

    def is_text(self) -> bool:
        return True
