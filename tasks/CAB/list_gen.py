import os
import random
import pickle
from glob import glob
import copy
import sys

# Function gathers images from image file, searches for previously used images,
# and creates a single block of AssBind trials
#def get_stim(images_per_trial,number_of_learn_trials,image_path, subj_dir):
def get_stim(config, subj_dir):
    # gather all possible images
    images = glob(os.path.join(config.TASK_DIR, "stim",'*'))
    # gather previously used images:
    if os.path.isdir(os.path.join(subj_dir, 'ass_bind_pickles')):
        old_pickles = glob(os.path.join(subj_dir,'ass_bind_pickles','*'))

        if len(old_pickles) == 0:
            print("No previous sessions detected")
            possible_images = images
            old_images = []

        else:
            old_pics = [pickle.load(open(i,'rb')) for i in old_pickles]
            old_images = sum(old_pics,[])
            if old_images == []:
                print("No previous sessions detected")
                # comment out line below for demo
                os.makedirs(os.path.join(subj_dir, 'ass_bind_pickles'))
                possible_images = images
                old_images = []
            else:
                # remove old images from list of all images
                #print images
                [images.remove(i) for i in old_images]
                print(len(old_images), 'removed from pool')
                possible_images = images

    else:
        # comment out line below for demo
        os.makedirs(os.path.join(subj_dir, 'ass_bind_pickles'))
        print("No previous sessions detected")
        possible_images = images
        old_images = []


    # Create trials from current pool
    new_pool = []
    for i in range(config.NUM_IMAGES):
        pic = random.choice(possible_images)
        possible_images.remove(pic)
        new_pool.append(pic)

    # store list of used images:
    old_images = new_pool + old_images
    if len(old_images) > config.NUM_IMAGES*config.NUM_BLOCKS_CULL:
        del old_images[-1*config.NUM_IMAGES:]

    else:
        pass
    pickle.dump(old_images,open(os.path.join(subj_dir, 'ass_bind_pickles', 'last_pickle.p'),'wb'))

    # return pool of images to be used
    return new_pool


