import itertools
import random



def gen_moving_dot_trials(config):
    # block generation
    # create every pairwise combination of coherence condition
    trials_1 = [dict(zip(['left_coherence', 'right_coherence'], x))
                for x in itertools.product(config.COHERENCES, config.COHERENCES)]
    temp_extra = []
    temp_real = []
    # loop through each pairwise combination of coherence condition
    for trial in trials_1:
        # assign a correct response for equal coherence trials
        # need a correct response for each coherence condition
        # in both directions to avoid inducing a directional bias
        if trial['right_coherence'] == trial['left_coherence']:
            trial_temp = trial.copy()
            trial['correct_resp'] = config.RESP_KEYS[-1]
            trial['incorrect_resp'] = config.RESP_KEYS[0]
            trial_temp['correct_resp'] = config.RESP_KEYS[0]
            trial_temp['incorrect_resp'] = config.RESP_KEYS[-1]
            temp_extra.append(trial_temp)
            temp_real.append(trial)
        # assign a correct response for unequal coherence trials
        else:
            if trial['right_coherence'] > trial['left_coherence']:
                trial['correct_resp'] = config.RESP_KEYS[-1]
                trial['incorrect_resp'] = config.RESP_KEYS[0]
            else:
                trial['correct_resp'] = config.RESP_KEYS[0]
                trial['incorrect_resp'] = config.RESP_KEYS[-1]
            # add extra coherence trials for the easiest conditions
            # i.e. conditions with a nonzero difference greater than the smallest difference
            if round(abs(trial['right_coherence'] - trial['left_coherence']), 2) != round(config.COHERENCES[1] - config.COHERENCES[0], 2):
                temp_extra.append(trial)
            temp_real.append(trial)
    
    # combine all trials together
    trials = temp_extra + temp_real
    blocks = []
    # randomize each block and create list of blocks
    # based on NUM_BLOCKS attribute
    for i in range(config.NUM_BLOCKS):
        random.shuffle(trials)
        blocks.append(trials)
    return blocks
