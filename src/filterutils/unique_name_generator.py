class UniqueNameGenerator:
    def __init__(
        self,
        count_first: bool = False,
        prefix: str | None = None,
        suffix: str | None = None,
    ) -> None:
        self._count_first = count_first
        self._prefix = prefix
        self._suffix = suffix
        self._counter: dict[str, int] = {}

    def next(self, name: str) -> str:
        name_counter = self._counter.get(name, 1)
        self._counter[name] = name_counter + 1

        unique_name = name

        if self._prefix:
            unique_name = f"{self._prefix}_{unique_name}"

        if self._suffix:
            unique_name = f"{unique_name}_{self._suffix}"

        if name_counter == 1 and not self._count_first:
            return unique_name

        return f"{unique_name}_{name_counter}"
