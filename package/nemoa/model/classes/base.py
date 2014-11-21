# -*- coding: utf-8 -*-

__author__  = 'Patrick Michl'
__email__   = 'patrick.michl@gmail.com'
__license__ = 'GPLv3'

import nemoa
import copy
import os

class Model:
    """Model base class.

    Attributes:
        about (str): Short description of the content of the resource.
            Hint: Read- & writeable wrapping attribute to get('about')
                and set('about', str).
        accuracy (numpy.float64): Average reconstruction accuracy of
            output units, defined by:
                accuracy := 1 - mean(residuals) / mean(data)
            Hint: Readonly wrapping attribute to get('accuracy')
        author (str): A person, an organization, or a service that is
            responsible for the creation of the content of the resource.
            Hint: Read- & writeable wrapping attribute to get('author')
                and set('author', str).
        branch (str): Name of a duplicate of the original resource.
            Hint: Read- & writeable wrapping attribute to get('branch')
                and set('branch', str).
        dataset (dataset instance):
        email (str): Email address to a person, an organization, or a
            service that is responsible for the content of the resource.
            Hint: Read- & writeable wrapping attribute to get('email')
                and set('email', str).
        error (numpy.float64): Average reconstruction error of
            output units, defined by:
                error := mean(residuals)
            Hint: Readonly wrapping attribute to get('error')
        fullname (str): String concatenation of name, branch and
            version. Branch and version are only conatenated if they
            exist.
            Hint: Readonly wrapping attribute to get('fullname')
        license (str): Namereference to a legal document giving official
            permission to do something with the resource.
            Hint: Read- & writeable wrapping attribute to get('license')
                and set('license', str).
        name (str): Name of the resource.
            Hint: Read- & writeable wrapping attribute to get('name')
                and set('name', str).
        network (network instance):
        path (str):
            Hint: Read- & writeable wrapping attribute to get('path')
                and set('path', str).
        precision (numpy.float64): Average reconstruction precision
            of output units defined by:
                precision := 1 - dev(residuals) / dev(data).
            Hint: Readonly wrapping attribute to get('precision')
        system (system instance):
        type (str): String concatenation of module name and class name
            of the instance.
            Hint: Readonly wrapping attribute to get('type')
        version (int): Versionnumber of the resource.
            Hint: Read- & writeable wrapping attribute to get('version')
                and set('version', int).

    """

    dataset  = None
    network  = None
    system   = None
    _config  = None
    _default = {}
    _attr    = {'error': 'r', 'accuracy': 'r', 'precision': 'r',
                'fullname': 'r', 'type': 'r', 'name': 'rw',
                'branch': 'rw', 'version': 'rw', 'about': 'rw',
                'author': 'rw', 'email': 'rw', 'license': 'rw',
                'path': 'rw'}

    def __init__(self, *args, **kwargs):
        """Import model from dictionary."""

        self._set_copy(**kwargs)

    def __getattr__(self, key):
        """Attribute wrapper to method get(key)."""

        if key in self._attr:
            if 'r' in self._attr[key]: return self.get(key)
            return nemoa.log('warning',
                "attribute '%s' can not be accessed directly.")

        raise AttributeError('%s instance has no attribute %r'
            % (self.__class__.__name__, key))

    def __setattr__(self, key, val):
        """Attribute wrapper to method set(key, val)."""

        if key in self._attr:
            if 'w' in self._attr[key]: return self.set(key, val)
            return nemoa.log('warning',
                "attribute '%s' can not be changed directly.")

        self.__dict__[key] = val

    def configure(self):
        """Configure model."""

        if not nemoa.type.isdataset(self.dataset):
            return nemoa.log('error', """could not configure model:
                dataset is not valid.""")
        if not nemoa.type.isnetwork(self.network):
            return nemoa.log('error', """could not configure model:
                network is not valid.""")
        if not nemoa.type.issystem(self.system):
            return nemoa.log('error', """could not configure model:
                system is not valid.""")

        retval = True

        # configure dataset columns to network
        retval &= self.dataset.configure(self.network)
        # configure network to restrict nodes to found columns
        retval &= self.network.configure(self.dataset)
        # configure system to nodes in network
        retval &= self.system.configure(self.network)

        return retval

    def initialize(self):
        """Initialize model parameters."""

        if not nemoa.type.isdataset(self.dataset):
            return nemoa.log('error', """could not initialize model:
                dataset is not valid.""")
        if not nemoa.type.isnetwork(self.network):
            return nemoa.log('error', """could not initialize model:
                network is not valid.""")
        if not nemoa.type.issystem(self.system):
            return nemoa.log('error', """could not initialize model:
                system is not valid.""")

        retval = True

        # initialize dataset to system including normalization
        retval &= self.dataset.initialize(self.system)
        # initialize system parameters by using statistics from dataset
        retval &= self.system.initialize(self.dataset)
        # initialize network parameters with system parameters
        retval &= self.network.initialize(self.system)

        return retval

    def optimize(self, *args, **kwargs):
        """Optimize system parameters."""

        if not nemoa.type.isdataset(self.dataset):
            return nemoa.log('error', """could not optimize model:
                dataset is not valid.""")
        if not nemoa.type.isnetwork(self.network):
            return nemoa.log('error', """could not optimize model:
                network is not valid.""")
        if not nemoa.type.issystem(self.system):
            return nemoa.log('error', """could not optimize model:
                system is not valid.""")

        retval = True

        # optimize system paramaters
        retval &= self.system.optimize(
            dataset = self.dataset, *args, **kwargs)

        # update network parameters from system parameters
        retval &= self.network.initialize(self.system)

        ## Todo: find better solution for multistage optimization
        #if 'stage' in schedule and len(schedule['stage']) > 0:
            #for stage, params in enumerate(config['stage']):
                #self.system.optimize(self.dataset, **params)

        return retval

    def get(self, key = 'name', *args, **kwargs):
        """Get meta information and content."""

        # meta information
        if key == 'about': return self._get_about()
        if key == 'algorithms': return self._get_algorithms()
        if key == 'author': return self._get_author()
        if key == 'branch': return self._get_branch()
        if key == 'email': return self._get_email()
        if key == 'fullname': return self._get_fullname()
        if key == 'license': return self._get_license()
        if key == 'name': return self._get_name()
        if key == 'path': return self._get_path()
        if key == 'type': return self._get_type()
        if key == 'version': return self._get_version()

        # content
        if key == 'error': return self.calc('system', 'error')
        if key == 'accuracy': return self.calc('system', 'accuracy')
        if key == 'precision': return self.calc('system', 'precision')

        # direct access
        if key == 'copy': return self._get_copy(*args, **kwargs)
        if key == 'config': return self._get_config(*args, **kwargs)
        if key == 'dataset': return self.dataset.get(*args, **kwargs)
        if key == 'network': return self.network.get(*args, **kwargs)
        if key == 'system': return self.system.get(*args, **kwargs)

        return nemoa.log('warning', "unknown key '%s'" % (key))

    def _get_fullname(self):
        """Get fullname of model."""
        fullname = ''
        name = self._get_name()
        if name: fullname += name
        branch = self._get_branch()
        if branch: fullname += '.' + branch
        version = self._get_version()
        if version: fullname += '.' + str(version)
        return fullname

    def _get_name(self):
        """Get name of model."""
        if 'name' in self._config: return self._config['name']
        return None

    def _get_branch(self):
        """Get branch of model."""
        if 'branch' in self._config: return self._config['branch']
        return None

    def _get_version(self):
        """Get version number of model branch."""
        if 'version' in self._config: return self._config['version']
        return None

    def _get_about(self):
        """Get description of model."""
        if 'about' in self._config: return self._config['about']
        return None

    def _get_author(self):
        """Get author of model."""
        if 'author' in self._config: return self._config['author']
        return None

    def _get_email(self):
        """Get email of author of model."""
        if 'email' in self._config: return self._config['email']
        return None

    def _get_license(self):
        """Get license of model."""
        if 'license' in self._config: return self._config['license']
        return None

    def _get_type(self):
        """Get type of model, using module and class name."""
        module_name = self.__module__.split('.')[-1]
        class_name = self.__class__.__name__
        return module_name + '.' + class_name

    def _get_algorithms(self, *args, **kwargs):
        """Get evaluation algorithms provided by model."""
        structured = {
            'dataset': self.dataset.get('algorithms', *args, **kwargs),
            'network': self.network.get('algorithms', *args, **kwargs),
            'system': self.system.get('algorithms', *args, **kwargs)}
        return structured

    def _get_path(self):
        """Get path of model."""
        if 'path' in self._config: return self._config['path']
        return None

    def _get_copy(self, key = None, *args, **kwargs):
        """Get model copy as dictionary."""

        if key == None: return {
            'config': self._get_config(),
            'dataset': self._get_dataset(),
            'network': self._get_network(),
            'system': self._get_system()
        }

        if key == 'config': return self._get_config(*args, **kwargs)
        if key == 'dataset': return self._get_dataset(*args, **kwargs)
        if key == 'network': return self._get_network(*args, **kwargs)
        if key == 'system': return self._get_system(*args, **kwargs)

        return nemoa.log('error', """could not get copy of
            configuration: unknown section '%s'.""" % (key))

    def _get_config(self, key = None, *args, **kwargs):
        """Get configuration or configuration value."""

        if key == None: return copy.deepcopy(self._config)

        if isinstance(key, str) and key in self._config.keys():
            if isinstance(self._config[key], dict):
                return self._config[key].copy()
            return self._config[key]

        return nemoa.log('error', """could not get configuration:
            unknown key '%s'.""" % (key))

    def _get_dataset(self, type = 'dict'):

        if type == 'dataset': return self.dataset.copy()
        if type == 'dict': return self.dataset.get('copy')

    def _get_network(self, type = 'dict'):

        if type == 'network': return self.network.copy()
        if type == 'dict': return self.network.get('copy')

    def _get_system(self, type = 'dict'):

        if type == 'dataset': return self.system.copy()
        if type == 'dict': return self.system.get('copy')

    def set(self, key = None, *args, **kwargs):
        """Set meta information and parameters of model."""

        # set meta information
        if key == 'name': return self._set_name(*args, **kwargs)
        if key == 'branch': return self._set_branch(*args, **kwargs)
        if key == 'version': return self._set_version(*args, **kwargs)
        if key == 'about': return self._set_about(*args, **kwargs)
        if key == 'author': return self._set_author(*args, **kwargs)
        if key == 'email': return self._set_email(*args, **kwargs)
        if key == 'license': return self._set_license(*args, **kwargs)
        if key == 'path': return self._set_path(*args, **kwargs)

        # set model parameters
        if key == 'network': return self.network.set(*args, **kwargs)
        if key == 'dataset': return self.dataset.set(*args, **kwargs)
        if key == 'system': return self.system.set(*args, **kwargs)

        # import configuration
        if key == 'copy': return self._set_copy(*args, **kwargs)
        if key == 'config': return self._set_config(*args, **kwargs)

        return nemoa.log('warning', "unknown key '%s'" % (key))

    def _set_name(self, name):
        """Set name of model."""
        if not isinstance(name, basestring): return False
        self._config['name'] = name
        return True

    def _set_branch(self, branch):
        """Set branch of model."""
        if not isinstance(branch, basestring): return False
        self._config['branch'] = branch
        return True

    def _set_version(self, version):
        """Set version number of model branch."""
        if not isinstance(version, int): return False
        self._config['version'] = version
        return True

    def _set_about(self, about):
        """Get description of model."""
        if not isinstance(about, basestring): return False
        self._config['about'] = about
        return True

    def _set_author(self, author):
        """Set author of model."""
        if not isinstance(author, basestring): return False
        self._config['author'] = author
        return True

    def _set_email(self, email):
        """Set email of author of model."""
        if not isinstance(email, str): return False
        self._config['email'] = email
        return True

    def _set_license(self, model_license):
        """Set license of model."""
        if not isinstance(model_license, str): return False
        self._config['license'] = model_license
        return True

    def _set_path(self, model_path):
        """Set path of model."""
        if not isinstance(model_path, basestring): return False
        self._config['path'] = model_path
        return True

    def _set_copy(self, config = None, dataset = None, network = None,
        system = None):
        """Set configuration, parameters and data of model.

        Args:
            config (dict or None, optional): model configuration
            dataset (dict or None, optional): dataset copy as dictionary
            network (dict or None, optional): network copy as dictionary
            system (dict or None, optional): system copy as dictionary

        Returns:
            Bool which is True if and only if no error occured.

        """

        retval = True

        if config: retval &= self._set_config(config)
        if dataset: retval &= self._set_dataset(dataset)
        if network: retval &= self._set_network(network)
        if system: retval &= self._set_system(system)

        return retval

    def _set_config(self, config = None):
        """Set configuration from dictionary."""

        # initialize or update configuration dictionary
        if not hasattr(self, '_config') or not self._config:
            self._config = self._default.copy()
        if config:
            config_copy = copy.deepcopy(config)
            nemoa.common.dict_merge(config_copy, self._config)
        return True

    def _set_dataset(self, dataset):
        """Set dataset to model.

        Create a new dataset from dataset dictionary or reconfigure
        existing dataset with dataset dictionary or copy a dataset
        instance.

        Args:
            dataset (dict or dataset instance): dataset dictionary
                or dataset instance

        Returns:
            bool: True if no error occured

        """

        if nemoa.type.isdataset(dataset):
            self.dataset = dataset
            return True

        if not isinstance(dataset, dict):
            return False

        if nemoa.type.isdataset(self.dataset):
            return self.dataset.set('copy', **dataset)

        self.dataset = nemoa.dataset.new(**dataset)
        return True

    def _set_network(self, network):
        """Set network to model.

        Create a new network from network dictionary or reconfigure
        existing network with network dictionary or copy a network
        instance.

        Args:
            network (dict or network instance): network dictionary
                or network instance

        Returns:
            bool: True if no error occured

        """

        if nemoa.type.isnetwork(network):
            self.network = network
            return True

        if not isinstance(network, dict):
            return False

        if nemoa.type.isnetwork(self.network):
            return self.network.set('copy', **network)

        self.network = nemoa.network.new(**network)
        return True

    def _set_system(self, system):
        """Set system to model.

        Create a new system from system dictionary or reconfigure
        existing system with system dictionary or copy a system
        instance.

        Args:
            system (dict or system instance): system dictionary
                or system instance

        Returns:
            bool: True if no error occured

        """

        if nemoa.type.issystem(system):
            self.system = system
            return True

        if not isinstance(system, dict):
            return False

        if nemoa.type.issystem(self.system):
            return self.system.set('copy', **system)

        self.system = nemoa.system.new(**system)
        return True

    def calc(self, key = None, *args, **kwargs):
        """Get evaluation of model."""

        if not key: key = 'system'

        # evaluate dataset
        if key == 'dataset':
            return self.dataset.calc(*args, **kwargs)
        if key == 'network':
            return self.network.calc(*args, **kwargs)
        if key == 'system':
            # get data for system evaluation
            if 'data' in kwargs.keys():
                # get data from keyword argument
                data = kwargs['data']
                del kwargs['data']
            else:
                # fetch data from dataset using parameters:
                # 'preprocessing', 'statistics'
                if 'preprocessing' in kwargs.keys():
                    preprocessing = kwargs['preprocessing']
                    del kwargs['preprocessing']
                else: preprocessing = {}
                if not isinstance(preprocessing, dict):
                    preprocessing = {}
                if preprocessing:
                    dataset_backup = self.dataset.get('copy')
                    self.dataset.preprocess(preprocessing)
                if 'statistics' in kwargs.keys():
                    statistics = kwargs['statistics']
                    del kwargs['statistics']
                else: statistics = 0
                cols = self.system.get('layers', visible = True)
                data = self.dataset.get('data',
                    size = statistics, cols = tuple(cols))
                if preprocessing:
                    self.dataset.set('copy', dataset_backup)

            return self.system.calc(data, *args, **kwargs)

        return nemoa.log('warning', 'could not evaluate model')

    def save(self, *args, **kwargs):
        """Export model to file."""
        return nemoa.model.save(self, *args, **kwargs)

    def show(self, *args, **kwargs):
        """Show model as image."""
        return nemoa.model.show(self, *args, **kwargs)

    def copy(self, *args, **kwargs):
        """Create copy of model."""
        return nemoa.model.copy(self, *args, **kwargs)
