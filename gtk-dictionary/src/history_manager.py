class HistoryManager:
    """The dictionary history manager"""

    def __init__(self) -> None:
        self.clear_history()

    def clear_history(self) -> None:
        """Create or clear history"""
        self.storage = []
        self.index = -1

    def add(self, filename: str) -> None:
        """Add an element and remove branches of the history where necessary"""
        if self.index < len(self.storage) - 1:
            self.storage = self.storage[: self.index + 1]

        # Avoid adding the same word twice
        if self.storage and self.storage[-1] == filename:
            return

        self.storage.append(filename)
        self.index += 1

    def back(self) -> list[str] | None:
        """Move back in the history"""
        if self.can_go_back():
            self.index -= 1
            return self.storage[self.index]
        return None

    def forward(self) -> list[str] | None:
        """Move forward in the history"""
        if self.can_go_forward():
            self.index += 1
            return self.storage[self.index]
        return None

    def can_go_back(self) -> bool:
        """Assess whether user can move back"""
        return self.index > 0

    def can_go_forward(self) -> bool:
        """Assess whether user can move forward"""
        return self.index < len(self.storage) - 1
