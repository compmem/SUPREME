

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

import math
import copy
# RunDEMC
from RunDEMC import Model, Param, dists
from RunDEMC import Hierarchy, HyperPrior
from RunDEMC.density import kdensity
from RunDEMC.io import save_results
from RunDEMC.io import load_results
from joblib import Parallel, delayed
import numba
from numba import jit
from numba import jitclass
from numba import float64
from numba import cuda
from numba.cuda import random
import gzip
import pickle
import cProfile

sns.set_context('talk')

def tacos(filename):
    """
    Load in a simulation that was saved to a pickle.gz.
    """
    gf = gzip.open(filename, 'rb')
    res = pickle.loads(gf.read(), encoding='latin1')
    gf.close()
    return res


# ## Model equations
#Updating E_future
#Optimal E_future would be the average reward over current trial number.
#If E_future is ignored, set to 0.
@jit(nopython=True)
def update_E_future(pop_prob_estimate,gamma,gamma_n,n,rb,true_avg,avg,ticker):
    if true_avg == True:
        avg = 0.15
    else:
        pass
    E_future=0.
    fut = int(n)-ticker
    run_prob = (1.-pop_prob_estimate)
    for i in range(fut):
        x = int(n)-(ticker+i+1)
        if x == 0:
            future_prob = 1.
        else:
            future_prob = 1./(x)
        run_prob = run_prob*(1.-future_prob)
        if rb<0 and avg < 0:
            E_future += -1.*((run_prob)*(abs(avg)**gamma_n))
        elif rb < 0 and avg > 0:
            E_future += ((run_prob)*(abs(avg)**gamma_n))
        elif rb > 0 and avg < 0:
            E_future += -1.*((run_prob)*(abs(avg)**gamma))
        else:
            E_future += (run_prob)*(avg**gamma)
    return E_future

#Updating E (calls update_E_future)
@jit(nopython=True)
def update_E(pop_prob_estimate,gamma,gamma_n,theta,n,rb,true_avg,avg,ticker,total):
    E_future = update_E_future(pop_prob_estimate,gamma,gamma_n,n,rb,true_avg,avg,ticker)
    if rb < 0:
        E = (E_future - theta*(abs(rb)**gamma_n))
    else:
        a = (1-pop_prob_estimate)*rb**gamma
        b = theta*pop_prob_estimate*(total**gamma_n)
        E = a + E_future - b
    return E

#Update estimated probability
@jit(nopython=True)
def estimated_prob_update(n,ticker):
    x = (int(n)-ticker)
    if x == 0:
        pop_prob_estimate = numba.float32(1.)
    else:
        pop_prob_estimate = numba.float32(1./x)
    return pop_prob_estimate

#Updating estimated n
@jit(nopython=True)
def n_update(alpha,pop_prob_estimate,n,trial,I,balloon_number):
    delta_n = (pop_prob_estimate-I)*(trial+(I*(n-(2*trial))))
    n = n + alpha*delta_n
    return n

#Choice_gen
@jit(nopython=True)
def choice_like(alpha,beta,gamma,gamma_n,theta,ns,balloons,
               start_money_observed,start_avg_ticker,true_avg,
               bank,number_of_bags,ranges,targets):
    log_like = 0.0
    grand_total = numba.float32(bank)
    av_ticker = start_avg_ticker
    cashmoney = start_money_observed
    ntics = [0,0,0]
    #begin main loop
    for balloon in range(len(balloons)):
        target = targets[balloon]
        if ranges[balloon] == 0:
            n_index = 0
            n = ns[0]
            pop_prob_estimate = numba.float32(1./n)
        elif ranges[balloon] == 1:
            n_index = 1
            n = ns[1]
            pop_prob_estimate = numba.float32(1./n)
        elif ranges[balloon] == 2:
            n_index = 2
            n = ns[2]
            pop_prob_estimate = numba.float32(1./n)
        else:
            n_index = 1000000000000000000
        hh = True
        total = numba.float32(0.00)
        tic = numba.int32(0)
        outcome = balloons[balloon,target,0]
        if outcome == 1:
            trials = target + 1
        else:
            trials = target
        for trial in range(trials):
            if balloons[balloon,trial,0] == -1.:
                break
            else:
                rb = balloons[balloon,trial,1]
                av_ticker += 1
                cashmoney += rb
                if true_avg == True:
                    avg = numba.float32(.15)
                else:
                    avg = numba.float32(cashmoney/av_ticker)
                if rb>=0.:
                    tic+=1
                pop_prob_estimate = estimated_prob_update(n,tic)
                E = update_E(pop_prob_estimate,gamma,gamma_n,theta,n,rb,
                             true_avg,avg,tic,total)
                d_choice = numba.float32((math.exp(beta*E))/(1.+math.exp(beta*E)))

                status = balloons[balloon,trial,0]
                if trial < target:
                    if status == 1:      # not popped
                        total += rb
                        n = n_update(alpha,pop_prob_estimate,n,
                                     tic,0.,balloon)
                        ns[n_index] = n
                        log_like += np.log(d_choice)
                else:
                    if outcome == 1:# Collect
                        grand_total += total
                        n = n_update(alpha,pop_prob_estimate,n,tic,0.,balloon)
                        ns[n_index] = n
                        d_choice = 1 - d_choice
                        log_like += np.log(d_choice)
                        break
                    else:
                        total += rb
                        n = n_update(alpha,pop_prob_estimate,n,
                                 tic,1.,balloon)
                        ns[n_index] = n
                        log_like += np.log(d_choice)
                        break
    return log_like

