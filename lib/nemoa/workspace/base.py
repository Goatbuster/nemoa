# -*- coding: utf-8 -*-

__author__  = 'Patrick Michl'
__email__   = 'patrick.michl@gmail.com'
__license__ = 'GPLv3'

import glob
import imp
import nemoa
import os

class Workspace:
    """Nemoa workspace class."""

    _config = None
    _attr_meta = {'name': 'r', 'about': 'rw', 'path': 'r', 'base': 'r'}

    def __init__(self, workspace = None, base = None):
        """Initialize shared configuration."""

        self._config = {}

        if workspace:
            self.load(workspace, base = base)

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
                "attribute '%s' is not writeable." % (key))

        self.__dict__[key] = val

    def load(self, workspace, base = None):
        """Import workspace and update paths and logfile."""

        if nemoa.workspace.load(workspace, base = base):
            self._config['name'] = workspace
            self._config['base'] = base
            return True

        return nemoa.log('error', """could not load workspace:
            no workspace '%s' could be found.""" % (workspace))

    def _get_meta(self, key):
        """Get meta information like 'name' or 'path'."""

        if key == 'about': return self._get_about()
        if key == 'base': return self._get_about()
        if key == 'name': return self._get_name()
        if key == 'path': return self._get_path()

        return nemoa.log('warning', "unknown key '%s'" % (key))

    def _get_about(self):
        """Get description.

        Short description of the content of the resource.

        Returns:
            Basestring containing a description of the resource.

        """

        if 'about' in self._config: return self._config['about']

        return None

    def _get_base(self):
        """Get workspace base."""

        if 'base' in self._config: return self._config['base']

        return None

    def _get_name(self):
        """Get name."""

        if 'name' in self._config: return self._config['name']

        return None

    def _get_path(self):
        """Get path."""

        if 'path' in self._config: return self._config['path']

        return None

    def _set_meta(self, key, *args, **kwargs):
        """Set meta information like 'name' or 'path'."""

        if key == 'about': return self._set_about(*args, **kwargs)

        return nemoa.log('warning', "unknown key '%s'" % (key))

    def _set_about(self, val):
        """Set description."""

        if not isinstance(val, basestring): return nemoa.log('warning',
            "attribute 'about' requires datatype 'basestring'.")
        self._config['about'] = val

        return True

    def list(self, type = None):
        """Return a list of known objects."""

        return nemoa.workspace.list(type = type,
            workspace = self._get_name(), base = self._get_base())

    def execute(self, name = None, *args, **kwargs):
        """Execute script."""

        config = nemoa.workspace.get('script', name)
        if not config: return False
        if not os.path.isfile(config['path']):
            return nemoa.log('error', """could not run script '%s':
                file '%s' not found.""" % (name, config['path']))

        module = imp.load_source('script', config['path'])
        return module.main(self, *args, **kwargs)

