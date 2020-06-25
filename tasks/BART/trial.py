from smile.common import *
from smile.scale import scale as s
from smile.lsl import LSLPush
import os


# adding button/key press subroutine
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
def BARTSub(self,
            config,
            balloon=[],
            block=0,
            set_number=0,
            balloon_number_session=0,
            grand_total=0.00,
            subject="test000",
            run_num=0,
            trkp_press_time=None,
            pulse_server=None):
    BANK_IMG = os.path.join(config.TASK_DIR, "stim", "Bank.png")
    POP_IMG = os.path.join(config.TASK_DIR, 'stim', 'Pop.png')

    #sets updating index from main.py
    self.set_number = set_number

    #setting up necessary refs for experiment
    self.subject = subject

    #self.reward_dist_type = self.balloon['reward_dist']
    self.total = 0.00
    self.grand_total = grand_total
    self.curr_balloon_size = config.BALLOON_START_SIZE

    self.eeg_pulse_time = None

    ###################################################################
    #Conditional that breaks loop when false.
    self.pressed_key = True
    if (config.FLIP_BART):
        pos = -1
    else:
        pos = 1

    # Generating images,labels, and objects on screen
    with Parallel():

        Nozzle = Triangle(color=balloon['color'],
                          points=[self.exp.screen.center_x,
                                  self.exp.screen.center_y + s(config.TRIAN_SIZE),
                                  self.exp.screen.center_x - s(config.TRIAN_SIZE)/2.,
                                  self.exp.screen.center_y,
                                  self.exp.screen.center_x + s(config.TRIAN_SIZE)/2.,
                                  self.exp.screen.center_y])
        Balloon = Ellipse(color=balloon['color'],
                          size=(s(self.curr_balloon_size), s(self.curr_balloon_size)),
                          bottom=Nozzle.top-s(18))
        Bank_outline1 = Rectangle(color=(0,0,0,0),
                         center_x=self.exp.screen.center_x + (s(250)*pos),
                         center_y=self.exp.screen.center_y - s(75),
                         width=s(config.BANK_WIDTH) + s(5),
                         height=s(config.BANK_HEIGHT) + s(5))
        Bank = Image(source=BANK_IMG,
                     center=Bank_outline1.center,
                     allow_stretch=True, keep_ratio=False,
                     width=s(config.BANK_WIDTH),
                     height=s(config.BANK_HEIGHT))
        Gtotal = Label(text=Ref(str.format, '${:,.2f}', self.grand_total),
                      font_size=s(config.TOTAL_FONT_SIZE),
                      center=Bank.center)
        Air_line = Rectangle(color='white',
                             center_x=self.exp.screen.center_x,
                             top=Nozzle.bottom + s(25),
                             width=s(config.NOZZLE_WIDTH),
                             height=s(config.NOZZLE_HEIGHT))
        Air_pump_outline = Rectangle(color='white',
                             center_x=self.exp.screen.center_x,
                             top=Air_line.bottom,
                             width=s(config.AIR_PUMP_WIDTH) + s(5),
                             height=s(config.AIR_PUMP_HEIGHT) + s(5))
        Air_pump = Rectangle(color='black',
                             center=Air_pump_outline.center,
                             width=s(config.AIR_PUMP_WIDTH),
                             height=s(config.AIR_PUMP_HEIGHT))
        Total = Label(text=Ref(str.format, '${:.2f}', self.total),
                      font_size=s(config.TOTAL_FONT_SIZE),
                      color='black',
                      center=Balloon.center)
        LChoice_label = Label(text='%s to pump'%config.KEY_TEXT[0],
                              font_size=s(config.TRIAL_FONT_SIZE),
                              color='white', halign="center",
                              top=Air_pump_outline.bottom - s(10),
                              )
        RChoice_label = Label(text='%s to collect'%config.KEY_TEXT[1],
                          font_size=s(config.TRIAL_FONT_SIZE),
                          color='white', halign="center",
                          center_x=Bank_outline1.center_x,
                          top=Bank_outline1.bottom - s(1))


    with UntilDone():
        with Loop(Ref(len,balloon['pop'])) as trial:
            with If(self.pressed_key==True):
                Wait(0.5, jitter=.3)
                Fixation_cross = Label(text='+',
                                       font_size=s(config.CROSS_FONT_SIZE),
                                       color=config.CROSS_COLOR,
                                       center=Air_pump.center)
                with UntilDone():
                    Wait(0.5, jitter=0.3)
                Reward_label = Label(text=Ref(str.format, '${:,.2f}', balloon['rewards'][trial.i]),
                                     font_size=s(config.TRIAL_FONT_SIZE),
                                     color='white',
                                     center=Air_pump.center)
                with UntilDone():
                    Wait(until=Reward_label.appear_time)
                    if config.EEG:
                        pulse_fn = LSLPush(server=pulse_server,
                                           val=Ref.getitem(config.EEG_CODES, "code"))
                        Log(name="BARTUVA_PULSES",
                            start_time=pulse_fn.push_time)
                        self.eeg_pulse_time = pulse_fn.push_time
                    with Serial():
                        Gtotal.update(color='white')
                        Wait(until=Reward_label.appear_time)
                        with Loop():
                            Wait(0.4)
                            with Parallel():
                                self.grand_total -= 0.01
                                Gtotal.update(text=Ref(str.format, '${:,.2f}', self.grand_total),
                                              color='yellow')
                            Wait(0.05)
                            Gtotal.update(color='white')
                    # get response using subroutine
                    with UntilDone():
                        gr = GetResponse(keys=config.RESP_KEYS,
                                         base_time=Reward_label.appear_time['time'])
                        self.grand_total += 0.01
                        Gtotal.update(text=Ref(str.format, '${:,.2f}', self.grand_total),
                                      color='white')
                        self.pressed = gr.pressed
                        self.press_time = gr.press_time
                        self.rt = gr.rt

                    with If(self.pressed == config.RESP_KEYS[0]):
                        with If(balloon['pop'][trial.i] == 0):
                            self.total = 0
                            with Serial():
                                Reward_label.slide(duration=config.REWARD_SLIDE_DURATION,
                                                   center=Balloon.center,
                                                   color=(0,0,0,0))
                                with Parallel():
                                    Total.slide(duration=0.5,
                                                center_y=Balloon.center_y)
                                    Balloon.slide(duration=0.5,
                                                  size=(s(config.BALLOON_EXPLODE_SIZE[0]),
                                                        s(config.BALLOON_EXPLODE_SIZE[1])),
                                                  color=(0,0,0,0))
                                with Parallel():
                                    Pop_image = Image(source=POP_IMG,
                                                      duration=config.POP_ANIMATION_DURATION,
                                                      size=(s(config.POP_SIZE[0]), s(config.POP_SIZE[1])),
                                                      center=Balloon.center)
                                    Total.update(color=(0,0,0,0))
                                    Nozzle.update(color=(0,0,0,0))

                                Gtotal.update(text=Ref(str.format, '${:,.2f}', self.grand_total))
                                self.pop_status='popped'
                                self.pressed_key = False

                        with Elif(balloon['pop'][trial.i] != 0):

                            with If(balloon['rewards'][trial.i] >= 0):
                                self.total +=  balloon['rewards'][trial.i]

                                with Parallel():
                                    self.curr_balloon_size += s(config.INC_BALLOON_SIZE)

                                    with Serial():
                                        Reward_label.slide(duration=config.REWARD_SLIDE_DURATION,
                                                           center=Balloon.center,
                                                           color=(0,0,0,0))

                                        with Parallel():
                                            Balloon.slide(duration=config.BALLOON_GROWTH_DURATION,
                                                          size=(s(self.curr_balloon_size),s(self.curr_balloon_size)),
                                                          #center_y=Balloon.center_y + s(config.INC_BALLOON_SIZE))
                                                          )
                                            Total.slide(duration=config.BALLOON_GROWTH_DURATION,
                                                        center_y=Balloon.center_y
                                                        )

                                        Total.update(text=Ref(str.format, '${:,.2f}', self.total))

                                    self.pop_status = 'not_popped'

                            with Elif(balloon['rewards'][trial.i]<0):

                                with Serial():
                                    Reward_label.slide(duration=config.PUMP_DURATION,
                                                       center=Bank.center,
                                                       color=(0,0,0,0))
                                    self.grand_total +=  balloon['rewards'][trial.i]
                                    Gtotal.update(text=Ref(str.format, '${:,.2f}', self.grand_total))
                                    self.pop_status = 'buy-in'

                    with Elif(self.pressed == config.RESP_KEYS[-1]):

                        with Parallel():
                            Total.update(text=Ref(str.format, '${:,.2f}', self.total))

                            with Serial():
                                Nozzle.update(color=(0,0,0,0))

                                with Parallel():
                                    Total.slide(duration=config.COLLECT_DURATION,
                                                center=Bank.center)
                                    Balloon.slide(duration=config.COLLECT_DURATION,
                                                  center=Bank.center)

                                Balloon.update(color=(0,0,0,0))
                                Total.update(color=(0,0,0,0))
                                self.grand_total += self.total
                                Gtotal.update(text=Ref(str.format, '${:,.2f}', self.grand_total))
                                self.pop_status="not_popped"

                        self.pressed_key = False

                #Logging trial info
                Log(name="OBART",
                    subject=self.subject,
                    run_num=run_num,
                    balloon_number_session=balloon_number_session,
                    set_number=self.set_number,
                    balloon_number=balloon['balloon_number'],
                    block=block,
                    bag_ID_number=balloon['bag_ID_number'],
                    balloon_in_bag=balloon['balloon_in_bag'],
                    trial=trial.i,
                    pop_range=balloon['pump_range'],
                    pop_status=self.pop_status,
                    reward_appear_time=Reward_label.appear_time,
                    rt=self.rt,
                    press_time=self.press_time,
                    key_pressed=self.pressed,
                    total=self.total,
                    grand_total=self.grand_total,
                    rewards=balloon['rewards'][trial.i],
                    balloon_size=self.curr_balloon_size,
                    trkp_press_time=trkp_press_time,
                    eeg_pulse_time=self.eeg_pulse_time)
                    # reward_dist_type=self.reward_dist_type[trial.i],

    Wait(config.INTER_PUMP_DURATION)
    grand_total_carryover = self.grand_total
