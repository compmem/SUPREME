from smile.common import *
from smile.scale import scale as s
from smile.lsl import LSLPush
from widget import Flanker


@Subroutine
def GetResponse(self,
                keys,
                base_time=None,
                correct_resp=None,
                duration=None):
    self.pressed = None
    self.rt = None
    self.correct = None
    self.press_time = None
    with Parallel():
        kp = KeyPress(base_time=base_time,
                      keys=keys,
                      correct_resp=correct_resp,
                      duration=duration,
                      blocking=False)
        with Serial(blocking=False):
            with ButtonPress(correct_resp=correct_resp,
                             base_time=base_time,
                             duration=duration,
                             ) as bp:
                Button(width=self.exp.screen.width*.45,
                       height=self.exp.screen.height,
                       name=keys[0], text="",
                       left=0, bottom=0, background_color=(0, 0, 0, 0))
                Button(width=self.exp.screen.width*.45, height=self.exp.screen.height,
                       name=keys[-1], text="", right=self.exp.screen.width,
                       bottom=0, background_color=(0, 0, 0, 0))

    self.pressed = Ref.cond((bp.pressed == ''), kp.pressed, bp.pressed)
    self.rt = Ref.cond((bp.pressed == ''), kp.rt, bp.rt)
    self.correct = Ref.cond((bp.pressed == ''), kp.correct, bp.correct)
    self.press_time = Ref.cond((bp.pressed == ''), kp.press_time, bp.press_time)


@Subroutine
def Trial(self,
          config,
          stim,
          center_x,
          center_y,
          condition,
          correct_resp=None,
          color='white',
          pulse_server=None):

    self.eeg_pulse_time = None
    # present the dots
    fl = Flanker(center_x=center_x, center_y=center_y,
            sep=s(config.CONFIG_SEP), df=s(config.CONFIG_DF), line_width=s(config.LW),
            stim=stim)
    with UntilDone():
        # Collect key response
        Wait(until=fl.appear_time)
        if config.EEG:
            pulse_fn = LSLPush(server=pulse_server,
                               val=Ref.getitem(config.EEG_CODES, condition))
            Log(name="FLKR_PULSES",
                start_time=pulse_fn.push_time)
            self.eeg_pulse_time = pulse_fn.push_time
        gr = GetResponse(correct_resp=correct_resp,
                         base_time=fl.appear_time['time'],
                         duration=config.RESPONSE_DURATION,
                         keys=config.RESP_KEYS)

    self.pressed = gr.pressed
    self.press_time = gr.press_time
    self.rt = gr.rt
    self.correct = gr.correct

    # save vars
    self.appear_time = fl.appear_time
    self.disappear_time = fl.disappear_time
