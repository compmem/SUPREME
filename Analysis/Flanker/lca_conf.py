import pycuda.driver as cuda
import pycuda.compiler
import pycuda.autoinit
from pycuda.compiler import SourceModule
import numpy as np
import os
from cutools import mt_rand, GPUStruct
from RunDEMC.density import kdensity


# set up the path to this module
modpath = os.path.dirname(os.path.realpath(__file__))
MODEL_ID = {'time': 0, 'conflict': 1}

class SpotLCA(object):
    """
    Leaky-Competitive Accumulator model with shrinking spotlight.
    """
    def __init__(self, nitems=2, nbins=1, nsims=1000, data=None,
                 log_shift=.05, log_max=100., mbins=2000, mod_name=1,
                 nreps=1):
        """
        nitems is number of accumulators
        nsims is number of simulations
        """
        self.data = data
        self.log_shift = log_shift
        self.log_max = log_max
        self.mbins = mbins
        self.nsims = nsims
        self.nitems = nitems
        self.nbins = nbins
        self.model_id = mod_name
        self.model_name = mod_name
        self.nreps = nreps

        # set default params
        self._dp = {'max_time': 2.0,
                    'K': 0.1,
                    'L': 0.5,
                    'U': 0.0,
                    'eta': 1.0,
                    'thresh': 1.0,
                    'dt': .01,
                    'tau': .1,
                    'truncate': True,
                    'r': .1,
                    'p': 1.0,
                    'sd0': 2.0,
                    'sd_min': .01,
                    'alpha':0.0
                    }

        # set the lengths
        lengths = {'nitems': nitems,
                   'nsims': nsims,
                   'nbins': nbins,
                   'model_id': self.model_id,
                   'hack': '"%d, x[%d]=%f, xout[%d]=%f, t=%d\\n"'}

        # read in the cuda code
        code = open(os.path.join(modpath, 'lca_mt_conf.cu.h'), 'r').read()
        self._mod = SourceModule(code % lengths,
                                 no_extern_c=True,
                                 options=['-ccbin', 'clang-3.8','-std=c++11'],
                                 include_dirs=[modpath,
                                               mt_rand.get_include_dir()])

        # get the kernel functions to call
        self._setup_sim = self._mod.get_function('setup_sim')
        self._iaccumulate = self._mod.get_function("iaccumulate")

        # set up the i/o params (order and type matter!)
        self.io = GPUStruct([(np.float32,'*out_time',np.zeros((nsims), dtype=np.float32)),
                             (np.float32,'*x_out',np.zeros((nsims,nitems), dtype=np.float32)),
                             (np.float32,'*confidence',np.zeros((nsims), dtype=np.float32)),
                             (np.int32,'*x_ind',np.zeros((nsims), dtype=np.int32)),
                             (np.float32,'*x_init', np.ones((nitems), dtype=np.float32)*((self._dp['thresh'])*(1/3.))),
                             (np.float32,'*bins',np.zeros((nbins,2), dtype=np.float32)),
                             (np.int32,'*bin_ind',np.zeros((nbins), dtype=np.int32)),
                             (np.float32,'sd0',self._dp['sd0']),
                             (np.float32,'sd_min',self._dp['sd_min']),
                             (np.float32,'r',self._dp['r']),
                             (np.float32,'p',self._dp['p']),
                             (np.int32,'max_iter',
                              np.round(self._dp['max_time']/self._dp['dt'])),
                             (np.float32,'max_time',self._dp['max_time']),
                             (np.float32,'K',self._dp['K']),
                             (np.float32,'L',self._dp['L']),
                             (np.float32,'U',self._dp['U']),
                             (np.float32,'eta',self._dp['eta']),
                             (np.float32,'thresh',self._dp['thresh']),
                             (np.float32,'alpha',self._dp['alpha']),
                             (np.float32,'dt',self._dp['dt']),
                             (np.float32,'tau',self._dp['tau']),
                             (np.float32,'dt_tau',self._dp['dt']/self._dp['tau']),
                             (np.float32,'sqrt_dt_tau',
                              np.sqrt(self._dp['dt']/self._dp['tau'])),
                             (np.int32,'truncate',self._dp['truncate'])])

        # do full copy once
        self.io.copy_to_gpu()

        # set up the kernel grid parameters
        bsize = 256
        gsize = (nsims/bsize)
        if gsize*bsize < nsims:
            gsize += 1
        self._gsize = gsize
        self._bsize = bsize

        # set up the functions
        self._setup_sim.prepare('')
        self._iaccumulate.prepare('P')

        # setup the simulations
        mt_rand.seed(cuda,self._mod)
        timer = self._setup_sim.prepared_timed_call((self._gsize, 1),
                                                    (self._bsize, 1, 1))
        runtime = timer()

    def simulate(self, **params):
        # start with defaults
        for p in self._dp:
            if hasattr(self.io, p) and not p in params:
                setattr(self.io, p, self._dp[p])

        # set the params
        for p in params:
            if hasattr(self.io, p):
                setattr(self.io, p, params[p])

        # set some calculated params
        self.io.max_iter = np.round(self.io.max_time/self.io.dt)
        self.io.dt_tau = self.io.dt/self.io.tau
        self.io.sqrt_dt_tau = np.sqrt(self.io.dt_tau)

        # copy what might have changed
        self.io.copy_to_gpu(skip=['out_time', 'x_out',
                                  'x_ind', 'confidence'])

        # prepare for appending data
        out_time = None

        # run the simulation for the desired reps
        for r in range(self.nreps):
            # run the sim
            timer = self._iaccumulate.prepared_timed_call((self._gsize, 1),
                                                          (self._bsize, 1, 1),
                                                          self.io.get_ptr())
            # get the params back
            self.io.copy_from_gpu()

            # set or append
            if out_time is None:
                # set the data
                # save the time
                self.runtime = timer()

                # append the results
                out_time = self.io.out_time*self.io.dt
                x_ind = self.io.x_ind
                x_out = self.io.x_out
                conf = self.io.confidence
            else:
                # append the data
                self.runtime += timer()
                out_time = np.concatenate([out_time, self.io.out_time*self.io.dt])
                x_ind = np.concatenate([x_ind, self.io.x_ind])
                x_out = np.concatenate([x_out, self.io.x_out])
                conf = np.concatenate([conf, self.io.confidence])

        # process the non-responses
        resp_ind = x_ind >= 0
        out_time = out_time + params['t0']
        out_time[~resp_ind] = -1

        # process the results and return them
        return (out_time, x_ind, x_out, conf)

    def log_like(self, params, data=None):
        # default starting val
        ll = 0.0

        # grab from constructor if not passed in
        if data is None:
            data = self.data

        for k in data:
            data[k] = np.atleast_1d(data[k])

        # run sim
        out_time, x_ind, x_out, conf = self.simulate(**params)

        # set extrema based on log range
        extrema = (np.log(self.log_shift),
                   np.log(self.log_max))

        # loop over data responses
        for resp in np.unique(data['resp']):
            # get mod data and proportion
            mod_ind = x_ind==resp
            prop = mod_ind.sum()/float(self.nsims)
            dat_ind = data['resp']==resp

            # see if calc rt density
            if data.has_key('rt'):
                mod = out_time[mod_ind]
                dat = data['rt'][dat_ind]
                try:
                    pdf, xd = kdensity(np.log(mod+self.log_shift),
                                       xx=dat,
                                       nbins=self.mbins,
                                       extrema=extrema,
                                       kernel='epanechnikov')
                except:
                    return -np.inf
                if np.any(pdf == 0.):
                    return -np.inf
                # add to the log like
                ll += np.log(pdf*prop).sum()

            # see if calc conf density
            if 'conf' in data:
                mod = conf[mod_ind]
                dat = data['conf'][dat_ind]
                try:
                    pdf, xd = kdensity(mod,
                                       xx=dat,
                                       nbins=self.mbins,
                                       extrema=(1./self.nitems, 1.0),
                                       kernel='epanechnikov')
                except:
                    return -np.inf

                if np.any(pdf == 0.):
                    return -np.inf
                # add to the log like
                ll += np.log(pdf*prop).sum()

        if ll == 0.0:
            ll = -np.inf

        return ll

    def resp_prop(self, params):
        # run sim
        out_time, x_ind, x_out, conf = self.simulate(**params)

        # calc proportions of each response based on max conf value
        # returned on each trial (currently will not handle identical max)

        # loop over data responses (don't allow where all zeros)
        max_inds = x_out.argmax(1)[x_out.sum(1) > 0]
        props = np.array([(max_inds == resp).sum()/float(self.nsims)
                          for resp in range(len(self.nitems))])
        return props
