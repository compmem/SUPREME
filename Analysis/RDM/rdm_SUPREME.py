import numpy as np
import pandas as pd
from RunDEMC import Model, Param, dists
from RunDEMC.density import kdensity
from RunDEMC.io import save_results
import simulate_lca_model as un
import scoop
from scoop import futures
        
# set up the simulation
nsims = 50000
nbins = 2000
log_shift = 0.05
log_max = 100.
extrema = (np.log(log_shift), np.log(log_max))
ncohs = 6
two_pi = 2.0/np.pi

def eval_mod_lca(params, param_names, subj_num=None):
    d = 0.0
    p = {i: params[n]
         for n, i in enumerate(param_names)}
    coh_sep = 0.06 # max_coherence/(num_coherences-1)
    if p['a']<0 or p['c']<0 or p['beta']<0 or p['kappa']<0 or p['alpha']<0 or p['t0']<0:
        return -np.inf
    # check for a negative rho
    for i in range(ncohs):
        coh = i*coh_sep
        # check for negative rho
        rho1 = d + (p['a']-d)/(1.+np.exp(-(coh-p['b'])*p['c']))
        if rho1 < 0:
            return -np.inf
        # check for denominator of 0
        if (1.+np.exp(-(coh-p['b'])*p['c']))==0:
            return -np.inf
    log_like = 0.0

    if subj_num:
        subj_ind = data['subj'] == subj_num
    else:
        subj_ind = data['subj'] != None

    # double for-loop iterates through all possible conditions
    for j in range(ncohs):
        left_coh = j*coh_sep
        for k in range(j, ncohs):
            right_coh = k*coh_sep
            tf_lc = left_coh + ((1.0- (left_coh+right_coh))/2.0)*two_pi
            tf_rc = right_coh + ((1.0- (left_coh+right_coh))/2.0)*two_pi
            # transform into rhos via sigmoid function
            rho1 = d + (p['a']-d)/(1.+np.exp(-(tf_lc-p['b'])*p['c']))
            rho2 = d + (p['a']-d)/(1.+np.exp(-(tf_rc-p['b'])*p['c']))
            rts, choices = un.uber_sim(rho=(np.array([rho1, rho2])),
                                       kappa=p['kappa'], beta=p['beta'],
                                       alpha=p['alpha'], dt=0.01, tau=0.1,
                                       eta=1.0, max_time=3.0,
                                       nsims=nsims, t0=p['t0'])

            # pull out rts for each choice
            rt1 = rts[choices == 1]
            rt2 = rts[choices == 2]

            # look up the coh index
            coh_index = str(left_coh)+', '+str(right_coh)

            # parse the behavioral data into left and right responses
            rts_for_left = np.array(data[subj_ind &
                                              (data['coherence'] == coh_index) &
                                              (data['correct']==False)]['rt'])
            rts_for_right = np.array(data[subj_ind &
                                            (data['coherence'] == coh_index) &
                                            (data['correct']==True)]['rt'])

            # check if there are any behavioral responses for that choice
            if ((len(rts_for_left) > 0) and
                ((len(rt1) < 3) or (np.std(rt1) < 0.001))) or \
                ((len(rts_for_right) > 0) and
                 ((len(rt2) < 3) or (np.std(rt2) < 0.001))):
               return -np.inf
            else:
                # calculate log_likes for each choice
                # first for incorrect
                if len(rts_for_left) > 0:
                    pp, xx = kdensity(np.log(rt1+log_shift),
                                  xx=np.log(rts_for_left+log_shift),
                                  nbins=nbins,
                                  extrema=extrema,
                                  kernel='epanechnikov')
                    pp *= float(len(rt1))/nsims
                    log_like += np.log(pp).sum()

                # then for correct
                if len(rts_for_right) > 0:
                    pp, xx = kdensity(np.log(rt2+log_shift),
                                      xx=np.log(rts_for_right+log_shift),
                                      nbins=nbins,
                                      extrema=extrema,
                                      kernel='epanechnikov')
                    pp *= float(len(rt2))/nsims
                    log_like += np.log(pp).sum()
            
        
    return log_like


def eval_fun_lca(pop, *args):
    likes = list(futures.map(eval_mod_lca, [indiv for indiv in pop], [pnames]*len(pop),
                             [args[0]]*len(pop)))
    return np.array(likes)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("datafile", type=str,
                        help="session identifier")
    args = parser.parse_args()
    s = args.datafile
    data = pd.read_csv(s)
    print("Fitting model to %s"%s)
    
    # remove response times faster than 0.2 seconds
    data = data[data['rt']>0.2]
    data = data.reset_index()
    
    # create the coherence column
    data['coherence'] = ''
    for i in range(len(data)):
        left_coherence = data.at[i,'left_coherence']
        right_coherence = data.at[i,'right_coherence']
        if left_coherence>right_coherence:
            data.at[i, 'coherence'] = str(right_coherence)+', '+str(left_coherence)
        elif right_coherence>=left_coherence:
            data.at[i, 'coherence'] = str(left_coherence)+', '+str(right_coherence)
    # loop through each participant
    for s in data.subj.unique():
        subj_ind = data['subj'] == s
        min_rt = data[subj_ind]['rt'].min()

        # set up the params
        params = [Param(name='a',
                      prior=dists.trunc_normal(5.0, 20.0,
                                               lower=0.0, upper=50.0)),
                Param(name='b',
                      prior=dists.normal(0.0, 5.0)),
                Param(name='c',
                      prior=dists.trunc_normal(5.0, 10.0,
                                               lower=0.0, upper=30.0)),
                Param(name='kappa', prior=dists.normal(0.0, 1.4),
                      transform=dists.invlogit),
                Param(name='beta', prior=dists.normal(0.0, 1.4),
                      transform=dists.invlogit),
                Param(name='alpha',
                      prior=dists.trunc_normal(2.5, 10.0,
                                               lower=0.0, upper=30.0)),
                Param(name='t0', prior=dists.uniform(0., min_rt))]
        pnames = [p.name for p in params]
        # instantiate model object
        m = Model('urdm_lca', params=params,
                    like_fun=eval_fun_lca,
                    like_args=(s,),
                    init_multiplier=4,
                    verbose=True, purify_every=5)

        # set up the run name
        output_name = 'rdm_lca_tcv_both_cb_afrl_mri_subj_'+str(int(s))+'.tgz'

        # do some burnin
        for i in range(5):
            times = m(100, burnin=True)
            save_results(output_name, m)

        # sample the posterior
        for i in range(10):
            times = m(100, burnin=False)
            save_results(output_name, m)
