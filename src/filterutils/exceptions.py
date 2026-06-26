class FilterError(Exception): ...


class FilterConfigurationError(FilterError): ...


class FilterExpressionError(FilterError):
    def __init__(self, expression: str, detail: str | None = None) -> None:
        message = f"Invalid filter expression: '{expression}'."
        if detail:
            message += f" {detail}"

        super().__init__(message)
        self.expression = expression
        self.detail = detail


class FilterExpressionParsingError(FilterError): ...


class FilterEvaluationError(FilterError): ...
