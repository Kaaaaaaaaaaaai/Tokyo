from uuid import UUID, uuid4


class IdFactory:
    """Central UUID factory for externally visible IDs."""

    def new(self) -> UUID:
        return uuid4()

