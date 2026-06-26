class UniqueNameGenerator:
    def __init__(self, modify_first: bool = False) -> None:
        self._modify_first_name = modify_first
        self._counter: dict[str, int] = {}

    def next(self, name: str) -> str:
        self._counter[name] = self._counter.get(name, 0) + 1
        if self._counter[name] == 1 and not self._modify_first_name:
            return name

        return f"{name}_{self._counter[name]}"
