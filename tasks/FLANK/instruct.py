# -*- coding: utf-8 -*-
from smile.common import *
from smile.scale import scale as s

from widget import Flanker
from kivy.utils import platform
from trial import Trial, GetResponse
from math import cos, sin, sqrt, pi, radians


def get_instructions(config):
    if len(config.CONT_KEY) > 1:
        cont_key = str(config.CONT_KEY[0]) + " or " + str(config.CONT_KEY[-1])
    else:
        cont_key = str(config.CONT_KEY[0])


    inst = {}
    inst['top_text'] = 'You will be presented with a group of symbols. \n' + \
                       'You will be asked to indicate the direction that the \n' + \
                       '[b]middle arrow is pointing[/b], while ignoring any other symbols. \n\n'

    inst['inst_1'] = '[b]Practice 1:[/b] \n \n' + \
                     'Respond to the arrow in the red circle while ignoring the other symbols. \n'

    inst['inst_2'] = '[b]Practice 2:[/b] \n \n' + \
                     'Now, the group of symbols will appear in different locations around the screen. \n' + \
                     'Look at the arrow inside the red circle and indicate its direction. \n'
    inst['inst_3'] = '[b]Practice 3:[/b] \n \n' + \
                     'The final practice set will look like the actual task. \n' + \
                     'The group of symbols will appear at different locations around the screen. \n' + \
                     'Find the arrow at the center of the group, and indicate its direction. \n' + \
                     'In between responses, please direct your gaze to the cross at the center of the screen. \n'
    if config.TOUCH:
        inst_temp = 'Press the [b]left side of the screen[/b] ' + \
                    'if the arrow is pointing [b]left[/b]. \n' + \
                    'Press the [b]right side of the screen[/b] ' + \
                    'if the arrow is pointing [b]right[/b].\n'
        inst['top_text'] += inst_temp + 'Press the screen to begin.'
        inst['inst_1'] += inst_temp
        inst['inst_2'] += inst_temp + 'Press the screen to begin.'
        inst['inst_3'] += inst_temp + 'Press the screen to begin.'
        inst['to_cont'] = "Press the screen to continue!"
        inst['done'] = 'You have finished the Practice!\nPress the screen to continue!'
    else:
        inst_temp = 'Press the [b]%s[/b] '%(config.RESP_KEYS[0]) + \
                    'key if the arrow is pointing [b]left[/b]. \n' + \
                    'Press the [b]%s[/b] '%(config.RESP_KEYS[-1]) + \
                    'key if the arrow is pointing [b]right[/b].\n'

        inst['top_text'] += inst_temp + 'Press ' + cont_key + ' to begin.'
        inst['inst_1'] += inst_temp
        inst['inst_2'] += inst_temp + 'Press ' + cont_key + ' to begin.'
        inst['inst_3'] += inst_temp + 'Press ' + cont_key + ' to begin.'
        inst['to_cont'] = 'Press ' + cont_key + ' to continue!'
        inst['done'] = 'You have finished the Practice!\nPress ' + cont_key + ' to continue!'


    inst['skip_text'] = "Skip Practice"
    inst['p_fdbk'] = "CORRECT!"
    inst['n_fdbk'] = "INCORRECT!"

    return inst


