import os

# config
NUM_BLOCKS = 1
SHUFFLE_BAGS = True
# Parameter for randomize the number of balloons per pop range (aka bag)
RANDOMIZE_BALLOON_NUM = False
BALLOON_SETUP = [{'range': [0, 8], 'number_of_balloons':8},
                 {'range': [0, 16], 'number_of_balloons':8},
                 {'range': [8, 16], 'number_of_balloons':8}]
PRACTICE_SETUP = [{'range': [10,10], 'number_of_balloons':0},
                 {'range': [3,3], 'number_of_balloons':0},
                 {'range': [6,6], 'number_of_balloons':0}]
NUM_BALLOONS = 18
NUM_BAGS = len(BALLOON_SETUP)
BALLOONS_PER_BAG = NUM_BALLOONS/NUM_BAGS
TOUCH=False
TOUCH_TEXT = ["Touch left side\n","Touch right side\n"]
TOUCH_INST = ['left side of the screen', 'right side of the screen']
TASK_DIR = "."
INST2_IMG_PATH = os.path.join("inst", "INST2.png")

RESP_KEYS = ['F', 'J']
CONT_KEY = ['SPACEBAR']
CONT_KEY_STR = "Spacebar"
KEY_TEXT = RESP_KEYS

REWARD_LOW = 0.05
REWARD_HIGH = 0.25
#starting value in bank
GRAND_TOTAL = 1.00

RST_WIDTH = 600

FEEDBACK_TIME = 0.75
ISI = 0.25
INTER_PUMP_DURATION = 0.75
REWARD_SLIDE_DURATION = 0.25
PUMP_DURATION = 0.25
COLLECT_DURATION = 0.5
BALLOON_GROWTH_DURATION = 0.3
POP_ANIMATION_DURATION = 1.0

BALLOON_START_SIZE = 100
BALLOON_EXPLODE_SIZE = (500, 500)
FLIP_BART = False
INC_BALLOON_SIZE = 5
TRIAN_SIZE = 10
CROSS_COLOR = (1.0, 1.0, 1.0, 1.0)
CROSS_FONTSIZE = 90

BANK_WIDTH = 150
BANK_HEIGHT = 150

POP_SIZE = (600, 600)
AIR_PUMP_WIDTH = 100
AIR_PUMP_HEIGHT = 100

NOZZLE_WIDTH = 4
NOZZLE_HEIGHT = 40

FEEDBACK_FONT_SIZE = 90
INST_FONT_SIZE = 20
CROSS_FONT_SIZE = 75
FONT_SIZE = 30
LABEL_FONT_SIZE = 30

SKIP_SIZE = [200, 50]
SKIP_FONT_SIZE = 22
# font sizes for labels
TOTAL_FONT_SIZE = 35
TRIAL_FONT_SIZE = 30

FMRI = False
FMRI_TR = ["5"]
FMRI_TECH_KEYS = ['ENTER']
FMRI_TR_DUR = .8
INIT_TR_WAIT = 6.0
POST_TR_WAIT = 16.0
POST_CHECK_TR_DUR = 3.0*FMRI_TR_DUR

EEG = False
EEG_CODES = {"code":18}
