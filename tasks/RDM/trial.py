from smile.common import *
from smile.scale import scale as s
from smile.lsl import LSLPush


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
          cross,
          config,
          correct_resp=None,
          incorrect_resp=None,
          color='white',
          num_dots=100,
          right_coherence=0.0,
          left_coherence=0.0,
          pulse_server=None
          ):


    self.eeg_pulse_time = None
    with Serial():
        # present the dots
        with Parallel():
            cross.update(color=(.35, .35, .35, 1.0))
            md = MovingDots(color=color, scale=s(config.SCALE),
                            num_dots=num_dots, radius=s(config.RADIUS),
                            motion_props=[{"coherence": right_coherence,
                                           "direction": 0,
                                           "direction_variance": 0},
                                          {"coherence": left_coherence,
                                           "direction": 180,
                                           "direction_variance": 0}],
                            lifespan=config.LIFESPAN,
                            lifespan_variance=config.LIFESPAN_VAR,
                            speed=s(config.SPEED))
        with UntilDone():
            # Collect key response
            Wait(until=md.appear_time)
            if config.EEG:
                pulse_fn = LSLPush(server=pulse_server,
                                   val=Ref.getitem(config.EEG_CODES,
                                                    "code"))
                Log(name="RDM_PULSES",
                    start_time=pulse_fn.push_time)
                self.eeg_pulse_time = pulse_fn.push_time

            gr = GetResponse(correct_resp=correct_resp,
                        base_time=md.appear_time['time'],
                        duration=config.RESPONSE_DURATION,
                        keys=config.RESP_KEYS)
        self.pressed = gr.pressed
        self.press_time = gr.press_time
        self.rt = gr.rt
        self.correct = gr.correct
        # give feedback
        with If(self.pressed == correct_resp):
            # They got it right
            Label(text=u"\u2713", color='green', duration=config.FEEDBACK_TIME,
                  font_size=s(config.FEEDBACK_FONT_SIZE),
                  font_name='DejaVuSans.ttf')
        with Elif(self.pressed == incorrect_resp):
            # they got it wrong
            Label(text=u"\u2717", color='red',
                  font_size=s(config.FEEDBACK_FONT_SIZE),
                  duration=config.FEEDBACK_TIME, font_name='DejaVuSans.ttf')
        with Else():
            # too slow
            Label(text="Too Slow!", font_size=s(config.FEEDBACK_FONT_SIZE),
                  duration=config.FEEDBACK_TIME*2.)

    # bring the cross back
    cross.update(color=config.CROSS_COLOR)

    # save vars
    self.appear_time = md.appear_time
    self.disappear_time = md.disappear_time
    self.refresh_rate = md.widget.refresh_rate
