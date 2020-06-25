'''
This script sets configural options for the associative binding task.
'''

import sys

# touchscreen or keyboard?
TOUCH=False

##################################################
############## configs for listgen ###############
##################################################

# number of previous blocks with the current participant that are used to cull the list of available stimuli
NUM_BLOCKS_CULL = 12

TASK_DIR = "."

# define strength conditions and order of trials within strength condition
# note that the strength refers to the memory strength of intact pairs at the time when pairs are recombined (i.e. number of repetitions prior to recombination)
COND_TRIAL_ORDERS = {'weak': ['new', 'recombined', 'old 1', 'old 2'],
                     'med': ['new', 'old 1', 'recombined', 'old 2'],
                     'strong': ['new', 'old 1', 'old 2', 'recombined']}
# list of strength conditions
CONDS_STRENGTH = list(COND_TRIAL_ORDERS.keys())
# number of strength conditions
NUM_CONDS_STRENGTH = len(CONDS_STRENGTH)
# trial types within condition
CONDS_TRIAL = COND_TRIAL_ORDERS[CONDS_STRENGTH[0]]
# number of trial types within condition
NUM_CONDS_TRIAL = len(CONDS_TRIAL)
# number of pairs for each trial type in each condition; ***this should be changed to increase or decrease length of block***
NUM_PAIRS_COND = 4
# total total number of trials and images
NUM_TRIALS = NUM_CONDS_STRENGTH * NUM_CONDS_TRIAL * NUM_PAIRS_COND
NUM_IMAGES = NUM_CONDS_STRENGTH * NUM_PAIRS_COND * 2

# lag_constraint places a limit on the "lag" between when the same image is presented in the experiment,
# i.e. the number of intervening trials between trial types for a given image;
# if lag_constraint = num_trials, there's no constraint
LAG_CONSTRAINT = NUM_TRIALS
# sets the number of times the listgen can loop through, if needed, to form recombined pairs properly and to fulfill the lag constraint
NUM_ATTEMPTS = 10000


#######################################################
############## configs for presentation ###############
#######################################################

# response key mappings
RESP_KEYS = {'old':'F', 'new':'J'}
RESP_KY = ["F", "J"]
CONT_KEY = ['SPACEBAR']

SKIP_SIZE = [200, 50]
SKIP_FONT_SIZE = 25

# font size of the instructions
INST_FONT_SIZE = 40
INST_TITLE_FONT_SIZE = 45

# width and height of images used in instructions, in pixels; IMG_WIDTH * 1.5
INST_IMG_WIDTH = 512
INST_IMG_HEIGHT = 256

# percentage of the pixels on the screen, used to adjust image/label spacing in instructions
PIXEL_PERCENT = .08

# presentation time, in s, of each pair
STIM_PRES_TIME = 2.5

MIN_RT = .35
MAX_RT = 2.5

# base time and jitter between trials
ISI_BASE = 0.5
ISI_JIT = 0.5

# width and height of images, in pixels (used to draw rectangle around pair upon response)
IMG_WIDTH = 256
IMG_HEIGHT = 256

# response frame size in pixels outside of image sizes
RESP_FRAME_SIZE = 25

# color of response-indicating rectangle
COLOR_RECT = (0.0, 0.0, 0.0)

# color of score announcement rectangle
COLOR_SCORE_RECT = (144./255., 175./255., 197./255.)

# dimensions of score rectangle
WIDTH_SCORE_RECT = 1200
HEIGHT_SCORE_RECT = 900
TEXT_SIZE_WIDTH = 1300

# font size of the score announcement at the end of the block
SCORE_FONT_SIZE = 70
RST_FONT_SIZE = 45
FONT_SIZE = 50
CROSS_FONTSIZE = 90
FINAL_FONT_SIZE = 35

# SYNC PULSING
FMRI = False
FMRI_KEYS =  {'old':'1', 'new':'2'}
FMRI_TR = ["5"]
FMRI_CONT = ["1","2"]
FMRI_TECH_KEYS = ["ENTER"]
FMRI_TR_DUR = 1.6
INIT_TR_WAIT = 4*FMRI_TR_DUR
POST_TR_WAIT = 8*FMRI_TR_DUR
POST_CHECK_TR_DUR = 1.5*FMRI_TR_DUR

EEG = False
EEG_CODES = {"new":14,
             "old 1":15,
             "old 2":16,
             "recombined":17}




# function to retrieve correct image paths
def resource_path(relative_path):
    basedir = sys.executable
    last_dir = basedir.rfind("/")
    basedir = basedir[:last_dir]
    #return os.path.join(basedir, "tasks", "cont_ass_bind", relative_path)
    return relative_path
