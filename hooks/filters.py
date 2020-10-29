FILTERS = {}


def add_filter(name=None):
    def decorator(func):
        """
        :param function func:
        :return staticmethod:
        """
        class_name = '.'.join(func.__qualname__.split('.')[0:-1])
        if class_name not in FILTERS:
            FILTERS[class_name] = {}
        if name:
            FILTERS[class_name][name] = func
        else:
            FILTERS[class_name][func.__name__] = func
        return staticmethod(func)
    return decorator

