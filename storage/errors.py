class DatabaseError(Exception):
    def __init__(self, message: str, **kwargs):
        self.message = message
        self.context = kwargs  # keep all extra info for logging or debugging
        
        # Build a detailed message string
        context_str = " | ".join(f"{key}={value}" for key, value in kwargs.items())
        if context_str:
            full_message = f"{message} ({context_str})"
        else:
            full_message = message
        
        super().__init__(full_message)

class InnerTypeError(TypeError):
    def __init__(self, *args):
        super().__init__("Datatype within addition[key] doesnt exist",*args)

class InnerKeyError(KeyError):
    def __init__(self, *args):
        super().__init__("Key within addition doesnt exist",*args)

class ConditionError(Exception):
    def __init__(self):
        super().__init__("Condition was not callable")

class FunctionChoiceError(Exception):
    def __init__(self, message, **kwargs):
        context_str = " | ".join(f"{key}={value}" for key, value in kwargs.items())
        if context_str:
            full_message = f"{message} ({context_str})"
        else:
            full_message = message
        super().__init__(full_message)

class UpdateError(Exception):
    def __init__(self, message, **kwargs):
        context_str = " | ".join(f"{key}={value}" for key, value in kwargs.items())
        if context_str:
            full_message = f"{message} ({context_str})"
        else:
            full_message = message
        super().__init__(full_message)

