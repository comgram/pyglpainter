"""
pyglpainter - Copyright (c) 2015 Michael Franzl

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.
"""

import re
import numpy as np
import OpenGL
from OpenGL.GL import *

from ..gcode_preprocessor import GcodePreprocessor
from .item import Item

class GcodePath(Item):
    """
    Plot the path laid out by G-Code commands for CNC machines.
    
    Supports G0, G1, G2, G3, G90, G91, and G54-G59.
    
    G2 and G3 arcs are approximated by line segments. Different motion
    modes are drawn with different colors for better visualization.
    """

    def __init__(self, label, prog_id, gcode_list, cwpos, ccs, cs_offsets):
        """
        param label
        A string containing a unique name for this item.
            
        @param prog_id
        OpenGL program ID (determines shaders to use) to use for this item.
        
        @param gcode_list
        A Python list of strings of G-codes that will be plotted.
        
        @param cwpos
        Current working position. G-Codes imply a state machine knowing
        its position. This is the initial position of the state machine.
        A 3-tuple of global coordinates.
        
        @param ccs
        Current coordinate system. G-Codes imply a state machine knowing
        its current coordinate system. This is the initial coordinate system
        name of the state machine. It is an integer in the range from
        4..9 (corresponding to G54-G59). `ccs` must be a key in `cs_offsets`.
        
        @param cs_offsets
        Coordinate system offsets. A Python dict with integer keys and
        3-tuples as offsets. Keys must correspond to the range of `ccs`.
        When a G54-G59 change coordinate system command is encountered,
        the position for the next movement command will be relative to the
        selected offset. This emulates the movement behavior of a classical
        CNC machine.
        """

        super(GcodePath, self).__init__(label, prog_id, GL_LINE_STRIP, 2)
        
        self.ccs = ccs
        self.cs_offsets = cs_offsets
        self.position = list(cwpos)
        
        self._lines_to_highlight = [] # line segments can be highlighted
        
        self.axes = ["X", "Y", "Z"]
        self._re_axis_values = []
        for i in range(0, 3):
            axis = self.axes[i]
            self._re_axis_values.append(re.compile(".*" + axis + "([-.\d]+)"))
            
        self._re_contains_spindle = re.compile(".*S(\d+)")
        self._re_comment_colorvalues_grbl = re.compile(".*_gerbil.color_begin\[(.*?),(.*?),(.*?)\]")
        self._re_allcomments_remove = re.compile(";.*")
        self._re_motion_mode = re.compile("G([0123])*([^\\d]|$)")
        self._re_distance_mode = re.compile("(G9[01])([^\d]|$)")

        # Run the G-codes through a preprocessor. It will clean up the
        # G-Code from unsupported things and also break arcs down into
        # line segments since OpenGL has no notion about arcs.
        self.gcode = []
        self.preprocessor = GcodePreprocessor()
        self.preprocessor.position = list(self.position) # initial state
        self.preprocessor.target = list(self.position)   # initial state
        for line in gcode_list:
            self.preprocessor.set_line(line)
            self.preprocessor.tidy()
            self.preprocessor.parse_state()
            lines = self.preprocessor.fractionize()
            self.gcode += lines
            self.preprocessor.done()

        self.set_vertexcount(2 * len(self.gcode) + 1)

        self.render()
        self.upload()
        
        
    def highlight_line(self, line_number):
        """
        Remember which lines to highlight.
        
        The color of a highlighted line will be substituted directly on
        the GPU. Substitution will happen during the next `draw()`
        call which is why this function is very efficient, and can be
        called from threads.
        """
        self._lines_to_highlight.append(line_number)
        pass
        
        
    def draw(self, viewmatrix=None):
        for line_number in self._lines_to_highlight:
            # Substitute color of highlighted lines directly in the GPU.
            stride = self.data.strides[0]
            position_size = self.data.dtype["position"].itemsize
            color_size = self.data.dtype["color"].itemsize
            
            # 2 opengl segments for each logical line, see below
            offset = 2 * line_number * stride + position_size
            
            col = np.array([1, 1, 1, 0.8], dtype=np.float32)
            
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
            glBufferSubData(GL_ARRAY_BUFFER, offset, color_size, col)
            
        del self._lines_to_highlight[:]

        super(GcodePath, self).draw(viewmatrix)
        
        
    def render(self):
        """
        Appends vertices corresponding to the path traveled by G-Code.
        
        This emulates the state machine of a CNC machine. The color
        of drawn paths is taken from a special comment environment
        `_gerbil.color_begin` and `_gerbil.color_end`. If color is not
        set via comments, default colors are taken from the motion mode.
        
        This method only supports G0 and G1 linear motions. Use a
        preprocessor to break arcs down into lines.
        """
        
        colors = {
            0: (.5, .5, .6, 1),
            1: (.7, .7, 1, 1),
            2: (0.7, 1, 0.8, 1),
            3: (.9, .7, 0.9, 1),
            }
        col = colors[0] # initial color

        # state machine states
        current_motion_mode = 0
        distance_mode = "G90"
        spindle_speed = None
        diff = [0, 0, 0]
        comment_color = None # if current in color mode (_gerbil.color_begin comments)
        
        # create vertex at start of path
        end = np.add(self.cs_offsets[self.ccs], self.position)
        self.append_vertices([[tuple(end), col]])
        
        for line in self.gcode:
            # find colors in comments
            if "color_begin" in line:
                m = re.match(self._re_comment_colorvalues_grbl, line)
                comment_color = (m.group(1), m.group(2), m.group(3), 1)
            elif "color_end" in line:
                comment_color = None
            
            # remove all comments
            line = re.sub(self._re_allcomments_remove, "", line)
            
            # get current motion mode
            m = re.match(self._re_motion_mode, line)
            if m:
                current_motion_mode = int(m.group(1))
                if current_motion_mode == 2 or current_motion_mode == 3:
                    print("GcodePath.render(): Encountered G2 or G3 command. Will draw a straight line from position to target. Use preprocessor to correctly break down arcs.")

            # get spindle speed / laser intensity
            m = re.match(self._re_contains_spindle, line)
            if m:
                spindle_speed = int(m.group(1))

            # select color from comment if present, else default color
            col = comment_color if comment_color else colors[current_motion_mode]
                
            # parse distance mode (absolute, relative)
            m = re.match(self._re_distance_mode, line)
            if m: distance_mode = m.group(1)
            
            # get current coordinate system G54-G59
            mcs = re.match("G(5[4-9]).*", line)
            if mcs: 
                self.ccs = "G" + mcs.group(1)

            # parse X, Y, Z axis target of thie line
            for i in range(0, 3):
                axis = self.axes[i]
                cr = self._re_axis_values[i]
                m = re.match(cr, line)
                if m:
                    a = float(m.group(1)) # axis value
                    if distance_mode == "G90":
                        # absolute
                        self.position[i] = a
                    else:
                        # relative
                        self.position[i] += a

            start = end
            end = np.add(self.cs_offsets[self.ccs], self.position)
            diff = np.subtract(end, start)
            
            # each line segment will have a gradient from selected color
            # to either dark, or a color depending on the S value, to better
            # illustrate the intensity of a laser for engraving.
            color1 = col
            if spindle_speed == None or spindle_speed == 0:
                color2 = (col[0], col[1], col[2], 0.3)
            else:
                color2 = (0.3, 0.2, spindle_speed/255, 0.8) # blueish hue
            
            self.append_vertices([[start + diff * 0.001, color1]])
            self.append_vertices([[start + diff, color2]])