_rng_states = None
_rng_size = -1
def simulations(alpha,beta,gamma,gamma_n,theta,n_0,n_1,n_2,
                balloon_tensor,start_money_observed,
                start_avg_ticker,true_avg,bank,
                number_of_bags,targets,ranges,
                num_sims=5000,seed=None):
    global _rng_states
    global _rng_size
    ns = [n_0,n_1,n_2]
    ns = np.asarray(ns)

    log_like = choice_like(np.float32(alpha),
                          np.float32(beta),
                          np.float32(gamma),
                          np.float32(gamma_n),
                          np.float32(theta),
                          ns,
                          balloon_tensor,
                          np.float32(start_money_observed),
                          np.float32(start_avg_ticker),
                          np.float32(true_avg),
                          np.float32(bank),
                          np.int32(3),
                          ranges,
                          targets)

    return log_like


# ## RunDEMC
#RunDEMC required functions
#Calls choice_like, gets log_likes
def eval_mod(params, param_names,balloon_tensor,
             start_money_observed,
             start_avg_ticker,true_avg,
             bank,number_of_bags,
             targets,ranges,
             verbose=False):
    # turn param list into dict
    mod_params = params.copy()
    mod_params = ({x: params[n]
                    for n, x in enumerate(param_names)})

    alpha = mod_params['alpha']
    beta = mod_params['beta']
    gamma = mod_params['gamma']
    gamma_n = mod_params['gamma_n']
    theta = mod_params['theta']
    n_0 = mod_params['n_0']
    n_1 = mod_params['n_1']
    n_2 = mod_params['n_2']
    # calculate the log likes
    ll = simulations(alpha,beta,gamma,gamma_n,theta,n_0,n_1,n_2,
                     balloon_tensor,start_money_observed,
                     start_avg_ticker,true_avg,bank,
                     number_of_bags,targets,ranges)

    return ll

#Calls eval_mod in RunDEMC
def eval_fun(pop, *args):
    pnames = args[1]
    balloon_tensor = args[2]
    start_money_observed = args[3]
    start_avg_ticker = args[4]
    true_avg = args[5]
    bank = args[6]
    number_of_bags = args[7]
    targets = args[8]
    ranges = args[9]

    likes = client.map(eval_mod, [indiv for indiv in pop],
                                 [pnames]*len(pop),[balloon_tensor]*len(pop),
                                             [start_money_observed]*len(pop),
                                             [start_avg_ticker]*len(pop),[true_avg]*len(pop),
                                             [bank]*len(pop),[number_of_bags]*len(pop),
                                             [targets]*len(pop),[ranges]*len(pop))

    return np.array(client.gather(likes))

# ## Run Model

