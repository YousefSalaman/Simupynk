
from Simupynk.runners import BaseRunner


class SequentialRunner(BaseRunner):

    def __init__(self, group_key, group_funcs, group_vars, group_trans=None):

        super().__init__(group_key, group_funcs, group_vars, group_trans)

    def _runSystemPrivate(self, group_key, sys_name, **kwargs):

        curr_sys_vars = self.group_vars[sys_name]
        sys_func = self.group_func_lists[sys_name]
        curr_sys_vars.update(sys_func(**curr_sys_vars))
        return self._extractDataFromSystemVariables(sys_name)
