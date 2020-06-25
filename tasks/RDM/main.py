# -*- coding: utf-8 -*-

# load all the states
from smile.common import Log, Label, Wait, Ref, Rectangle, Func, Debug, Loop, \
                         UntilDone, If, Else, Parallel, Subroutine, KeyPress
from smile.scale import scale as s
from smile.lsl import LSLPush
from list_gen import gen_moving_dot_trials
from math import log
from trial import Trial, GetResponse
from instruct import Instruct
import version


def _get_score(config, corr_trials, num_trials, rt_trials):
    min_rt = log(config.FAST_TIME+1.0)
    max_rt = log(config.SLOW_TIME+1.0)

    acc_tf = (corr_trials/num_trials - .5)/.5
    rt_list = []
    for x in rt_trials:
        rt_list.append((max_rt - log(x + 1.0))/(max_rt - min_rt))

    # transform rts
    rts_tf = sum(rt_list)/len(rt_list)
    # calculate performance measures
    perf = acc_tf * rts_tf

    if perf < 0:
        perf = 0.

    return int(perf * 100)


@Subroutine
def RDMExp(self, config, run_num=0, lang="E", pulse_server=None):

    if len(config.CONT_KEY) > 1:
        cont_key_str = str(config.CONT_KEY[0]) + " or " + \
                       str(config.CONT_KEY[-1])
    else:
        cont_key_str = str(config.CONT_KEY[0])

    res = Func(gen_moving_dot_trials, config)

    Log(name="RDMinfo",
        version=version.__version__,
        author=version.__author__,
        date_time=version.__date__,
        email=version.__email__)

    self.md_blocks = res.result

    Instruct(config, lang=lang)
    Wait(1.0)

    self.trials_corr = 0.
    self.trials_num = 0.
    self.trials_rt = []
    self.trkp_press_time = None

    # FMRI STUFF
    if config.FMRI:
        KeyPress(keys=config.FMRI_TECH_KEYS)
        Label(text="Waiting for Experimenter...",
              font_size=s(config.INST_FONT_SIZE))
        with UntilDone():
            trkp = KeyPress(keys=config.FMRI_TR)
            Log(name="FLKR_TR",
                press_time=trkp.press_time)
            self.trkp_press_time = trkp.press_time
        Label(text="+", font_size=s(config.CROSS_FONTSIZE),
              duration=config.INIT_TR_WAIT)

    # loop over blocks
    with Loop(self.md_blocks) as block:
        # put up the fixation cross
        cross = Label(text='+', color=config.CROSS_COLOR,
                      font_size=s(config.CROSS_FONTSIZE))
        with UntilDone():
            # loop over trials
            with Loop(block.current) as trial:
                # Wait the ISI
                Wait(config.ISI, jitter=config.JITTER)

                # do the trial
                mdt = Trial(cross,
                            config,
                            correct_resp=trial.current['correct_resp'],
                            incorrect_resp=trial.current['incorrect_resp'],
                            num_dots=config.NUM_DOTS,
                            right_coherence=trial.current['right_coherence'],
                            left_coherence=trial.current['left_coherence'],
                            pulse_server=pulse_server)

                self.cor = [trial.current['left_coherence'],
                            trial.current['right_coherence']]
                self.trials_num = self.trials_num + 1.

                with If(self.cor[0] != self.cor[1]):
                    with If(mdt.correct):
                        # If they got it right, add 1 to
                        # the final total correct
                        self.trials_corr = self.trials_corr + 1.
                with Else():
                    # Add .5 for chance performance on all equal coherence
                    # trials
                    self.trials_corr = self.trials_corr + .5

                with If(mdt.rt == None):
                    self.trials_rt = self.trials_rt + [config.SLOW_TIME]
                with Else():
                    self.trials_rt = self.trials_rt + [mdt.rt]

                # log what we need
                Log(trial.current,
                    name='MD',
                    run_num=run_num,
                    appear_time=mdt.appear_time,
                    disappear_time=mdt.disappear_time,
                    pressed=mdt.pressed,
                    press_time=mdt.press_time,
                    rt=mdt.rt,
                    correct=mdt.correct,
                    refresh_rate=mdt.refresh_rate,
                    fmri_tr_time=self.trkp_press_time,
                    eeg_pulse_time=mdt.eeg_pulse_time)

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

    self.block_score = Func(_get_score, config, self.trials_corr,
                            self.trials_num, self.trials_rt)
    with Parallel():
        Rectangle(width=s(config.WIDTH_SCORE_RECT),
                  height=s(config.HEIGHT_SCORE_RECT),
                  color=[144./255., 175./255., 197./255.])
        pbfbC = Label(text=Ref(str, self.block_score.result)+" Points!",
                      font_size=s(config.FINAL_FONT_SIZE))
        Label(text="Your score for this block:",
              font_size=s(config.FINAL_FONT_SIZE), bottom=pbfbC.top + s(10.))
        if config.TOUCH:
            Label(text="Press the screen to continue.",
                  font_size=s(config.FINAL_FONT_SIZE),
                  top=pbfbC.bottom - s(10.))
        else:
            Label(text="Press %s to continue." % (cont_key_str),
                  font_size=s(config.FINAL_FONT_SIZE),
                  top=pbfbC.bottom - s(10.))

    with UntilDone():
        Wait(1.5)
        GetResponse(keys=config.CONT_KEY)

    Log(name="moving_dots_block_score",
        block_score=self.block_score)
    Wait(.5)


if __name__ == "__main__":
    import config
    from smile.startup import InputSubject
    from smile.common import Experiment
    from smile.lsl import init_lsl_outlet

    config.FMRI = False
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

    exp = Experiment(background_color=(.35, .35, .35, 1.0),
                     name="RDMExp", scale_down=True, scale_box=(1200, 900))
    Wait(1.0)
    InputSubject(exp_title="RandomDotMotion")
    RDMExp(config, run_num=0, lang="E",
           pulse_server=pulse_server)
    Label(text="Task Complete! Please wait for the program to automatically close.",
          font_size=s(config.INST_FONT_SIZE), duration=2.0)

    exp.run()
