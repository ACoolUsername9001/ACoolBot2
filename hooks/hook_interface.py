from hooks.filters import FILTERS


class HookInterface(object):
    def __init__(self, hook_type, hook):
        self._hook_type = hook_type
        self._hook = hook
        self._filters = hook['filters']
        self._actions = hook['actions']
        self._namespace = {}

    def _filter(self):
        filters_result = (FILTERS[self.__class__.__name__][f_name](args) for f_name, args in self._filters.items() if f_name in FILTERS[self.__class__.__name__])
        if all(filters_result):
            return True
        return False

    def _action(self):
        raise NotImplemented()

    async def __call__(self):
        if self._filter():
            await self._action()
