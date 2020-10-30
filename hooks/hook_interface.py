class HooksManager(object):
    FILTERS = {}
    HOOK_TYPE = {}
    ACTIONS = {}

    @staticmethod
    def add_filter(name=None):
        def decorator(func):
            """
            :param function func:
            :return staticmethod:
            """
            class_name = func.__qualname__.split('.')[-2]
            if class_name not in HooksManager.FILTERS:
                HooksManager.FILTERS[class_name] = {}
            if name:
                HooksManager.FILTERS[class_name][name] = func
            else:
                HooksManager.FILTERS[class_name][func.__name__] = func
            return staticmethod(func)

        return decorator

    @staticmethod
    def add_action(name=None):
        def decorator(func):
            """
            :param function func:
            :return staticmethod:
            """
            class_name = func.__qualname__.split('.')[-2]
            if class_name not in HooksManager.ACTIONS:
                HooksManager.ACTIONS[class_name] = {}
            if name:
                HooksManager.ACTIONS[class_name][name] = func
            else:
                HooksManager.ACTIONS[class_name][func.__name__] = func
            return func

        return decorator

    @staticmethod
    def add_hook_handler(name):
        def decorator(hook_class):
            if not issubclass(hook_class, HookInterface):
                raise ValueError('hook class must inherit from ' + HookInterface.__name__)
            HooksManager.HOOK_TYPE[name] = hook_class
            return hook_class
        return decorator

    @staticmethod
    async def handle_hooks(hooks_type, hooks_list, *args, **kwargs):
        hooks_class = HooksManager.HOOK_TYPE[hooks_type]
        for hook_data in hooks_list:
            hook = hooks_class(hook_data, *args, **kwargs)
            await hook()


class HookInterface(object):

    def __init__(self, hook):
        self._hook = hook
        self._actions = hook['actions']
        self._namespace = {}

    def _filter(self):
        raise NotImplemented

    async def _action(self):
        for name, args in self._actions.items():
            if name in HooksManager.ACTIONS[self.__class__.__name__]:
                if isinstance(args, dict):
                    await HooksManager.ACTIONS[self.__class__.__name__][name](self, **args)
                else:
                    await HooksManager.ACTIONS[self.__class__.__name__][name](self, *args if type(args) is list else [args])

    async def __call__(self):
        if self._filter():
            await self._action()
