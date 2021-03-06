# -*- coding: utf-8 -*-

__author__  = 'Patrick Michl'
__email__   = 'patrick.michl@gmail.com'
__license__ = 'GPLv3'

import nemoa.network.builder.layer

def types(type = None):
    """Get supported network types of network builders."""

    type_dict = {}

    # get supported layered networks
    layer_types = nemoa.network.builder.layer.types()
    for key, val in list(layer_types.items()):
        type_dict[key] = ('layer', val)

    if type == None:
        return {key: val[1] for key, val in list(type_dict.items())}
    if type in type_dict:
        return type_dict[type]

    return None

def build(type, *args, **kwargs):
    """Build network from parameters, datasets, etc. ."""

    # test if type is supported
    if not type in list(types().keys()):
        nemoa.log('error', """could not build network:
            type '%s' is not supported.""" % type)
        return {}

    module_name = types(type)[0]

    if module_name == 'layer':
        network = nemoa.network.builder.layer.build(type, *args,
            **kwargs)

    return network or {}
