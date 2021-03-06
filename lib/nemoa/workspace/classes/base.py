# -*- coding: utf-8 -*-

__author__  = 'Patrick Michl'
__email__   = 'patrick.michl@gmail.com'
__license__ = 'GPLv3'

import imp
import nemoa
import os

class Workspace:
    """Nemoa workspace class."""

    _config    = None
    _default   = {}
    _attr_meta = {'name': 'r', 'about': 'rw', 'path': 'r', 'base': 'r'}

    def __getattr__(self, key):
        """Attribute wrapper to getter methods."""

        if key in self._attr_meta:
            if 'r' in self._attr_meta[key]: return self._get_meta(key)
            return nemoa.log('warning',
                "attribute '%s' is not readable.")

        raise AttributeError('%s instance has no attribute %r'
            % (self.__class__.__name__, key))

    def __setattr__(self, key, val):
        """Attribute wrapper to setter methods."""

        if key in self._attr_meta:
            if 'w' in self._attr_meta[key]:
                return self._set_meta(key, val)
            return nemoa.log('warning',
                "attribute '%s' is not writeable." % key)

        self.__dict__[key] = val

    def __init__(self, *args, **kwargs):
        """Import object configuration and content from dictionary."""

        self._set_copy(**kwargs)

    def get(self, key = 'name', *args, **kwargs):
        """Get meta data of workspace."""

        # meta information
        if key in self._attr_meta: return self._get_meta(key)

        return nemoa.log('warning', "unknown key '%s'" % key)

    def _get_meta(self, key):
        """Get meta information like 'name' or 'path'."""

        if key == 'about': return self._get_about()
        if key == 'base': return self._get_about()
        if key == 'name': return self._get_name()
        if key == 'path': return self._get_path()

        return nemoa.log('warning', "unknown key '%s'" % key)

    def _get_about(self):
        """Get description.

        Short description of the content of the resource.

        Returns:
            Basestring containing a description of the resource.

        """

        return self._config.get('about', None)

    def _get_base(self):
        """Get workspace base."""

        return self._config.get('base', None)

    def _get_name(self):
        """Get name."""

        return self._config.get('name', None)

    def _get_path(self):
        """Get path."""

        return self._config.get('path', None)

    def set(self, key = None, *args, **kwargs):
        """Set meta data of workspace."""

        # set meta information
        if key in self._attr_meta:
            return self._set_meta(key, *args, **kwargs)

        # import workspace configuration configuration and dataset tables
        if key == 'copy': return self._set_copy(*args, **kwargs)
        if key == 'config': return self._set_config(*args, **kwargs)

        return nemoa.log('warning', "unknown key '%s'" % key)

    def _set_meta(self, key, *args, **kwargs):
        """Set meta information like 'name' or 'path'."""

        if key == 'about': return self._set_about(*args, **kwargs)

        return nemoa.log('warning', "unknown key '%s'" % key)

    def _set_about(self, val):
        """Set description."""

        if not isinstance(val, str): return nemoa.log('warning',
            "attribute 'about' requires datatype 'basestring'.")
        self._config['about'] = val

        return True

    def _set_copy(self, config = None):
        """Set workspace configuration and dataset tables.

        Args:
            config (dict or None, optional): workspace configuration

        Returns:
            Bool which is True if and only if no error occured.

        """

        retval = True

        if config: retval &= self._set_config(config)

        return retval

    def _set_config(self, config = None):
        """Set configuration of workspace.

        Args:
            config (dict or None, optional): workspace configuration

        Returns:
            Bool which is True if and only if no error occured.

        """

        # initialize configuration dictionary
        if not self._config: self._config = self._default.copy()

        # update configuration dictionary
        if not config: return True
        self._config = nemoa.common.dict.merge(config, self._config)

        return True

    def list(self, type):
        """Return a list of known objects."""

        return nemoa.list(type,
            workspace = self._get_name(), base = self._get_base())
