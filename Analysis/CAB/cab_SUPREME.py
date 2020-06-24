# import needed libraries and scripts
import numpy as np
from scoop import futures
import sys
import os
import pandas as pd
from glob import glob
from scipy import stats

from RunDEMC import Model, Param, dists
from RunDEMC import Hierarchy, HyperPrior
from RunDEMC import save_results
import log as lg

from bigtcm import bigTCM

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


def eval_mod(params, param_names, bdat=None, save_posts=False, verbose=False):

    if bdat is None:
        bdat = dat

    # turn param list into dict
    mod_params = default_params.copy()
    mod_params.update({x: params[n]
                       for n, x in enumerate(param_names)})

    # initialize log-likelihood at zero
    ll = 0.0

    # get list of subject's blocks
    blocks = np.unique(bdat['block'])
    for block in blocks:
        # index into specific block for analysis
        d = bdat[bdat['block'] == block]

        if verbose:
            sys.stdout.write('.')
            sys.stdout.flush()

        # run bigTCM on this block's data
        bigtcm = bigTCM(d = d, params = mod_params)
        # get the log like
        lls = bigtcm.calc_assbind_like(d)
        ll += np.sum(lls)

    return ll


# function needed for RunDEMC
def eval_fun(pop, *args):
    # call each particle in parallel
    bdat = args[1]
    pnames = args[2]
    likes = list(futures.map(eval_mod, [indiv for indiv in pop],
                             [pnames]*len(pop), [bdat]*len(pop)))

    return np.array(likes)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()

    # need a command line argument specifying the desired name for an output folder
    parser.add_argument("datafile", type=str,
                        help="run identifier")
    args = parser.parse_args()
    s = args.datafile
    dat = pd.read_csv(s)
    print("Fitting model to %s"%s)

    # initialize list for cleaned data
    dats = []

    sub_df = dat
    blocks = sub_df.block.unique()
    for block in blocks:
        block_df = sub_df[sub_df['block'] == block]
        # isolate data where subject made a response
        block_df_responded = block_df[block_df['resp_rt'] > 0]

        # make sure subject responded on over 2/3 of trials
        if block_df_responded.shape[0] > block_df.shape[0]*2/3.:
            # occasionally participants get confused about which key corresponds to which response;
            # here we check to see if accuracy on a block *for the easiest trials only* was significantly *below* chance,
            # as determined by a binomial test; if so, we switch the accuracy values for that block, to correct the mistake
            this_df = block_df[(block_df['cond_trial'] == 'new') | (block_df['cond_trial'] == 'old 2')]
            binom_neg = stats.binom_test(this_df[this_df['resp_acc'] == 1].shape[0], this_df.shape[0], .5, alternative='less')
            if binom_neg < .05:
                print('Subject %s, Block %s, Accuracy below chance; switching response acuracies for this block' %(sub, block))
                print(this_df[this_df['resp_acc'] == 1].shape[0])
                # make a mask for trials where subject made a response (RT > 0), but it was recorded as incorrect (so we can change it to correct)
                mask_cor = (block_df['resp_acc'] == False) & (block_df['resp_rt'] > 0)
                # make a mask for trials where response was recorded as correct (so we can change it to incorrect)
                mask_incor = (block_df['resp_acc'] == True)
                # change masked resposnes
                block_df.loc[mask_cor, 'resp_acc'] = True
                block_df.loc[mask_incor, 'resp_acc'] = False

            # find differences between trial start times
            diffs = np.diff(block_df['appearL_time'])
            # take stimulus presentation time (2.5 s) away from trial time differences to get inter-stimulus interval
            isis = np.append(diffs-2.5, 0)
            # add ISI to dataframe
            block_df = block_df.assign(isi = isis)
            # get the data for the easiest trials only
            this_df = block_df[(block_df['cond_trial'] == 'new') | (block_df['cond_trial'] == 'old 2')]
            # were responses significantly above chance?
            binom = stats.binom_test(this_df[this_df['resp_acc'] == 1].shape[0], this_df.shape[0], .5, alternative='greater')

            if binom < .05:
                # if yes, we can analyze these data, so append to data list
                dats.append(block_df)
            else:
                print('Subject %s, Block %s, Accuracy not above chance; excluding data from analysis' %(sub, block))
                print(this_df[this_df['resp_acc'] == 1].shape[0])

    # make a dataframe of all the data we can analyze
    data_sub = pd.concat(dats)

    # get the subject's RTs
    RTs = data_sub['resp_rt']
    # select RTs greater than 350 ms
    RTs_x = RTs[RTs > .35]
    # get minimum RT (that is greater than 350 ms) -- this is needed for t0 prior
    min_RT = np.min(RTs_x)
    print ('*** subject ', s)

    # get name of output file
    out_file = 'cab_'+s[:-4]+'.tgz'

    # define model parameters and priors
    params = [

              Param(name='lambda',
                    display_name=r'$\lambda$',
                    prior = dists.trunc_normal(.5, 2, 0, 5)
                    ),
#
              Param(name='alpha',
                    display_name=r'$\alpha$',
                    prior = dists.trunc_normal(1., 4, 0, 10)
                    ),

              Param(name='omega',
                  display_name=r'$\omega$',
                  prior = dists.normal(mean=0, std=1.4),
                  transform=dists.invlogit
                  ),

              Param(name='delta',
                   display_name=r'$\delta$',
                   prior=dists.trunc_normal(1., 10, 0, 20.0),
                   ),

              Param(name='sigma',
                    display_name=r'$\sigma$',
                    prior = dists.normal(mean=0, std=1.4),
                    transform=dists.invlogit
                    ),


              Param(name='nu',
                    display_name=r'$\nu$',
                    prior = dists.trunc_normal(mean=2., std=10., lower=0., upper=10.),
                    ),

              Param(name='a',
                    display_name=r'$a$',
                    prior = dists.trunc_normal(mean=2., std=10., lower=0., upper=10.)
                    ),

              Param(name='w',
                    display_name=r'$w$',
                    prior = dists.normal(mean=0, std=1.4),
                    transform=dists.invlogit
                    ),

              Param(name='t0',
                    display_name=r'$t_0$',
                    prior=dists.uniform(0,min_RT),
                    ),
              ]

    # grab the param names
    pnames = [p.name for p in params]
    # initialize the model
    m = Model(s,params=params,
                     like_fun=eval_fun,
                     like_args=(s,data_sub,pnames),
                     num_chains = 80,
                     init_multiplier = 4,
                     verbose=True)

    # set number of desired burn-in trials
    num_burnin = 400
    # interval of how often simulations should be saved
    interval = 25
    # total number of intervals
    num_intervals = int(num_burnin / interval)
    # how many simulations have been completed?
    done_sims = 0
    for i in range(num_intervals):
        print(done_sims, 'done in burn-in')
        # run this model simulation for the number of simulations in each interval
        m(interval, burnin = True)
        # save the simulations so far into an output file
        save_results(out_file, m)
        done_sims += interval

    # repeat process with posterior (not burn-in) simulations
    num_posts = 800
    interval = 25
    num_intervals = int(num_posts / interval)
    done_sims = 0
    for i in range(num_intervals):
        print(done_sims, 'done in posterior')
        m(interval, burnin = False)
        save_results(out_file, m)
        done_sims += interval
