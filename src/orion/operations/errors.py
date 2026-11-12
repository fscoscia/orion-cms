class RevisionConflictError(Exception):
    """The page has a newer revision than the one the caller expected."""

    def __init__(self, expected, current):
        super().__init__(
            f"The page changed: you expected revision {expected} but the latest is "
            f"{current}. Read the page again and apply the change on top of it."
        )
        self.expected = expected
        self.current = current
