from smile.common import *
import os
from smile.scale import scale as s
from GetResponse import GetResponse

# present instructions
@Subroutine
def Instruct(self, config, text_names):#, resp_keys, touch, font_size):

    texts = get_text(config)
    with Parallel():
        if not config.TOUCH:
            MouseCursor(blocking=False)
        with Serial(blocking=False):
            for doc in text_names:
                with Parallel():
                    title = Label(text='Memory Task Instructions',
                                  font_size=s(config.INST_TITLE_FONT_SIZE),
                                  text_size=(s(config.TEXT_SIZE_WIDTH), None),
                                  top=self.exp.screen.center_y + s(415))

                # image != None for 4 example slides
                    with If(texts[doc]['image'] != None):
                        image = Image(source=texts[doc]['image'],
                                      top=(title.bottom - s(10)),
                                      width=s(config.INST_IMG_WIDTH),
                                      height=s(config.INST_IMG_HEIGHT),
                                      allow_stretch=True, keep_ratio=False)
                    with If(texts[doc]['image'] != None):
                       Label(text=texts[doc]['text'],
                             font_size=s(config.INST_FONT_SIZE),
                             text_size=(s(config.TEXT_SIZE_WIDTH), None),
                             top=(image.bottom - s(10)))

                 # image == None for first and last slides (instructions and reminder)
                    with If(texts[doc]['image'] == None):
                        Label(text=texts[doc]['text'],
                              text_size=(s(config.TEXT_SIZE_WIDTH), None),
                              font_size=s(config.INST_FONT_SIZE),
                              top=(title.bottom - s(10)))

                with UntilDone():
                    Wait(1.0)
                    GetResponse(keys=texts[doc]['keys'])

                #RstDocument(text=texts[doc]['text'],
                            #width=self.exp.screen.height,
                            #height=self.exp.screen.height,
                            #base_font_size=s(config.RST_FONT_SIZE))


        with Serial(blocking=False):
            with ButtonPress():
                Button(text="Skip Practice", right=self.exp.screen.width,
                       bottom=0, width=s(config.SKIP_SIZE[0]),
                       height=s(config.SKIP_SIZE[1]), blocking=False,
                       font_size=s(config.SKIP_FONT_SIZE))
    Wait(2.0)


