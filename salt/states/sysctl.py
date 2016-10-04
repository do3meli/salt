# -*- coding: utf-8 -*-
'''
Configuration of the Linux kernel using sysctl
==============================================

Control the kernel sysctl system.

.. code-block:: yaml

  vm.swappiness:
    sysctl.present:
      - value: 20
'''
from __future__ import absolute_import

# Import python libs
import re

# Import salt libs
from salt.exceptions import CommandExecutionError


def __virtual__():
    '''
    This state is only available on Minions which support sysctl
    '''
    return 'sysctl.show' in __salt__



def present(name, value, config=None):
    '''
    Ensure that the named sysctl value is set in memory and persisted to the
    named configuration file. The default sysctl configuration file is
    /etc/sysctl.conf

    name
        The name of the sysctl value to edit

    value
        The sysctl value to apply

    config
        The location of the sysctl configuration file. If not specified, the
        proper location will be detected based on platform.
    '''
    ret = {'name': name,
           'result': True,
           'changes': {},
           'comment': ''}

    current = __salt__['sysctl.get'](name)

    if config is None:
        # Certain linux systems will ignore /etc/sysctl.conf, get the right
        # default configuration file.
        if 'sysctl.default_config' in __salt__:
            config = __salt__['sysctl.default_config']()
        else:
            config = '/etc/sysctl.conf'

    if 'unknown oid' in current:
        # previous versions of this state wrote an unknown oid to the
        # given config file even if the state failed to persist the key/value
        # in memory. now abort very early if one tries to do this.
        ret['result'] = False
        ret['comment'] = ('This sysctl parameter is unknown to the system')
        return ret

    if __opts__['test']:

        configured = __salt__['sysctl.show'](config_file=config)

        # eval comparison first for faster test
        memory_value_correct = str(current).split() == str(value).split()
        config_value_correct = str(configured[name]).split() == str(value).split()

        if memory_value_correct and config_value_correct:
            ret['result'] = True
            ret['comment'] = ('Sysctl value {0} = {1} is already set'.format(name, value))
            return ret

        elif memory_value_correct and not config_value_correct:
            ret['result'] = None
            ret['changes'] = { 'old' : configured[name], 'new' : value }
            ret['comment'] = ('Sysctl value is currently set on the running system but not '
                              'correct in config file. Will adjust config file accordingly.')
            return ret

        elif not memory_value_correct and config_value_correct:
            ret['result'] = None
            ret['changes'] = { 'old' : str(current), 'new' : str(value) }
            ret['comment'] = ('Current running sysctl configuration is different from config. '
                              'Will adjust running sysctl value.')
            return ret

        else:
            # use "else" instead of "not memory_value_correct and not config_value_correct"
            # to make sure we return at least something before actual execution...
            ret['result'] = None
            ret['changes'] = { 'new' : value }
            ret['comment'] = ('Sysctl option set to be changed.')
            return ret

    try:
        update = __salt__['sysctl.persist'](name, value, config)
    except CommandExecutionError as exc:
        ret['result'] = False
        ret['comment'] = (
            'Failed to set {0} to {1}: {2}'.format(name, value, exc)
        )
        return ret

    if update == 'Updated':
        ret['changes'] = {name: value}
        ret['comment'] = 'Updated sysctl value {0} = {1}'.format(name, value)
    elif update == 'Already set':
        ret['comment'] = (
            'Sysctl value {0} = {1} is already set'
            .format(name, value)
        )

    return ret