class Config:
    """nemoa workspace module internal configuration object."""

    _config = None
    _default = {
        'baseconf': ('%user_config_dir%', 'nemoa.ini'), # base config
        'basepath': { # paths for shared ressources and workspaces
            'user': ('%user_data_dir%', 'workspaces'),
            'common': ('%site_data_dir%', 'workspaces') },
        'path': {}, # paths for logfile, cachefile, etc.
        'workspace': None, # current workspace
        'workspace_base': None,
        'workspace_path': { # paths for datasets, networks, models, etc.
            'datasets': ('%workspace%', 'datasets'),
            'networks': ('%workspace%', 'networks'),
            'systems': ('%workspace%', 'systems'),
            'models': ('%workspace%', 'models'),
            'scripts': ('%workspace%', 'scripts'),
            'cache': ('%workspace%', 'cache'),
            'logfile': ('%workspace%', 'nemoa.log') },
        'store': { # information storage for known objects
            'dataset': {},
            'network': {},
            'system': {},
            'model': {},
            'script': {} }}

    def __init__(self, shared = True, **kwargs):
        """ """

        self._config = nemoa.common.dict.merge(kwargs, self._default)

        # update basepaths from user configuration
        baseconfpath = self._get_path(self._config['baseconf'])
        if os.path.exists(baseconfpath):
            ini_dict = nemoa.common.inifile.load(
                baseconfpath, {
                'folders': {
                    'user': 'str',
                    'cache': 'str',
                    'common': 'str' },
                'files': {
                    'logfile': 'str' }})

            if 'folders' in ini_dict:
                for key, val in ini_dict['folders'].iteritems():
                    path = self._get_path(val)
                    if path: self._config['basepath'][key] = path

            if 'files' in ini_dict:
                for key, val in ini_dict['files'].iteritems():
                    path = self._get_path(val)
                    if path: self._config['path'][key] = path

        # import shared resources
        if shared:
            for workspace in self._get_common_workspaces():
                self._set_workspace_scan_files(workspace, 'common')

    def workspace(self):
        """Return name of current workspace."""

        return self._config['workspace']

    def _get_base(self):
        """Return base paths."""

        return self._config['workspace_base']

    def name(self):
        """Return name of current workspace."""

        return self._config['workspace']

    def path(self, type = None, workspace = None, base = 'user'):
        """Return path."""

        # (optional) load workspace of given object
        cur_workspace = self._get_workspace()
        cur_base = self._get_base()
        if workspace == None:
            workspace = cur_workspace
            base = cur_base
        elif not workspace == cur_workspace or not base == cur_base:
            if not self.load(workspace, base):
                nemoa.log('warning', """could not get path:
                    workspace '%s' does not exist.""" % (workspace))
                return  {}

        # get path
        if type == None: path = self._config['path'].copy()
        elif not isinstance(type, basestring):
            nemoa.log('warning', """could not get path:
                object type is not valid.""")
            path = None
        elif not type in self._config['path'].keys():
            nemoa.log('warning', """could not get path:
                object type '%s' is not valid.""" % (type))
            path = None
        else: path = self._config['path'][type]

        # (optional) load current workspace
        if cur_workspace:
            if not workspace == cur_workspace or not base == cur_base:
                self.load(cur_workspace, cur_base)

        return path

    def load(self, workspace, base = None):
        """Import workspace."""

        if not base in ['user', 'common']:
            if workspace in self._get_user_workspaces():
                base = 'user'
            elif workspace in self._get_common_workspaces():
                base = 'common'
            else:
                return False

        self._set_workspace(workspace, base = base)
        logfilepath = self._get_path(self._config['path']['logfile'])
        nemoa.log('init', logfile = logfilepath)
        self._set_workspace_scan_files()

        return True

    def list(self, type = None, workspace = None, base = None):
        """List known object configurations."""

        if type == 'workspace':
            if base == None:
                return sorted(self._get_user_workspaces()
                    + self._get_common_workspaces())
            if base == 'user':
                return sorted(self._get_user_workspaces())
            if base == 'common':
                return sorted(self._get_common_workspaces())
            return False

        if type:
            if not type in self._config['store']: return False

        # create dictionary
        objlist = []
        for key in self._config['store'].keys():
            if type and not key == type: continue
            for obj in self._config['store'][key].itervalues():
                if base and not base == obj['base']: continue
                if workspace and not workspace == obj['workspace']:
                    continue
                objlist.append(obj)

        return sorted(objlist, key = lambda obj: obj['name'])

    def _get_user_workspaces(self):
        """Return list of workspaces in user data directory."""
        user_workspaces = (self._config['basepath']['user'], '*')
        user_workspaces_path = self._get_path(user_workspaces)
        user_workspaces_list = []
        for w in glob.iglob(user_workspaces_path):
            if not os.path.isdir(w):
                continue
            # 2DO: check for workspace.ini or nemoa.ini etc
            user_workspaces_list.append(os.path.basename(w))
        return user_workspaces_list

    def _get_common_workspaces(self):
        """Return list of common workspaces."""
        share = self._get_path((self._config['basepath']['common'], '*'))
        return [os.path.basename(w) for w in glob.iglob(share)
            if os.path.isdir(w)]

    def get(self, type, name = None, workspace = None, base = 'user'):
        """Return object configuration as dictionary."""

        if not type in self._config['store'].keys():
            return nemoa.log('warning', """could not get configuration:
                object class '%s' is not supported.""" % (type))
        if not isinstance(name, basestring):
            return nemoa.log('warning', """could not get %s:
                name of object is not valid.""" % (type))

        # (optional) load workspace of given object
        cur_workspace = self._get_workspace()
        cur_base = self._get_base()
        if workspace == None:
            workspace = cur_workspace
            base = cur_base
        elif not workspace == cur_workspace or not base == cur_base:
            if not self.load(workspace, base):
                nemoa.log('warning', """could not get configuration:
                    workspace '%s' does not exist.""" % (workspace))
                return  {}

        # find object configuration in workspace
        search = [name, '%s.%s.%s' % (base, workspace, name),
            name + '.default', 'base.' + name]
        config = None
        for fullname in search:
            if fullname in self._config['store'][type].keys():
                config = self._config['store'][type][fullname]
                break

        # (optional) load current workspace
        if cur_workspace:
            if not workspace == cur_workspace or not base == cur_base:
                self.load(cur_workspace, cur_base)

        if not config:
            return nemoa.log('warning', """could not get configuration:
                %s with name '%s' is not found in
                %s workspace '%s'.""" % (type, name, base, workspace))

        return config.copy()

    def _get_workspace(self):
        return self._config['workspace']

    def _get_path(self, path, check = False, create = False):
        """Return string containing expanded path.
        
        Args:
            path"""
        
        path = nemoa.common.ospath.normpath(path)
        
        # expand nemoa environment variables
        replace = {
            'workspace': self._config['workspace'],
            'base': self._config['workspace_base'] }
        for key, val in self._config['path'].iteritems():
            replace[key] = nemoa.common.ospath.normpath(val)
        for key, val in self._config['basepath'].iteritems():
            replace[key] = nemoa.common.ospath.normpath(val)
        for key in ['user_cache_dir', 'user_config_dir',
            'user_data_dir', 'user_log_dir', 'site_config_dir',
            'site_data_dir']:
            replace[key] = nemoa.common.ospath.getstorage(
                key, appname = 'nemoa', appauthor = 'fishroot')

        update = True
        while update:
            update = False
            for key, val in replace.iteritems():
                if not '%' + key + '%' in path:
                    continue
                path = path.replace('%' + key + '%', val)
                update = True

        # (optional) create directory
        if create and not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))

        # (optional) check path
        if check and not os.path.exists(path):
            return nemoa.log('warning',
                "directory '%s' does not exist!" % (path))

        return path

    def _get_path_expand_env(self, path = ''):
        """Expand nemoa environment variables in path string."""
        
        # create replace dictionary
        # 2DO: get appname and authorname from nemoa.__init__
        replace = {
            'workspace': self._config['workspace'],
            'base': self._config['workspace_base'] }
        for key, val in self._config['path'].iteritems():
            replace[key] = val
        for key, val in self._config['basepath'].iteritems():
            replace[key] = val
        for key in ['user_cache_dir', 'user_config_dir',
            'user_data_dir', 'user_log_dir', 'site_config_dir',
            'site_data_dir']:
            replace[key] = nemoa.common.ospath.getstorage(
                key, appname = 'nemoa', appauthor = 'fishroot')

        # expand env vars
        update = True
        while update:
            update = False
            for key, val in replace.iteritems():
                if not '%' + key + '%' in path:
                    continue
                path = path.replace('%' + key + '%', val)
                update = True

        return path

    def _set_workspace(self, workspace, base = 'user', refresh = False):

        if workspace == None: return True
        if workspace == self._config['workspace'] and not refresh:
            return True
        if base == 'user':
            if not workspace in self._get_user_workspaces():
                return nemoa.log('warning', """could not open workspace
                    '%s': folder could not be found in '%s'."""
                    % (workspace, self._config['basepath'][base]))
        elif base == 'common':
            if not workspace in self._get_common_workspaces():
                return nemoa.log('warning', """could not open workspace
                    '%s': folder could not be found in '%s'."""
                    % (workspace, self._config['basepath'][base]))
        else:
            return nemoa.log('error', """could not open workspace
                '%s': base of workspace is not valid.""" % (workspace))

        # update workspace name, base and paths
        self._config['workspace'] = workspace
        self._config['workspace_base'] = base
        for key in self._config['workspace_path']:
            path = self._get_path(('%' + base + '%',
                self._config['workspace_path'][key]))
            self._config['path'][key] = path

        return True

    def _set_workspace_scan_files(self, workspace = None, base = None):
        """Scan workspace for files."""

        # change current workspace
        if workspace:
            cur_workspace = self._config['workspace']
            cur_workspace_base = self._config['workspace_base']
            if not self._set_workspace(workspace, base = base):
                return False
        else:
            cur_workspace = None
            cur_workspace_base = None
            workspace = self._config['workspace']

        for type in self._config['store'].keys():
            filemask = self._get_path(
                (self._config['path'][type + 's'], '*.*'))
            if type == 'dataset':
                filetypes = nemoa.dataset.imports.filetypes()
            elif type == 'network':
                filetypes = nemoa.network.imports.filetypes()
            elif type == 'system':
                filetypes = nemoa.system.imports.filetypes()
            elif type == 'model':
                filetypes = nemoa.model.imports.filetypes()
            elif type == 'script':
                filetypes = ['py']

            # scan for files
            for path in glob.iglob(filemask):
                filetype = nemoa.common.ospath.fileext(path)
                if not filetype in filetypes:
                    continue
                name = nemoa.common.ospath.basename(path)
                workspace = self._get_workspace()
                base = self._get_base()
                fullname = '%s.%s.%s' % (base, workspace, name)
                if fullname in self._config['store'][type]:
                    continue

                # add configuration to object tree
                self._config['store'][type][fullname] = {
                    'name': name,
                    'type': type,
                    'path': path,
                    'workspace': workspace,
                    'base': base,
                    'fullname': fullname }

        # change current workspace and update paths
        if workspace and not workspace == cur_workspace:
            self._set_workspace(cur_workspace,
                base = cur_workspace_base)

        return True
