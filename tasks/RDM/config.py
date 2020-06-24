# config
NUM_BLOCKS = 1
NUM_DOTS = 100

TOUCH = False

RADIUS = 275
SCALE = 5
LIFESPAN = 0.75
LIFESPAN_VAR = 0.5
SPEED = 200.0
TEST_WIDTH = 1600
COHERENCES = [0., .06, .12, .18, .24, .30]

RESP_KEYS = ['F', 'J']
CONT_KEY = ['SPACEBAR']

RESPONSE_DURATION = 3.
FEEDBACK_TIME = 0.5
ISI = 0.25
JITTER = 0.50

FAST_TIME = 0.5
SLOW_TIME = 3.0

CROSS_COLOR = (1.0, 1.0, 1.0, 1.0)

FEEDBACK_FONT_SIZE = 120
INST_FONT_SIZE = 32
CROSS_FONTSIZE = 90
FONT_SIZE = 50
FINAL_FONT_SIZE = 35

# dimensions of score rectangle
WIDTH_SCORE_RECT = 1200
HEIGHT_SCORE_RECT = 900

# SYNC PULSING
FMRI = False
FMRI_TR = ["T"]
FMRI_TECH_KEYS = ["ENTER"]
FMRI_TR_DUR = 1.6
INIT_TR_WAIT = 4*FMRI_TR_DUR
POST_TR_WAIT = 8*FMRI_TR_DUR
POST_CHECK_TR_DUR = 1.5*FMRI_TR_DUR

EEG = False
EEG_CODES = {"code":18}

INST_RADIUS = 225
INST_SCALE = 4
INST_LIFESPAN = 0.75
INST_LIFESPAN_VAR = 0.5
INST_SPEED = 200.0
