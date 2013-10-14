# -*- coding: utf-8 -*-
import metapath.common as mp
import os, copy, pprint

class workspace:
    """metaPath base class for workspaces"""

    #
    # WORKSPACE CONFIGURATION
    #

    def __init__(self, project = None):

        # reset local variables
        self._config = None

        # get base configuration
        import metapath.workspace.config
        self._config = metapath.workspace.config.config()

        # import all common definitions
        self._config.loadCommon()

        # load user definitions
        if not project == None:
            self.load(project)

        # link configuration
        mp.shared['config'] = self._config

    def load(self, project):
        """Import configuration from project and update paths and logfile"""
        return self._config.loadProject(project)

    def list(self, type = None):
        """Return a list of object configurations"""
        list = self._config.list(type)
        if not type:
            for item in list:
                mp.log('info', "'%s' (%s)" % (item[2], item[1]))
        elif type == 'model':
            for item in list:
                mp.log('info', "'%s'" % (item))
        else:
            for item in list:
                mp.log('info', "'%s'" % (item[2]))
        return len(list)

    def show(self, type = None, name = None, **kwargs):
        """Print object configuration from type and name"""
        return pprint.pprint(self._config.get(type, name))

    def dataset(self, config = None, quiet = False, **kwargs):
        """Return new dataset instance"""
        return self.__getInstance('dataset', config, quiet, **kwargs)

    def network(self, config = None, quiet = False, **kwargs):
        """Return new network instance"""
        return self.__getInstance('network', config, quiet, **kwargs)

    def system(self, config = None, quiet = False, **kwargs):
        """Return new system instance"""
        return self.__getInstance('system', config, quiet, **kwargs)

    def model(self, config = None,
        dataset = None, network = None, system = None,
        configure = True, initialize = True, name = None,
        optimize = False, autosave = False, quiet = False, **kwargs):
        """Return new model instance"""

        # prepare parameters
        if network == None:
            network = {'type': 'auto'}

        # create instances
        dataset = self.__getInstance(type = 'dataset', config = dataset, quiet = True, **kwargs)
        network = self.__getInstance(type = 'network', config = network, quiet = True, **kwargs)
        system = self.__getInstance(type = 'system', config = system, quiet = True, **kwargs)

        # create model instance
        if dataset == None or network == None or system == None:
            # fallback: empty model
            mp.log('error', 'could not create model! creating empty model as fallback', quiet = quiet)
            model = self.__getInstance(type = 'model', config = config,
                name = name, quiet = True, empty = True, **kwargs)
        else:
            model = self.__getInstance(type = 'model', config = config,
                dataset = dataset, network = network, system = system,
                name = name, quiet = quiet, **kwargs)

        # configure model (optional)
        if configure:
            model.configure(quiet = quiet)

        # initialize model parameters (optional)
        if initialize:
            model.initialize(quiet = quiet)

        # optimize model (optional)
        if optimize:
            self.optimize(model, optimize, quiet = quiet)

        # save model (optional)
        if autosave:
            self.saveModel(model)

        return model

    def __getInstance(self, type = None, config = None, quiet = False, empty = False, **kwargs):
        """Return new instance of given object class and configuration"""

        # import module
        import importlib
        module = importlib.import_module("metapath." + str(type))

        # get objects configuration as dictionary
        config = self.__getConfig(type = type, config = config, quiet = quiet, **kwargs)
        if config == None:
            mp.log('error', 'could not create %s instance: unknown configuration!' % (type), quiet = quiet)
            return None

        # create new instance of given class and initialize with configuration
        instance = module.empty() if empty \
            else module.new(config = config, quiet = quiet, **kwargs)

        # check class instance
        if not mp.isInstanceType(instance, type):
            mp.log('error', 'could not create %s instance: invalid configuration!' % (type), quiet = quiet)
            mp.log('debuginfo', str(config), quiet = quiet)
            return None

        # return instance
        if empty:
            mp.log('info', 'create empty %s instance: \'%s\'' % (type, instance.getName()), quiet = quiet)
        else:
            mp.log('info', 'create new %s instance: \'%s\'' % (type, instance.getName()), quiet = quiet)

        return instance

    def __getConfig(self, type = None, config = None, merge = ['params'], **kwargs):
        """Return object configuration as dictionary"""
        if config == None:
            return {}
        if isinstance(config, dict):
            return copy.deepcopy(config)
        elif isinstance(config, str) and isinstance(type, str):
            name, params = mp.strSplitParams(config)
            if 'params' in kwargs and isinstance(kwargs['params'], dict):
                params = mp.dictMerge(kwargs['params'], params)
            return self._config.get(
                type = type, name = name, merge = merge, params = params)
        return False

    def copy(self, model):
        """Return copy of model instance"""
        return self.model(quiet = True,
            config = model.getConfig(),
            dataset = model.dataset.getConfig(),
            network = model.network.getConfig(),
            system = model.system.getConfig(),
            configure = False, initialize = False)._set(model._get())

    def __getPlot(self, name = None, params = {}, config = {}, quiet = False, **options):
        """Return new plot instance"""

        # return empty plot instance if no configuration information was given
        if not name and not config:
            import metapath.plot as plot
            return plot.new()

        # get plot configuration
        if name == None:
            cfgPlot = config.copy()
        else:
            cfgPlot = self._config.get('plot', name = name, params = params)

        # create plot instance
        if not cfgPlot == None:
            if not quiet:
                mp.log("info", "create plot instance: '" + name + "'")
            # merge params
            for param in params.keys():
                cfgPlot['params'][param] = params[param]
            import metapath.plot as plot
            return plot.new(config = cfgPlot)
        else:
            if not quiet:
                mp.log("error", "could not create plot instance: unkown plot-id '" + name + "'")
            return None

    #def branchModel(self, model, name = None,
        #system = None, network = None, dataset = None,
        #optimize = None, quiet = False):
        #"""
        #Return branch of model instance.
        #"""

        ### 2DO: split name and params

        #if not mp.isModel(model):
            #mp.log("error", "could not branch model: 'model' has to be mpModel instance!")
            #return None
        #if not system == None and not system in self._config.system:
            #mp.log("error", "could not modify model: unknown system name '" + system + "'!")
            #return None
        #if not network == None and not network in self._config.network:
            #mp.log("error", "could not modify model: unknown network name '" + network + "'!")
            #return None
        #if not dataset == None and not dataset in self._config.dataset:
            #mp.log("error", "could not modify model: unknown dataset name '" + dataset + "'!")
            #return None

        ## make copy of model
        #objModel = self.copy(model)

        ## update name
        #if not name == None:
            #objModel.cfg['name'] = name
        #else:
            #objModel.cfg['name'] = objModel.cfg['name'] + '-branch'

        ## console message
        #if not quiet:
            #mp.log("info", "create model branch: '" + model.cfg['name'] + "' -> '" + objModel.cfg['name'] + "'")

        ## reconfigure system, network and dataset
        #if not system == None:
            #objModel.configure(system = self.system(system, quiet = True))
        #if not network == None:
            #objModel.configure(network = self.network(network, quiet = True))
        #if not dataset == None:
            #objModel.configure(dataset = self.dataset(dataset, quiet = True))

        ## optimize model
        #if not optimize == None:
            #objModel = self.optimizeModel(objModel, optimize)

        #return objModel

    def optimize(self, model, schedule, quiet = False, **kwargs):
        """Optimize model instance"""

        # check model
        if model.isEmpty():
            mp.log('warning', 'empty model can not be optimized!')
            return model

        # get optimization configuration
        config = self.__getConfig(
            type = 'schedule', config = schedule,
            merge = ['params', model.system.getName()],
            quiet = True, **kwargs)

        return model.optimize(schedule = config, quiet = quiet)

    def loadModel(self, file, quiet = False):
        """Load model settings from file and return model instance"""

        # check file
        if not os.path.exists(file):
            if os.path.exists(self._config.path('models') + file + '.mp'):
                file = self._config.path('models') + file + '.mp'
            else:
                mp.log("error", "could not load model '%s': file does not exist." % file)
                return None

        # load model parameters and configuration from file
        mp.log('info', 'load model: \'%s\'' % file, quiet = quiet)
        import cPickle, gzip
        config = cPickle.load(gzip.open(file, 'rb'))

        # create empty model instance and set dict
        return self.model(quiet = True,
            config = config['config'],
            dataset = config['dataset']['cfg'],
            network = config['network']['cfg'],
            system = config['system']['config'],
            configure = False, initialize = False)._set(config)

    def saveModel(self, model, file = None, quiet = False):
        """Save model settings to file and return filepath"""

        # check object class
        if not mp.isModel(model):
            mp.log("warning", "could not save model: invalid model instance given!")
            return False

        # get filename
        if file == None:
            fileName = '%s.mp' % (model.getName())
            filePath = self._config.path('models')
            file = filePath + fileName
        file = mp.getEmptyFile(file)

        # save model parameters and configuration to file
        import cPickle, gzip
        cPickle.dump(
            obj = model._get(),
            file = gzip.open(file, "wb", compresslevel = 3),
            protocol = 2)

        # create console message
        if not quiet:
            finalName = os.path.basename(file)[:-3]
            mp.log("info", "save model as: '%s'" % (finalName))

        return file

    def plot(self, model, plot, output = 'file', file = None, quiet = False, **kwargs):
        """Create plot of model"""

        singleModelPlot = True

        # if 'model' parameter is a string, load model
        if isinstance(model, str):
            model = self.loadModel(model, quiet = quiet)
        # if 'model' parameter is a list of models, load models
        elif isinstance(model, (list, tuple)):
            singleModelPlot = False
            models = model
            for i, model in enumerate(models):
                if isinstance(model, str):
                    models[i] = self.loadModel(model, quiet = quiet)
        elif not mp.isModel(model):
            mp.log("warning", "could not create plot: invalid parameter 'model' given")
            return None

        # get plot instance
        if isinstance(plot, str):
            plotName, plotParams = mp.strSplitParams(plot)
            mergeDict = plotParams
            for param in kwargs.keys():
                plotParams[param] = kwargs[param]
            objPlot = self.__getPlot(name = plotName, params = plotParams, quiet = quiet)
            if not objPlot:
                mp.log("warning", "could not create plot: unknown configuration '%s'" % (plotName))
                return None
        elif isinstance(plot, dict):
            objPlot = self.__getPlot(config = plot, quiet = quiet)
        else:
            objPlot = self.__getPlot(quiet = quiet)
        if not objPlot:
            return None

        # prepare filename
        if output == 'display':
            file = None
        elif output == 'file' and not file:
            file = mp.getEmptyFile(self._config.path('plots') + \
                model.getName() + '/' + objPlot.cfg['name'] + \
                '.' + objPlot.settings['fileformat'])
            mp.log("console", "create plot: " + file)

        if singleModelPlot:
            # if type of plot not is singleModelPlot
            return objPlot.create(model, file = file)
        else:
            return objPlot.create(models, file = file)
