# -*- coding: utf-8 -*-
"""Artificial Neuronal Network (ANN) Evaluation.

This module includes various implementations for quantifying structural
and statistical values of whole artificial neural networks, units, links
and relations. These methods include:

    (a) data based methods like data manipulation tests
    (b) graphical methods on weighted graphs
    (c) function based methods like partial derivations

"""

__author__  = 'Patrick Michl'
__email__   = 'patrick.michl@gmail.com'
__license__ = 'GPLv3'

import nemoa
import numpy

from nemoa.model.evaluation.base import Evaluation

class ANN(Evaluation):

    @nemoa.common.decorators.attributes(
        name     = 'error',
        category = 'model',
        args     = 'all',
        formater = lambda val: '%.3f' % (val),
        optimum  = 'min'
    )
    def modelerror(self, *args, **kwargs):
        """Mean data reconstruction error of output units."""
        return numpy.mean(self.uniterror(*args, **kwargs))

    @nemoa.common.decorators.attributes(
        name     = 'accuracy',
        category = 'model',
        args     = 'all',
        formater = lambda val: '%.1f%%' % (val * 100.),
        optimum  = 'max'
    )
    def modelaccuracy(self, *args, **kwargs):
        """Mean data reconstruction accuracy of output units."""
        return numpy.mean(self.unitaccuracy(*args, **kwargs))

    @nemoa.common.decorators.attributes(
        name     = 'precision',
        category = 'model',
        args     = 'all',
        formater = lambda val: '%.1f%%' % (val * 100.),
        optimum  = 'max'
    )
    def modelprecision(self, *args, **kwargs):
        """Mean data reconstruction precision of output units."""
        return numpy.mean(self.unitprecision(*args, **kwargs))

    @nemoa.common.decorators.attributes(
        name     = 'mean',
        category = 'units',
        args     = 'input',
        retfmt   = 'scalar',
        formater = lambda val: '%.3f' % (val),
        plot     = 'diagram'
    )
    def unitmean(self, data, mapping = None, block = None):
        """Mean values of reconstructed target units.

        Args:
            data: numpy array containing source data corresponding to
                the source unit layer (first argument of the mapping)
            mapping: n-tuple of strings containing the mapping
                from source unit layer (first argument of tuple)
                to target unit layer (last argument of tuple)
            block: list of strings containing labels of source units
                that are 'blocked' by setting their values to the means
                of their values.

        Returns:
            Numpy array of shape (targets).

        """

        if mapping == None: mapping = self.model.system._get_mapping()
        if block == None:
            model_out = self.unitexpect(data[0], mapping)
        else:
            data_in_copy = numpy.copy(data)
            for i in block:
                data_in_copy[:,i] = numpy.mean(data_in_copy[:,i])
            model_out = self.unitexpect(
                data_in_copy, mapping)

        return model_out.mean(axis = 0)

    @nemoa.common.decorators.attributes(
        name     = 'variance',
        category = 'units',
        args     = 'input',
        retfmt   = 'scalar',
        formater = lambda val: '%.3f' % (val),
        plot     = 'diagram'
    )
    def unitvariance(self, data, mapping = None, block = None):
        """Return variance of reconstructed unit values.

        Args:
            data: numpy array containing source data corresponding to
                the first layer in the mapping
            mapping: n-tuple of strings containing the mapping
                from source unit layer (first argument of tuple)
                to target unit layer (last argument of tuple)
            block: list of strings containing labels of source units
                that are blocked by setting the values to their means
        """

        if mapping == None: mapping = self.model.system._get_mapping()
        if block == None:
            model_out = self.unitexpect(data, mapping)
        else:
            data_in_copy = numpy.copy(data)
            for i in block:
                data_in_copy[:,i] = numpy.mean(data_in_copy[:,i])
            model_out = self.unitexpect(
                data_in_copy, mapping)

        return model_out.var(axis = 0)

    @nemoa.common.decorators.attributes(
        name     = 'expect',
        category = 'units',
        args     = 'input',
        retfmt   = 'vector',
        formater = lambda val: '%.3f' % (val),
        plot     = 'histogram'
    )
    def unitexpect(self, *args, **kwargs):
        """Expectation values of target units.

        Args:
            data: numpy array containing source data corresponding to
                the source unit layer (first argument of the mapping)
            mapping: n-tuple of strings containing the mapping
                from source unit layer (first argument of tuple)
                to target unit layer (last argument of tuple)
            block: list of strings containing labels of source units
                that are 'blocked' by setting their values to the means
                of their values.

        Returns:
            Numpy array of shape (data, targets).

        """

        return self.model.system._get_unitexpect(*args, **kwargs)

    @nemoa.common.decorators.attributes(
        name     = 'values',
        category = 'units',
        args     = 'input',
        retfmt   = 'vector',
        formater = lambda val: '%.3f' % (val),
        plot     = 'histogram'
    )
    def unitvalues(self, *args, **kwargs):
        """Unit maximum likelihood values of target units.

        Args:
            data: numpy array containing source data corresponding to
                the source unit layer (first argument of the mapping)
            mapping: n-tuple of strings containing the mapping
                from source unit layer (first argument of tuple)
                to target unit layer (last argument of tuple)
            block: list of strings containing labels of source units
                that are 'blocked' by setting their values to the means
                of their values.
            expect_last: return expectation values of the units
                for the last step instead of maximum likelihood values.

        Returns:
            Numpy array of shape (data, targets).

        """

        return self.model.system._get_unitvalues(*args, **kwargs)

    @nemoa.common.decorators.attributes(
        name     = 'samples',
        category = 'units',
        args     = 'input',
        retfmt   = 'vector',
        formater = lambda val: '%.3f' % (val),
        plot     = 'histogram'
    )
    def unitsamples(self, *args, **kwargs):
        """Sampled unit values of target units.

        Args:
            data: numpy array containing source data corresponding to
                the source unit layer (first argument of the mapping)
            mapping: n-tuple of strings containing the mapping
                from source unit layer (first argument of tuple)
                to target unit layer (last argument of tuple)
            block: list of strings containing labels of source units
                that are 'blocked' by setting their values to the means
                of their values.
            expect_last: return expectation values of the units
                for the last step instead of sampled values

        Returns:
            Numpy array of shape (data, targets).

        """

        return self.model.system._get_unitsamples(*args, **kwargs)

    @nemoa.common.decorators.attributes(
        name     = 'residuals',
        category = 'units',
        args     = 'all',
        retfmt   = 'vector',
        formater = lambda val: '%.3f' % (val),
        plot     = 'histogram'
    )
    def unitresiduals(self, data, mapping = None, block = None):
        """Reconstruction residuals of target units.

        Args:
            data: 2-tuple of numpy arrays containing source and target
                data corresponding to the first and the last argument
                of the mapping
            mapping: n-tuple of strings containing the mapping
                from source unit layer (first argument of tuple)
                to target unit layer (last argument of tuple)
            block: list of strings containing labels of source units
                that are 'blocked' by setting their values to the means
                of their values.

        Returns:
            Numpy array of shape (data, targets).

        """

        d_src, d_tgt = data

        # set mapping: inLayer to outLayer (if not set)
        if mapping == None: mapping = self.model.system._get_mapping()

        # set unit values to mean (optional)
        if isinstance(block, list):
            d_src = numpy.copy(d_src)
            for i in block: d_src[:, i] = numpy.mean(d_src[:, i])

        # calculate estimated output values
        m_out = self.unitexpect(d_src, mapping)

        # calculate residuals
        return d_tgt - m_out

    @nemoa.common.decorators.attributes(
        name     = 'error',
        category = 'units',
        args     = 'all',
        retfmt   = 'scalar',
        formater = lambda val: '%.3f' % (val),
        plot     = 'diagram'
    )
    def uniterror(self, data, norm = 'MSE', **kwargs):
        """Unit reconstruction error.

        The unit reconstruction error is defined by:
            error := norm(residuals)

        Args:
            data: 2-tuple of numpy arrays containing source and target
                data corresponding to the first and the last layer in
                the mapping
            mapping: n-tuple of strings containing the mapping
                from source unit layer (first argument of tuple)
                to target unit layer (last argument of tuple)
            block: list of strings containing labels of source units
                that are blocked by setting the values to their means
            norm: used norm to calculate data reconstuction error from
                residuals. see nemoa.common.ndarray.meannorm for a list
                of provided norms

        """

        res = self.unitresiduals(data, **kwargs)
        error = nemoa.common.ndarray.meannorm(res, norm = norm)

        return error

    @nemoa.common.decorators.attributes(
        name     = 'accuracy',
        category = 'units',
        args     = 'all',
        retfmt   = 'scalar',
        formater = lambda val: '%.3f' % (val),
        plot     = 'diagram'
    )
    def unitaccuracy(self, data, norm = 'MSE', **kwargs):
        """Unit reconstruction accuracy.

        The unit reconstruction accuracy is defined by:
            accuracy := 1 - norm(residuals) / norm(data).

        Args:
            data: 2-tuple of numpy arrays containing source and target
                data corresponding to the first and the last layer
                in the mapping
            mapping: n-tuple of strings containing the mapping
                from source unit layer (first argument of tuple)
                to target unit layer (last argument of tuple)
            block: list of strings containing labels of source units
                that are blocked by setting the values to their means
            norm: used norm to calculate accuracy
                see nemoa.common.ndarray.meannorm for a list of provided
                norms

        """

        res = self.unitresiduals(data, **kwargs)
        normres = nemoa.common.ndarray.meannorm(res, norm = norm)
        normdat = nemoa.common.ndarray.meannorm(data[1], norm = norm)

        return 1. - normres / normdat

    @nemoa.common.decorators.attributes(
        name     = 'precision',
        category = 'units',
        args     = 'all',
        retfmt   = 'scalar',
        formater = lambda val: '%.3f' % (val),
        plot     = 'diagram'
    )
    def unitprecision(self, data, norm = 'SD', **kwargs):
        """Unit reconstruction precision.

        The unit reconstruction precision is defined by:
            precision := 1 - dev(residuals) / dev(data).

        Args:
            data: 2-tuple of numpy arrays containing source and target
                data corresponding to the first and the last layer
                in the mapping
            mapping: n-tuple of strings containing the mapping
                from source unit layer (first argument of tuple)
                to target unit layer (last argument of tuple)
            block: list of strings containing labels of source units
                that are blocked by setting the values to their means
            norm: used norm to calculate deviation for precision
                see nemoa.common.ndarray.devnorm for a list of provided
                norms

        """

        res = self.unitresiduals(data, **kwargs)
        devres = nemoa.common.ndarray.devnorm(res, norm = norm)
        devdat = nemoa.common.ndarray.devnorm(data[1], norm = norm)

        return 1. - devres / devdat

    @nemoa.common.decorators.attributes(
        name     = 'correlation',
        category = 'relation',
        directed = False,
        signed   = True,
        normal   = True,
        args     = 'all',
        retfmt   = 'scalar',
        plot     = 'heatmap',
        formater = lambda val: '%.3f' % (val)
    )
    def correlation(self, data, mapping = None, **kwargs):
        """Data correlation between source and target units.

        Undirected data based relation describing the 'linearity'
        between variables (units).

        Args:
            data: 2-tuple with numpy arrays: input data and output data
            mapping: tuple of strings containing the mapping
                from input layer (first argument of tuple)
                to output layer (last argument of tuple)

        Returns:
            Numpy array of shape (source, target) containing pairwise
            correlation between source and target units.

        """

        # Todo: allow correlation between hidden units

        # calculate symmetric correlation matrix
        corr = numpy.corrcoef(numpy.hstack(data).T)

        # create asymmetric output matrix
        mapping = self.model.system._get_mapping()
        srcunits = self.model.system._get_units(layer = mapping[0])
        tgtunits = self.model.system._get_units(layer = mapping[-1])
        units = srcunits + tgtunits
        relation = numpy.zeros(shape = (len(srcunits), len(tgtunits)))
        for i, u1 in enumerate(srcunits):
            k = units.index(u1)
            for j, u2 in enumerate(tgtunits):
                l = units.index(u2)
                relation[i, j] = corr[k, l]

        return relation

    @nemoa.common.decorators.attributes(
        name     = 'connectionweight',
        category = 'relation',
        directed = True,
        signed   = True,
        normal   = False,
        args     = 'all',
        retfmt   = 'scalar',
        plot     = 'heatmap',
        formater = lambda val: '%.3f' % (val)
    )
    def connectionweight(self, data, mapping = None, **kwargs):
        """Weight sum product from source to target units.

        Directed graph based relation describing the matrix product from
        source to target units (variables) given by mapping.

        Args:
            data: 2-tuple with numpy arrays: input data and output data
            mapping: tuple of strings containing the mapping
                from input layer (first argument of tuple)
                to output layer (last argument of tuple)

        Returns:
            Numpy array of shape (source, target) containing pairwise
            weight sum products from source to target units.

        """

        if not mapping: mapping = self.model.system._get_mapping()

        # calculate product of weight matrices
        for i in range(1, len(mapping))[::-1]:
            weights = self.model.system._units[mapping[i - 1]].links(
                {'layer': mapping[i]})['W']
            if i == len(mapping) - 1: wsp = weights.copy()
            else: wsp = numpy.dot(wsp.copy(), weights)

        return wsp.T

    @nemoa.common.decorators.attributes(
        name     = 'knockout',
        category = 'relation',
        directed = True,
        signed   = True,
        normal   = False,
        args     = 'all',
        retfmt   = 'scalar',
        plot     = 'heatmap',
        formater = lambda val: '%.3f' % (val)
    )
    def knockout(self, data, mapping = None, **kwargs):
        """Knockout effect from source to target units.

        Directed data manipulation based relation describing the
        increase of the data reconstruction error of a given output
        unit, when setting the values of a given input unit to its mean
        value.

        Knockout single source units and measure effects on target units
        respective to given data

        Args:
            data: 2-tuple with numpy arrays: input data and output data
            mapping: tuple of strings containing the mapping
                from input layer (first argument of tuple)
                to output layer (last argument of tuple)

        Returns:
            Numpy array of shape (source, target) containing pairwise
            knockout effects from source to target units.

        """

        if not mapping: mapping = self.model.system._get_mapping()
        in_labels = self.model.system._get_units(layer = mapping[0])
        out_labels = self.model.system._get_units(layer = mapping[-1])

        # prepare knockout matrix
        R = numpy.zeros((len(in_labels), len(out_labels)))

        # calculate unit values without knockout
        if not 'measure' in kwargs: measure = 'error'
        else: measure = kwargs['measure']
        default = self.evaluate(algorithm = measure,
            category = 'units', mapping = mapping)

        if not default: return None

        # calculate unit values with knockout
        for in_id, in_unit in enumerate(in_labels):

            # modify unit and calculate unit values
            knockout = self.evaluate(algorithm = measure,
                category = 'units', mapping = mapping, block = [in_id])

            # store difference in knockout matrix
            for out_id, out_unit in enumerate(out_labels):
                R[in_id, out_id] = \
                    knockout[out_unit] - default[out_unit]

        return R

    @nemoa.common.decorators.attributes(
        name     = 'coinduction',
        category = 'relation',
        directed = True,
        signed   = False,
        normal   = False,
        args     = 'all',
        retfmt   = 'scalar',
        plot     = 'heatmap',
        formater = lambda val: '%.3f' % (val)
    )
    def coinduction(self, data, *args, **kwargs):
        """Coinduced deviation from source to target units."""

        # Todo: Open Problem:
        #       Normalization of CoInduction
        # Ideas:
        #       - Combine CoInduction with common distribution
        #         of induced values
        #       - Take a closer look to extreme Values

        # Todo: Proove:
        # CoInduction <=> Common distribution in 'deep' latent variables

        # algorithmic default parameters
        gauge = 0.1 # setting gauge lower than induction default
                    # to increase sensitivity

        mapping = self.model.system._get_mapping()
        srcunits = self.model.system._get_units(layer = mapping[0])
        tgtunits = self.model.system._get_units(layer = mapping[-1])

        # prepare cooperation matrix
        coop = numpy.zeros((len(srcunits), len(srcunits)))

        # create keawords for induction measurement

        if not 'gauge' in kwargs: kwargs['gauge'] = gauge

        # calculate induction without manipulation
        ind = self._get_induction(data, *args, **kwargs)
        norm = numpy.sqrt((ind ** 2).sum(axis = 1))

        # calculate induction with manipulation
        for sid, sunit in enumerate(srcunits):

            # manipulate source unit values and calculate induction
            datamp = [numpy.copy(data[0]), data[1]]
            datamp[0][:, sid] = 10.0
            indmp = self._get_induction(datamp, *args, **kwargs)

            print('manipulation of', sunit)
            vals = [-2., -1., -0.5, 0., 0.5, 1., 2.]
            maniparr = numpy.zeros(shape = (len(vals), data[0].shape[1]))
            for vid, val in enumerate(vals):
                datamod = [numpy.copy(data[0]), data[1]]
                datamod[0][:, sid] = val #+ datamod[0][:, sid].mean()
                indmod = self._get_induction(datamod, *args, **kwargs)
                maniparr[vid, :] = numpy.sqrt(((indmod - ind) ** 2).sum(axis = 1))
            manipvar = maniparr.var(axis = 0)
            #manipvar /= numpy.amax(manipvar)
            manipnorm = numpy.amax(manipvar)
            # 2do
            print(manipvar * 1000.)
            print(manipvar / manipnorm)

            coop[:,sid] = \
                numpy.sqrt(((indmp - ind) ** 2).sum(axis = 1))

        return coop

    @nemoa.common.decorators.attributes(
        name     = 'induction',
        category = 'relation',
        directed = True,
        signed   = False,
        normal   = False,
        args     = 'all',
        retfmt   = 'scalar',
        plot     = 'heatmap',
        formater = lambda val: '%.3f' % (val)
    )
    def induction(self, data, mapping = None, points = 10,
        amplify = 1., gauge = 0.25, contrast = 20.0, **kwargs):
        """Induced deviation from source to target units.

        Directed data manipulation based relation describing the induced
        deviation of reconstructed values of a given output unit, when
        manipulating the values of a given input unit.

        For each sample and for each source the induced deviation on
        target units is calculated by respectively fixing one sample,
        modifying the value for one source unit (n uniformly taken
        points from it's own distribution) and measuring the deviation
        of the expected valueas of each target unit. Then calculate the
        mean of deviations over a given percentage of the strongest
        induced deviations.

        Args:
            data: 2-tuple with numpy arrays: input data and output data
            mapping: tuple of strings containing the mapping
                from source layer (first argument of tuple)
                to target layer (last argument of tuple)
            points: number of points to extrapolate induction
            amplify: amplification of the modified source values
            gauge: cutoff for strongest induced deviations
            contrast:

        Returns:
            Numpy array of shape (source, target) containing pairwise
            induced deviation from source to target units.

        """

        if not mapping: mapping = self.model.system._get_mapping()
        inputs = self.model.system._get_units(layer = mapping[0])
        outputs = self.model.system._get_units(layer = mapping[-1])
        sdata = data[0]
        tdata = data[1]
        R = numpy.zeros((len(inputs), len(outputs)))

        # get indices of representatives
        r_ids = [int((i + 0.5) * int(float(sdata.shape[0])
            / points)) for i in xrange(points)]

        for inid, inunit in enumerate(inputs):
            try:
                i_curve = numpy.take(numpy.sort(sdata[:, inid]), r_ids)
            except: # 2Do
                print('ok1', sdata)
                print('ok2', sdata[:, inid])
                print('ok3', numpy.sort(sdata[:, inid]))
                print(r_ids)
                print(numpy.take(numpy.sort(sdata[:, inid]), r_ids))

            i_curve = amplify * i_curve

            # create output matrix for each output
            C = {outunit: numpy.zeros((sdata.shape[0], points)) \
                for outunit in outputs}
            for p_id in xrange(points):
                i_data  = sdata.copy()
                i_data[:, inid] = i_curve[p_id]
                o_expect = self.unitexpect(i_data, mapping = mapping)
                for tid, outunit in enumerate(outputs):
                    C[outunit][:, p_id] = o_expect[:, tid]

            # calculate mean of standard deviations of outputs
            for outid, outunit in enumerate(outputs):

                # calculate norm by mean over part of data
                bound = int((1. - gauge) * sdata.shape[0])
                subset = numpy.sort(C[outunit].std(axis = 1))[bound:]
                norm = subset.mean() / tdata[:, outid].std()

                # calculate influence
                R[inid, outid] = norm

        # amplify contrast of induction
        A = R.copy()
        for inid, inunit in enumerate(inputs):
            for outid, outunit in enumerate(outputs):
                if ':' in outunit: inlabel = outunit.split(':')[1]
                else: inlabel = outunit
                if ':' in inunit: outlabel = inunit.split(':')[1]
                else: outlabel = inunit
                if inlabel == outlabel: A[inid, outid] = 0.0
        bound = numpy.amax(A)

        R = nemoa.common.math.intensify(R, factor = contrast,
            bound = bound)

        return R
