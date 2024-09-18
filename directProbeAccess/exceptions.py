class UserError(Exception):
    default_description = 'User error'
    def __init__(self, *args: object,message=None, **kwargs) -> None:
        if args:
            message = args[0]
            args = args[1:]
        super().__init__(*args, **kwargs)
        self.message = message

    def __str__(self) -> str:
        return self.message or self.default_description


class TooManyProbes(UserError):
    default_description = 'too many probes plugged in at once'
    def __init__(self, *args: object,message=None,  **kwargs) -> None:
        if args:
            message = args[0]
            args = args[1:]
        super().__init__(*args, message=message, **kwargs)

    def __str__(self) -> str:
        return self.message or self.default_description