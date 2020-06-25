from smile.video import WidgetState
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ListProperty, StringProperty
from kivy.graphics import Point, Color, Line
from math import cos, sin, sqrt, pi


@WidgetState.wrap
class Flanker(Widget):
    """Display a box filled with random square dots.

    Parameters
    ----------
    num_dots : integer
        Number of dots to draw
    pointsize : integer
        Radius of dot (see `Point`)
    color : tuple or string
        Color of dots
    backcolor : tuple or string
        Color of background rectangle

    """
    color = ListProperty([1, 1, 1, 1])
    stim = StringProperty("<<><<")
    sep = NumericProperty(10)
    df = NumericProperty(2)
    line_width = NumericProperty(2)

    def __init__(self, **kwargs):
        super(type(self), self).__init__(**kwargs)

        self._color = self.color
        self._stim = self.stim
        self._sep = self.sep
        self._df = self.df
        self._line_width = self.line_width

        self.bind(color=self._update_color,
                  stim=self._update_stim,
                  df=self._update_df,
                  line_width=self._update_line_width,
                  sep=self._update_sep)
        self._update_stim()


    def _update_color(self, *pargs):
        self._color.rgba = self.color

    def _update_sep(self, *pargs):
        self._sep = self.sep
        self._update_stim()

    def _update_df(self, *pargs):
        self._df = self.df
        self._update_stim()

    def _update_line_width(self, *pargs):
        self._line_width = self.line_width

    def _update_stim(self, *pargs):
        self._stim = self.stim
        self._ncols = self._stim.find("\n")
        self._nrows = len(self._stim.split("\n")) - 1
        self._X0 = self.center_x
        self._Y0 = self.center_y
        self._height = (self._nrows - 1)*self._sep
        self._width = (self._ncols - 1)*self._sep
        self._top_row = self._Y0 + self._height/2.
        self._left_col = self._X0 - self._width/2.

        self._update()


    def _update(self, *pargs):
        # calc new point locations
        # draw them
        row_num = 0.
        col_num = 0.
        self.canvas.clear()
        with self.canvas:
            # set the color
            self._color = Color(*self.color)
            for i in self._stim:
                if i == "_":
                    col_num += 1.
                elif i == "\n":
                    row_num += 1.
                    col_num = 0.
                elif (i == "<") or (i == ">"):
                    Xi = self._left_col + col_num*self._sep
                    Yi = self._top_row - row_num*self._sep
                    if i == "<":
                        radians = pi/4.
                    else:
                        radians = -1.*pi/4.

                    Line(points=[Xi - cos(radians)*sqrt(2.)*self._df,
                                 (Yi+self._df) - sin(radians)*sqrt(2.)*self._df,
                                 Xi + cos(radians)*sqrt(2.)*self._df,
                                 (Yi+self._df) + sin(radians)*sqrt(2.)*self._df],
                                 cap="square", width=self._line_width)
                    Line(points=[Xi - cos(radians)*sqrt(2.)*self._df,
                                 (Yi-self._df) + sin(radians)*sqrt(2.)*self._df,
                                 Xi + cos(radians)*sqrt(2.)*self._df,
                                 (Yi-self._df) - sin(radians)*sqrt(2.)*self._df],
                                 cap="square", width=self._line_width)

                    col_num += 1.
