#!/usr/bin/env python
# -*- coding: utf-8 -*-

########################################################################
# This python module contains a generic class for layered artificial   #
# neural networks aimed to provide common attributes, methods and      #
# optimization strategies like backpropagation and subclasses like     #
# different types of units to special subtypes of artificial neural    #
# networks like restricted boltzmann machines or deep beliefe networks #
########################################################################

import nemoa.system.base, numpy

class ann(nemoa.system.base.system):
    """Artificial Neuronal Network (ANN).

    References:
        "Learning representations by back-propagating errors",
        Rumelhart, D. E., Hinton, G. E., and Williams, R. J. (1986)"""

    ####################################################################
    # (Artificial Neuronal Network) System Configuration               #
    ####################################################################

    def _configure(self, config = {},
        network = None, dataset = None, update = False):
        """Configure ANN to network and dataset.
        
        Keyword Arguments:
            config -- dictionary containing system configuration
            network -- nemoa network instance
            dataset -- nemoa dataset instance """

        if not 'check' in self._config: self._config['check'] = {
            'config': False, 'network': False, 'dataset': False}
        self.setConfig(config)
        if not network == None: self._setNetwork(network, update)
        if not dataset == None: self._setDataset(dataset)

        return self.isConfigured()

    def _updateUnitsAndLinks(self, *args, **kwargs):

        nemoa.log('update system units and links')
        self.setUnits(self._params['units'], initialize = False)
        self.setLinks(self._params['links'], initialize = False)

        return True

    def _setNetwork(self, network, update = False, *args, **kwargs):
        """Update units and links to network instance. """

        nemoa.log("""get system units and links from network '%s'
            """ % (network.name()))
        nemoa.setLog(indent = '+1')

        if not nemoa.type.isNetwork(network):
            nemoa.log('error', """could not configure system:
                network instance is not valid!""")
            nemoa.setLog(indent = '-1')
            return False

        self.setUnits(self._getUnitsFromNetwork(network),
            initialize = (update == False))
        self.setLinks(self._getLinksFromNetwork(network),
            initialize = (update == False))

        self._config['check']['network'] = True
        nemoa.setLog(indent = '-1')

        return True

    def _setDataset(self, dataset, *args, **kwargs):
        """check if dataset columns match with visible units. """

        # check dataset instance
        if not nemoa.type.isDataset(dataset): return nemoa.log('error',
            'could not configure system: dataset instance is not valid!')

        # compare visible units labels with dataset columns
        mapping = self.getMapping()
        unitsInGroups = self.getUnits(visible = True)
        units = []
        for group in unitsInGroups: units += group
        if dataset.getColLabels() != units: return nemoa.log('error',
            'could not configure system: visible units differ from dataset columns!')

        self._config['check']['dataset'] = True

        return True

    def _checkParams(self, params):
        """Check if system parameter dictionary is valid. """

        return self._checkUnitParams(params) \
            and self._checkLinkParams(params)

    ####################################################################
    # (Artificial Neuronal Network) Unit Configuration                 #
    ####################################################################

    def _initUnits(self, dataset = None):
        """Initialize unit parameteres.

        Keyword Arguments:
            dataset -- nemoa dataset instance OR None

        Description:
            Initialize all unit parameters. """

        if not (dataset == None) and not nemoa.type.isDataset(dataset):
            return nemoa.log('error', """
                could not initilize unit parameters:
                invalid dataset argument given!""")

        for layerName in self.units.keys():
            if dataset == None \
                or self.units[layerName].params['visible'] == False:
                data = None
            else:
                rows = self._config['params']['samples'] \
                    if 'samples' in self._config['params'] else '*'
                cols = layerName \
                    if layerName in dataset.getColGroups() else '*'
                data = dataset.getData(100000, rows = rows, cols = cols)

            self.units[layerName].initialize(data)

        return True

    def _setUnits(self, units):
        """Create instances for units."""

        if not isinstance(units, list): return False
        if len(units) < 2: return False
        self._params['units'] = units

        # get unit classes from system config
        visibleUnitsClass = self._config['params']['visibleClass']
        hiddenUnitsClass = self._config['params']['hiddenClass']
        for id in range(len(self._params['units'])):
            if self._params['units'][id]['visible'] == True:
                self._params['units'][id]['class'] = visibleUnitsClass
            else: self._params['units'][id]['class'] = hiddenUnitsClass

        # create instances of unit classes
        # and link units params to local params dict
        self.units = {}
        for id in range(len(self._params['units'])):
            unitClass = self._params['units'][id]['class']
            name = self._params['units'][id]['name']
            if unitClass == 'sigmoid': self.units[name] = self.SUnitLayer()
            elif unitClass == 'gauss': self.units[name] = self.GUnitLayer()
            else: return nemoa.log('error', """
                could not create system:
                unit class '%s' is not supported!""" % (unitClass))
            self.units[name].params = self._params['units'][id]

        return True

    def _checkUnitParams(self, params):
        """Check if system parameter dictionary is valid respective to units. """

        if not isinstance(params, dict) \
            or not 'units' in params.keys() \
            or not isinstance(params['units'], list): return False
        for id in range(len(params['units'])):
            layer = params['units'][id]
            if not isinstance(layer, dict):
                return False
            for attr in ['name', 'visible', 'class', 'label']:
                if not attr in layer.keys():
                    return False
            if layer['class'] == 'gauss' \
                and not self.GUnitLayer.check(layer):
                return False
            elif params['units'][id]['class'] == 'sigmoid' \
                and not self.SUnitLayer.check(layer):
                return False

        return True

    def _getUnitsFromNetwork(self, network):
        """Return tuple with lists of unit labels from network. """

        units = [{'name': layer, 'label':
            network.nodes(type = layer)}
            for layer in network.layers()]
        for group in units:
            group['visible'] = network.node(group['label'][0])['params']['visible']
            group['id'] = network.node(group['label'][0])['params']['type_id']

        return units

    def _getUnitInformation(self, unit, layer = None):
        """Return dict information for a given unit. """

        if not layer: layer = self.getGroupOfUnit(unit)
        if not layer in self.units: return {}

        return self.units[layer].get(unit)

    def _removeUnits(self, layer = None, label = []):
        """Remove units from parameter space. """

        if not layer == None and not layer in self.units.keys():
            return nemoa.log('error', """could not remove units:
                unknown layer '%'""" % (layer))

        # search for labeled units in given layer
        layer = self.units[layer].params
        select = []
        labels = []
        for id, unit in enumerate(layer['label']):
            if not unit in label:
                select.append(id)
                labels.append(unit)

        # remove units from unit labels
        layer['label'] = labels

        # delete units from unit parameter arrays
        if layer['class'] == 'gauss':
            self.GUnitLayer.remove(layer, select)
        elif layer['class'] == 'sigmoid':
            self.SUnitLayer.remove(layer, select)

        # delete units from link parameter arrays
        self._removeUnitsLinks(layer, select)

        return True

    ####################################################################
    # (Artificial Neuronal Network) Link Configuration                 #
    ####################################################################

    def _setLinks(self, links):

        # update link parameters
        self._params['links'] = {}
        for layerID in range(len(self._params['units']) - 1):
            source = self._params['units'][layerID]['name']
            target = self._params['units'][layerID + 1]['name']
            x = len(self.units[source].params['label'])
            y = len(self.units[target].params['label'])
            self._params['links'][(layerID, layerID + 1)] = {
                'source': source, 'target': target,
                'A': numpy.ones([x, y], dtype = bool)}

        return True

    def _initLinks(self, dataset = None):
        """Initialize link parameteres (weights).

        Keyword Arguments:
            dataset -- nemoa dataset instance OR None

        Description:
            If dataset is None, initialize weights matrices with zeros
            and all adjacency matrices with ones.
            if dataset is nemoa network instance,
            initialize weights with random values, that fit ...."""

        if not(dataset == None) and \
            not nemoa.type.isDataset(dataset): return nemoa.log('error', """
            could not initilize link parameters:
            invalid dataset argument given!""")

        for links in self._params['links']:
            source = self._params['links'][links]['source']
            target = self._params['links'][links]['target']
            A = self._params['links'][links]['A']
            x = len(self.units[source].params['label'])
            y = len(self.units[target].params['label'])
            alpha = self._config['init']['wSigma'] \
                if 'wSigma' in self._config['init'] else 1.0
            sigma = numpy.ones([x, 1], dtype = float) * alpha / x

            if dataset == None: random = \
                numpy.random.normal(numpy.zeros((x, y)), sigma)
            elif source in dataset.getColGroups():
                rows = self._config['params']['samples'] \
                    if 'samples' in self._config['params'] else '*'
                data = dataset.getData(100000, rows = rows, cols = source)
                random = numpy.random.normal(numpy.zeros((x, y)),
                    sigma * numpy.std(data, axis = 0).reshape(1, x).T)
            elif dataset.getColLabels('*') \
                == self.units[source].params['label']:
                rows = self._config['params']['samples'] \
                    if 'samples' in self._config['params'] else '*'
                data = dataset.getData(100000, rows = rows, cols = '*')
                random = numpy.random.normal(numpy.zeros((x, y)),
                    sigma * numpy.std(data, axis = 0).reshape(1, x).T)
            else: random = \
                numpy.random.normal(numpy.zeros((x, y)), sigma)

            self._params['links'][links]['W'] = A * random

        return True

    def _checkLinkParams(self, params):
        """Check if system parameter dictionary is valid respective to links."""

        if not isinstance(params, dict) \
            or not 'links' in params.keys() \
            or not isinstance(params['links'], dict): return False
        for id in params['links'].keys():
            if not isinstance(params['links'][id], dict): return False
            for attr in ['A', 'W', 'source', 'target']:
                if not attr in params['links'][id].keys(): return False

        return True

    def _indexLinks(self):

        self._links = {units: {'source': {}, 'target': {}} 
            for units in self.units.keys()}
        for id in self._params['links'].keys():
            source = self._params['links'][id]['source']
            target = self._params['links'][id]['target']
            self._links[source]['target'][target] = \
                self._params['links'][id]
            self.units[source].target = \
                self._params['links'][id]
            self._links[target]['source'][source] = \
                self._params['links'][id]
            self.units[target].source = \
                self._params['links'][id]

        return True

    def _getWeightsFromLayers(self, source, target):
        """Return ..."""

        if self._config['optimize']['useAdjacency']:
            if target['name'] in self._links[source['name']]['target']:
                return self._links[source['name']]['target'][target['name']]['W'] \
                    * self._links[source['name']]['target'][target['name']]['A']
            elif source['name'] in self._links[target['name']]['target']:
                return (self._links[target['name']]['target'][source['name']]['W'] \
                    * self._links[source['name']]['target'][target['name']]['A']).T
        else:
            if target['name'] in self._links[source['name']]['target']:
                return self._links[source['name']]['target'][target['name']]['W']
            elif source['name'] in self._links[target['name']]['target']:
                return self._links[target['name']]['target'][source['name']]['W'].T

        return nemoa.log('error', """Could not get links:
            Layer '%s' and layer '%s' are not connected.
            """ % (source['name'], target['name']))

    def _getLinksFromConfig(self):
        """Return links from adjacency matrix. """

        groups = self.getGroups()
        if not groups: return False

        links = ()
        for g in range(len(groups) - 1):
            s = groups[g]
            t = groups[g + 1]
            
            lg = []
            for i, u in enumerate(self.units[s].params['label']):
                for j, v in enumerate(self.units[t].params['label']):
                    if not 'A' in self._params \
                        or self._params['links'][(g, g + 1)]['A'][i, j]:
                        lg.append((u, v))

            links += (lg, )

        return links

    def _removeUnitsLinks(self, layer, select):
        """Remove links to a given list of units."""

        links = self._links[layer['name']]

        for src in links['source'].keys():
            links['source'][src]['A'] = \
                links['source'][src]['A'][:, select]
            links['source'][src]['W'] = \
                links['source'][src]['W'][:, select]
        for tgt in links['target'].keys():
            links['target'][tgt]['A'] = \
                links['target'][tgt]['A'][select, :]
            links['target'][tgt]['W'] = \
                links['target'][tgt]['W'][select, :]

        return True

    ####################################################################
    # (Artificial Neuronal Network) Parameter Interface                #
    ####################################################################

    # Parameter Initialization

    def _initParams(self, dataset = None):
        """Initialize system parameters.

        Keyword Arguments:
            dataset -- nemoa dataset instance

        Description:
            Initialize all unit and link parameters to dataset. """

        if not nemoa.type.isDataset(dataset): return nemoa.log('error',
            'could not initilize system: invalid dataset instance given!')

        return self._initUnits(dataset) and self._initLinks(dataset)

    # Parameter Optimization

    # Generic Parameter Functions

    def _optimizeGetValues(self, inputData):
        """Forward pass (compute estimated values, from given input). """

        layers = self.getMapping()
        out = {}
        for id, layer in enumerate(layers):
            if id == 0:
                out[layer] = inputData
                continue
            out[layer] = self.getUnitExpect(
                out[layers[id - 1]], layers[id - 1:id + 1])

        return out

    def getParamDeltas(self, outputData, out):
        """Return weight delta from backpropagation of error. """

        layers = self.getMapping()
        delta = {}
        for id in range(len(layers) - 1)[::-1]:
            src = layers[id]
            tgt = layers[id + 1]
            if id == len(layers) - 2:
                delta[(src, tgt)] = out[tgt] - outputData
                continue
            inData = self.units[tgt].params['bias'] \
                + numpy.dot(out[src], self._params['links'][(id, id + 1)]['W'])
            grad = self.units[tgt].grad(inData)
            delta[(src, tgt)] = numpy.dot(delta[(tgt, layers[id + 2])],
                self._params['links'][(id + 1, id + 2)]['W'].T) * grad

        return delta

    def updateParams(self, updates):
        """Update parameters from dictionary."""

        layers = self.getMapping()
        for id, layer in enumerate(layers[:-1]):
            src = layer
            tgt = layers[id + 1]
            self._params['links'][(id, id + 1)]['W'] += \
                updates['links'][(src, tgt)]['W']
            self.units[tgt].update(updates['units'][tgt])

        return True

    # Backpropagation of Error (BPROP) specific Functions

    def optimizeBProp(self, dataset, schedule, inspector):
        """Optimize parameters using backpropagation."""

        cnf = self._config['optimize']
        layers = self.getMapping()

        # update parameters
        for epoch in xrange(cnf['updates']):

            # Get data (sample from minibatches)
            if epoch % cnf['minibatchInterval'] == 0:
                data = dataset.getData(size = cnf['minibatchSize'],
                    cols = (layers[0], layers[-1]))
            # Forward pass (Compute value estimations from given input)
            out = self._optimizeGetValues(data[0])
            # Backward pass (Compute deltas from backpropagation of error)
            delta = self.getParamDeltas(data[1], out)
            # Compute parameter updates
            updates = self.getParamUpdatesBProp(out, delta)
            # Update parameters
            self.updateParams(updates)
            # Trigger inspector (getch, calc inspect function etc)
            event = inspector.trigger()
            if event:
                if event == 'abort': break

        return True

    def getParamUpdatesBProp(self, out, delta, rate = 0.1):
        """Compute parameter update directions from weight deltas."""

        def getUpdate(grad, rate): return {
            key: rate * grad[key] for key in grad.keys()}

        layers = self.getMapping()
        links = {}
        units = {}
        for id, src in enumerate(layers[:-1]):
            tgt = layers[id + 1]
            units[tgt] = getUpdate(
                self.units[tgt].getUpdatesFromDelta(
                delta[src, tgt]), rate)
            links[(src, tgt)] = getUpdate(
                self.LinkLayer.getUpdatesFromDelta(out[src],
                delta[src, tgt]), rate)

        return {'units': units, 'links': links}

    # Resilient Backpropagation (RPROP) specific Functions

    def optimizeRProp(self, dataset, schedule, inspector):
        """Optimize parameters using resiliant backpropagation."""

        cnf = self._config['optimize']
        layers = self.getMapping()

        # update parameters
        for epoch in xrange(cnf['updates']):

            # Get data (sample from minibatches)
            if epoch % cnf['minibatchInterval'] == 0:
                data = dataset.getData(size = cnf['minibatchSize'],
                    cols = (layers[0], layers[-1]))
            # Forward pass (Compute value estimations from given input)
            out = self._optimizeGetValues(data[0])
            # Backward pass (Compute deltas from backpropagation of error)
            delta = self.getParamDeltas(data[1], out)
            # Compute updates
            updates = self.getParamUpdatesRProp(out, delta, inspector)
            # Update parameters
            self.updateParams(updates)
            # Trigger inspector (getch, calc inspect function etc)
            event = inspector.trigger()
            if event:
                if event == 'abort': break

        return True

    def getParamUpdatesRProp(self, out, delta, inspector):

        def getDict(dict, val): return {key: val * numpy.ones(
            shape = dict[key].shape) for key in dict.keys()}

        def getUpdate(prevGrad, prevUpdate, grad, accel, minFactor, maxFactor):
            update = {}
            for key in grad.keys():
                sign = numpy.sign(grad[key])
                a = numpy.sign(prevGrad[key]) * sign
                magnitude = numpy.maximum(numpy.minimum(prevUpdate[key] \
                    * (accel[0] * (a == -1) + accel[1] * (a == 0)
                    + accel[2] * (a == 1)), maxFactor), minFactor)
                update[key] = magnitude * sign
            return update

        # RProp parameters
        accel     = (0.5, 1.0, 1.2)
        initRate  = 0.001
        minFactor = 0.000001
        maxFactor = 50.0

        layers = self.getMapping()

        # Compute gradient from delta rule
        grad = {'units': {}, 'links': {}}
        for id, src in enumerate(layers[:-1]):
            tgt = layers[id + 1]
            grad['units'][tgt] = \
                self.units[tgt].getUpdatesFromDelta(delta[src, tgt])
            grad['links'][(src, tgt)] = \
                self.LinkLayer.getUpdatesFromDelta(out[src], delta[src, tgt])

        # Get previous gradients and updates
        prev = inspector.readFromStore()
        if not prev:
            prev = {
                'gradient': grad,
                'update': {'units': {}, 'links': {}}}
            for id, src in enumerate(layers[:-1]):
                tgt = layers[id + 1]
                prev['update']['units'][tgt] = \
                    getDict(grad['units'][tgt], initRate)
                prev['update']['links'][(src, tgt)] = \
                    getDict(grad['links'][(src, tgt)], initRate)
        prevGradient = prev['gradient']
        prevUpdate = prev['update']

        # Compute updates
        update = {'units': {}, 'links': {}}
        for id, src in enumerate(layers[:-1]):
            tgt = layers[id + 1]

            # calculate current rates for units
            update['units'][tgt] = getUpdate(
                prevGradient['units'][tgt],
                prevUpdate['units'][tgt],
                grad['units'][tgt],
                accel, minFactor, maxFactor)

            # calculate current rates for links
            update['links'][(src, tgt)] = getUpdate(
                prevGradient['links'][(src, tgt)],
                prevUpdate['links'][(src, tgt)],
                grad['links'][(src, tgt)],
                accel, minFactor, maxFactor)

        # Save updates to store
        inspector.writeToStore(gradient = grad, update = update)

        return update

    ####################################################################
    # (Artificial Neuronal Network) System Evaluation                  #
    ####################################################################

    def eval(self, data, func = 'accuracy', **kwargs):
        """Evaluate system respective to data.

        Keyword Arguments:
            data -- 2-tuple with numpy arrays: input data and output data
            func -- string containing system evaluation function
                For a full list of available system evaluation functions
                see: system.about('eval') """

        # get system evaluation function
        methods = self._getEvalMethods()
        if not func in methods.keys(): return nemoa.log('error',
            "could not evaluate system: unknown method '%s'" % (func))
        method = methods[func]['method']
        if not hasattr(self, method): return nemoa.log('error',
            "could not evaluate units: unknown method '%s'" % (method))

        # prepare params for system evaluation
        params = kwargs.copy()
        if not 'mapping' in params.keys() or params['mapping'] == None:
            params['mapping'] = self.getMapping()
        inFmt = methods[func]['input']
        if   inFmt == 0: pass
        elif inFmt == 1: params['data'] = data[0]
        elif inFmt == 2: params['data'] = data[1]
        elif inFmt == 3: params['data'] = data
        else: return nemoa.log('error', 
            "could not evaluate system: unknown method '%s'" % (method))

        # evaluate system
        value = getattr(self, method)(**params)

        return value

    @staticmethod
    def _getEvalMethods(): return {
        'energy': {
            'name': 'energy sum',
            'method': 'getEnergy',
            'input': 3, 'output': 0, 'format': '%.3f'},
        'error': {
            'name': 'mean data reconstruction error',
            'method': 'getError',
            'input': 3, 'output': 0, 'format': '%.3f'},
        'accuracy': {
            'name': 'mean data reconstruction accuracy',
            'method': 'getAccuracy',
            'input': 3, 'output': 0, 'format': '%.3f'},
        'precision': {
            'name': 'mean data reconstruction precision',
            'method': 'getPrecision',
            'input': 3, 'output': 0, 'format': '%.3f'}
        }

    def getError(self, *args, **kwargs):
        """Return sum of data reconstruction errors of output units. """
        return numpy.sum(self.getUnitError(*args, **kwargs))

    def getAccuracy(self, *args, **kwargs):
        """Return mean data reconstruction accuracy of output units. """
        return numpy.mean(self.getUnitAccuracy(*args, **kwargs))

    def getPrecision(self, *args, **kwargs):
        """Return mean data reconstruction precision of output units. """
        return numpy.mean(self.getUnitPrecision(*args, **kwargs))

    def getEnergy(self, data, *args, **kwargs):
        """Return system energy. """

        mapping = list(self.getMapping())
        E = 0.0

        # get energy of units
        for i in range(1, len(mapping) + 1): E += \
            numpy.sum(self.getUnitEnergy(data[0],
            mapping = tuple(mapping[:i])))

        # get energy of links
        for i in range(1, len(mapping)): E += \
            numpy.sum(self.getLinkEnergy(data[0],
            mapping = tuple(mapping[:i+1])))

        return E

    ####################################################################
    # (Artificial Neuronal Network) Unit Evaluation                    #
    ####################################################################

    def evalUnits(self, data, func = 'accuracy', units = None, **kwargs):
        """Return dictionary with unit evaluation values.

        Keyword Arguments:
            data -- 2-tuple with numpy arrays: input data and output data
            func -- string containing unit evaluation function
                For a full list of available system evaluation functions
                see: system.about('units', 'eval') """

        # get unit evaluation function
        methods = self._getUnitEvalMethods()
        if not func in methods.keys(): return nemoa.log('error',
            "could not evaluate units: unknown method '%s'" % (func))
        method = methods[func]['method']
        if not hasattr(self, method): return nemoa.log('error',
            "could not evaluate units: unknown method '%s'" % (method))

        # prepare arguments for unit evaluation functions
        evalArgs   = []
        evalKwargs = kwargs.copy()
        if not 'mapping' in evalKwargs.keys() \
            or evalKwargs['mapping'] == None:
            evalKwargs['mapping'] = self.getMapping()
        if isinstance(units, str):
            evalKwargs['mapping'] = self.getMapping(tgt = units)

        inFmt = methods[func]['input']
        if   inFmt == 0: evalArgs.append(data)
        elif inFmt == 1: evalArgs.append(data[0])
        elif inFmt == 2: evalArgs.append(data[1])
        elif inFmt == 3: evalArgs.append(data)

        # evaluate units
        values = getattr(self, method)(*evalArgs, **evalKwargs)

        # create unit dictionary
        labels = self.getUnits(group = evalKwargs['mapping'][-1])[0]
        outFmt = methods[func]['output']
        if outFmt == 0: return {unit: values[:, id] \
            for id, unit in enumerate(labels)}
        elif outFmt == 1: return {unit: values[id] \
            for id, unit in enumerate(labels)}

        return nemoa.log('error',
            "could not evaluate units: unknown method '%s'" % (method))

    @staticmethod
    def _getUnitEvalMethods(): return {
        'energy': {
            'name': 'local energy',
            'method': 'getUnitEnergy',
            'input': 1, 'output': 1, 'format': '%.3f'},
        'expect': {
            'name': 'expectation values',
            'method': 'getUnitExpect',
            'input': 1, 'output': 0, 'format': '%.3f'},
        'values': {
            'name': 'reconstructed values',
            'method': 'getUnitValues',
            'input': 1, 'output': 0, 'format': '%.3f'},
        'samples': {
            'name': 'reconstructed samples',
            'method': 'getUnitSamples',
            'input': 1, 'output': 0, 'format': '%.3f'},
        'residuals': {
            'name': 'data reconstruction residuals',
            'method': 'getUnitResiduals',
            'input': 3, 'output': 0, 'format': '%.3f'},
        'error': {
            'name': 'data reconstruction error',
            'method': 'getUnitError',
            'input': 3, 'output': 1, 'format': '%.2f'},
        'accuracy': {
            'name': 'data reconstruction accuracy',
            'method': 'getUnitAccuracy',
            'input': 3, 'output': 1, 'format': '%.2f'},
        'precision': {
            'name': 'data reconstruction precision',
            'method': 'getUnitPrecision',
            'input': 3, 'output': 1, 'format': '%.2f'},
        'rcorr': {
            'name': 'data reconstruction correlation',
            'method': 'getUnitRCorr',
            'input': 1, 'output': 1, 'format': '%.3f'},
        'mean': {
            'name': 'data reconstruction mean values',
            'method': 'getUnitMean',
            'input': 1, 'output': 1, 'format': '%.3f'},
        'variance': {
            'name': 'data reconstruction variance',
            'method': 'getUnitVariance',
            'input': 1, 'output': 1, 'format': '%.3f'}
        }

    def getUnitExpect(self, data, mapping = None, block = None):
        """Return expected values of a layer.

        Keyword Arguments:
            data -- numpy array containing data corresponding
                to the input layer (first argument of mapping)
            mapping -- tuple of strings containing the mapping
                from input layer (first argument of tuple)
                to output layer (last argument of tuple) """

        if mapping == None: mapping = self.getMapping()
        if block == None: inData = data
        else:
            inData = numpy.copy(data)
            for i in block: inData[:,i] = numpy.mean(inData[:,i])
        if len(mapping) == 2: return self.units[mapping[1]].expect(
            inData, self.units[mapping[0]].params)
        outData = numpy.copy(inData)
        for id in range(len(mapping) - 1):
            outData = self.units[mapping[id + 1]].expect(
                outData, self.units[mapping[id]].params)

        return outData

    def getUnitValues(self, data, mapping = None, block = None, expectLast = False):
        """Return unit values calculated from mappings.

        Keyword Arguments:
            mapping -- tuple of strings containing the mapping
                from input layer (first argument of tuple)
                to output layer (last argument of tuple)
            expectLast -- return expectation values of the units
                for the last step instead of maximum likelihood values """

        if mapping == None: mapping = self.getMapping()
        if block == None: inData = data
        else:
            inData = numpy.copy(data)
            for i in block: inData[:,i] = numpy.mean(inData[:,i])
        if expectLast:
            if len(mapping) == 1: return inData
            elif len(mapping) == 2: return self.units[mapping[1]].expect(
                self.units[mapping[0]].getSamples(inData),
                self.units[mapping[0]].params)
            return self.units[mapping[-1]].expect(
                self.getUnitValues(data, mapping[0:-1]),
                self.units[mapping[-2]].params)
        else:
            if len(mapping) == 1: return self.units[mapping[0]].getValues(inData)
            elif len(mapping) == 2: return self.units[mapping[1]].getValues(
                self.units[mapping[1]].expect(inData,
                self.units[mapping[0]].params))
            data = numpy.copy(inData)
            for id in range(len(mapping) - 1):
                data = self.units[mapping[id + 1]].getValues(
                    self.units[mapping[id + 1]].expect(data,
                    self.units[mapping[id]].params))
            return data

    def getUnitSamples(self, data, mapping = None, block = None, expectLast = False):
        """Return sampled unit values calculated from mapping.
        
        Keyword Arguments:
            mapping -- tuple of strings containing the mapping
                from input layer (first argument of tuple)
                to output layer (last argument of tuple)
            expectLast -- return expectation values of the units
                for the last step instead of sampled values """

        if mapping == None: mapping = self.getMapping()
        if block == None: inData = data
        else:
            inData = numpy.copy(data)
            for i in block: inData[:,i] = numpy.mean(inData[:,i])
        if expectLast:
            if len(mapping) == 1: return data
            elif len(mapping) == 2: return self.units[mapping[1]].expect(
                self.units[mapping[0]].getSamples(data),
                self.units[mapping[0]].params)
            return self.units[mapping[-1]].expect(
                self.getUnitSamples(data, mapping[0:-1]),
                self.units[mapping[-2]].params)
        else:
            if len(mapping) == 1: return self.units[mapping[0]].getSamples(data)
            elif len(mapping) == 2: return self.units[mapping[1]].getSamplesFromInput(
                    data, self.units[mapping[0]].params)
            data = numpy.copy(data)
            for id in range(len(mapping) - 1):
                data = self.units[mapping[id + 1]].getSamplesFromInput(
                    data, self.units[mapping[id]].params)
            return data

    def getUnitResiduals(self, data, mapping = None, block = None):
        """Return reconstruction residuals of units.

        Keyword Arguments:
            data -- 2-tuple with numpy arrays containing input and
                output data coresponding to the first and the last layer
                in the mapping
            mapping -- tuple of strings containing the mapping
                from input layer (first argument of tuple)
                to output layer (last argument of tuple)
            block -- list of strings containing labels of units in the input
                layer that are blocked by setting the values to their means """

        dIn, dOut = data

        # set mapping: inLayer to outLayer (if not set)
        if mapping == None: mapping = self.getMapping()

        # set unit values to mean (optional)
        if isinstance(block, list):
            dIn = numpy.copy(dIn)
            for i in block: dIn[:, i] = numpy.mean(dIn[:, i])

        # calculate estimated output values
        mOut = self.getUnitExpect(dIn, mapping)

        # calculate residuals
        res = dOut - mOut

        return res

    def getUnitEnergy(self, data, mapping = None):
        """Return unit energies of a layer.

        Keyword Arguments:
            mapping -- tuple of strings containing the mapping
                from input layer (first argument of tuple)
                to output layer (last argument of tuple) """

        #if len(mapping) == 1: pass
        #elif len(mapping) == 2: data = self.getUnitValues(data, mapping)
        #else: data = self.getUnitValues(
        #    self.getUnitExpect(data, mapping[0:-1]), mapping[-2:])

        data = self.getUnitExpect(data, mapping)

        return self.units[mapping[-1]].energy(data)

    def getUnitMean(self, data, mapping = None, block = None, **kwargs):
        """Return mean of reconstructed unit values.

        Keyword Arguments:
            data -- input data
            mapping -- tuple of strings containing the mapping
                from input layer (first argument of tuple)
                to output layer (last argument of tuple)
            block -- list of string containing labels of units in the input
                layer that are blocked by setting the values to their means """

        if mapping == None: mapping = self.getMapping()
        if block == None: modelOut = self.getUnitExpect(data[0], mapping)
        else:
            dataInCopy = numpy.copy(data)
            for i in block: dataInCopy[:,i] = numpy.mean(dataInCopy[:,i])
            modelOut = self.getUnitExpect(dataInCopy, mapping)

        return modelOut.mean(axis = 0)

    def getUnitVariance(self, data, mapping = None, block = None, **kwargs):
        """Return variance of reconstructed unit values.

        Keyword Arguments:
            data -- input data
            mapping -- tuple of strings containing the mapping
                from input layer (first argument of tuple)
                to output layer (last argument of tuple)
            block -- list of string containing labels of units in the input
                layer that are blocked by setting the values to their means """

        if mapping == None: mapping = self.getMapping()
        if block == None: modelOut = self.getUnitExpect(data, mapping)
        else:
            dataInCopy = numpy.copy(data)
            for i in block: dataInCopy[:,i] = numpy.mean(dataInCopy[:,i])
            modelOut = self.getUnitExpect(dataInCopy, mapping)

        return modelOut.var(axis = 0)

    def getUnitError(self, data, norm = 'ME', **kwargs):
        """Return reconstruction error of units (depending on norm)

        Keyword Arguments:
            data -- see getUnitResiduals
            mapping -- see getUnitResiduals
            block -- see getUnitResiduals
            norm -- used norm to calculate data reconstuction error
                from residuals. see getDataMean for a list of provided norms """

        res = self.getUnitResiduals(data, **kwargs)
        error = self.getDataMean(res, norm = norm)

        return error

    def getUnitAccuracy(self, data, norm = 'MSE', **kwargs):
        """Return unit reconstruction accuracy.

        Arguments:
            data -- see getUnitResiduals
            mapping -- see getUnitResiduals
            block -- see getUnitResiduals
            norm -- used norm to calculate accuracy
                see getDataNorm for a list of provided norms

        Description:
            accuracy := 1 - norm(residuals) / norm(data). """

        res = self.getUnitResiduals(data, **kwargs)
        normres = self.getDataMean(res, norm = norm)
        normdat = self.getDataMean(data[1], norm = norm)

        return 1.0 - normres / normdat

    def getUnitPrecision(self, data, norm = 'SD', **kwargs):
        """Return unit reconstruction precision.

        Arguments:
            data -- see getUnitResiduals
            mapping -- see getUnitResiduals
            block -- see getUnitResiduals
            norm -- used norm to calculate precision
                see getDataDeviation for a list of provided norms

        Description:
            precision := 1 - dev(residuals) / dev(data). """

        res = self.getUnitResiduals(data, **kwargs)
        devres = self.getDataDeviation(res, norm = norm)
        devdat = self.getDataDeviation(data[1], norm = norm)

        return 1.0 - devres / devdat

    # 2 Do
    def getUnitRCorr(self, data, mapping = None, block = None, **kwargs):
        """Return reconstruction correlation of units.

        Keyword Arguments:
            data -- input data
            mapping -- tuple of strings containing the mapping
                from input layer (first argument of tuple)
                to output layer (last argument of tuple)
            block -- list of string containing labels of units in the input
                layer that are blocked by setting the values to their means """

        if mapping == None: mapping = self.getMapping()
        if block == None: modelOut = self.getUnitExpect(data, mapping)
        else:
            dataInCopy = numpy.copy(data)
            for i in block: dataInCopy[:,i] = numpy.mean(dataInCopy[:,i])
            modelOut = self.getUnitExpect(dataInCopy, mapping)

        M = numpy.corrcoef(numpy.hstack(data).T)

        return True

    #def _getUnitEvalIntAccuracy(self, data, k = 1, **kwargs):
        #"""Return 'intrinsic accuracy' of units.

        #'intrinsic accuracy' := relperf
            #where model(v) is generated with: data(u not v) = mean(data(u))"""
        #vSize = len(self.units['visible'].params['label'])
        #relIntApprox = numpy.empty(vSize)
        #for v in range(vSize):
            #block = range(vSize)
            #block.pop(v)
            #relIntApprox[v] = self._getUnitEvalAccuracy(
                #data, block = block, k = k)[0][v]
        #return relIntApprox, None

    #def _getUnitEvalExtAccuracy(self, data, block = [], k = 1, **kwargs):
        #"""Return 'extrinsic accuracy' of units.
        
        #'extrinsic accuracy' := relApprox
            #where model(v) is generated with data(v) = mean(data(v))"""
        #relExtApprox = numpy.empty(len(self.units['visible'].params['label']))
        #for v in range(len(self.units['visible'].params['label'])):
            #relExtApprox[v] = self._getUnitEvalAccuracy(
                #data, block = block + [v], k = k)[0][v]
        #return relExtApprox, None

    #def _getUnitEvalRelativeIntAccuracy(self, data, k = 1, **kwargs):
        #"""Return 'intrinsic relative accuracy' of units
        
        #'intrinsic relative accuracy' := relperf
            #where model(v) is generated with data(u not v) = mean(data(u))"""
        #vSize = len(self.units['visible'].params['label'])
        #relIntApprox = numpy.empty(vSize)
        #for v in range(vSize):
            #block = range(vSize)
            #block.pop(v)
            #relIntApprox[v] = self._getUnitEvalRelativeAccuracy(
                #data = data, block = block, k = k)[0][v]
        #return relIntApprox, None

