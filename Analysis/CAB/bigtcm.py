# import libraries / functions
import numpy as np
from wfpt2019 import wfpt_like
from wfpt2019 import wfpt_gen
from sith_py import SITH as TILT

class bigTCM(object):
    """BigTCM
    """
    # dictionary of default parameter values
    default_params = {
        # memory
        'lambda': 1.0, # scales familiarity strength (free)
        'alpha': 1.0, # item-context learning rate (free)
        'delta': 1.0, # scales baseline context drift (free)
        'sigma': 0.0, # scales context noise (free)
        'omega': 0.5, # proportion of context scan and associative prediction strength, used to scale context drift and item input (free)
        'beta': 0.5, # proportion of current and retrieved contexts for making predictions (fixed)
        # decision
        'nu': 1.0, # strength for "new" response (free)
        'a': 2.0, # decision threshold (free)
        'w': 0.5, # decision bias (over 0.5 --> biased toward "old"; under 0.5 --> biased toward "new")
        't0': 0.5 # non-decision (perceptual / motor) time
        }

    def __init__(self, d, params=None): # d = data to model, params = parameter values

        # process the params
        # start with defaults
        p = dict(**self.default_params)
        if params is not None:
            # get provided param vals
            p.update(params)
        self.params = p
        self.d = d

        # make list of every stimulus presented
        self.feature_list = []
        # loop through each trial
        for i in range(self.d.shape[0]):
            # get trial info
            trial = self.d.iloc[i]
            # name each item
            img_left = 'item_%s' %trial['img_L']
            img_right = 'item_%s' %trial['img_R']
            # add each item name to stimulus list (but only once)
            if img_left not in self.feature_list:
                self.feature_list.append(img_left)
            if img_right not in self.feature_list:
                self.feature_list.append(img_right)

        # we "fill" context with some items prior to introducing experimental items,
        # so that even early-presented items have something in context to bind to
        self.n_filleritems = 12
        # add filler items to item list
        for i in range(self.n_filleritems):
            self.feature_list.append('filler_%s' %i)

        # initatialize empty feature vector
        self.empty_features = np.zeros(len(self.feature_list))

        # make dictionary of all item one-hot vector representations
        self.features = {}
        feature_counter = 0
        for i in range(self.d.shape[0]):
            trial = self.d.iloc[i]
            img_left = 'item_%s' %trial['img_L']
            img_right = 'item_%s' %trial['img_R']

            if img_left not in self.features:
                self.features[img_left] = self.empty_features.copy()
                self.features[img_left][feature_counter] = 1
                feature_counter += 1
            if img_right not in self.features:
                self.features[img_right] = self.empty_features.copy()
                self.features[img_right][feature_counter] = 1
                feature_counter += 1

        # start from the end, make filler item one-hot vectors
        feature_counter = len(self.feature_list)
        for i in range(self.n_filleritems):
            feature_counter -= 1
            self.features['filler_%s' %i] = self.empty_features.copy()
            self.features['filler_%s' %i][feature_counter] = 1

        # set up the model
        self.reset()


    def reset(self):
        # allocate for all matrices and vectors
        vlen = len(self.features.keys())

        # initialize TILT with some parameter settings
        self.bt = TILT(in_features = vlen, out_features = None,
                      alpha = self.params['delta'], # scale context drift
                      dur = 2.5, # how long to present items, in seconds
                      tau_0 = .1, # time of first taustar
                      ntau = 90, # number of taustars
                      k = 4, # controls degree of approximation
                      c = 0.1, # controls spacing of "s" decay rates
                      T_toskip = 8 # controls what taustars to skip when indexing into T
                      )

        self.bt.reset()


        self.T_full_ind = self.bt._T_full_ind # indexing into T
        self.times = self.bt.tau_star[self.bt.k:-self.bt.k][self.T_full_ind] # taustars

        # create array of numerical indices into taustars (shortest taustar = 0, next one = 1, etc.)
        time_nums = np.arange(len(self.times))
        # initialize noise
        # noise is essentially a slope, starting at 1, decreasing in value by sigma at each taustar, down to a minimum of zero
        # values in current and retrieved Ts are later multiplied by these values to lose activation,
        # more so at later taustars
        self.noise = np.clip(1 - (self.params['sigma'] * time_nums), 0, None)
        # turn noise into a matrix
        self.noise = np.atleast_2d(self.noise)
        # items are columns, noise at each taustar are rows
        self.noise_scaler = np.repeat(self.noise, vlen, axis = 0).T

        # initalize M matrix
        self.M = np.zeros((len(self.features.keys()), self.bt.T.shape[0]))

        # loop through filler items, add to context T
        for i in range(self.n_filleritems):
            self.filler_item(self.features['filler_%s' %i])
        pass



    def filler_item(self, f):

        self.f = f
        # update SITH with filler
        self.bt.update(inputs = self.f)

    def present_pair(self, f1, f2, isi):

        # select the item representations
        self.f1 = f1
        self.f2 = f2
        self.f = self.f1 + self.f2

        # get indices of which item features are active
        inds = np.where(self.f > 0)[0]
        self.inds = inds

        # make matrix of T, shaped tau_star X item features
        T_full = self.bt.T.reshape((self.times.shape[0], self.f1.shape[0]))
        # inject noise into current T, which decreases activation, more so at later taustars
        T_full_noised = T_full * self.noise_scaler

        # predict items from current noisy context (and clip at 0 for only positive activation)
        p_T = np.clip(np.dot(self.M, T_full_noised.flatten()), 0, None)
        # "read out" presented items from predicted items
        s_pT = np.dot(self.f, p_T)

        # get item strength by integrating the feature activations over tau stars, scale by lambda
        this_strength = np.trapz(y = T_full_noised[:, inds[0]], x = self.times) + np.trapz(y = T_full_noised[:, inds[1]], x = self.times)
        self.s_f = self.params['lambda'] * this_strength

        # calculate non-linear r term for asymptotic learning
        immediate_str = self.params['omega']*self.s_f + (1-self.params['omega'])*s_pT
        self.r = np.exp(-immediate_str)

        # retrieve each item's context (Tp)
        f1_retrieved_T = np.dot(self.f1, self.M)
        Tp1 = f1_retrieved_T.reshape((self.times.shape[0], self.f1.shape[0]))
        f2_retrieved_T = np.dot(self.f2, self.M)
        Tp2 = f2_retrieved_T.reshape((self.times.shape[0], self.f2.shape[0]))
        # inject noise
        Tp1 = Tp1 * self.noise_scaler
        Tp2 = Tp2 * self.noise_scaler

        # calculate overlap in retrieved contexts at each tau star
        m = [np.dot(Tp1[i, :], Tp2[i, :]) for i in range(Tp1.shape[0])]
        # integrate overlap over tau stars, which serves as "match" signal
        self.s_b_m = np.trapz(m, x = self.times)

        # calculate "mismatch" between the retrieved contexts at each tau star
        mm = [np.dot(Tp1[i, :] - Tp2[i, :], Tp1[i, :] - Tp2[i, :]) for i in range(Tp1.shape[0])]
        # integrate mismatch over tau stars, make negative
        self.s_b_mm = -np.trapz(mm, x = self.times)

        # calculate overall memory strength as sum of familiarity, match, and mismatch
        self.mem_strength = self.s_f + self.s_b_m + self.s_b_mm

        # combine current and (averaged) retrieved contexts (beta fixed to .5)
        context_mix = (1 - self.params['beta'])*T_full_noised + self.params['beta'] * ((Tp1 + Tp2)/2.)
        context_mix = context_mix.flatten()

        # predict item activations based on noisy context_mix
        p = np.dot(self.M, context_mix)
        # clip predictions between 0 and 1 to avoid weirdness
        p = np.clip(p, 0, 1)
        # calculate prediction error
        pred_err =  self.f - p.T

        # bind prediction error (which is positive for correctly predicted presented features,
        # negative for incorrectly predicted unpresented features), scale by learning rate alpha
        self.M += self.params['alpha'] * np.outer(pred_err, context_mix)

        # update TILT with item features, scaled by non-linear term r (so that repeated items will not get into context as much as new items)
        # and move SITH along to a degree scaled by r (so that repeated items will not update context as much as new items)
        self.bt.update(inputs = self.r*self.f, alpha = self.r*self.params['delta'], durs = 2.5)
        # drift context (with no input) for duration of inter-stimulus interval
        self.bt.update(inputs = self.empty_features, alpha = self.r*self.params['delta'], durs = isi)



        #################################################################



    def calc_assbind_like(self, data, sim = False):
        # initialize list of log-likelihoods for model-fitting
        log_like = []
        # if data are being simulated...
        if sim:
            # make a dictionary in which to store output information
            self.output = {}
            # this function updates the output dictionary
            def outputify(label, dat):
                if label not in self.output:
                    self.output[label] = []
                self.output[label].append(dat)


        # determine which key was used to respond "old" and which for "new"
        df_old = data[data['resp_correct'] == 'old']
        self.key_old = df_old[df_old['resp_acc'] == True]['pressed'].unique()[0]
        df_new = data[data['resp_correct'] == 'new']
        self.key_new = df_new[df_new['resp_acc'] == True]['pressed'].unique()[0]

        # loop through trials
        for i in range(data.shape[0]):
            # get test trial info
            self.trial = data.iloc[i]
            # get what images were presented
            left_img = self.trial['img_L']
            right_img = self.trial['img_R']

            isi = self.trial['isi']

            # get feature representations from features dictionary
            f1 = self.features['item_%s' %left_img]
            f2 = self.features['item_%s' %right_img]

            # model this trial
            self.present_pair(f1 = f1, f2 = f2, isi = isi)

            # get the strength
            strength = self.mem_strength

            # get the RT and button press
            rt = self.trial['resp_rt']
            r = self.trial['pressed']

            # calculate log-likelihood, but only if a response was made and it wasn't too fast to be meaningful
            if rt > 0.35:
                ll = self._recog_like_ddm(r, strength, rt)
                log_like.append(ll)

            # if results are being simulated by the model...
            if sim:
                v = self.params['nu'] - strength # drift rate is difference between "new" and "old" strengths
                w = self.params['w']
                v_mean = v
                a = self.params['a']
                w_mode = w
                nsamp = 1000
                v_std = 0

                # generate choices and RTs given drift rate and other decision parameters
                self.m_choices, self.m_rts = wfpt_gen(v_mean = v_mean, a = a, w_mode = w_mode,
                                             v_std = v_std, nsamp = nsamp,
                                             trange = np.linspace(0, 2.5 - self.params['t0'], 1000))

                # save needed info in output dictionary
                outputify('s', strength)
                outputify('s_f', self.s_f)
                outputify('s_b_m', self.s_b_m)
                outputify('s_b_mm', self.s_b_mm)
                outputify('m_no_resp', np.mean(self.m_choices == 0))
                outputify('m_old_resp', np.mean(self.m_choices == 1))
                outputify('m_new_resp', np.mean(self.m_choices == 2))
                outputify('m_old_logrt', np.mean(np.log(self.m_rts[self.m_choices==1] + self.params['t0'] + 1)))
                outputify('m_new_logrt', np.mean(np.log(self.m_rts[self.m_choices==2] + self.params['t0'] + 1)))
                outputify('m_all_logrt', np.mean(np.log(self.m_rts[(self.m_choices==1) | (self.m_choices==2)] + self.params['t0'] + 1)))
                outputify('r', self.r)

        return log_like


    def _recog_like_ddm(self, resp, strength, rt, save_posts=False):

        # diffusion is to lower boundary, make that old
        v = self.params['nu'] - strength
        w = self.params['w']
        if resp == self.key_old:
            resp = 1
        elif resp == self.key_new:
            resp = 2
        else:
            resp = 0

        v_std = 0
        v_mean = v
        a = self.params['a']
        w_mode = w
        t0 = self.params['t0']
        nsamp = 1000

        # calc the likelihood
        like = wfpt_like(choices = np.array([resp]), rts = np.array([rt]), t0 = t0, v_mean = v_mean, v_std = v_std, a = a, w_mode = w_mode, nsamp = nsamp)
        like = like[0]

        # return the log-likelihood
        return np.log(like)
