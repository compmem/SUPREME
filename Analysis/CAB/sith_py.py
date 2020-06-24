# version of sith that is wrapped in pytorch modules
# and Functions

from math import factorial
import itertools

import numpy as np
# import torch
# import torch.nn

#####################################
# parameter creation methods for SITH
#####################################


def _calc_tau_star(tau_0, k, c, ntau):
    ntau = ntau + 2 * k
    tau_star = tau_0 * (1 + c)**np.arange(-k, ntau + k)
    s = k / tau_star
    return tau_star, s


def _calc_D(s):
    # calc all the differences
    s0__1 = s[1:-1] - s[:-2]
    s1_0 = s[2:] - s[1:-1]
    s1__1 = s[2:] - s[:-2]

    # calc the -1, 0, and 1 diagonals
    A = -((s1_0 / s1__1) / s0__1)
    B = -((s0__1 / s1__1) / s1_0) + (s1_0 / s1__1) / s0__1
    C = (s0__1 / s1__1) / s1_0

    # create the matrix
    D = np.zeros((len(s), len(s)))
    D.flat[len(s):-2:len(s) + 1] = A
    D.flat[len(s) + 1:-1:len(s) + 1] = B
    D.flat[len(s) + 2::len(s) + 1] = C
    D = D.T
    return D


def _calc_invL(s, k):
    # easier to do with matrices than ndarray to keep dimensions straight
    D = np.matrix(_calc_D(s))
    invL = (((-1.)**k) / factorial(k) * (D**k) * np.matrix(
        np.diag(s**(k + 1))))[:, k:-k]

    # return as ndarray
    return invL.A.T


class SITH():
    """Scale Invariant Temporal History (SITH)
    Recommended default values:
    alpha = 1.0
    dur = 1/30.
    tau_0 = 1/30.
    ntau = 30
    k = 4
    c = 0.1
    T_toskip = 8"""

    def __init__(self,
                 in_features,
                 out_features,
                 alpha,
                 dur,
                 tau_0,
                 ntau,
                 k,
                 c,
                 T_toskip):

        super(SITH, self).__init__()

        self.in_features = in_features
        self.out_features = out_features
        # only support batch dimension first, because I don't understand why
        # you wouldn't only do that
        self.batch_first = True
        self._default_dtype = np.float32

        self.alpha = alpha
        self._tau_0 = tau_0
        self._k = k
        self._c = c
        self._ntau = ntau
        self._T_full_ind = slice(None, None, T_toskip)
        self._dur = dur

        # verify number of output features given equals number
        # calculated from `ntau`, `k`, and `T_toskip`
        calc_out_size = (self.in_features * np.ceil(
            (self._ntau + 2 * self._k) / self._T_full_ind.step))
        # if (self.out_features != calc_out_size):
        #     raise ValueError("ERROR: Output size mismatch in SITH module, "
        #                      "expected {:n}, but got {}".format(
        #                          calc_out_size, self.out_features))

        # calc tau_star and s
        tau_star, s = _calc_tau_star(tau_0=tau_0, k=k, c=c, ntau=ntau)
        self._tau_star = tau_star
        self._s = s
        self._s.dtype = np.float64
        # get the inverse Laplacian
        self._invL = _calc_invL(self._s, self._k)
        # allocate t
        self._t = np.matrix(np.zeros((self._invL.shape[1], self.in_features)))
        self._T = ((self._invL * self._t)[self._T_full_ind, :]).flatten()
        self._T = np.array(self._T).flatten()

        # keep blank `t` so doesn't have to be recreated
        self.__blank_t = self._t

        self.invL = self._invL
        self.s = self._s
        self.alpha = self.alpha
        self.dur = self._dur

        # store and register stateful arrays
        self.t = self._t
        self.T = self._T

        # pre-allocate and cache blank `t` so doesn't need to be re-created in
        # `update()`
        self._blank_t = self.__blank_t

    def set_alpha(self, new_alpha):
        '''Convenience setter function, to set alpha with a float
        Not really necessary for numpy operators, so long as alpha is scalar'''
        self.alpha = new_alpha

    def reset(self):
        return self.reset_parameters()

    def reset_parameters(self):
        # reset all stateful buffers to zeros
        self.t.fill(0)
        self.T.fill(0)

    def update(self, inputs, g = 0, alpha=None, t_0=None, input_lengths=None, durs=None):
        '''Primary function to use with SITH; updates SITH with an item
        or items. Can specify initial t_0, sizes of inputs, and durations
        If only a single vector of size `in_features` is given as `inputs`,
            then only output `T` is returned, and `t` and `T` are stored.'''

        if alpha == None:
            alpha = self.alpha
        else:
            alpha = alpha

        input_dims = inputs.ndim
        # if only updating with a single vector
        if inputs.ndim == 1:
            store_output = True
            inputs = np.expand_dims(np.expand_dims(inputs, 0), 0)
        # if no sequence dimension, store resulting `t` and `T` values,
        # make batch dimension into sequence dimension
        elif inputs.ndim == 2:
            store_output = True
            inputs = np.expand_dims(inputs, 0)
        else:
            store_output = False
        # just always pull self._dur for the input duration
        if durs is None:
            durs = itertools.repeat(itertools.repeat(self._dur))
        # if durs is just a single float, use this duration for all updates
        elif isinstance(durs, float):
            durs = itertools.repeat(itertools.repeat(durs))
        # determine which previous `t` to use
        # if no sequence dim in inputs, use current stored `t`
        if store_output:
            t_context = np.expand_dims(self.t, 0)
        # use blank contextual `t`
        elif t_0 is None:
            t_context = np.repeat(
                np.expand_dims(self._blank_t, 0), len(inputs), dim=0)
        else:
            t_context = t_0

        t = []
        T = []
        # loop through inputs, calculate and store t's and T's
        for seq, t_i, seq_durs in zip(inputs, t_context, durs):
            for input_j, dur_j in zip(seq, seq_durs):
                # flatten inputs, and provide check on input size
                input_j = input_j.reshape(self.in_features)
                # calculate new `t` value(s)
                t_j = self._calc_t(input_j, t_i, dur_j, alpha, self.s)
                # t_j = self._calc_t(input_j, t_i, dur_j, self.alpha, self.s)
                # calculate `T`
                T_j = self._calc_T(t_j, self.invL, g, self._T_full_ind)
                t_i = t_j
            # store one `t` and `T` for every sequence
            t.append(t_j)
            T.append(T_j)

        t = np.array(t)
        T = np.array(T)
        # update stateful `t` and `T` values
        if store_output:
            self.t = t[-1]
            self.T = T[-1]

        # if only one vector was given as input, only give the final T value
        if input_dims == 1:
            T = T[-1]
            return T
        # otherwise if batches/sequences were used, return full T and t
        else:
            return T, t

    def _calc_t(self, item, t, dur, alpha, s):
        """
        Takes in a `t` state and updates with item
        Returns new `t` state
        """

        # diagonalize for element-wise multiplication of vector*matrix
        e_alph_dur = np.diag(np.exp(s * alpha * (-1 * dur)))
        # calculate input over s*alpha
        f_over_as = np.outer((alpha * s)**-1, item)

        ## calculate new `t`
        t = np.matmul(e_alph_dur, (t - f_over_as)) + f_over_as

        return t

    def _calc_T(self, t, invL, g, T_ind=slice(None, None, 1)):

        # update T from t and index into it
        self._g = g
        # T = np.matmul(invL, t))[T_ind, :]
        T = ((self._tau_star**self._g)[self._k:-self._k].reshape(-1, 1)*np.matmul(invL, t))[T_ind, :]
        T = T.flatten()

        return T

    @property
    def k(self):
        return self._k

    @property
    def tau_star(self):
        """Return full set of `tau_star`s"""
        return self._tau_star

    @property
    def out_tau_star(self):
        """Return `tau_star`s that correspond to T output"""
        return self.tau_star[self.k:-self.k][self._T_full_ind]

    @property
    def out_times(self):
        """Return `tau_star`s in relation to number of `dur`s"""
        return self.out_tau_star / self._dur


