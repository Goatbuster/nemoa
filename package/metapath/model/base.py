# -*- coding: utf-8 -*-
import metapath.common as mp
import numpy as np
import copy
import time

class model:
    """
    metaPath base class for graphical models
    """

    #
    # METHODS FOR MODEL CONFIGURATION
    #

    def __init__(self, config = {}, dataset = None, network = None, system = None, name = None, **kwargs):
        """
        Initialize model and configure dataset, network and system.

        Parameters
        ----------
        dataset : dataset instance
        network : network instance
        system : system instance
        """

        # initialize local variables
        self.__config = {}
        self.dataset = None
        self.network = None
        self.system  = None

        # update model
        self.__setConfig(config)
        self.setName(name)
        self.__setDataset(dataset)
        self.__setNetwork(network)
        self.__setSystem(system)

        if not self.isEmpty() and self.__checkModel():
            self.updateConfig()

    def __setConfig(self, config):
        """
        Set configuration from dictionary
        """
        self.__config = config.copy()
        if not 'branches' in self.__config \
            or not isinstance(self.__config['branches'], dict):
            self.__config['branches'] = {}
        return True

    def __getConfig(self):
        """
        Return configuration as dictionary
        """
        return self.__config.copy()

    #
    # METHODS FOR DATASET CONFIGURATION
    #

    def __setDataset(self, dataset):
        """
        Set dataset
        """
        self.dataset = dataset
        return True

    def __confDataset(self, dataset = None, network = None, quiet = False, **kwargs):
        """
        configure model.dataset to given dataset and network

        Parameters
        ----------
        dataset : dataset instance
        network : network instance
        """

        # link dataset instance
        if mp.isDataset(dataset):
            self.dataset = dataset

        # check if dataset instance is valid
        if not mp.isDataset(self.dataset):
            mp.log('error', 'could not configure dataset: no dataset instance available!', quiet = quiet)
            return False

        # check if dataset is empty
        if self.dataset.isEmpty():
            return True

        # prepare params
        if not network and not self.network:
            mp.log("error", 'could not configure dataset: no network instance available!', quiet = quiet)
            return False

        mp.log('info', 'configure dataset: \'%s\'' % (self.dataset.getName()), quiet = quiet)
        return self.dataset.configure(quiet = quiet,
            network = network if not network == None else self.network)

    def __getDataset(self):
        """
        Return link to dataset instance
        """
        return self.dataset

    #
    # MODEL.NETWORK
    #

    def __setNetwork(self, network):
        """
        set network
        """
        self.network = network
        return True

    def __confNetwork(self, dataset = None, network = None, system = None, quiet = False, **kwargs):
        """
        configure model.network to given network, dataset and system

        Parameters
        ----------
        dataset : dataset instance
        network : network instance
        """

        # link network instance
        if mp.isNetwork(network):
            self.network = network
        
        # check if network instance is valid
        if not mp.isNetwork(self.network):
            mp.log('error', 'could not configure network: no network instance available!')
            return False

        # check if network instance is empty
        if self.network.isEmpty():
            return True

        # check if dataset instance is available
        if self.dataset == None and dataset == None:
            mp.log("error", 'could not configure network: no dataset instance available!')
            return False
 
         # check if system instance is available
        if self.system == None and system == None:
            mp.log("error", 'could not configure network: no system was given!')
            return False

        # configure system and 
        return self.network.configure(quiet = quiet,
            dataset = dataset if not dataset == None else self.dataset,
            system = system if not system == None else self.system)

    def __getNetwork(self):
        """
        Return link to network instance
        """
        return self.network

    #
    # MODEL.SYSTEM
    #

    def __setSystem(self, system):
        """
        Set system
        """
        self.system = system
        return True

    def __confSystem(self, dataset = None, network = None, system = None, quiet = False, **kwargs):
        """
        configure model.system to given dataset, network and system

        Keyword Arguments:
        dataset -- metapath dataset instance
        network -- metapath network instance
        system -- metapath system instance
        """

        # get current system parameters
        if mp.isSystem(system) and mp.isSystem(self.system):
            prevModelParams = self.system._get()
        else:
            prevModelParams = None

        # link system instance
        if mp.isSystem(system):
            self.system = system
        
        # verify system instance
        if not mp.isSystem(self.system):
            mp.log('error', 'could not configure system: no system instance available!')
            return False

        # verify dataset instance
        if not (mp.isDataset(self.dataset) or mp.isDataset(dataset)):
            mp.log('error', 'could not configure system: no dataset instance available!')
            return False
        elif not mp.isDataset(dataset):
            dataset = self.dataset

        # verify network instance
        if not (mp.isNetwork(self.network) or mp.isNetwork(network)):
            mp.log('error', 'could not configure system: no network instance available!')
            return False
        elif not mp.isNetwork(network):
            network = self.network

        # configure system
        if not quiet:
            mp.log('info', "configure system: '%s'" % (self.system.getName()))
        self.system.configure(network = network, dataset = dataset)

        # overwrite new model parameters with previous
        if prevModelParams:
            mp.log('info', 'get model parameters from previous model')
            self.system._overwrite_conf(**modelParams)
            #2DO create new entry in actual branch
        else:
            self.__config['branches']['main'] = self.system._get()

        ## update self
        #self.type = self.system.getClass()

        return True

    def __getSystem(self):
        """
        Return link to system instance
        """
        return self.system

    def __checkModel(self, allowNone = False):
        if (allowNone and self.dataset == None) \
            or not mp.isDataset(self.dataset):
            return False
        if (allowNone and self.network == None) \
            or not mp.isNetwork(self.network):
            return False
        if (allowNone and self.system == None) \
            or not mp.isSystem(self.system):
            return False
        return True

    def updateConfig(self):
        """
        Update model configuration
        """

        # set version of model
        self.__config['version'] = mp.version()

        # set name of model
        if not 'name' in self.__config or not self.__config['name']:
            if not self.network.getName():
                self.setName('%s-%s' % (
                    self.dataset.getName(), self.system.getName()))
            else:
                self.setName('%s-%s-%s' % (
                    self.dataset.getName(), self.network.getName(),
                    self.system.getName()))

        return True

    def configure(self, dataset = None, network = None, system = None, quiet = False, name = None, **kwargs):
        """
        configure model to dataset, network and system

        Parameters
        ----------
        dataset : dataset instance
        network : network instance
        system :  system instance
        """

        # verify parameters
        if dataset == None and self.dataset == None \
            and network == None and self.network == None \
            and system == None and self.system == None:
            if not self.isEmpty():
                mp.log("error", 'could not configure model: missing information!')
                return False
            else:
                return True
        if not (dataset == None or mp.isDataset(dataset)):
            mp.log("error", 'could not configure model: parameter "dataset" is not valid!')
            return False
        if not (network == None or mp.isNetwork(network)):
            mp.log("error", 'could not configure model: parameter "network" is not valid!')
            return False
        if not (system == None or mp.isSystem(system)):
            mp.log("error", 'could not configure model: parameter "system" is not valid!')
            return False

        # configure model
        if not quiet and not self.isEmpty():
            mp.log("info", "configure model: '" + self.__config['name'] + "'")
        if not self.__confDataset(dataset = dataset,
            network = network, quiet = quiet):
            return False
        if not self.__confNetwork(dataset = self.dataset,
            network = network, system = system, quiet = quiet):
            return False
        if not self.__confSystem(dataset = self.dataset,
            network = self.network, system = system, quiet = quiet):
            return False

        return True

    def getName(self):
        """
        return name of model
        """
        return self.__config['name'] if 'name' in self.__config else ''

    def setName(self, name):
        """
        set name of model
        """
        if isinstance(self.__config, dict):
            self.__config['name'] = name
            return True
        return False

    def isEmpty(self):
        """
        return true if model is empty
        """
        return not 'name' in self.__config or not self.__config['name']

    #
    # MODEL PARAMETER HANDLING
    #

    def findRelatedSampleGroups(self, **params):
        mp.log("info", "find related sample groups in dataset:")

        partition = self.dataset.createRowPartition(**params)
        return self.dataset.getRowPartition(partition)

    def createBranches(self, modify, method, **params):
        mp.log("info", 'create model branches:')
        
        if modify == 'dataset':
            if method == 'filter':
                filters = params['filter']

                # get params from main branch
                mainParams = self.system._get()

                # create branches for filters
                for filter in filters:
                    
                    branch = self.dataset.cfg['name'] + '.' + filter

                    # copy params from main branch
                    self.__config['branches'][branch] = mainParams.copy()

                    # modify params
                    self.__config['branches'][branch]['config']['params']['samplefilter'] = filter

                    # set modified params
                    self.system._set(**self.__config['branches'][branch])

                    # reinit system
                    self.system.initParams(self.dataset)

                    # save system params in branch
                    self.__config['branches'][branch] = self.system._get()

                    mp.log("info", "add model branch: '" + branch + "'")

                # reset system params to main branch
                self.system._set(**mainParams)

                return True

        return False

    #
    # MODIFY MODEL PARAMETERS
    #

    def initialize(self, quiet = False, **kwargs):
        """
        initialize model parameters and return self
        """

        # check if model is empty and can not be initialized
        if (self.dataset == None or self.system == None) \
            and self.isEmpty():
            return self

        # check system and dataset
        if self.dataset == None:
            mp.log("error", "could not initialize model parameters: dataset is not yet configured!", quiet = quiet)
            return False
        if self.system == None:
            mp.log("error", "could not initialize model parameters: system is not yet configured!", quiet = quiet)
            return False

        # initialization makes no sense in dummy systems
        if self.system.isEmpty():
            return False

        # initialize system parameters
        self.system.initParams(self.dataset)
        return self

    def optimize(self, schedule = None, quiet = False, **kwargs):
        """
        optimize model parameters and return self
        """

        # check if model is empty
        if (self.dataset == None or self.system == None) \
            and self.isEmpty():
            return self

        # check availability of system and dataset
        if self.dataset == None:
            mp.log("error", "could not optimize model parameters: dataset is not yet configured!", quiet = quiet)
            return False
        if self.system == None:
            mp.log("error", "could not optimize model parameters: system is not yet configured!", quiet = quiet)
            return False

        # check if schedule was given
        if not isinstance(schedule, dict):
            mp.log("error", "could not optimize model parameters: no valid optimization configuration given!", quiet = quiet)
            return False

        # optimization of system parameters
        mp.log('info', 'optimize model \'%s\': using algorithm \'%s\''
            % (self.getName(), schedule['name']), quiet = quiet)
            
        if 'stage' in schedule and len(schedule['stage']) > 0:
            for stage, params in enumerate(config['stage']):
                self.system.optimizeParams(self.dataset, **params)
        elif 'params' in schedule:
            self.system.optimizeParams(self.dataset, quiet = quiet, **schedule)
        return self

    #
    # GENERAL INFORMATION
    #

    def unit(self, unit):
        return self.network.node(unit)

    def link(self, link):
        return self.network.edge(link)

    #
    # RELATIONS BETWEEN SAMPLES
    #

    def getSampleMeasure(self, data, func = None):

        if not func or func == 'plain':
            return data

        return self.system.getSampleMeasure(data, func)

    def getSampleRelationInfo(self, relation):

        rel  = {}
        list = relation.lower().split('_')

        # get relation type
        reType = re.search('\Adistance|correlation', relation.lower())
        if reType:
            rel['type'] = reType.group()
        else:
            rel['type'] = None
            mp.log("warning", "unknown sample relation '" + relation + "'!")

        # get relation params and info
        rel['params'] = {}
        rel['properties'] = {}
        if rel['type'] == 'correlation':
            rel['properties']['symmetric'] = True
            if len(list) > 1:
                rel['params']['func'] = list[1]
        elif rel['type'] == 'distance':
            rel['properties']['symmetric'] = False
            if len(list) > 1:
                rel['params']['distfunc'] = list[1]
            if len(list) > 2:
                rel['params']['func'] = list[2]

        return rel

    def getSampleRelationMatrix(self, samples = '*', relation = 'distance_euclidean_hexpect'):

        rel = self.getSampleRelationInfo(relation)

        if rel['type'] == 'correlation':
            return self.getSampleCorrelationMatrix(**rel['params'])
        if rel['type'] == 'distance':
            return self.getSampleDistanceMatrix(samples, **rel['params'])

        return None

    def getSampleRelationMatrixMuSigma(self, matrix, relation):

        rel = self.getSampleRelationInfo(relation)

        numRelations = matrix.size
        numUnits = matrix.shape[0]

        ## TODO: correlation vs causality effect

        # create temporary array which does not contain diag entries
        A = np.zeros((numRelations - numUnits))
        k = 0
        for i in range(numUnits):
            for j in range(numUnits):
                if i == j:
                    continue
                A[k] = matrix[i, j]
                k += 1

        mu = np.mean(A)
        sigma = np.std(A)

        return mu, sigma

    # calculate correlation matrix
    def getSampleCorrelationMatrix(self, func = 'plain'):

        # get data
        data = self.getSampleMeasure(self.dataset.getData(), func = func)

        # calculate correlation matrix
        return np.corrcoef(data)

    # calculate sample distance matrix
    def getSampleDistanceMatrix(self, samples = '*', distfunc = 'euclidean', func = 'plain'):

        # get data
        data = self.getSampleMeasure(self.dataset.getData(), func = func)

        # calculate distance matrix
        D = np.zeros(shape = (data.shape[0], data.shape[0]))
        for i in range(D.shape[0]):
            for j in range(D.shape[1]):
                if i > j:
                    continue

                D[i, j] = np.sqrt(np.sum((data[i,:] - data[j,:]) ** 2))
                D[j, i] = D[i, j]

        return D

    #
    # SYSTEM EVALUATION
    #

    def _getEval(self, data = None, statistics = 100000, **kwargs):
        """
        Return dictionary with units and evaluation values.
        """
        if data == None: # get data if not given
            data = self.dataset.getData(statistics)
        return self.system.getDataEval(data, **kwargs)

    #
    # UNIT EVALUATION
    #

    def _getUnitEval(self, data = None, statistics = 10000, **kwargs):
        """
        Return dictionary with units and evaluation values.
        """
        if data == None: # get data if not given
            data = self.dataset.getData(statistics)
        return self.system.getUnitEval(data, **kwargs)

    def getUnitEvalInfo(self, func):
        return self.system.getUnitEvalInfo(func)

    #
    # LINK EVALUATION
    #

    def _getLinkEval(self, data= None, statistics = 10000, **kwargs):
        """
        Return dictionary with links and evaluation values.
        """
        if data == None: # get data if not given
            data = self.dataset.getData(statistics)
        return self.system.getLinkEval(data, **kwargs)

    #
    # MODEL EVALUATION
    #

    def eval(self, func = 'expect', data = None, block = [],
        k = 1, m = 1, statistics = 10000):

        # set default values to params if not set
        if data == None:
            data = self.dataset.getData(statistics)

        vEval, hEval = self.system.getUnitEval(data, func, block, k, m)
        mEval = np.mean(vEval)

        units = {}
        for i, v in enumerate(self.system.params['v']['label']):
            units[v] = vEval[i]
        for j, h in enumerate(self.system.params['h']['label']):
            units[h] = hEval[j]

        return mEval, units

    #
    # RELATIONS BETWEEN UNITS
    #

    def getUnitRelationMatrix(self, units = None, x = None, y = None,
        relation = 'correlation()', preprocessing = None, statistics = 10000):

        # get visible and hidden units
        # and set visble as default for unknown unit lists
        visible, hidden = self.system.getUnits()
        if units:
            x = units
            y = units
        elif x and not y:
            units = x
            y = x
        elif not x and y:
            units = y
            x = y
        elif not x and not y:
            units = visible
            x = visible
            y = visible

        relFunc, relParams = mp.strSplitParams(relation)

        # get data and perform data preprocessing
        data = self.dataset.getData(statistics)
        if not preprocessing == None:
            plain = np.copy(data)
            data = self.system.getDataRepresentation(data, transformation = preprocessing)

        # get relation as matrix
        if relFunc == 'correlation':
            M = self.__getUnitCorrelationMatrix(units = units, data = data, **relParams)
        elif relFunc == 'causality':
            M = self.__getUnitCausalityMatrix(x = x, y = y, data = data, **relParams)
        else:
            return None

        # transform matrix
        if 'transform' in relParams:
            if 'C' in relParams['transform']:
                if not preprocessing == None:
                    C = self.__getUnitCorrelationMatrix(units = units, data = plain)
                else:
                    C = self.__getUnitCorrelationMatrix(units = units, data = data)
            try:
                T = eval(relParams['transform'])
            except:
                mp.log('warning', 'could not transform unit relation matrix: invalid syntax!')
                return M
            return T

        return M

    def getUnitRelationMatrixMuSigma(self, matrix, relation):

        # parse relation
        reType = re.search('\Acorrelation|causality', relation.lower())
        if not reType:
            mp.log("warning", "unknown unit relation '" + relation + "'!")
            return None
        type = reType.group()

        numRelations = matrix.size
        numUnits = matrix.shape[0]

        # create temporary array which does not contain diag entries
        A = np.zeros((numRelations - numUnits))
        k = 0
        for i in range(numUnits):
            for j in range(numUnits):
                if i == j:
                    continue
                A[k] = matrix[i, j]
                k += 1

        mu = np.mean(A)
        sigma = np.std(A)

        if type == 'causality':
            Amax = np.max(A)
            Aabs = np.abs(A)
            Alist = []
            for i in range(Aabs.size):
                if Aabs[i] > Amax:
                    continue
                Alist.append(Aabs[i])
            A = np.array(Alist)

            mu = np.mean(A)
            sigma = np.std(A)

        return mu, sigma

    def __getUnitCorrelationMatrix(self, units = None, data = None, **kwargs):

        """
        Description:
        calculate correlation matrix

        Keyword arguments:
        units -- list of strings with valid unitIDs
        """

        # create data and calulate correlation matrix
        M = np.corrcoef(data.T)

        # create output matrix
        C = np.zeros(shape = (len(units), len(units)))
        for i, u1 in enumerate(units):
            k = self.system.getUnitInfo(u1)['id']
            for j, u2 in enumerate(units):
                l = self.system.getUnitInfo(u2)['id']
                C[i, j] = M[k, l]

        return C

    def __getUnitCausalityMatrix(self, x = None, y = None,
        measure = 'relapprox', modify = 'setmean', data = None, **kwargs):

        """
        Description:
        modify units and and measure effect on other units

        Keyword arguments:
        y : list with manipulated units on y axis of matrix
        x : list with effected units on x axis of matrix
        """

        # set default values to params if not set
        if not x:
            x = self.system.getUnits()[0]
        if not y:
            y = self.system.getUnits()[0]

        # prepare causality matrix
        K = np.zeros((len(y), len(x)))

        # calculate unit values without modification
        mp.log("info", 'calculate %s effect on %s' % (modify, self.getUnitEvalInfo(measure)['name']))
        tStart = time.time()
        uLink  = self._getUnitEval(func = measure, data = data)
        tStop  = time.time()
        mp.log("info", 'estimated duration: %.1fs' % ((tStop - tStart) * len(y)))
        
        for i, kUnit in enumerate(y):

            # modify unit and calculate unit values
            if modify == 'unlink':
                links = self.system.getLinks()
                self.system.unlinkUnit(kUnit)
                uUnlink = self._getUnitEval(func = measure, data = data)
                self.system.setLinks(links)
            elif modify == 'setmean':
                uID = self.system.getUnitInfo(kUnit)['id']
                uUnlink = self._getUnitEval(func = measure, data = data, block = [uID])

            # store difference in causality matrix
            for j, mUnit in enumerate(x):
                if mUnit == kUnit:
                    continue
                K[i,j] = uUnlink[mUnit] - uLink[mUnit]

        return K

    #
    # get / set all model parameters as dictionary
    #
    
    def _get(self, sec = None):
        dict = {
            'config': copy.deepcopy(self.__config),
            'network': self.network._get() if hasattr(self.network, '_get') else None,
            'dataset': self.dataset._get() if hasattr(self.dataset, '_get') else None,
            'system': self.system._get() if hasattr(self.system, '_get') else None
        }

        if not sec:
            return dict
        if sec in dict:
            return dict[sec]

        return None

    def _set(self, dict):
        """
        set configuration, parameters and data of model from given dictionary
        return true if no error occured
        """

        # get config from dict
        config = self.importConfigFromDict(dict)

        # check self
        if not mp.isDataset(self.dataset):
            mp.log('error', """
                could not configure dataset:
                model does not contain dataset instance!""")
            return False
        if not mp.isNetwork(self.network):
            mp.log('error', """
                could not configure network:
                model does not contain network instance!""")
            return False
        if not mp.isSystem(self.system):
            mp.log('error', """
                could not configure system:
                model does not contain system instance!""")
            return False

        self.__config = config['config'].copy()
        self.network._set(**config['network'])
        self.dataset._set(**config['dataset'])

        ## prepare
        if not 'update' in config['system']['config']:
            config['system']['config']['update'] = {'A': False}

        ## 2do system._set(...) shall create system
        ## and do something like self.configure ...

        # create system
        import metapath.system as system
        self.system = system.new(
            config  = config['system']['config'].copy(),
            network = self.network,
            dataset = self.dataset
        )
        self.system._set(**config['system'])

        return self

    def importConfigFromDict(self, dict):
        """
        check if config is valid
        """
        config = {}

        # model configuration
        if 'config' in dict.keys():
            config['config'] = dict['config'].copy()
        else:
            mp.log('error', """
                could not set configuration:
                given dictionary does not contain configuration information!""")
            return None

        # get version of config
        version = config['config']['version']

        # dataset configuration
        if not 'dataset' in dict:
            mp.log('error', """
                could not configure dataset:
                given dictionary does not contain dataset information!""")
            return None
        else:
            config['dataset'] = dict['dataset'].copy()

        # network configuration
        if not 'network' in dict:
            mp.log('error', """
                could not configure network:
                given dictionary does not contain network information!""")
            return None
        else:
            config['network'] = dict['network'].copy()

        # system configuration
        if not 'system' in dict:
            mp.log('error', """
                could not configure system:
                given dictionary does not contain system information!""")
            return None
        else:
            config['system'] = dict['system'].copy()

        return config

class empty(model):
    pass
