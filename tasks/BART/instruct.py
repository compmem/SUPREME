# -*- coding: utf-8 -*-

from smile.common import *
from smile.scale import scale as s
from inst.computer import computer_list
from inst.mobile import mobile_list

from list_gen import add_air
from trial import BARTSub, GetResponse

import os


@Subroutine
def Instruct(self, config, run_num, sub_dir, task_dir=None,
             full_instructions=True, practice=True, lang="E",):

    if len(config.CONT_KEY) > 1:
        cont_key_str = str(config.CONT_KEY[0]) + " or " + str(config.CONT_KEY[-1])
    else:
        cont_key_str = str(config.CONT_KEY[0])

    if config.TOUCH:
        with Loop(computer_list) as instruction:
            txt = instruction.current
            with Parallel():
                with If((instruction.i==3)):
                    Label(text=txt%(config.TOUCH_INST[0],
                                    config.TOUCH_INST[-1]),
                          halign='left',
                          font_size=s(config.LABEL_FONT_SIZE))
                with Elif((instruction.i==7)):
                    Label(text=txt%(config.NUM_BALLOONS),
                          halign='left',
                          font_size=s(config.LABEL_FONT_SIZE))
                with Elif((instruction.i==8)):
                    Label(text=txt%(config.NUM_BAGS,
                                    config.BALLOONS_PER_BAG),
                          halign='left',
                          font_size=s(config.LABEL_FONT_SIZE))
                with Else():
                    Label(text=txt,
                          halign='left',
                          font_size=s(config.LABEL_FONT_SIZE))
                Label(text='Press %s to continue'%(config.CONT_KEY_STR),
                      halign='left',
                      bottom=(self.exp.screen.center_x,0),
                      font_size=s(config.LABEL_FONT_SIZE))
            with UntilDone():
                Wait(.5)
                GetResponse(keys=config.CONT_KEY)

    else:
        with Parallel():
            MouseCursor(blocking=False)
            with Serial(blocking=False):
                with If(full_instructions):
                    with Loop(computer_list) as instruction:
                        txt = instruction.current
                        with Parallel():
                            with If((instruction.i==2)):
                                with Parallel():
                                    img2 = Image(source=config.INST2_IMG_PATH,
                                                 top=self.exp.screen.height,
                                                 keep_ratio=True, allow_stretch=True,
                                                 width=s(1000))
                                    lbl2 = Label(text=txt%(config.KEY_TEXT[0],
                                                           config.KEY_TEXT[-1]),
                                                 halign='left', top=img2.bottom + s(100),
                                                 font_size=s(config.LABEL_FONT_SIZE))
                                    Label(text='Press %s to continue'%(config.CONT_KEY_STR),
                                          halign='left',
                                          top=lbl2.bottom,
                                          font_size=s(config.LABEL_FONT_SIZE))
                            with Else():
                                with Parallel():
                                    lbl1 = Label(text=txt,
                                                 halign='left',
                                                 font_size=s(config.LABEL_FONT_SIZE))
                                    Label(text='Press %s to continue'%(config.CONT_KEY_STR),
                                          halign='left',
                                          top=lbl1.bottom - s(75),
                                          font_size=s(config.LABEL_FONT_SIZE))
                        with UntilDone():
                            Wait(.5)
                            GetResponse(keys=config.CONT_KEY)

                with If(practice):

                    Label(text="You will now have a short practice bag of balloons.\n" +
                               "Please note how the money in the bank drops until you" +
                               " make a decision.\nPress %s to continue." % (cont_key_str),
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

                    Wait(1.)
                    # Loop over practice blocks
                    with Loop(number_of_sets):
                        Wait(.5, jitter=.5)

                        # Calling listgen as 'bags'
                        bg = Func(add_air,
                                  total_number_of_balloons=len(config.PRACTICE_SETUP),
                                  num_ranges=len(config.PRACTICE_SETUP),
                                  balloon_setup=config.PRACTICE_SETUP,
                                  randomize=config.RANDOMIZE_BALLOON_NUM,
                                  reward_low=config.REWARD_LOW,
                                  reward_high=config.REWARD_HIGH,
                                  subject_directory=sub_dir,
                                  practice=True,
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
                                              trkp_press_time=self.trkp_press_time)
                            self.balloon_number_session += 1
                            self.grand_total = Balloon.grand_total
                        self.block_tic += 1

                        self.set_number += 1

                    Wait(.5)
                    Label(text='You have completed the practice.\n' +
                               'Press %s to continue.' % (cont_key_str),
                          halign='center',
                          font_size=s(config.LABEL_FONT_SIZE))
                    with UntilDone():
                        Wait(1.5)
                        GetResponse(keys=config.CONT_KEY)
            with Serial(blocking=False):
                with ButtonPress():
                    Button(text="Skip Practice", width=s(config.SKIP_SIZE[0]),
                           bottom=0, right=self.exp.screen.width,
                           height=s(config.SKIP_SIZE[1]),
                           font_size=s(config.SKIP_FONT_SIZE))