if __name__ == "__main__":

    pass

    ## NOTE: Unused for numpy version of SITH
    # device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    # # SITH parameters
    # fps = 30
    # dur = fps**-1
    # ntau = 25
    # T_toskip = 8
    # k = 4
    # alpha = 1.0
    # input_size = 2
    # num_slices = int(np.ceil((ntau + 2 * k) / T_toskip))
    # output_size = input_size * num_slices
    # sith = SITH(
    #     input_size,
    #     output_size,
    #     alpha,
    #     dur,
    #     tau_0=dur,
    #     k=k,
    #     ntau=ntau,
    #     T_toskip=T_toskip)
    # sith.to(device)

    # num_points = 100
    # total_time = dur * num_points
    # times = np.linspace(0, total_time, num_points)
    # pulse = [1.0] * (num_points // 10)
    # pulse += ([0.0] * (num_points - num_points // 10))
    # pulse = torch.tensor(pulse).to(device).unsqueeze(-1)
    # # or, random pulses
    # pulse = torch.rand(num_points, input_size).to(device)
    # T = torch.Tensor().to(device)
    # sith.reset()
    # for p in pulse:
    #     p = p.unsqueeze(0)
    #     T_i, t_i = sith(p)
    #     T = torch.cat((T, T_i))
    #     print(sith.t.shape, sith.T.shape)
    # del sith
    # sith = SITH(
    #     input_size,
    #     output_size,
    #     alpha,
    #     dur,
    #     tau_0=dur,
    #     k=k,
    #     ntau=ntau,
    #     T_toskip=T_toskip)
    # sith.to(device)
    # print("#######")
    # print(sith.t.shape, sith.T.shape)
    # sith(pulse)
    # print(sith.t.shape, sith.T.shape)
