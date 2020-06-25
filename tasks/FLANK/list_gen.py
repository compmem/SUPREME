import random
from math import cos, sin, sqrt, pi, radians



# list generation
def gen_fblocks(config):
    flanker_blocks = []
    for blo in range(config.NUM_BLOCKS):
        for b in range(config.NUM_REPS):
            temp_block = []
            for i in range(config.NUM_TRIALS):
                for l in range(config.NUM_LOCS):
                    for s in config.EVIDENCE_CONDITIONS:
                        if s == 0.:
                            # MIXED EASY RIGHT
                            trial = {'condition': "=",
                                     'stim':"__<__\n_<><_\n<>>><\n_<><_\n__<__\n",
                                     'loc_x':cos(radians((360./config.NUM_LOCS)*l)),
                                     'loc_y':sin(radians((360./config.NUM_LOCS)*l)),
                                     'corr_resp': config.RESP_KEYS[-1]}
                            temp_block.append(trial.copy())


                            #Mixed Hard RIGHT
                            trial['stim'] = "__>__\n_><>_\n><><>\n_><>_\n__>__\n"
                            trial['condition'] = "~"
                            temp_block.append(trial.copy())

                            # Mixed Hard LEFt
                            trial['corr_resp'] = config.RESP_KEYS[0]
                            trial['stim'] = "__<__\n_<><_\n<><><\n_<><_\n__<__\n"
                            temp_block.append(trial.copy())

                            # Mixed easy LEFT
                            trial['stim'] = "__>__\n_><>_\n><<<>\n_><>_\n__>__\n"
                            trial['condition'] = "="
                            temp_block.append(trial.copy())
                        else:
                            # CONGRUENT RIGHT
                            trial = {'condition': "+",
                                     'stim':"__>__\n_>>>_\n>>>>>\n_>>>_\n__>__\n",
                                     'loc_x':cos(radians((360./config.NUM_LOCS)*l)),
                                     'loc_y':sin(radians((360./config.NUM_LOCS)*l)),
                                     'corr_resp': config.RESP_KEYS[-1]}
                            temp_block.append(trial.copy())

                            # CONGRUENT LEFT
                            trial['corr_resp'] = config.RESP_KEYS[0]
                            trial['stim'] = "__<__\n_<<<_\n<<<<<\n_<<<_\n__<__\n"
                            trial['condition'] = "+"
                            temp_block.append(trial.copy())
            random.shuffle(temp_block)
            flanker_blocks.append(temp_block)
    return flanker_blocks