###########################
###########################
##### make trial list #####
###########################
###########################
def make_trials(config, num_attempts, lag_constraint, num_pairs_cond, subj_dir):

    # initialize dictionary to fill with lists of trial info
    cond_dicts = {cond_strength: {} for cond_strength in config.CONDS_STRENGTH}
    # initialize dictionary to fill with lists of previously "used" trials when filling trial list
    cond_dicts_used = copy.deepcopy(cond_dicts)
    # initialize inner used trial dictionaries of each trial type within strength conditions, e.g. {weak: {recombined: x, old 1: x... } ... }
    for cond in cond_dicts_used:
        cond_dicts_used[cond] = {cond_trial: {} for cond_trial in config.CONDS_TRIAL}

    #####################################
    ##### create trial dictionaries #####
    #####################################

    # initialize counter for stimulus indices
    stim_i = 0
    # loop through strength conditions
    for cond_strength in config.CONDS_STRENGTH:
        # initalize a list for original (intact) pairs
        intact_pairs = []
        # loop to fill list of intact pairs with indices (placeholders for image files)
        for pair_i in range(config.NUM_PAIRS_COND):
            # define stimulus indices for a pair, append to list
            pair = [stim_i, stim_i+1]
            intact_pairs.append(pair)
            # move counter forward 2 spaces to avoid repeated iamges
            stim_i += 2

        # variable acts as a flag for whether loop can move on to next trial
        worked = 0
        # this outer recombination loop is number of attempts to get recombined pairs that are always recombined, because ocassionally,
        # by chance, "recombined" pairs are same as intact after shuffling
        for attempt in range(config.NUM_ATTEMPTS):
            # make list of right-side object indices from intact pairs
            avail_R = [this_pair[1] for this_pair in intact_pairs[:]]
            # if haven't solved it yet, continue
            if not worked:
                #initialize list to fill with recombined pairs
                rec_pairs = []
                # inner recombination loop through intact pairs
                for this_pair in intact_pairs:
                    # for each intact pair, get left-side item index
                    rec_pair_L = this_pair[0]
                    # make a copy of available right-side images
                    avail_R_forpair = avail_R[:]
                    # if this intact pair's right side item is in list of available items, take it out (to ensure no accidental intact pairs)
                    if this_pair[1] in avail_R_forpair:
                        avail_R_forpair.remove(this_pair[1])
                    # if list of available items is empty, this attempt has failed, break inner loop to start over through outer loop
                    if len(avail_R_forpair) == 0:
                        break
                    else:
                        # if there is at least one available item for recombination, randomly choose a right-side item for recombined pair
                        rec_pair_R = random.choice(avail_R_forpair)
                        # append recombined pair to list, remove chosen right-side item from list of available items
                        rec_pairs.append([rec_pair_L, rec_pair_R])
                        avail_R.remove(rec_pair_R)
                # check if all recombined pair slots have been successfully filled; if so, break outer recombination loop
                if len(rec_pairs) == num_pairs_cond:
                    worked = 1
                    break
        # for current strength condition, make lists of trial dictionaries for each trial type (i.e., new, old 1, etc.)
        cond_dicts[cond_strength]['new'] = [{'pair_inds': pair, 'cond_strength': cond_strength,
                                            'cond_trial': 'new', 'resp_correct': 'new'} for pair in intact_pairs]
        cond_dicts[cond_strength]['old 1'] = [{'pair_inds': pair, 'cond_strength': cond_strength,
                                            'cond_trial': 'old 1', 'resp_correct': 'old'} for pair in intact_pairs]
        cond_dicts[cond_strength]['old 2'] = [{'pair_inds': pair, 'cond_strength': cond_strength,
                                            'cond_trial': 'old 2', 'resp_correct': 'old'} for pair in intact_pairs]
        cond_dicts[cond_strength]['recombined'] = [{'pair_inds': pair, 'cond_strength': cond_strength,
                                            'cond_trial': 'recombined', 'resp_correct': 'new'} for pair in rec_pairs]

    # make list of strength-trial conditions (e.g. strong new, weak old 1, etc.); this list will be used to place all trial types in the trial list
    trial_types = []
    for cond_strength in config.CONDS_STRENGTH:
        for cond_trial in config.CONDS_TRIAL:
            trial_types.append({'cond_strength': cond_strength, 'cond_trial': cond_trial})
    # repeat so that there's a separate entry for every trial in the list, which defines the condition of the trial
    trial_types_list = trial_types*num_pairs_cond


    ############################################
    ############### place trials ###############
    ############################################

    # loop through attempts
    for attempt in range(config.NUM_ATTEMPTS):
        # get a fresh copy of trial dictionaries (this object will store currently available trials)
        cond_dicts_block = copy.deepcopy(cond_dicts)
        # fresh copy of dictionary of already-used trials
        cond_dicts_used_block = copy.deepcopy(cond_dicts_used)
        # fresh copy of the list of conditions for each trial
        trial_types_block = copy.deepcopy(trial_types_list)
        trials = [None]*config.NUM_TRIALS

        # shuffle the trial condition list
        random.shuffle(trial_types_list)
        # loop through trial condition list (outer loop of trials)
        for i in range(len(trial_types_list)):
            # define this trial number
            # shuffle second trial condition list
            num_trial = i + 1
            random.shuffle(trial_types_block)
            # for each trial in the outer loop, loop through second trial condition list to try to fill that trial
            for j in range(len(trial_types_block)):
                # flag for whether the trial placement is successful
                worked = False
                # index info for the currently proposed trial
                trial_info = trial_types_block[j]
                # use the trial type just indexed to index into currently available (i.e., unused) trials of that type
                candidate_trials = cond_dicts_block[trial_info['cond_strength']][trial_info['cond_trial']]

                # if the proposed trial type is new...
                if trial_info['cond_trial'] == 'new':
                    # randomly choose from list of candidate trials and accept it automatically
                    trial = random.choice(candidate_trials)
                    trials[i] = copy.deepcopy(trial)
                    # update trial dictionary with trial number and empty placeholders for lags (no lag for new)
                    trials[i].update({'num_trial': num_trial, 'lag_L': None, 'lag_R': None})
                    # remove this trial from the dict/lists of available trials for a given condition
                    cond_dicts_block[trial_info['cond_strength']][trial_info['cond_trial']].remove(trial)
                    # index into list of already used trials, make a new dictionary with keys of accepted object index and value of the current trial number
                    cond_dicts_used_block[trial_info['cond_strength']][trial_info['cond_trial']][trial['pair_inds'][0]] = trials[i]['num_trial']
                    cond_dicts_used_block[trial_info['cond_strength']][trial_info['cond_trial']][trial['pair_inds'][1]] = trials[i]['num_trial']
                    # remove the accepted trial type from list so it can't be used again
                    trial_types_block.remove(trial_types_block[j])
                    # move on to next trial in outer loop
                    break
                # if the proposed trial type is anything other than new...
                else:
                    # get the index of this type of trial in the ordered list of trial types for the trial's strength
                    # e.g. if the trial is weak & recombined, the index would be 1, since recombined always comes second in the order of trials for the weak condition
                    current_cond_ind = config.COND_TRIAL_ORDERS[trial_info['cond_strength']].index(trial_info['cond_trial'])
                    # find the the most recently presented trial type
                    # e.g., if the current trial is weak & recombined, the most recently presented trial type was "new"
                    prev_cond = config.COND_TRIAL_ORDERS[trial_info['cond_strength']][current_cond_ind-1]
                    # next, get list of object indices that have been used in the previous trial type
                    # e.g., if the current trial is weak & recombined, the following line the list of trial numbers that already presented weak & new pairs
                    # (this is needed to make sure both items in current trial were already presented for the previous trial condition, and to constrain lags)
                    prev_items_cond = cond_dicts_used_block[trial_info['cond_strength']][prev_cond]

                    # loop through trials that might work
                    for candidate_trial in candidate_trials:
                        # get the object indices for this possible trial
                        candidate_pair = candidate_trial['pair_inds']
                        # ensure that both objects were already presented in previous condition
                        if candidate_pair[0] in prev_items_cond and candidate_pair[1] in prev_items_cond:
                            # calculate lags from the previous condition's trial number for each candidate object
                            lag_L = num_trial - prev_items_cond[candidate_pair[0]]
                            lag_R = num_trial - prev_items_cond[candidate_pair[1]]
                            # check if both object's lags meet lag criterion
                            if lag_L < lag_constraint and i+1 - lag_R < lag_constraint:
                                # all placement criteria have been met, so accept this trial
                                trials[i] = copy.deepcopy(candidate_trial)
                                # update trial dict with trial number and lag trial_info
                                trials[i].update({'num_trial': num_trial, 'lag_L': lag_L, 'lag_R': lag_R})
                                # remove this trial from dict/lists of available trials for each condition
                                cond_dicts_block[trial_info['cond_strength']][trial_info['cond_trial']].remove(candidate_trial)
                                # index into list of already used trials, make a new dictionary with keys of accepted object indices and values of the current trial number
                                cond_dicts_used_block[trial_info['cond_strength']][trial_info['cond_trial']][candidate_trial['pair_inds'][0]] = trials[i]['num_trial']
                                cond_dicts_used_block[trial_info['cond_strength']][trial_info['cond_trial']][candidate_trial['pair_inds'][1]] = trials[i]['num_trial']
                                # remove the accepted trial type from list so it can't be used again
                                trial_types_block.remove(trial_types_block[j])
                                # a trial was successfully placed, so break this candidate_trial loop
                                worked = True
                                break
                    # if trial was successfully placed, move on to the next trial by breaking the inner loop
                    if worked:
                        break
        # if all trials were successfully placed, break the loop of attempts
        if worked:
            print('worked!', attempt)
            break
    # raise an error if the not all trials were successfully placed in the number of attempts allowed
    if not worked:
        raise RuntimeError("Unable to generate list." +
                               " Try adjusting your config.")
    # get list of stimuli
    imgs = get_stim(config, subj_dir)
    # update trial dictionaries with stimuli paths/file names
    for trial in trials:
        trial.update({'img_L': config.resource_path(imgs[trial['pair_inds'][0]]),
                      'img_R': config.resource_path(imgs[trial['pair_inds'][1]])})

    return trials
