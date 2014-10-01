# -*- coding: utf-8 -*-

__author__  = 'Patrick Michl'
__email__   = 'patrick.michl@gmail.com'
__license__ = 'GPLv3'

import nemoa
import numpy
import copy
import os
import re
import scipy.cluster.vq
import csv

class dataset:

    _config = None
    _data = None

    def __init__(self, config = {}):
        """Set configuration of dataset from dictionary."""
        self._config = config.copy()
        self._data = {}

    def _get_config(self):
        """Return configuration as dictionary."""
        return self._config.copy()

    def _is_empty(self):
        """Return true if dataset is empty."""
        return not 'name' in self._config or not self._config['name']

    def _is_binary(self):
        """Test if dataset contains only binary data.

        Returns:
            Boolean value which is True if dataset contains only
            binary values.

        """

        data = self.data()
        binary = ((data == data.astype(bool)).sum() == data.size)

        if not binary: return nemoa.log('error',
            'The dataset does not contain binary data!')

        return True

    def _is_gauss_normalized(self, size = 100000,
        max_mean = 0.05, max_sdev = 1.05):
        """Test if dataset contains gauss normalized data.

        Args:
            size (int, optional): number of samples used to calculate
                mean of absolute values and standard deviation
            max_mean (float, optional): allowed maximum for mean of
                absolute values
            max_sdev (float, optional): allowed maximum for standard
                deviation

        Returns:
            Boolean value which is True if the following conditions are
            satisfied:
            (1) The mean of the absolute values of a given number of
                random samples of the dataset is below max_mean
            (2) The standard deviation of a given number of random
                samples of the dataset is below max_sdev

        """

        data = self.data(size) # get numpy array with data

        # test mean of absolute values
        mean = data.mean()
        if numpy.abs(mean) >= max_mean: return nemoa.log('error',
            """Dataset does not contain gauss normalized data:
            mean of absolute values is %.3f!""" % (mean))

        # test standard deviation
        sdev = data.std()
        if sdev >= max_sdev: return nemoa.log('error',
            """Dataset does not contain gauss normalized data:
            standard deviation is %.3f!""" % (sdev))

        return True

    def _is_configured(self):
        """Return true if dataset is configured."""
        return len(self._data.keys()) > 0

    def configure(self, network, use_cache = False, **kwargs):
        """Configure dataset to a given network object

        Args:
            network (object): nemoa network object
            use_cache (bool, optional): shall data be cached

        """

        nemoa.log("configure dataset '%s' to network '%s'" % \
            (self.name(), network.name()))
        nemoa.log('set', indent = '+1')

        # load data from cachefile (if caching and cachefile exists)
        cacheFile = self._search_cache_file(network) if use_cache else None
        if cacheFile and self.load(cacheFile):
            nemoa.log('load cachefile: \'%s\'' % (cacheFile))

            # preprocess data
            if 'preprocessing' in self._config.keys():
                self.preprocess(**self._config['preprocessing'])
            nemoa.log('set', indent = '-1')
            return True

        # create table with one record for every single dataset files
        if not 'table' in self._config:
            conf = self._config.copy()
            self._config['table'] = {}
            self._config['table'][self._config['name']] = conf
            self._config['table'][self._config['name']]['fraction'] = 1.

        # Annotation

        # get nodes from network and convert to common format
        if network._config['type'] == 'auto': netGroups = {'v': None}
        else:
            # get grouped network node labels and label format
            netGroups = network.nodes(type = 'visible',
                group_by_layer = True)

            netGroupsOrder = []
            for layer in netGroups: netGroupsOrder.append(
                (network.layer(layer)['id'], layer))
            netGroupsOrder = sorted(netGroupsOrder)

            # convert network node labels to common format
            nemoa.log('search network nodes in dataset sources')
            convNetGroups = {}
            convNetGroupsLost = {}
            convNetNodes = []
            convNetNodesLost = []
            netLblFmt = network._config['label_format']
            for id, group in netGroupsOrder:
                convNetGroups[group], convNetGroupsLost[group] = \
                    nemoa.dataset.annotation.convert(netGroups[group],
                    input = netLblFmt)
                convNetNodes += convNetGroups[group]
                convNetNodesLost += convNetGroupsLost[group]

            # notify if any network node labels could not be converted
            if convNetNodesLost:
                nemoa.log("""%s of %s network nodes could not
                    be converted! (see logfile)"""
                    % (len(convNetNodesLost), len(convNetNodes)))
                # TODO: get original node labels for log file
                nemoa.log('logfile', nemoa.common.str_to_list(
                    convNetNodesLost))

        # get columns from dataset files and convert to common format
        colLabels = {}
        nemoa.log('configure data sources')
        nemoa.log('set', indent = '+1')
        for src in self._config['table']:
            nemoa.log("configure '%s'" % (src))
            srcCnf = self._config['table'][src]

            # get column labels from csv-file
            csvType = srcCnf['source']['csvtype'].strip().lower() \
                if 'csvtype' in srcCnf['source'] else None
            origColLabels = nemoa.common.csv_get_col_labels(
                srcCnf['source']['file'], type = csvType)
            if not origColLabels: continue

            # set annotation format
            format = srcCnf['source']['columns'] \
                if 'columns' in srcCnf['source'] else 'generic:string'

            # convert column labes
            convColLabels, convColLabelsLost = \
                nemoa.dataset.annotation.convert(
                origColLabels, input = format)

            # notify if any dataset columns could not be converted
            if convColLabelsLost:
                nemoa.log('warning', """%i of %i dataset columns
                    could not be converted! (see logfile)""" %
                    (len(convColLabelsLost), len(convColLabels)))
                nemoa.log('logfile', ", ".join([convColLabels[i] \
                    for i in convColLabelsLost]))

            if not network._config['type'] == 'auto':

                # search converted nodes in converted columns
                numLost = 0
                numAll = 0
                lostNodes = {}
                for id, group in netGroupsOrder:
                    lostNodesConv = \
                        [val for val in convNetGroups[group] \
                        if val not in convColLabels]
                    numAll += len(convNetGroups[group])
                    if not lostNodesConv: continue
                    numLost += len(lostNodesConv)

                    # get original labels
                    lostNodes[group] = [netGroups[group][
                        convNetGroups[group].index(val)]
                        for val in lostNodesConv]

                # notify if any network nodes could not be found
                if numLost:
                    nemoa.log('warning', """%i of %i network nodes
                        could not be found in dataset source!
                        (see logfile)""" % (numLost, numAll))
                    for group in lostNodes: nemoa.log('logfile',
                        'missing nodes (group %s): ' % (group)
                        + ', '.join(lostNodes[group]))

            # prepare dictionary for column source ids
            colLabels[src] = {
                'conv': convColLabels,
                'usecols': (),
                'notusecols': convColLabelsLost }

        nemoa.log('set', indent = '-1')

        # intersect converted dataset column labels
        interColLabels = colLabels[colLabels.keys()[0]]['conv']
        for src in colLabels:
            list = colLabels[src]['conv']
            blackList = [list[i] for i in colLabels[src]['notusecols']]
            interColLabels = [val for val in interColLabels \
                if val in list and not val in blackList]

        # if network type is 'auto', set network visible nodes
        # to intersected data from database files (without label column)
        if network._config['type'] == 'auto':
            netGroups['v'] = [label for label in interColLabels \
                if not label == 'label']
            convNetGroups = netGroups

        # search network nodes in dataset columns
        self._config['columns'] = ()
        for groupid, group in netGroupsOrder:
            found = 0

            for id, col in enumerate(convNetGroups[group]):
                if not col in interColLabels: continue
                found += 1

                # add column (use network label and group)
                self._config['columns'] += ((group, netGroups[group][id]), )
                for src in colLabels: colLabels[src]['usecols'] \
                    += (colLabels[src]['conv'].index(col), )

            if not found:
                nemoa.log('error', """no node from network group '%s'
                    could be found in dataset source!""" % (group))
                nemoa.log('set', indent = '-1')
                return False

        # update source file config
        for src in colLabels: self._config['table'][src]['source']['usecols'] \
            = colLabels[src]['usecols']

        # Column & Row Filters

        # add column filters and partitions from network node groups
        self._config['colFilter'] = {'*': ['*:*']}
        self._config['colPartitions'] = {'groups': []}
        for group in netGroups:
            self._config['colFilter'][group] = [group + ':*']
            self._config['colPartitions']['groups'].append(group)

        # add row filters and partitions from sources
        self._config['rowFilter'] = {'*': ['*:*']}
        self._config['rowPartitions'] = {'source': []}
        for source in self._config['table']:
            self._config['rowFilter'][source] = [source + ':*']
            self._config['rowPartitions']['source'].append(source)

        # Import data from CSV-files into numpy arrays

        # import data from sources
        nemoa.log('import data from sources')
        nemoa.log('set', indent = '+1')
        self._data = {}
        for src in self._config['table']:
            self._data[src] = {
                'fraction': self._config['table'][src]['fraction'],
                'array': self._csv_get_data(src) }
        nemoa.log('set', indent = '-1')

        # save cachefile
        if use_cache:
            cacheFile = self._create_cache_file(network)
            nemoa.log('save cachefile: \'%s\'' % (cacheFile))
            self.save(cacheFile)

        # preprocess data
        if 'preprocessing' in self._config.keys():
            self.preprocess(**self._config['preprocessing'])

        nemoa.log('set', indent = '-1')
        return True

    def preprocess(self, **kwargs):
        """Data preprocessing.

        Stratification, normalization and transformation of data.

        Args:
            stratify: see method self._stratify()
            normalize: see method self._normalize()
            transform: see method self._transform()

        """

        nemoa.log('preprocessing data')
        nemoa.log('set', indent = '+1')

        if 'stratify' in kwargs.keys():
            self._stratify(kwargs['stratify'])

        if 'normalize' in kwargs.keys():
            self._normalize(kwargs['normalize'])

        if 'transform' in kwargs.keys():
            self._transform(kwargs['transform'])

        nemoa.log('set', indent = '-1')

        return True

    def _stratify(self, algorithm = 'auto'):
        """Stratify data.

        Args:
            algorithm (str): name of algorithm used for stratification
                'none':
                    probabilities of sources are
                    number of all samples / number of samples in source
                'auto':
                    probabilities of sources are hierarchical distributed
                    as defined in the configuration
                'equal':
                    probabilities of sources are
                    1 / number of sources

        """

        nemoa.log("stratify data using '%s'" % (algorithm))

        if algorithm.lower() in ['none']:
            allSize = 0
            for src in self._data:
                allSize += self._data[src]['array'].shape[0]
            for src in self._data: self._data[src]['fraction'] = \
                float(allSize) / float(self._data[src]['array'].shape[0])
            return True
        if algorithm.lower() in ['auto']: return True
        if algorithm.lower() in ['equal']:
            frac = 1. / float(len(self._data))
            for src in self._data: self._data[src]['fraction'] = frac
            return True
        return False

    def _normalize(self, algorithm = 'gauss'):
        """Normalize stratified data

        Args:
            algorithm: name of algorithm used for data normalization
                'gauss': Gaussian normalization

        """
        nemoa.log('normalize data using \'%s\'' % (algorithm))

        if algorithm.lower() == 'gauss':

            # get data for calculation of mean and variance
            # for single source datasets take all data
            # for multi source datasets take a big bunch of stratified data
            if len(self._data.keys()) > 1:
                data = self.data(size = 1000000, output = 'recarray')
            else:
                data = self._get_data_from_source(
                    source = self._data.keys()[0])

            # iterative update sources
            # get mean and standard deviation per column (recarray)
            # and update the values
            for src in self._data:
                if self._data[src]['array'] == None: continue
                for col in self._data[src]['array'].dtype.names[1:]:
                    self._data[src]['array'][col] = \
                        (self._data[src]['array'][col] - data[col].mean()) \
                        / data[col].std()
            return True
        return False

    def _transform(self, algorithm = 'system', system = None,
        mapping = None, **kwargs):
        """Transform dataset.

        Args:
            algorithm (str): name of algorithm used for data
                transformation
                'system':
                    Transform data using nemoa system instance
                'gaussToBinary':
                    Transform Gauss distributed values to binary values
                    in {0, 1}
                'gaussToWeight':
                    Transform Gauss distributed values to weights
                    in [0, 1]
                'gaussToDistance': ??
                    Transform Gauss distributed values to distances
                    in [0, 1]
            system: nemoa system instance (nemoa object root class
                'system') used for model based transformation of data
            mapping: ...

        """

        if not isinstance(algorithm, str): return False

        # system based data transformation
        if algorithm.lower() == 'system':
            if not nemoa.type.is_system(system):
                return nemoa.log('error', """could not transform data
                    using system: invalid system.""")
            nemoa.log("transform data using system '%s'"
                % (system.name()))
            nemoa.log('set', indent = '+1')

            if mapping == None: mapping = system.mapping()

            sourceColumns = system.getUnits(group = mapping[0])[0]
            targetColumns = system.getUnits(group = mapping[-1])[0]

            self._set_col_labels(sourceColumns)

            for src in self._data:
                data = self._data[src]['array']

                dataArray = data[sourceColumns].view('<f8').reshape(
                    data.size, len(sourceColumns))
                transArray = system.map_data(
                    dataArray, mapping = mapping, **kwargs)

                # create empty record array
                numRows = self._data[src]['array']['label'].size
                colNames = ('label',) + tuple(targetColumns)
                colFormats = ('<U12',) + tuple(['<f8' for x in targetColumns])
                newRecArray = numpy.recarray((numRows,),
                    dtype = zip(colNames, colFormats))

                # set values in record array
                newRecArray['label'] = self._data[src]['array']['label']
                for colID, colName in enumerate(newRecArray.dtype.names[1:]):

                    # update source data columns
                    newRecArray[colName] = \
                        (transArray[:, colID]).astype(float)

                self._data[src]['array'] = newRecArray # set record array

            self._set_col_labels(targetColumns)
            nemoa.log('set', indent = '-1')
            return True

        # gauss to binary data transformation
        elif algorithm.lower() in ['gausstobinary', 'binary']:
            nemoa.log('transform data using \'%s\'' % (algorithm))
            for src in self._data:
                # update source per column (recarray)
                for colName in self._data[src]['array'].dtype.names[1:]:
                    # update source data columns
                    self._data[src]['array'][colName] = \
                        (self._data[src]['array'][colName] > 0.
                        ).astype(float)
            return True

        # gauss to weight in [0, 1] data transformation
        elif algorithm.lower() in ['gausstoweight', 'weight']:
            nemoa.log('transform data using \'%s\'' % (algorithm))
            for src in self._data:
                # update source per column (recarray)
                for colName in self._data[src]['array'].dtype.names[1:]:
                    # update source data columns
                    self._data[src]['array'][colName] = \
                        (2. / (1. + numpy.exp(-1. * \
                        self._data[src]['array'][colName] ** 2))
                        ).astype(float)
            return True

        # gauss to distance data transformation
        # ????
        elif algorithm.lower() in ['gausstodistance', 'distance']:
            nemoa.log('transform data using \'%s\'' % (algorithm))
            for src in self._data:
                # update source per column (recarray)
                for colName in self._data[src]['array'].dtype.names[1:]:
                    self._data[src]['array'][colName] = \
                        (1. - (2. / (1. + numpy.exp(-1. * \
                        self._data[src]['array'][colName] ** 2)))
                        ).astype(float)
            return True

        return nemoa.log('error', """could not transform data:
            unknown algorithm '%s'!""" % (algorithm))

    #def value(self, row = None, col = None):
        #"""Return single value from dataset."""
        #retVal = self.data(cols = ([col]), output = 'list,array')
        #return retVal[1][retVal[0].index(row)]

    def data(self, size = 0, rows = '*', cols = '*',
        corruption = (None, 0.), output = 'array'):
        """Return a given number of stratified samples.

        Args:
            size: Size of data (Number of samples)
                default: value 0 returns all samples unstratified
            rows: string describing row filter (row groups)
                default: value '*' selects all rows
            cols: string describing column filter (column group)
                default: value '*' selects all columns
            corruption: 2-tuple describing artificial data corruption
                first entry of tuple: type of corruption / noise model
                    'none': no corruption
                    'mask': Masking Noise
                        A fraction of every sample is forced to zero
                    'gauss': Gaussian Noise
                        Additive isotropic Gaussian noise
                    'salt': Salt-and-pepper noise
                        A fraction of every sample is forced to min or max
                        with equal possibility
                    default: Value None equals to 'no'
                second entry of tuple: corruption factor
                    float in interval [0, 1] describing the strengt
                    of the corruption. The influence of the parameter
                    depends on the corruption type
                    default: Value 0.5
            fmt: tuple of strings describing data output. Supported strings:
                'array': numpy array with data
                'recarray': numpy record array with data
                'cols': list of column names
                'rows': list of row names
                default: 'array'

        """

        # check Configuration and Keyword Arguments
        if not self._is_configured(): return nemoa.log('error',
            'could not get data: dataset is not yet configured!')
        if not isinstance(size, int) or size < 0: return nemoa.log(
            'error', 'could not get data: invalid argument size!')

        # stratify and filter data
        srcStack = ()
        for source in self._data.keys():
            if size > 0: srcData = self._get_data_from_source(source,
                size = size + 1, rows = rows)
            else: srcData = self._get_data_from_source(source, rows = rows)
            if srcData == False or srcData.size == 0: continue
            srcStack += (srcData, )
        if not srcStack: return nemoa.log('error',
            'could not get data: no valid data sources found!')
        data = numpy.concatenate(srcStack)

        # (optionally) Shuffle data and correct size
        if size:
            numpy.random.shuffle(data)
            data = data[:size]

        # format data
        if isinstance(cols, str): fmtData = self._format(
            data, cols = self._get_col_labels(cols), output = output)
        elif isinstance(cols, list): fmtData = self._format(
            data, cols = cols, output = output)
        elif isinstance(cols, tuple): fmtData = tuple(
            [self._format(data, cols = self._get_col_labels(grp),
            output = output) for grp in cols])
        else: return nemoa.log('error', """could not get data:
            invalid argument for columns!""")

        # Corrupt data (optionally)
        return self._corrupt(fmtData, \
            type = corruption[0], factor = corruption[1])

    def _get_data_from_source(self, source, size = 0, rows = '*'):
        """Return numpy recarray with data from a single source.

        Args:
            source: name of data source to get data from
            size: number of random choosen samples to return
                default: value 0 returns all samples of given source
            rows: string describing a row filter using wildcards
                default: value '*' selects all rows

        """

        # Check source
        if not isinstance(source, str) \
            or not source in self._data \
            or not isinstance(self._data[source]['array'], numpy.ndarray): \
            return nemoa.log('error', """could not retrieve data:
            invalid source: '%s'!""" % (source))

        # check row Filter
        if not rows in self._config['rowFilter']: return nemoa.log('error',
            "could not retrieve data: invalid row filter: '%s'!" % (rows))

        # apply row filter
        if rows == '*' or source + ':*' in self._config['rowFilter'][rows]:
            srcArray = self._data[source]['array']
        else:
            rowFilter = self._config['rowFilter'][rows]
            rowFilterFiltered = [
                row.split(':')[1] for row in rowFilter
                        if row.split(':')[0] in [source, '*']]
            rowSelect = numpy.asarray([
                rowid for rowid, row in enumerate(self._data[source]['array']['label'])
                    if row in rowFilterFiltered])
            if rowSelect.size == 0: return rowSelect
            srcArray = numpy.take(self._data[source]['array'], rowSelect)

        # stratify and return data as numpy record array
        if size == 0 or size == None: return srcArray
        srcFrac = self._data[source]['fraction']
        rowSelect = numpy.random.randint(srcArray.size,
            size = round(srcFrac * size))
        return numpy.take(srcArray, rowSelect)

    def _corrupt(self, data, type = None, factor = 0.5):
        """Corrupt given data.

        Args:
            data: numpy array containing data
            type (str): algorithm for corruption
                'mask': Masking Noise
                    A fraction of every sample is forced to zero
                'gauss': Gaussian Noise
                    Additive isotropic Gaussian noise
                'salt': Salt-and-pepper noise
                    A fraction of every sample is forced to min or max
                    with equal possibility
            factor (float, optional): strengt of the corruption
                The influence of the parameter depends on the
                type of the corruption

        Returns:
            Numpy array with (partly) corrupted data. The shape is
            identical to the shape of the given data.

        """

        if type in [None, 'none']: return data
        elif type == 'mask': return data * numpy.random.binomial(
            size = data.shape, n = 1, p = 1. - factor)
        elif type == 'gauss': return data + numpy.random.normal(
            size = data.shape, loc = 0., scale = factor)
        # TODO: implement salt and pepper noise
        #elif type == 'salt': return
        else: return nemoa.log('error',
            "unkown data corruption type '%s'!" % (type))

    def _format(self, data, cols = '*', output = 'array'):
        """Return data in given format.

        Args:
            cols: name of column group
                default: value '*' does not filter columns
            output: ...

        """

        # check columns
        if cols == '*': cols = self._get_col_labels()
        elif not len(cols) == len(set(cols)): return nemoa.log('error',
            'could not retrieve data: columns are not unique!')
        elif [c for c in cols if c not in self._get_col_labels()]: \
            return nemoa.log('error',
            'could not retrieve data: unknown columns!')

        # check format
        if isinstance(output, str): fmtTuple = (output, )
        elif isinstance(output, tuple): fmtTuple = output
        else: return nemoa.log('error',
            "could not retrieve data: invalid 'format' argument!")

        # format data
        retTuple = ()
        for fmtStr in fmtTuple:
            if fmtStr == 'array': retTuple += (
                data[cols].view('<f8').reshape(data.size, len(cols)), )
            elif fmtStr == 'recarray': retTuple += (
                data[['label'] + cols], )
            elif fmtStr == 'cols': retTuple += (
                [col.split(':')[1] for col in cols], )
            elif fmtStr in ['rows', 'list']: retTuple += (
                data['label'].tolist(), )
        if isinstance(output, str): return retTuple[0]
        return retTuple

    # column Labels and Column Groups
    def _get_col_labels(self, group = '*'):
        """Return list of strings containing column groups and labels."""
        if group == '*': return ['%s:%s' % (col[0], col[1])
            for col in self._config['columns']]
        if not group in self._config['colFilter']: return []
        colFilter = self._config['colFilter'][group]
        labels = []
        for col in self._config['columns']:
            if ('*:*') in colFilter \
                or ('%s:*' % (col[0])) in colFilter \
                or ('*:%s' % (col[1])) in colFilter \
                or ('%s:%s' % (col[0], col[1])) in colFilter:
                labels.append('%s:%s' % (col[0], col[1]))
        return labels

    def _set_col_labels(self, labels):
        """Set column labels from list of strings."""
        self._config['columns'] = tuple([col.split(':') for col in labels])
        return True

    def _get_col_groups(self):
        groups = {}
        for group, label in self._config['columns']:
            if not group in groups: groups[group] = []
            groups[group].append(label)
        return groups

    def _set_col_filter(self, group, columns):
        # TODO: check columns!
        self._config['colFilter'][group] = columns
        return True

    #def addRowFilter(self, name, filter):
        ## create unique name for filter
        #filterName = name
        #i = 1
        #while filterName in self._config['rowFilter']:
            #i += 1
            #filterName = '%s.%i' % (name, i)

        ## TODO: check filter
        #self._config['rowFilter'][filterName] = filter
        #return filterName

    #def delRowFilter(self, name):
        #if name in self._config['rowFilter']:
            #del self._config['rowFilter'][name]
            #return True
        #return False

    #def getRowFilter(self, name):
        #if not name in self._config['rowFilter']:
            #nemoa.log('warning', "unknown row filter '" + name + "'!")
            #return []
        #return self._config['rowFilter'][name]

    #def getRowFilterList(self):
        #return self._config['rowFilter'].keys()

    #def addColFilter(self):
        #pass

    #def delColFilter(self, name):
        #if name in self._config['colFilter']:
            #del self._config['colFilter'][name]
            #return True
        #return False

    #def getColFilters(self):
        #return self._config['colFilter']

    #def addRowPartition(self, name, partition):
        #if name in self._config['rowPartitions']:
            #nemoa.log('warning', "row partition '" + name + "' allready exists!")

        ## create unique name for partition
        #partitionName = name
        #i = 1
        #while partitionName in self._config['rowPartitions']:
            #i += 1
            #partitionName = '%s.%i' % (name, i)

        #filterNames = []
        #for id, filter in enumerate(partition):
            #filterNames.append(
                #self.addRowFilter('%s.%i' % (name, id + 1), filter))

        #self._config['rowPartitions'][partitionName] = filterNames
        #return partitionName

    #def delRowPartition(self, name):
        #pass

    #def getRowPartition(self, name):
        #if not name in self._config['rowPartitions']:
            #nemoa.log('warning', "unknown row partition '" + name + "'!")
            #return []
        #return self._config['rowPartitions'][name]

    #def getRowPartitionList(self):
        #return self._config['rowPartitions'].keys()

    #def createRowPartition(self, algorithm = 'bcca', **params):
        #if algorithm == 'bcca':
            #partition = self.getBccaPartition(**params)
        #else:
            #nemoa.log('warning', "unknown partition function '%s'")

        ## add partition
        #return self.addRowPartition(algorithm, partition)

    #def getBccaPartition(self, **params):
        #rowLabels, data = self.data(output = 'list,array')
        #numRows, numCols = data.shape

        ## check parameters
        #if 'groups' in params:
            #groups = params['groups']
        #else:
            #nemoa.log('warning', "parameter 'groups' is needed to create BCCA partition!")
            #return []

        ## get BCCA biclusters
        #biclusters = self.getBccaBiclusters(**params)

        ## get bicluster distances
        #distance = self.getBiclusterDistance(biclusters, **params)

        ## cluster samples using k-means
        #nemoa.log('cluster distances using k-means with k = %i' % (groups))
        #clusters = self.getClusters(algorithm = 'k-means', data = distance, k = groups)
        #cIDs = numpy.asarray(clusters)
        #partition = []
        #for cID in xrange(groups):
            #partition.append(numpy.where(cIDs == cID)[0].tolist())

        ## get labels
        #labeledPartition = []
        #for pID, c in enumerate(partition):
            #labels = []
            #for sID in c:
                #labels.append(rowLabels[sID])
            #labeledPartition.append(list(set(labels)))

        #return labeledPartition

    #def getClusters(self, algorithm = 'k-means', **params):
        #if algorithm == 'k-means':
            #return self.getKMeansClusters(**params)

        #nemoa.log('warning', "unsupported clustering algorithm '" + algorithm + "'!")
        #return None

    #def getKMeansClusters(self, data, k = 3):
        #return scipy.cluster.vq.vq(data, scipy.cluster.vq.kmeans(data, k)[0])[0]

    #def getBiclusters(self, algorithm = 'bcca', **params):
        #if algorithm == 'bcca':
            #return getBccaBiclusters(**params)

        #nemoa.log('warning', "unsupported biclustering algorithm '" + algorithm + "'!")
        #return None

    #def getBccaBiclusters(self, **params):
        #data = self.data(output = 'array')
        #numRows, numCols = data.shape

        ## check params
        #if not 'threshold' in params:
            #nemoa.log("param 'threshold' is needed for BCCA Clustering!")
            #return []
        #if not ('minsize' in params or 'size' in params):
            #nemoa.log("param 'size' or 'minsize' is needed for BCCA Clustering!")
            #return []

        ## get params
        #threshold = params['threshold']
        #if 'minsize' in params:
            #minsize = params['minsize']
            #size = 0
        #else:
            #minsize = 3
            #size = params['size']

        ## start clustering
        #nemoa.log('detecting bi-correlation clusters')
        #startTime = time.time()

        #biclusters = []
        #for i in xrange(numCols - 1):
            #for j in xrange(i + 1, numCols):

                #npRowIDs = numpy.arange(numRows)

                ## drop rows until corr(i, j) > sigma or too few rows are left
                #rowIDs = npRowIDs.tolist()
                #corr = numpy.corrcoef(data[:,i], data[:,j])[0, 1]

                #while (size and len(rowIDs) > size) or \
                    #(not size and len(rowIDs) > minsize and corr < threshold):
                    #rowCorr = numpy.zeros(len(rowIDs))

                    #for id in xrange(len(rowIDs)):
                        #mask = rowIDs[:id] + rowIDs[id:][1:]
                        #rowCorr[id] = numpy.corrcoef(data[mask, i], data[mask, j])[0, 1]

                    #rowMaxID = rowCorr.argmax()
                    #corr = rowCorr[rowMaxID]
                    #rowIDs.pop(rowMaxID)

                #if i == 0 and j == 1:
                    #elapsed = time.time() - startTime
                    #estimated = elapsed * numCols ** 2 / 2
                    #nemoa.log('estimated duration: %.1fs' % (estimated))

                #if corr < threshold:
                    #continue

                # expand remaining rows over columns
                #colIDs = [i, j]
                #for id in [id for id in xrange(numCols) if id not in colIDs]:
                    #if numpy.corrcoef(data[rowIDs, i], data[rowIDs, id])[0, 1] < threshold:
                        #continue
                    #if numpy.corrcoef(data[rowIDs, j], data[rowIDs, id])[0, 1] < threshold:
                        #continue
                    #colIDs.append(id)

                # append bicluster if not yet existing
                #bicluster = (list(set(rowIDs)), list(set(colIDs)))
                #if not bicluster in biclusters:
                    #biclusters.append(bicluster)

        ## info
        #if size:
            #nemoa.log('found %i biclusters with: correlation > %.2f, number of samples = %i' \
                #% (len(biclusters), threshold, size))
        #else:
            #nemoa.log('found %i biclusters with: correlation > %.2f, number of samples > %i' \
                #% (len(biclusters), threshold, minsize - 1))

        #return biclusters

    #def getBiclusterDistance(self, biclusters, **params):
        #if 'distance' in params:
            #type = params['distance']
        #else:
            #type = 'correlation'

        #if type == 'hamming':
            #return self.getBiclusterHammingDistance(biclusters)
        #elif type == 'correlation':
            #return self.getBiclusterCorrelationDistance(biclusters)

        #nemoa.log('warning', "   unknown distance type '" + type + "'!")
        #return None

    #def getBiclusterHammingDistance(self, biclusters):
        #data = self.data(output = 'array')
        #numRows, numCols = data.shape

        ## create distance matrix using binary metric
        #distance = numpy.ones(shape = (numRows, len(biclusters)))
        #for cID, (cRowIDs, cColIDs) in enumerate(biclusters):
            #distance[cRowIDs, cID] = 0

        #return distance

    #def getBiclusterCorrelationDistance(self, biclusters):
        ### EXPERIMENTAL!!
        #data = self.data(output = 'array')
        #numRows, numCols = data.shape

        ## calculate differences in correlation
        #corrDiff = numpy.zeros(shape = (numRows, len(biclusters)))
        #for cID, (cRowIDs, cColIDs) in enumerate(biclusters):

            ## calculate mean correlation within bicluster
            #cCorr = self.getMeanCorr(data[cRowIDs, :][:, cColIDs])

            ## calculate mean correlation by appending single rows
            #for rowID in xrange(numRows):
                #corrDiff[rowID, cID] = cCorr - self.getMeanCorr(data[cRowIDs + [rowID], :][:, cColIDs])

        ## calculate distances of samples and clusters
        #distance = corrDiff
        ##dist = numpy.nan_to_num(corrDiff / (numpy.max(numpy.max(corrDiff, axis = 0), 0.000001)))
        ##dist = (dist > 0) * dist
        #return distance

    #def getMeanCorr(self, array, axis = 1):
        #if not axis:
            #array = array.T
        #cCorr = numpy.asarray([])
        #for i in xrange(array.shape[1] - 1):
            #for j in xrange(i + 1, array.shape[1]):
                #cCorr = numpy.append(cCorr, numpy.corrcoef(array[:, i], array[:, j])[0, 1])

        #return numpy.mean(cCorr)

    # TODO: move to nemoa.common
    def _csv_get_data(self, name):
        conf = self._config['table'][name]['source']
        file = conf['file']
        delim = conf['delimiter'] if 'delimiter' in conf \
            else nemoa.common.csv_get_delimiter(file)
        cols = conf['usecols']
        names = tuple(self._get_col_labels())
        formats = tuple(['<f8' for x in names])
        if not 'rows' in conf or conf['rows']:
            cols = (0,) + cols
            names = ('label',) + names
            formats = ('<U12',) + formats
        dtype = {'names': names, 'formats': formats}

        nemoa.log("import data from csv file: " + file)

        try:
            data = numpy.loadtxt(file, skiprows = 1, delimiter = delim,
                usecols = cols, dtype = dtype)
        except:
            return nemoa.log('error', 'could not import data from file!')

        return data

    def save(self, file):
        """Export dataset to numpy zip compressed file."""
        numpy.savez(file, cfg = self._config, data = self._data)

    def export(self, file, **kwargs):
        """Export data to file."""

        file = nemoa.common.get_empty_file(file)
        type = nemoa.common.get_file_ext(file).lower()

        nemoa.log('export data to file')
        nemoa.log('set', indent = '+1')

        nemoa.log('exporting data to file: \'%s\'' % (file))
        if type in ['gz', 'data']: retVal = self.save(file)
        elif type in ['csv', 'tsv', 'tab', 'txt']:
            cols, data = self.data(output = ('cols', 'recarray'))
            retVal = nemoa.common.csv_save_data(file, data,
                cols = [''] + cols, **kwargs)
        else: retVal = nemoa.log('error', """could not export dataset:
            unsupported file type '%s'""" % (type))

        nemoa.log('set', indent = '-1')
        return retVal

    def _get_cache_file(self, network):
        """Return cache file path."""
        return '%sdata-%s-%s.npz' % (
            self._config['cache_path'], network._config['id'], self._config['id'])

    def _search_cache_file(self, network):
        """Return cache file path if existent."""
        file = self._get_cache_file(network)
        return file if os.path.isfile(file) else None

    def _create_cache_file(self, network):
        """Return empty cache file if existent."""
        file = self._get_cache_file(network)
        if not os.path.isfile(file):
            basedir = os.path.dirname(file)
            if not os.path.exists(basedir): os.makedirs(basedir)
            with open(file, 'a'): os.utime(file, None)
        return file

    def load(self, file):
        npzfile = numpy.load(file)
        self._config  = npzfile['cfg'].item()
        self._data = npzfile['data'].item()
        return True

    def _get(self, sec = None):
        dict = {
            'data': copy.deepcopy(self._data),
            'cfg':  copy.deepcopy(self._config)
        }

        if not sec: return dict
        if sec in dict: return dict[sec]
        return None

    def _set(self, **dict):
        if 'data' in dict: self._data = copy.deepcopy(dict['data'])
        if 'cfg' in dict: self._config = copy.deepcopy(dict['cfg'])
        return True

    def about(self, *args):
        """Return generic information about various parts of the dataset.

        Args:
            *args: tuple of strings, containing a breadcrump trail to
                a specific information about the dataset

        Examples:
            about()

        """

        if not args: return {
            'name': self.name(),
            'description': self.__doc__
        }

        if args[0] == 'name': return self.name()
        if args[0] == 'description': return self.__doc__
        return None

    def name(self):
        """Return string containing name of dataset."""
        return self._config['name'] if 'name' in self._config else ''