# this function reads in the text for each instruction slide and dynamically changes it based on response keys
def get_text(config):#resp_keys, touch):

    # dictionary containing the text for each instruction slide
    inst = {}

    inst['main'] = 'In the memory task you will see pairs of objects side by side and be asked to indicate whether each pair is "new" or "old."' + \
                    'A pair is "old" only if it is EXACTLY the same as a pair you saw earlier in the task. ' + \
                    'Be very careful, because sometimes you will have seen both objects, but not in that exact pairing. ' + \
                    'If the objects are paired differently, or if you have not seen the objects before, the pair is "new." \n\n' + \
                    'You will use both of your hands to respond. If the pair is "old," %s with one hand; ' + \
                    'if the pair is "new," %s with your other hand. \n\n' + \
                    'You will need to make a response for every pair that you see. ' + \
                    'Please respond as accurately as possible, but you will only have 2.5 seconds to respond, so don\'t wait too long! \n\n' + \
                    '%s to see some examples. '

    inst['ex1'] = 'Here is an example of a pair of objects. \n\n' + \
                  'You have not seen these objects before in the task, ' + \
                  'so the correct response would be to %s which indicates that the pair is "new." \n\n' + \
                  '%s to see the next example.'

    inst['ex2'] = 'You have not seen the objects in this pair in the task, ' + \
                  'so the correct response is again to %s indicating that the pair is "new." \n\n' + \
                  '%s to see the next example.'


    inst['ex3'] = 'In this example, you have seen these objects before, and in this exact pairing, ' + \
                    'so the correct response is to %s indicating that the pair is "old." \n\n' + \
                    '%s to see the next example.'

    inst['ex4'] = 'This one is tricky! You saw both of these objects before, but not in the same pairing. ' + \
                    'Because the pairing is different, the correct response is to %s indicating that the pair is "new." \n\n' + \
                    '%s to continue. '

    inst['remind'] = 'It is now time for the memory task. \n\n' + \
                    'Remember, %s with one hand if a pair is EXACTLY the same as one that you saw earlier in the task; ' + \
                    'if ANYTHING about the pair is new, %s with your other hand. \n\n' + \
                    '%s to begin. '

    # dictionary containing image path, response keys, and text for each slide
    texts = {'main': {'image': None,
                      'keys': [config.RESP_KEYS['new'], config.RESP_KEYS['old']],
                      'text': inst['main']},
            'ex1': {'image': str(config.resource_path(os.path.join(config.TASK_DIR, "inst", "examples", "beehouse.jpg"))),
                    'keys': [config.RESP_KEYS['new']],
                    'text': inst['ex1']},
            'ex2': {'image': str(config.resource_path(os.path.join(config.TASK_DIR, "inst", "examples", "canoejoystick.jpg"))),
                    'keys': [config.RESP_KEYS['new']],
                    'text': inst['ex2']},
            'ex3': {'image': str(config.resource_path(os.path.join(config.TASK_DIR, "inst", "examples", "beehouse.jpg"))),
                    'keys': [config.RESP_KEYS['old']],
                    'text': inst['ex3']},
            'ex4': {'image': str(config.resource_path(os.path.join(config.TASK_DIR, "inst", "examples", "beejoystick.jpg"))),
                    'keys': [config.RESP_KEYS['new']],
                    'text': inst['ex4']},
            'remind': {'image': None,
                       'keys': [config.RESP_KEYS['new'], config.RESP_KEYS['old']],
                       'text': inst['remind']}}

    #texts = {'main': {'file': 'inst.rst', 'keys': [config.RESP_KEYS['new'], config.RESP_KEYS['old']]},
            #'ex1': {'file': 'ex1.rst', 'keys': [config.RESP_KEYS['new']]},
            #'ex2': {'file': 'ex2.rst', 'keys': [config.RESP_KEYS['new']]},
            #'ex3': {'file': 'ex3.rst', 'keys': [config.RESP_KEYS['old']]},
            #'ex4': {'file': 'ex4.rst', 'keys': [config.RESP_KEYS['new']]},
            #'remind': {'file': 'remind.rst', 'keys': [config.RESP_KEYS['new'], config.RESP_KEYS['old']]}}

    if config.TOUCH:
        texts['main']['replacements'] = ("touch the LEFT side of the screen",
                                         "touch the RIGHT side of the screen",
                                         "Touch the screen")
        texts['ex1']['replacements'] = ("touch the RIGHT side of the screen,",
                                        "Touch the RIGHT side of the screen",)
        texts['ex2']['replacements'] = ("touch the RIGHT side of the screen,",
                                        "Touch the RIGHT side of the screen")
        texts['ex3']['replacements'] = ("touch the LEFT side of the screen,",
                                        "Touch the LEFT side of the screen")
        texts['ex4']['replacements'] = ("touch the RIGHT side of the screen,",
                                        "Touch the RIGHT side of the screen")
        texts['remind']['replacements'] = ("touch the LEFT side of the screen",
                                           "touch the RIGHT side of the screen",
                                           "Touch the screen")

    else:
        texts['main']['replacements'] = ("press the %s key" %config.RESP_KEYS['old'], "press %s key" %config.RESP_KEYS['new'],
                                            "Press the %s or %s key" %(config.RESP_KEYS['old'], config.RESP_KEYS['new']))
        texts['ex1']['replacements'] = ("press %s," %config.RESP_KEYS['new'],
                                        "Press the %s key" %config.RESP_KEYS['new'])
        texts['ex2']['replacements'] = ("press %s," %config.RESP_KEYS['new'],
                                        "Press the %s key" %config.RESP_KEYS['new'])
        texts['ex3']['replacements'] = ("press %s," %config.RESP_KEYS['old'],
                                        "Press the %s key" %config.RESP_KEYS['old'])
        texts['ex4']['replacements'] = ("press %s," %config.RESP_KEYS['new'],
                                        "Press the %s key" %config.RESP_KEYS['new'])
        texts['remind']['replacements'] = ("press %s key" %config.RESP_KEYS['old'],
                                           "press %s key" %config.RESP_KEYS['new'],
                                            "Press the %s or %s key" %(config.RESP_KEYS['old'],
                                                                        config.RESP_KEYS['new']))


    for doc in texts:
        texts[doc]['text'] = texts[doc]['text'] %texts[doc]['replacements']
        #texts[doc]['text'] = open(config.resource_path(os.path.join(config.TASK_DIR, "inst", texts[doc]['file']))).read() %texts[doc]['replacements']
    return texts
