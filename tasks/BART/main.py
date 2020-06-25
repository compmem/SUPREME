from smile.common import Log, Label, Wait, Func, Debug, Loop, \
                         UntilDone, Subroutine, KeyPress, If
from smile.scale import scale as s
from smile.lsl import LSLPush

from list_gen import add_air
from instruct import Instruct
from trial import BARTSub, GetResponse

import os

import version


@Subroutine
def BartuvaExp(self,
               config,
               run_num,
               sub_dir,
               task_dir=None,
               full_instructions=True,
               practice=False,
               pulse_server=None):

    if task_dir is not None:
        config.TASK_DIR = task_dir
    config.INST2_IMG_PATH = os.path.join(config.TASK_DIR,
                                         config.INST2_IMG_PATH)

    if config.TOUCH:
        config.KEY_TEXT = config.TOUCH_TEXT
        config.CONT_KEY_STR = "the screen"

    if len(config.CONT_KEY) > 1:
        cont_key_str = str(config.CONT_KEY[0]) + " or " + \
                       str(config.CONT_KEY[-1])
    else:
        cont_key_str = "the screen"

    Log(name="BARTUVAinfo",
        version=version.__version__,
        author=version.__author__,
        date_time=version.__date__,
        email=version.__email__)

    Wait(1.)

    # Do instructions along with a mini block.
    with If(practice | full_instructions):
        Instruct(config=config,
                 run_num=run_num,
                 sub_dir=sub_dir,
                 task_dir=task_dir,
                 full_instructions=full_instructions,
                 practice=practice)

    balloon_setup = config.BALLOON_SETUP
    num_balloons = config.NUM_BALLOONS

    Label(text='You will now begin the balloon task.' +
               '\nPress %s to continue.' % (cont_key_str),
          halign='center',
          font_size=s(config.LABEL_FONT_SIZE))
    with UntilDone():
        Wait(.5)
        GetResponse(keys=config.CONT_KEY)

    number_of_sets = 1
    self.set_number = 0
    self.grand_total = config.GRAND_TOTAL
    self.balloon_number_session = 0
    self.trkp_press_time = None

    # FMRI STUFF
    if config.FMRI:

        Label(text="Waiting for Experimenter...",
              font_size=s(config.INST_FONT_SIZE))
        with UntilDone():
            KeyPress(keys=config.FMRI_TECH_KEYS)

        Label(text="+", font_size=s(config.CROSS_FONTSIZE))
        with UntilDone():
            trkp = KeyPress(keys=config.FMRI_TR)
            Log(name="BARTUVA_TR",
                press_time=trkp.press_time)
            self.trkp_press_time = trkp.press_time
        Wait(duration=config.INIT_TR_WAIT)

    Wait(1.)
    # main loop
    with Loop(number_of_sets):
        Wait(.5, jitter=.5)

        # Calling listgen as 'bags'
        bg = Func(add_air,
                  total_number_of_balloons=config.NUM_BALLOONS,
                  num_ranges=len(config.BALLOON_SETUP),
                  balloon_setup=config.BALLOON_SETUP,
                  randomize=config.RANDOMIZE_BALLOON_NUM,
                  reward_low=config.REWARD_LOW,
                  reward_high=config.REWARD_HIGH,
                  subject_directory=sub_dir,
                  practice=False,
                  shuffle_bags=config.SHUFFLE_BAGS)
        bags = bg.result

        self.block_tic = 0

        # with Loop(bag.current) as balloon:
        with Loop(bags) as balloon:
            Balloon = BARTSub(config,
                              balloon=balloon.current,
                              block=self.block_tic,
                              set_number=self.set_number,
                              grand_total=self.grand_total,
                              balloon_number_session=self.balloon_number_session,
                              subject=self._exp.subject,
                              run_num=run_num,
                              trkp_press_time=self.trkp_press_time,
                              pulse_server=pulse_server)
            self.balloon_number_session += 1
            self.grand_total = Balloon.grand_total
        self.block_tic += 1

        self.set_number += 1

    # Press 6 to say we are done recording then show them their score.
    if config.FMRI:
        self.keep_tr_checking = True
        Wait(config.POST_TR_WAIT)
        Label(text="Waiting for Experimenter...",
              font_size=s(config.INST_FONT_SIZE))
        with UntilDone():
            with Loop(conditional=self.keep_tr_checking):
                post_trkp = KeyPress(keys=config.FMRI_TR,
                                     duration=config.POST_CHECK_TR_DUR)
                with If(post_trkp.pressed == ''):
                    self.keep_tr_checking = False
            KeyPress(keys=config.FMRI_TECH_KEYS)

        Wait(1.0)


if __name__ == "__main__":
    from smile.common import Experiment
    from smile.startup import InputSubject
    from smile.lsl import init_lsl_outlet
    import config

    config.EEG = True

    if config.EEG:
        pulse_server = init_lsl_outlet(server_name='MarkerStream',
                                       server_type='Markers',
                                       nchans=1,
                                       suggested_freq=500,
                                       channel_format='int32',
                                       unique_id='COGBATT_LSL_OUT')
    else:
        pulse_server = None

    config.FLIP_BART = True
    exp = Experiment(name="BARTUVA_ONLY", debug=True,
                     background_color=((.35, .35, .35, 1.0)))
    Wait(1.0)
    InputSubject(exp_title="BARTUVA")
    BartuvaExp(config,
               run_num=0,
               sub_dir=exp.subject_dir,
               full_instructions=True,
               practice=True,
               pulse_server=pulse_server)
    Label(text="Task Complete! Please wait for the program to automatically close.",
          font_size=s(config.INST_FONT_SIZE), duration=2.0)

    exp.run()