#    def _getUnitEvalRelativeExtAccuracy(self, data, block = [], k = 1, **kwargs):
#        """Return "accuracy (extrinsic)" of units.
#
#        extrelperf := relApprox where model(v) is generated with data(v) = mean(data(v))"""
#        relExtApprox = numpy.empty(len(self.units['visible'].params['label']))
#        for v in range(len(self.units['visible'].params['label'])):
#            relExtApprox[v] = self._getUnitEvalRelativeAccuracy(
#                data = data, block = block + [v], k = k)[0][v]
#        return relExtApprox, None


    ####################################################################
    # (Artificial Neuronal Network) Link Evaluation                    #
    ####################################################################

    def evalLinks(self, data, func = 'energy', **kwargs):
        """Evaluate system links respective to data.

        Keyword Arguments:
            data -- 2-tuple with numpy arrays: input data and output data
            func -- string containing link evaluation function
                For a full list of available link evaluation functions
                see: system.about('links', 'eval') """

        # get link evaluation function
        methods = self._getLinkEvalMethods()
        if not func in methods.keys(): return nemoa.log('error',
            "could not evaluate links: unknown method '%s'" % (func))
        method = methods[func]['method']
        if not hasattr(self, method): return nemoa.log('error',
            "could not evaluate links: unknown method '%s'" % (method))

        # prepare params for link evaluation
        params = kwargs.copy()
        if not 'mapping' in params.keys() or params['mapping'] == None:
            params['mapping'] = self.getMapping()
        inFmt = methods[func]['input']
        if   inFmt == 0: pass
        elif inFmt == 1: params['data'] = data[0]
        elif inFmt == 2: params['data'] = data[1]
        elif inFmt == 3: params['data'] = data
        else: return nemoa.log('error', 
            "could not evaluate links: unknown method '%s'" % (method))

        # evaluate system
        value = getattr(self, method)(**params)

        # 2Do
        # format output

        return value

    @staticmethod
    def _getLinkEvalMethods(): return {
        'energy': {
            'name': 'local energy',
            'method': 'getLinkEnergy',
            'input': 0, 'output': 0, 'format': '%.3f'}
        }

    def getLinkEnergy(self, data, mapping = None, **kwargs):
        """Return link energies of a layer.
        
        Keyword Arguments:
            mapping -- tuple of strings containing the mapping
                from input layer (first argument of tuple)
                to output layer (last argument of tuple) """

        if len(mapping) == 1:
            return nemoa.log('error', 'bad implementation of ann.getLinkEnergy')
        elif len(mapping) == 2:
            dIn  = data
            dOut = self.getUnitValues(dIn, mapping)
        else:
            dIn  = self.getUnitExpect(data, mapping[0:-1])
            dOut = self.getUnitValues(dIn, mapping[-2:])

        sID = self.getMapping().index(mapping[-2])
        tID = self.getMapping().index(mapping[-1])
        links = self._params['links'][(sID, tID)]
        src = self.units[mapping[-2]].params
        tgt = self.units[mapping[-1]].params

        return self.LinkLayer.energy(dIn, dOut, src, tgt, links)

    ####################################################################
    # Unit groups                                                      #
    ####################################################################

    def getMapping(self, src = None, tgt = None):
        """Return tuple with names of unit groups from source to target.
        
        Keyword Arguments:
            src -- name of source unit group
            tgt -- name of target unit group """

        mapping = tuple([g['name'] for g in self._params['units']])
        sid = mapping.index(src) \
            if isinstance(src, str) and src in mapping else 0
        tid = mapping.index(tgt) \
            if isinstance(tgt, str) and tgt in mapping else len(mapping)

        return mapping[sid:tid + 1] if sid <= tid \
            else mapping[tid:sid + 1][::-1]

    def _getTestData(self, dataset):
        """Return tuple with default test data."""

        return dataset.getData(
            cols = (self.getMapping()[0], self.getMapping()[-1]))

    ####################################################################
    # Link Layer Classes                                               #
    ####################################################################

    class LinkLayer():
        """Class to unify common ann link attributes."""

        params = {}

        def __init__(self): pass

        # 2Do
        # create classes for links

        @staticmethod
        def energy(dIn, dOut, src, tgt, links):
            """Return link energy as numpy array."""
            W = links['W']
            A = links['A']
            dSize = dIn.shape[0]
            classes = {'gauss': 0, 'sigmoid': 1}
            srcType = classes[src['class']]
            tgtType = classes[tgt['class']]
            lType = (srcType, tgtType)

            if lType == (0, 0): return \
                -(A * W * numpy.dot((dIn / numpy.exp(src['lvar'])).T, dOut) / dSize)
            if lType == (0, 1): return \
                -(A * W * numpy.dot((dIn / numpy.exp(src['lvar'])).T, dOut) / dSize)
            if lType == (1, 0): return \
                -(A * W * numpy.dot(dIn.T, dOut) / dSize)
            if lType == (1, 1): return \
                -(A * W * numpy.dot(dIn.T, dOut) / dSize)

        @staticmethod
        def getUpdates(data, model):
            """Return weight updates of a link layer."""

            D = numpy.dot(data[0].T, data[1]) / float(data[1].size)
            M = numpy.dot(model[0].T, model[1]) / float(data[1].size)

            return { 'W': D - M }

        @staticmethod
        def getUpdatesFromDelta(data, delta):

            return { 'W': -numpy.dot(data.T, delta) / data.size }

        # lets calculate with link params

        @staticmethod
        def one(dict):

            return {key: numpy.ones(shape = dict[key].shape) \
                for key in dict.keys()}

        @staticmethod
        def zero(dict):

            return {key: numpy.zeros(shape = dict[key].shape) \
                for key in dict.keys()}

        @staticmethod
        def sign(dict, remap = None):

            if remap == None: return {key: numpy.sign(dict[key]) \
                for key in dict.keys()}

            return {key:
                (remap[0] * (numpy.sign(dict[key]) < 0.0)
                + remap[1] * (numpy.sign(dict[key]) == 0.0)
                + remap[2] * (numpy.sign(dict[key]) > 0.0)) \
                for key in dict.keys()}

        @staticmethod
        def minmax(dict, min = None, max = None):

            if min == None: return {key: numpy.minimum(dict[key], max)
                for key in dict.keys()}
            if max == None: return {key: numpy.maximum(dict[key], min)
                for key in dict.keys()}

            return {key: numpy.maximum(numpy.minimum(dict[key], max), min)
                for key in dict.keys()}

        @staticmethod
        def sum(left, right):

            if isinstance(left, float) or isinstance(left, int):
                return {key: left + right[key] for key in left.keys()}
            if isinstance(right, float) or isinstance(right, int):
                return {key: left[key] + right for key in left.keys()}

            return {key: left[key] + right[key] for key in left.keys()}

        @staticmethod
        def multiply(left, right):

            if isinstance(left, float) or isinstance(left, int):
                return {key: left * right[key] for key in left.keys()}
            if isinstance(right, float) or isinstance(right, int):
                return {key: left[key] * right for key in left.keys()}

            return {key: left[key] * right[key] for key in left.keys()}

    ####################################################################
    # Gaussian to Sigmoidal Link Layer                                 #
    ####################################################################