if __name__ == '__main__':
    
    import sys,os,argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--response_data", type=str, default=4, help="path/file name of response csv")
    parser.add_argument("--balloon_info", type=str, default=4, help="path/file name of balloon info h5.")
    parser.add_argument("--fits_storage", type=str, default=4, help="path/file name of saving fits")
    parser.add_argument("--fits_tag", type=str, default=4, help="tag to denote fits (e.g, eeg, fmri, etc.)")
    args = parser.parse_args()

    balloon_info= args.balloon_info
    response_info = args.response_data
    fits_storage = args.fits_storage
    tag = args.fits_tag
    
    sub_responses = pd.read_csv(response_info)
    sub_balloons = pd.HDFStore(balloon_info)
    from dask.distributed import LocalCluster, Client
    cluster = LocalCluster(10)
    client = Client(cluster)
    subs = list(set(list(sub_responses['subject'])))
    # getting fits already made

    for subject in subs:
        response_inds = list(set(list(sub_responses[(sub_responses['subject']==subject)]['run_num'])))
        blocks = len(set(list(response_inds)))
        for block in range(blocks):
            print('Subject: ' + str(subject))
            balloon_name = subject+'/block'+str(block)
            balloon_frame = sub_balloons.get(balloon_name)
            responses = copy.deepcopy(sub_responses[(sub_responses['subject']==subject)&
                                      (sub_responses['run_num']==response_inds[block])])
            count_1 = len(responses[responses.key_pressed==1])
            count_4 = len(responses[responses.key_pressed==4])
            if count_1 > count_4:
                lr = 'left'
            else:
                lr = 'right'
            for index,row in balloon_frame.iterrows():
                t = int(row['pump_range_0'])
                y = int(row['pump_range_1'])
                balloon_frame.loc[index,'range'] = str(t) + '_' + str(y)
            num_balloons = 18
            balloon_lengths = [len(balloon_frame[balloon_frame.balloon==i]) for i in range(num_balloons)]
            max_length = max(balloon_lengths)

            #loop through balloons to get trial information in matrix
            balloon_matrices = []
            for balloon in range(num_balloons):
                bb = balloon_frame[balloon_frame['balloon']==balloon]
                stats = []
                rews = []
                p0 = []
                p1 = []
                for index,row in bb.iterrows():
                    stats.append(int(row['pop_status']))
                    rews.append(row['rewards'])
                    p0.append(int(row['pump_range_0']))
                    p1.append(int(row['pump_range_1']))
                while len(stats) < max_length:
                    stats.append(-1.)
                    rews.append(-1.)
                    p0.append(-1.)
                    p1.append(-1.)
                balloon_matrix = np.column_stack((stats,rews,p0,p1))
                balloon_matrices.append(balloon_matrix)
            balloon_tensor = np.stack(balloon_matrices)
            total_money_observed = 0.0
            starting_avg_ticker = 0
            bank = 0.00
            #getting response targets
            if lr == 'left':
                targets = [len(responses[(responses.balloon_number_session==i)&
                                    (responses.key_pressed==1)]) for i in range(num_balloons)]
            else:
                targets = [len(responses[(responses.balloon_number_session==i)&
                                (responses.key_pressed==4)]) for i in range(num_balloons)]
            # getting balloon types
            gg = [list(balloon_frame[balloon_frame['balloon']==z]['range'])[0] for z in range(num_balloons)]
            r_r = list(set(list(balloon_frame['range'])))
            ranges = []
            for r in gg:
                if r == r_r[0]:
                    ranges.append(0)
                elif r == r_r[1]:
                    ranges.append(1)
                else:
                    ranges.append(2)
            ranges = np.asarray(ranges,dtype=np.int16)
            # priors
            params = [Param(name='alpha',
                            display_name=r'$\alpha$',
                            prior=dists.trunc_normal(mean=0.5,std=5.0,lower=0,upper=1.)
                           ),
                      Param(name='beta',
                            display_name=r'$\beta$',
                            prior=dists.trunc_normal(mean=5.,std=5.,lower=-10.,upper=10.)
                           ),
                      Param(name='gamma',
                            display_name=r'$\gamma$',
                            prior=dists.trunc_normal(mean=1.0,std=5.,lower=0.,upper=2.)
                           ),
                      Param(name='gamma_n',
                            display_name=r'$\gamma_n$',
                            prior=dists.trunc_normal(mean=1.0,std=5.,lower=0.,upper=2.)
                           ),
                      Param(name='theta',
                            display_name=r'$\theta$',
                            prior=dists.trunc_normal(mean=1.0,std=5.,lower=-10.,upper=10.)
                           ),
                      Param(name='n_0',
                            display_name=r'$\n_0$',
                            prior=dists.trunc_normal(mean=15.0,std=10.,lower=0.,upper=60.)
                           ),
                      Param(name='n_1',
                            display_name=r'$\n_1$',
                            prior=dists.trunc_normal(mean=15.0,std=10.,lower=0.,upper=60.)
                           ),
                      Param(name='n_2',
                            display_name=r'$\n_2$',
                            prior=dists.trunc_normal(mean=15.0,std=10.,lower=0.,upper=60.)
                           )
                     ]

            pnames = [p.name for p in params]
            #RunDEMC TIME
            m = Model(subject,
                      params=params,
                      like_fun=eval_fun,
                      like_args=('subject',
                                 pnames,
                                 balloon_tensor,
                                 total_money_observed,
                                 starting_avg_ticker,
                                 False,
                                 bank,
                                 3,
                                 targets,
                                 ranges),
                      verbose=True,
                      purify_every=5)
#             file_name = 'fits/sequential_fits/eeg_'+subject+'_block' + str(block) + '.tgz'
            print(fits_storage, tag, subject, str(block))
            file_name = os.path.join('{0}'.format(fits_storage),'{0}_{1}_block{2}.tgz'.format(tag, subject, str(block)))
            # run model
            m(400,burnin=True,migration_prob=0.0)  #Burnin
            m(1000,burnin=False,migration_prob=0.0) #Poseteriors
            save_results(file_name,m)
    hdf.close()