@Subroutine
def Instruct(self, config, lang="E"):

    inst = Func(get_instructions, config).result

    # with If(practice==True):
    with Parallel():
        if not config.TOUCH:
            MouseCursor(blocking=False)
        with Serial(blocking=False):
            with Parallel():
                toplbl = Label(text=inst['top_text'],
                               markup=True,
                               halign='center',
                               center_x=self.exp.screen.center_x,
                               center_y=self.exp.screen.center_y,
                               font_size=s(config.INST_FONT_SIZE))

                # upper left
                Flanker(center_x=self.exp.screen.center_x - s(400),
                        center_y=toplbl.top + s(125),
                        sep=s(config.CONFIG_SEP), df=s(config.CONFIG_DF),
                        line_width=s(config.LW),
                        stim="__<__\n_<<<_\n<<<<<\n_<<<_\n__<__\n")
                # upper middle
                Flanker(center_x=self.exp.screen.center_x,
                        center_y=toplbl.top + s(125),
                        sep=s(config.CONFIG_SEP), df=s(config.CONFIG_DF),
                        line_width=s(config.LW),
                        stim="__>__\n_><>_\n><<<>\n_><>_\n__>__\n")
                # upper right
                Flanker(center_x=self.exp.screen.center_x + s(400),
                        center_y=toplbl.top + s(125),
                        sep=s(config.CONFIG_SEP), df=s(config.CONFIG_DF),
                        line_width=s(config.LW),
                        stim="__<__\n_<><_\n<><><\n_<><_\n__<__\n")

                # lower left
                Flanker(center_x=self.exp.screen.center_x - s(400),
                        center_y=toplbl.bottom - s(125),
                        sep=s(config.CONFIG_SEP), df=s(config.CONFIG_DF),
                        line_width=s(config.LW),
                        stim="__<__\n_<><_\n<><><\n_<><_\n__<__\n")
                # lower middle
                Flanker(center_x=self.exp.screen.center_x,
                        center_y=toplbl.bottom - s(125),
                        sep=s(config.CONFIG_SEP), df=s(config.CONFIG_DF),
                        line_width=s(config.LW),
                        stim="__>__\n_><>_\n><><>\n_><>_\n__>__\n")
                # lower right
                Flanker(center_x=self.exp.screen.center_x + s(400),
                        center_y=toplbl.bottom - s(125),
                        sep=s(config.CONFIG_SEP), df=s(config.CONFIG_DF),
                        line_width=s(config.LW),
                        stim="__<__\n_<><_\n<>>><\n_<><_\n__<__\n")

            with UntilDone():
                Wait(until=toplbl.appear_time)
                GetResponse(keys=config.CONT_KEY)

            Wait(1.0)

            with Loop([["__<__\n_<<<_\n<<<<<\n_<<<_\n__<__\n", config.RESP_KEYS[0]],
                       ["__>__\n_><>_\n><<<>\n_><>_\n__>__\n", config.RESP_KEYS[0]],
                       ["__<__\n_<><_\n<>>><\n_<><_\n__<__\n", config.RESP_KEYS[-1]],
                       ["__>__\n_><>_\n><><>\n_><>_\n__>__\n", config.RESP_KEYS[-1]]]) as prac_ev:
                Wait(1.0)
                p2 = Trial(config,
                           stim=prac_ev.current[0],
                           center_x=self.exp.screen.center_x,
                           center_y=self.exp.screen.center_y,
                           correct_resp=prac_ev.current[1], condition='+')
                with If(p2.correct):
                    # They got it right
                    Label(text=u"\u2713", color='green', duration=config.FEEDBACK_TIME,
                          font_size=s(config.FEEDBACK_FONT_SIZE),
                          font_name='DejaVuSans.ttf')
                with Else():
                    # they got it wrong
                    Label(text=u"\u2717", color='red',
                          font_size=s(config.FEEDBACK_FONT_SIZE),
                          duration=config.FEEDBACK_TIME, font_name='DejaVuSans.ttf')

            with Meanwhile():
                with Parallel():
                    Ellipse(color='red', size=(s(55),s(55)))
                    Ellipse(color=config.INNER_CIRCLE_COLOR, size=(s(45),s(45)))
                    Label(text=inst['inst_1'],
                          markup=True,
                          halign='center',
                          center_x=self.exp.screen.center_x,
                          center_y=self.exp.screen.center_y + s(300),
                          font_size=s(config.INST_FONT_SIZE))

            Wait(1.0)
            Label(text=inst['inst_2'],
                  markup=True,
                  halign='center',
                  center_x=self.exp.screen.center_x,
                  center_y=self.exp.screen.center_y + s(300),
                  font_size=s(config.INST_FONT_SIZE))
            with UntilDone():
                GetResponse(keys=config.CONT_KEY)


            with Loop([["__<__\n_<><_\n<>>><\n_<><_\n__<__\n", config.RESP_KEYS[1],
                        cos(radians((360./config.NUM_LOCS)*5)), sin(radians((360./config.NUM_LOCS)*5))],
                       ["__<__\n_<><_\n<><><\n_<><_\n__<__\n", config.RESP_KEYS[0],
                        cos(radians((360./config.NUM_LOCS)*1)), sin(radians((360./config.NUM_LOCS)*1))],
                       ["__>__\n_><>_\n><><>\n_><>_\n__>__\n", config.RESP_KEYS[1],
                        cos(radians((360./config.NUM_LOCS)*3.)), sin(radians((360./config.NUM_LOCS)*3.))],
                       ["__>__\n_><>_\n><><>\n_><>_\n__>__\n", config.RESP_KEYS[1],
                        cos(radians((360./config.NUM_LOCS)*4.)), sin(radians((360./config.NUM_LOCS)*4.))],
                       ["__>__\n_>>>_\n>>>>>\n_>>>_\n__>__\n", config.RESP_KEYS[1],
                        cos(radians((360./config.NUM_LOCS)*0)), sin(radians((360./config.NUM_LOCS)*0))],
                       ["__>__\n_><>_\n><<<>\n_><>_\n__>__\n", config.RESP_KEYS[0],
                        cos(radians((360./config.NUM_LOCS)*2)), sin(radians((360./config.NUM_LOCS)*2))]
                      ]) as prac_ev:
                Wait(1.0)
                with Parallel():
                    Ellipse(color='red', size=(s(55),s(55)),
                            center_x=self.exp.screen.center_x + prac_ev.current[2]*s(config.FROM_CENTER),
                            center_y=self.exp.screen.center_y + prac_ev.current[3]*s(config.FROM_CENTER),
                            blocking=False)
                    Ellipse(color=config.INNER_CIRCLE_COLOR, size=(s(45),s(45)),
                            center_x=self.exp.screen.center_x + prac_ev.current[2]*s(config.FROM_CENTER),
                            center_y=self.exp.screen.center_y + prac_ev.current[3]*s(config.FROM_CENTER),
                            blocking=False)
                    p4 = Trial(config,stim=prac_ev.current[0],
                               center_x=self.exp.screen.center_x + prac_ev.current[2]*s(config.FROM_CENTER),
                               center_y=self.exp.screen.center_y + prac_ev.current[3]*s(config.FROM_CENTER),
                               correct_resp=prac_ev.current[1], condition='+')
                with If(p4.correct):
                    # They got it right
                    Label(text=u"\u2713", color='green', duration=config.FEEDBACK_TIME,
                          font_size=s(config.FEEDBACK_FONT_SIZE),
                          font_name='DejaVuSans.ttf')
                with Else():
                    # they got it wrong
                    Label(text=u"\u2717", color='red',
                          font_size=s(config.FEEDBACK_FONT_SIZE),
                          duration=config.FEEDBACK_TIME, font_name='DejaVuSans.ttf')


            Label(text=inst['to_cont'],
                  halign='center',
                  center_x=self.exp.screen.center_x,
                  center_y=self.exp.screen.center_y,
                  font_size=s(config.INST_FONT_SIZE))
            with UntilDone():
                GetResponse(keys=config.CONT_KEY)


            Wait(1.0)
            Label(text=inst['inst_3'],
                  markup=True,
                  halign='center',
                  center_x=self.exp.screen.center_x,
                  center_y=self.exp.screen.center_y + s(200),
                  font_size=s(config.INST_FONT_SIZE))
            with UntilDone():
                GetResponse(keys=config.CONT_KEY)


            with Loop([["__<__\n_<><_\n<>>><\n_<><_\n__<__\n", config.RESP_KEYS[1],
                        cos(radians((360./config.NUM_LOCS)*5)), sin(radians((360./config.NUM_LOCS)*5))],
                       ["__<__\n_<><_\n<><><\n_<><_\n__<__\n", config.RESP_KEYS[0],
                        cos(radians((360./config.NUM_LOCS)*1)), sin(radians((360./config.NUM_LOCS)*1))],
                       ["__>__\n_><>_\n><><>\n_><>_\n__>__", config.RESP_KEYS[1],
                        cos(radians((360./config.NUM_LOCS)*3)), sin(radians((360./config.NUM_LOCS)*3))],
                       ["__>__\n_>>>_\n>>>>>\n_>>>_\n__>__\n", config.RESP_KEYS[1],
                        cos(radians((360./config.NUM_LOCS)*6)), sin(radians((360./config.NUM_LOCS)*6))],
                       ["__>__\n_><>_\n><<<>\n_><>_\n__>__\n", config.RESP_KEYS[0],
                        cos(radians((360./config.NUM_LOCS)*2)), sin(radians((360./config.NUM_LOCS)*2))]
                      ]) as prac_ev:
                Wait(1.0)
                p5 = Trial(config, stim=prac_ev.current[0],
                           center_x=self.exp.screen.center_x + prac_ev.current[2]*s(config.FROM_CENTER),
                           center_y=self.exp.screen.center_y + prac_ev.current[3]*s(config.FROM_CENTER),
                           correct_resp=prac_ev.current[1], condition='+')

                with If(p5.correct):
                    # They got it right
                    Label(text=u"\u2713", color='green', duration=config.FEEDBACK_TIME,
                          font_size=s(config.FEEDBACK_FONT_SIZE),
                          center_y=self.exp.screen.center_y + s(50),
                          font_name='DejaVuSans.ttf')
                with Else():
                    # they got it wrong
                    Label(text=u"\u2717", color='red',
                          font_size=s(config.FEEDBACK_FONT_SIZE),
                          center_y=self.exp.screen.center_y + s(50),
                          duration=config.FEEDBACK_TIME, font_name='DejaVuSans.ttf')
            with Meanwhile():
                Label(text="+", font_size=s(config.ORIENT_FONT_SIZE))

        with Serial(blocking=False):
            with ButtonPress():
                Button(text=inst['skip_text'], right=self.exp.screen.width,
                       bottom=0, width=s(config.SKIP_SIZE[0]),
                       height=s(config.SKIP_SIZE[1]), blocking=False,
                       font_size=s(config.SKIP_FONT_SIZE))

    Wait(1.0)

    Label(text=inst['done'],
          halign='center',
          center_x=self.exp.screen.center_x,
          center_y=self.exp.screen.center_y,
          font_size=s(config.INST_FONT_SIZE))
    with UntilDone():
        GetResponse(keys=config.CONT_KEY)
