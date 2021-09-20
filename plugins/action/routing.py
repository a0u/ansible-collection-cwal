from ansible.errors import AnsibleAction
from ansible.module_utils.parsing.convert_bool import boolean
from ansible.plugins.action import ActionBase
import collections

class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        try:
            conf = dict()

            gateway = self._task.args.get('gateway')
            if gateway is not None:
                conf['gateway_enable'] = boolean(gateway, strict=False)

            defaultrouter = self._task.args.get('default')
            if defaultrouter is not None:
                conf['defaultrouter'] = defaultrouter

            routes = self._task.args.get('routes')
            if routes:
                if not isinstance(routes, collections.Mapping):
                    result['failed'] = True
                    result['msg'] = "parameter 'routes' must be a mapping"
                    return result
                conf['static_routes'] = ' '.join(routes.keys())
                conf.update({ 'route_{}'.format(k): v for k, v in routes.items() })

            if not conf:
                return result
            module_args = dict(
                file=self._task.args.get('file', '/etc/rc.conf.d/routing'),
                state='present',
                conf=conf,
            )

            result.update(self._execute_module(module_name='sysrc',
                module_args=module_args, task_vars=task_vars))
        except AnsibleAction as e:
            result.update(e.result)
        return result
