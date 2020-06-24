import numpy as np
import pandas as pd
from simulate_lca_model import uber_multi_sim as model_sim
from RunDEMC.io import load_results
import argparse

# import data file and preprocess
parser = argparse.ArgumentParser()
parser.add_argument("datafile", type=str,
                    help="session identifier")
args = parser.parse_args()
s = args.datafile
df = pd.read_csv(s)
df['coherence'] = ''
for i in range(len(df)):
    left_coherence = df.at[i,'left_coherence']
    right_coherence = df.at[i,'right_coherence']
    if left_coherence>right_coherence:
        df.at[i, 'coherence'] = str(right_coherence)+', '+str(left_coherence)
    elif right_coherence>=left_coherence:
        df.at[i, 'coherence'] = str(left_coherence)+', '+str(right_coherence)
df = df[df['rt']>0.2]
df = df.reset_index()

# sample from the posterior distribution and re-simulate
nsims = 20000
burnin = 600
coh_sep = .06
ncohs = 6
count = 0
max_ntrials = 16.0
slow_time = 3.0
fast_time = 0.3
min_rt = np.log(fast_time+1.0)
max_rt = np.log(slow_time+1.0)
total_n_conds = 21
two_pi = 2.0/np.pi
subjs = [2,3,58,64]
for subj in subjs:
    df_perf = pd.DataFrame(columns=['perf','subj','post_sample'])
    # change file path as necessary
    file_name = 'cogbat_afrl_data/model_fits/rdm_lca_tcv_both_cb_afrl_beh_subj_'+str(subj)+'.tgz'
    m1 = load_results(file_name)
    # sample from the posterior
    posteriors = []
    interval = 101
    for i in range(len(m1['param_names'])):
        posteriors.append(m1['particles'][burnin:,:,i].flatten()[::interval])
    df_obs = df[df['subj']==subj]
    # re-simulate with samples from the posterior distribution
    for n in range(len(posteriors[0])):
        # keep track of the total number of simulations
        nsims_total = 0.0
        # keep track of the total number of correct responses
        ncorrect_total = 0.0
        # keep track of the total value of the transformed rts
        rt_sum = 0.0
        for i in range(ncohs):
            left_coh = round(i*coh_sep,2)
            for j in range(i, ncohs):
                right_coh = round(j*coh_sep,2)
                coh_str = str(left_coh) +', '+str(right_coh)
                tf_lc = left_coh + ((1.0- (left_coh+right_coh))/2.0)*two_pi
                tf_rc = right_coh + ((1.0- (left_coh+right_coh))/2.0)*two_pi
                ntrials = len(df_obs[df_obs['coherence']==coh_str])
                trial_correction = ntrials/max_ntrials
                nsims_cor = int(nsims*trial_correction)
                # transform into rhos via sigmoid function
                rho1 = posteriors[0][n]/(1.+np.exp(-(tf_lc-posteriors[1][n])*posteriors[2][n]))
                rho2 = posteriors[0][n]/(1.+np.exp(-(tf_rc-posteriors[1][n])*posteriors[2][n]))
                rts,choices = model_sim(rho=np.array([rho1, rho2]),
                                        kappa=posteriors[3][n],
                                        beta=posteriors[4][n],
                                        alpha=posteriors[5][n],
                                        max_time=3.0, nsims=nsims_cor,
                                        t0=posteriors[6][n])
                # account for the equal coherence conditions
                if left_coh==right_coh:
                    ncorrect_total += nsims_cor/2.0
                else:
                    ncorrect_total += sum(choices-1)
                rt_sum += np.mean((max_rt-np.log(rts+1.0))/(max_rt-min_rt))
                nsims_total += nsims_cor
        rts_tf = rt_sum/total_n_conds
        acc_tf = (ncorrect_total/nsims_total -.5)/.5
        perf = acc_tf*rts_tf
        df_perf.loc[count] = [perf,subj,n]
        count+=1
        if n%300==0:
            print(n)
    df_perf.to_csv('ppds_subj_'+str(subj)+'.csv')