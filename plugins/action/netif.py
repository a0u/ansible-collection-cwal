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
            network = self._task.args.get('network')
            if network:
                if not isinstance(network, collections.Mapping):
                    result['failed'] = True
                    result['msg'] = "parameter 'network' must be a mapping"
                    return result

                clones = list()
                for iface, entry in network.items():
                    if 'ifconfig' in entry:
                        conf['ifconfig_{}'.format(iface)] = entry['ifconfig']
                    if 'alias' in entry:
                        conf.update({ 'ifconfig_{}_alias{}'.format(iface, idx): alias
                            for idx, alias in enumerate(entry['alias']) })
                    if 'aliases' in entry:
                        conf['ifconfig_{}_aliases'.format(iface)] = entry['aliases']

                    if 'cloned' in entry and boolean(entry['cloned'], strict=False):
                        clones.append(iface)

                if clones:
                    conf['cloned_interfaces'] = ' '.join(clones)

            if not conf:
                return result
            module_args = dict(
                file=self._task.args.get('file', '/etc/rc.conf.d/netif'),
                state='present',
                conf=conf,
            )

            result.update(self._execute_module(module_name='sysrc',
                module_args=module_args, task_vars=task_vars))
        except AnsibleAction as e:
            result.update(e.result)
        return result
