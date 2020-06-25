"""
This script presents stimuli for the associative binding task.

The task presents pairs of objects to participants, who must decide whether
each pair is "new" (i.e. not presented previously), or "old."

Each pair is presented 3 times (an initial presention plus 2 repetitions), and
recombined with other pairs once.

The order in which these events occur differs by "strength" condition.

"Weak" condition trials: new, recombined, old 1, old 2
"Medium" condition trials: new, old 1, recombined, old 2
"Strong" condition trials: new, old 1, old 2, recombined

"""

# import needed libraries
from smile.common import Log, Label, Wait, Ref, Rectangle, Func, Debug, Loop, \
                         UntilDone, If, Else, Parallel, Subroutine, KeyPress, \
                         Image, Meanwhile
from smile.scale import scale as s
from smile.lsl import LSLPush

from math import log

from list_gen import make_trials
from instruct import Instruct
from GetResponse import GetResponse

import version


# make_metric function takes subject's accuracy and RTs and converts them to a
# metric score ranging from 0 (worst performance) to 100 (best performance)
def make_metric(config, acc_list, rt_list):
    # define the minimum and maximum allowed RTs (in s)
    min_rt = config.MIN_RT
    max_rt = config.MAX_RT

    # loop through trials, and only include ones with
    # RT within acceptable range
    rts = []
    accs = []
    for i, rt in enumerate(rt_list):
        rts.append(rt)
        if (rt > min_rt):
            accs.append(acc_list[i])
        else:
            accs.append(False)
    # number of trials taken into account for metric
    num_trials = len(accs)

    # accuracy metric: distance of average accuracy from chance (50%), such
    # that perfect accuracy results in avec = 1.
    avec = ((sum(accs)/float(num_trials))-.5)/.5

    # RT metric: average distance from min and max RT, such that fastest
    # response on every trial results in rvec = 1.
    rvec = (sum([(log(max_rt + 1.) - log(r + 1.)) /
                 ((log(max_rt + 1.) - log(min_rt + 1.)))
                 for r in rts])/num_trials)

    # combine accuracy and RT metrics into single score
    score = int(avec * rvec * 100)

    return score


