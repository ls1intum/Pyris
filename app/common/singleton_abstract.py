from abc import ABCMeta


class SingletonABCMeta(ABCMeta):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            # Ensure the class implements __call__ if it's not the ABC itself
            # This checks if '__call__' is implemented directly in the subclass
            if "__call__" in cls.__dict__:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
            else:
                raise NotImplementedError(
                    f"{cls.__name__} must implement the __call__ method."
                )
        return cls._instances[cls]