#    class GSLinkLayer(LinkLayer):

    ####################################################################
    # Unit Layer Classes                                               #
    ####################################################################

    class UnitLayer():
        """Class to unify common ann unit attributes."""

        params = {}
        source = {}
        target = {}

        def __init__(self): pass

        def expect(self, data, source):

            if source['class'] == 'sigmoid': return \
                self.expectFromSLayer(data, source, self.getWeights(source))
            elif source['class'] == 'gauss': return \
                self.expectFromGLayer(data, source, self.getWeights(source))

            return False

        def getUpdates(self, data, model, source):

            return self.getParamUpdates(data, model, self.getWeights(source))

        def getDelta(self, inData, outDelta, source, target):

            return self.deltaFromBPROP(inData, outDelta,
                self.getWeights(source), self.getWeights(target))

        def getSamplesFromInput(self, data, source):

            if source['class'] == 'sigmoid': return self.getSamples(
                self.expectFromSLayer(data, source, self.getWeights(source)))
            elif source['class'] == 'gauss': return self.getSamples(
                self.expectFromGLayer(data, source, self.getWeights(source)))

            return False

        # 2DO
        # get weights from self.links[(a,b)].getWeights()

        def getWeights(self, source):



        # 2DO
                #if self._config['optimize']['useAdjacency']:
            #if target['name'] in self._links[source['name']]['target']:
                #return self._links[source['name']]['target'][target['name']]['W'] \
                    #* self._links[source['name']]['target'][target['name']]['A']
            #elif source['name'] in self._links[target['name']]['target']:
                #return (self._links[target['name']]['target'][source['name']]['W'] \
                    #* self._links[source['name']]['target'][target['name']]['A']).T
            if 'source' in self.source \
                and source['name'] == self.source['source']:
                return self.source['W']
            elif 'target' in self.target \
                and source['name'] == self.target['target']:
                return self.target['W'].T

            return nemoa.log('error', """Could not get links:
                Layers '%s' and '%s' are not connected!
                """ % (source['name'], self.params['name']))

        # lets calculate with unit params

        @staticmethod
        def one(dict):

            return {key: numpy.ones(shape = dict[key].shape) for key in dict.keys()}

        @staticmethod
        def zero(dict):

            return {key: numpy.zeros(shape = dict[key].shape) for key in dict.keys()}

        @staticmethod
        def sign(dict, remap = None):

            if remap == None: return {key: numpy.sign(dict[key]) \
                for key in dict.keys()}

            return {key: (remap[0] * (numpy.sign(dict[key]) < 0.0)
                + remap[1] * (numpy.sign(dict[key]) == 0.0)
                + remap[2] * (numpy.sign(dict[key]) > 0.0)) for key in dict.keys()}

        @staticmethod
        def minmax(dict, min = None, max = None):

            if min == None: return {key: numpy.minimum(dict[key], max)
                for key in dict.keys()}
            if max == None: return {key: numpy.maximum(dict[key], min)
                for key in dict.keys()}

            return {key: numpy.maximum(numpy.minimum(dict[key], max), min)
                for key in dict.keys()}

        @staticmethod
        def sum(left, right):

            if isinstance(left, float) or isinstance(left, int):
                return {key: left + right[key] for key in left.keys()}
            if isinstance(right, float) or isinstance(right, int):
                return {key: left[key] + right for key in left.keys()}

            return {key: left[key] + right[key] for key in left.keys()}

        @staticmethod
        def multiply(left, right):

            if isinstance(left, float) or isinstance(left, int):
                return {key: left * right[key] for key in left.keys()}
            if isinstance(right, float) or isinstance(right, int):
                return {key: left[key] * right for key in left.keys()}

            return {key: left[key] * right[key] for key in left.keys()}

    ####################################################################
    # Sigmoidal Unit Layer                                             #
    ####################################################################

    class SUnitLayer(UnitLayer):
        """Sigmoidal Unit Layer.
        
        Layer of units with sigmoidal activation function and binary distribution. """

        def initialize(self, data = None):
            """Initialize system parameters of sigmoid distributed units using data. """

            size = len(self.params['label'])
            shape = (1, size)

            self.params['bias'] = 0.5 * numpy.ones(shape)
            #self.params['bias'] = numpy.zeros(shape)

            return True

        def update(self, updates):
            """Update parameter of sigmoid units. """

            self.params['bias'] += updates['bias']

            return True

        def overwrite(self, params):
            """Merge parameters of sigmoid units."""

            for i, u in enumerate(params['label']):
                if u in self.params['label']:
                    l = self.params['label'].index(u)
                    self.params['bias'][0, l] = params['bias'][0, i]

            return True

        @staticmethod
        def remove(layer, select):
            """Delete selection (list of ids) of units from parameter arrays. """

            layer['bias'] = layer['bias'][0, [select]]

            return True

        @staticmethod
        def check(layer):

            return 'bias' in layer

        def energy(self, data):
            """Return system energy of sigmoidal units as numpy array. """

            bias = self.params['bias']

            return - numpy.mean(data * bias, axis = 0)

        def expectFromSLayer(self, data, source, weights):
            """Return expected values of a sigmoid output layer
            calculated from a sigmoid input layer. """

            bias = self.params['bias']

            return self.sigmoid(bias + numpy.dot(data, weights))

        def expectFromGLayer(self, data, source, weights):
            """Return expected values of a sigmoid output layer
            calculated from a gaussian input layer. """

            bias = self.params['bias']
            lvar = numpy.exp(source['lvar'])

            return self.sigmoid(bias + numpy.dot(data / lvar, weights))

        def getParamUpdates(self, data, model, weights):
            """Return parameter updates of a sigmoidal output layer
            calculated from real data and modeled data. """

            size = len(self.params['label'])

            return {'bias': numpy.mean(data[1] - model[1], axis = 0).reshape((1, size))}

        def getUpdatesFromDelta(self, delta):

            size = len(self.params['label'])

            return {'bias': - numpy.mean(delta, axis = 0).reshape((1, size))}

        def deltaFromBPROP(self, data_in, delta_out, W_in, W_out):

            bias = self.params['bias']

            return numpy.dot(delta_out, W_out) * \
                self.Dlogistic((bias + numpy.dot(data_in, W_in)))

        @staticmethod
        def grad(x):
            """Return gradiant of standard logistic function. """

            numpy.seterr(over = 'ignore')

            return ((1.0 / (1.0 + numpy.exp(-x)))
                * (1.0 - 1.0 / (1.0 + numpy.exp(-x))))

        @staticmethod
        def getValues(data):
            """Return median of bernoulli distributed layer
            calculated from expected values. """

            return (data > 0.5).astype(float)

        @staticmethod
        def getSamples(data):
            """Return sample of bernoulli distributed layer
            calculated from expected value. """

            return (data > numpy.random.rand(
                data.shape[0], data.shape[1])).astype(float)

        def get(self, unit):

            id = self.params['label'].index(unit)
            cl = self.params['class']
            visible = self.params['visible']
            bias = self.params['bias'][0, id]

            return {'label': unit, 'id': id, 'class': cl,
                'visible': visible, 'bias': bias}

        # common activation functions

        @staticmethod
        def sigmoid(x):
            """Standard logistic function."""

            return 1.0 / (1.0 + numpy.exp(-x))

        @staticmethod
        def logistic(x):
            """Standard logistic function."""

            return 1.0 / (1.0 + numpy.exp(-x))

        @staticmethod
        def Dlogistic(x):
            """Derivation of standard logistic function."""

            return ((1.0 / (1.0 + numpy.exp(-x)))
                * (1.0 - 1.0 / (1.0 + numpy.exp(-x))))

        @staticmethod
        def tanh(x):
            """Standard hyperbolic tangens function."""

            return numpy.tanh(x)

        @staticmethod
        def Dtanh(x):
            """Derivation of standard hyperbolic tangens function."""

            return 1.0 - tanh(x) ** 2

        @staticmethod
        def tanhEff(x):
            """Hyperbolic tangens function, proposed in paper:
            'Efficient BackProp' by LeCun, Bottou, Orr, Müller"""

            return 1.7159 * numpy.tanh(0.6666 * x)

    ####################################################################
    # Gaussian Unit Layer                                              #
    ####################################################################

    class GUnitLayer(UnitLayer):
        """Units with linear activation function and gaussian distribution"""

        def initialize(self, data = None, vSigma = 0.4):
            """Initialize parameters of gauss distributed units. """

            size = len(self.params['label'])
            if data == None:
                self.params['bias'] = numpy.zeros([1, size])
                self.params['lvar'] = numpy.zeros([1, size])
            else:
                self.params['bias'] = \
                    numpy.mean(data, axis = 0).reshape(1, size)
                self.params['lvar'] = \
                    numpy.log((vSigma * numpy.ones((1, size))) ** 2)

            return True

        def update(self, updates):
            """Update gaussian units. """

            self.params['bias'] += updates['bias']
            self.params['lvar'] += updates['lvar']

            return True

        def getParamUpdates(self, data, model, weights):
            """Return parameter updates of a gaussian output layer
            calculated from real data and modeled data. """

            shape = (1, len(self.params['label']))
            var = numpy.exp(self.params['lvar'])
            bias = self.params['bias']

            updBias = \
                numpy.mean(data[1] - model[1], axis = 0).reshape(shape) / var
            updData = \
                numpy.mean(0.5 * (data[1] - bias) ** 2 - data[1]
                * numpy.dot(data[0], weights), axis = 0)
            updModel = \
                numpy.mean(0.5 * (model[1] - bias) ** 2 - model[1]
                * numpy.dot(model[0], weights), axis = 0)
            updLVar = (updData - updModel).reshape(shape) / var

            return { 'bias': updBias, 'lvar': updLVar }

        def getUpdatesFromDelta(self, delta):
            # HINT: no update of lvar

            shape = (1, len(self.params['label']))

            return {
                'bias': - numpy.mean(delta, axis = 0).reshape(shape),
                'lvar': - numpy.zeros(shape = shape)}

        def overwrite(self, params):
            """Merge parameters of gaussian units. """

            for i, u in enumerate(params['label']):
                if u in self.params['label']:
                    l = self.params['label'].index(u)
                    self.params['bias'][0, l] = params['bias'][0, i]
                    self.params['lvar'][0, l] = params['lvar'][0, i]

            return True

        @staticmethod
        def remove(layer, select):
            """Delete selection (list of ids) of units from parameter arrays. """

            layer['bias'] = layer['bias'][0, [select]]
            layer['lvar'] = layer['lvar'][0, [select]]

            return True

        def expectFromSLayer(self, data, source, weights):
            """Return expected values of a gaussian output layer
            calculated from a sigmoid input layer. """

            return self.params['bias'] + numpy.dot(data, weights)

        @staticmethod
        def grad(x):
            """Return gradient of activation function. """

            return 1.0

        @staticmethod
        def check(layer):

            return 'bias' in layer and 'lvar' in layer

        def energy(self, data):

            bias = self.params['bias']
            lvar = numpy.exp(self.params['lvar'])
            energy = - 0.5 * numpy.mean((data - bias) ** 2, axis = 0) / lvar

            return energy.reshape(bias.size)

        @staticmethod
        def getValues(data):
            """Return median of gauss distributed layer
            calculated from expected values."""

            return data

        def getSamples(self, data):
            """Return sample of gauss distributed layer
            calculated from expected values. """

            sigma = numpy.sqrt(numpy.exp(self.params['lvar']))

            return numpy.random.normal(data, sigma)

        def get(self, unit):

            id = self.params['label'].index(unit)

            cl = self.params['class']
            bias = self.params['bias'][0, id]
            lvar = self.params['lvar'][0, id]
            visible = self.params['visible']

            return {
                'label': unit, 'id': id, 'class': cl,
                'visible': visible, 'bias': bias, 'lvar': lvar }