@Subroutine
def AssBindExp(self, config, sub_dir, task_dir=None, block=0,
               reminder_only=False, pulse_server=None, shuffle=False,
               conditions=None):
    if task_dir is not None:
        config.TASK_DIR = task_dir

    if len(config.CONT_KEY) > 1:
        cont_key_str = str(config.CONT_KEY[0]) + " or " + \
                       str(config.CONT_KEY[-1])
    else:
        cont_key_str = str(config.CONT_KEY[0])

    Log(name="AssBindinfo",
        version=version.__version__,
        author=version.__author__,
        date_time=version.__date__,
        email=version.__email__)

    # get needed variables from config file
    num_attempts = config.NUM_ATTEMPTS
    lag_constraint = config.LAG_CONSTRAINT
    num_pairs_cond = config.NUM_PAIRS_COND

    # generate trial dictionaries from listgen
    gen = Func(make_trials,
               config,
               num_attempts,
               lag_constraint,
               num_pairs_cond,
               sub_dir)
    trials = gen.result

    # present instructions / examples / reminder

    text_names = ['main', 'ex1', 'ex2', 'ex3', 'ex4', 'remind']
    rem_names = ['remind']
    with If(reminder_only):
        Instruct(config=config, text_names=rem_names)
    with Else():
        Instruct(config=config, text_names=text_names)

    Wait(1.0)

    self.eeg_pulse_time = None
    self.fmri_tr_time = None
    # FMRI STUFF
    if config.FMRI:
        KeyPress(keys=config.FMRI_TECH_KEYS)
        Label(text="Waiting for Experimenter...",
              font_size=s(config.INST_FONT_SIZE))
        with UntilDone():
            trkp = KeyPress(keys=config.FMRI_TR)
            Log(name="CABS_TR",
                press_time=trkp.press_time)
            self.trkp_press_time = trkp.press_time
        Label(text="+", font_size=s(config.CROSS_FONTSIZE),
              duration=config.INIT_TR_WAIT)

    # initialize lists of accuracies and RTs
    # (to calculate a metric score at the end)
    self.accs = []
    self.rts = []

    # loop through trials
    with Loop(trials) as trial:
        # delay until next trial based on a base time plus a jitter
        Wait(config.ISI_BASE, jitter=config.ISI_JIT)



        with Parallel():
            # initialize a frame around the images
            # (which is invisible until response)
            resp_rect = Rectangle(size=(s(2*config.IMG_WIDTH +
                                          config.RESP_FRAME_SIZE),
                                        s(config.IMG_HEIGHT +
                                          config.RESP_FRAME_SIZE)),
                                  color=(.35, .35, .35, 0.0),
                                  duration=config.STIM_PRES_TIME)
            # present pair of images
            left_image = Image(source=trial.current['img_L'],
                               duration=config.STIM_PRES_TIME,
                               right=self.exp.screen.center_x,
                               width=s(config.IMG_WIDTH),
                               height=s(config.IMG_HEIGHT),
                               allow_stretch=True, keep_ratio=False)
            right_image = Image(source=trial.current['img_R'],
                                duration=config.STIM_PRES_TIME,
                                left=left_image.right,
                                width=s(config.IMG_WIDTH),
                                height=s(config.IMG_HEIGHT),
                                allow_stretch=True, keep_ratio=False)

        # get new/old judgment
        with Meanwhile():
            Wait(until=left_image.appear_time)
            if config.EEG:
                pulse_fn = LSLPush(server=pulse_server,
                                   val=Ref.getitem(config.EEG_CODES,
                                                    trial.current['cond_trial']))
                Log(name="CAB_PULSES",
                    start_time=pulse_fn.push_time)
                self.eeg_pulse_time = pulse_fn.push_time

            Wait(0.2)
            response = GetResponse(keys=config.RESP_KY,
                                   base_time=left_image.appear_time['time'],
                                   correct_resp=Ref.getitem(config.RESP_KEYS,
                                                            trial.current['resp_correct']))

            # present frame around images to indicate response
            with If(response.pressed != None):
                with Parallel():
                    resp_rect.update(color=config.COLOR_RECT)
                    # add accuracy and RT to lists
                    # (to later calculate performance score)
                    self.accs += [response.correct]
                    self.rts += [response.rt]
            with Else():
                self.accs += [False]
                self.rts += [config.MAX_RT]

        # log data
        Log(trial.current,
            name="cont_ass_bind",
            appearL=left_image.appear_time,
            appearR=right_image.appear_time,
            disappearL=left_image.disappear_time,
            disappearR=right_image.disappear_time,
            resp_acc=response.correct,
            resp_rt=response.rt,
            press=response.press_time,
            pressed=response.pressed,
            block=block,
            fmri_tr_time=self.fmri_tr_time,
            eeg_pulse_time=self.eeg_pulse_time)

    # calculate this block's score
    self.this_score = Func(make_metric, config, self.accs, self.rts)

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
        Wait(1.0)

    # present this block's score to the participant
    Wait(.5)
    with Parallel():
        Rectangle(width=s(config.WIDTH_SCORE_RECT),
                  height=s(config.HEIGHT_SCORE_RECT),
                  color=[144./255., 175./255., 197./255.])
        pbfbC = Label(text=Ref(str, self.this_score.result)+" Points!",
                      font_size=s(config.FINAL_FONT_SIZE))
        Label(text="Your score for this block:",
              font_size=s(config.FINAL_FONT_SIZE), bottom=pbfbC.top + s(10.))
        if config.TOUCH:
            Label(text="Press the screen to continue.",
                  font_size=s(config.FINAL_FONT_SIZE),
                  top=pbfbC.bottom - s(10.))
        else:
            Label(text="Press %s to continue." % cont_key_str,
                  font_size=s(config.FINAL_FONT_SIZE),
                  top=pbfbC.bottom - s(10.))

    with UntilDone():
        Wait(1.5)
        GetResponse(keys=config.CONT_KEY)


if __name__ == "__main__":
    import zipfile
    import os
    if not os.path.isdir("stim"):
        with zipfile.ZipFile("stim.zip", 'r') as zip_ref:
            print("extracting...")
            zip_ref.extractall('stim')

    from smile.common import Experiment
    from smile.startup import InputSubject
    from smile.lsl import init_lsl_outlet
    import config



    config.RESP_KY = ['1', '4']
    config.RESP_KEYS = {'old': '1', 'new': '4'}
    config.CONT_KEY = ['1', '4']
    config.EEG = True

    if config.EEG:
        # Initialize the outlet
        pulse_server = init_lsl_outlet(server_name='MarkerStream',
                                       server_type='Markers',
                                       nchans=1,
                                       suggested_freq=500,
                                       channel_format='int32',
                                       unique_id='COGBATT_LSL_OUT')
    else:
        pulse_server = None

    exp = Experiment(background_color=(.35, .35, .35, 1.0),
                     name="CAB", scale_down=True, scale_box=(1200, 900))

    InputSubject(exp_title="Continuous Associative Binding")
    with Loop(2) as lp:
        exp.rem_only = (lp.i != 0)
        AssBindExp(config,
                   task_dir=os.path.join("."),
                   sub_dir=Ref.object(exp)._subject_dir,
                   block=lp.i+.1,
                   reminder_only=exp.rem_only,
                   pulse_server=pulse_server)
        Wait(1.0)
    Label(text="Task Complete! Please wait for the program to automatically close.",
          font_size=s(config.INST_FONT_SIZE), duration=2.0)
    exp.run()
