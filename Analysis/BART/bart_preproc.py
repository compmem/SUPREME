import numpy as np
import pandas as pd

# Calculate the future reward
def _future_rewards(maxx,trial,average,balloon_total,low_end_range):
    run_prob = 1. - (float(trial)/maxx)
    E_future = 0
    for f in range(trial+1,maxx+1):
        x = maxx - f
        if x == 0:
            #future_prob is the prob of balloon popping
            future_prob = 1.0
        elif f < low_end_range:
            future_prob = 0.
        else:
            future_prob = 1./x
        run_prob = run_prob * (1 - future_prob)
        E_future += run_prob * average
    return E_future

# Calculate the optimal score for all possible trials (up to where
# the balloon pops)
def _optimal_score(rewards,high_range,low_end_range,avg=True):
    E_list = []   # storage list
    total = 0.    #keeping track of reward - not used if avg = True
    # if we assume an optimal subject knows the average reward,
    # we calculate it based upon the reward distributions used
    #print type(ast.literal_eval(pops))
    if avg == True:
        aaa = np.linspace(0.05,0.26,21,endpoint=False)
        average = sum(aaa)/len(aaa)
    for i in range(60):
        total += rewards[i]
        buyin_tic = 0
        #average = total/(i+1)  Commented out for now: using true average score
        # add a ticker for when there is a buy-in
        if rewards[i] < 0.:
            buyin_tic += 1
        # Getting correct trial number, for buy-ins do not increase balloon size/pop prob.
        trial = i - buyin_tic
        if i < low_end_range:
            q = 1.
            p = 0.
        else:
            q = 1. - float(trial-low_end_range)/(high_range-low_end_range)
            p = float(trial-low_end_range)/(high_range-low_end_range)
        #print optimal_n
        E_future = _future_rewards(int(high_range),trial,average,total,low_end_range)
        if rewards[i] > 0:
            E = q*rewards[trial] + E_future - p*total
        else:
            E = E_future - rewards[i]
        #print E
        E_list.append(E)
    return E_list

def calculate_expected_values(data_frame):
    Es = []
    for index, row in data_frame.iterrows():
        x = _optimal_score(row['rewards'],row['pump_range'][1],row['pump_range'][0])
        Es.append(x)
    # Adding/updating column of optimal scores possible in balloon_frame
    data_frame['E_list'] = Es
    return data_frame

# 
def create_hdf_files(subjects):
    '''
    subjects: path to subject SMILE data
    '''
    # process bart pickle files that contain balloon information
    # create/open hdf5 file
    hdf = pd.HDFStore('balloon_info_bart.h5','a')
    # loop through directories and get pickle files
    for sub in subjects:
        sessions = glob(sub_name+'/*.p')
        for session in sessions:
            x = {'sub':str(sub)}
            d = pickle.load(open(session,'rb'))
            dat = pd.DataFrame(d)
            dat['balloon'] = 0
            for index,row in dat.iterrows():
                dat.loc[index,'balloon'] = index
            data = calculate_expected_values(dat)
            # flatten dataframe to be saved in hdf5
            flat = []
            for index, row in data.iterrows():
                for i in range(len(row['pop'])):
                    x = {}
                    x['pop_status'] = row['pop'][i]
                    x['rewards'] = row['rewards'][i]
                    x['expected_optimal'] = row['E_list'][i]
                    x['pump_range_0'] = row['pump_range'][0]
                    x['pump_range_1'] = row['pump_range'][1]
                    x['balloon'] = row['balloon']
                    flat.append(x)
            flat = pd.DataFrame(flat)
            hdf.put(sub_name + '/block' + str(sessions.index(session)),flat,format='table')
        if sub%10==0:
            print(sub)

    hdf.close()

