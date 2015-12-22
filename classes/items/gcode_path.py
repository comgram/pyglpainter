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

from .base_item import BaseItem

class GcodePath(BaseItem):
    """
    @param label
    A string containing a unique name for this object
        
    @param prog_id
    OpenGL program ID (determines shaders to use) to use for this object
    
    @param gcode
    A Python list of strings of G-codes to draw
    
    @param cwpos
    Current working position. The G-code way of drawing/moving requires
    a current working position for the first movement command, which
    would otherwise be unknown. Set the current machine position as 3-tuple.
    
    @param ccs
    Current coordinate system. Integer range from 4..9 (corresponding to G54-G59)
    `ccs` must be a key in `cs_offsets`
    
    @param cs_offsets
    Coordinate system offsets. A Python dict with integer keys and
    3-tuples as offsets. Keys must correspond to the range of `ccs`.
    When a G54-G59 change coordinate system command is encountered,
    the position for the next movement command will be relative to the
    selected offset. This emulates the movement behavior of a classical
    CNC machine.
    """
    def __init__(self, label, prog, gcode, cwpos, ccs, cs_offsets):
        vertex_count = 2 * (len(gcode) + 1)
        super(GcodePath, self).__init__(label, prog, vertex_count)
        
        self.primitive_type = GL_LINE_STRIP
        self.linewidth = 2
        
        self.gcode = gcode
        self.cwpos = list(cwpos)
        self.ccs = ccs
        self.cs_offsets = cs_offsets
        
        self.highlight_lines_queue = []
        
        self.axes = ["X", "Y", "Z"]
        
        self._re_axis_values = []
        for i in range(0, 3):
            axis = self.axes[i]
            self._re_axis_values.append(re.compile(".*" + axis + "([-.\d]+)"))
            
        self._re_contains_spindle = re.compile(".*S(\d+)")
        self._re_comment_grbl = re.compile(".*;(?:_gerbil)\.(.*)")
        self._re_allcomments_remove = re.compile(";.*")
        self._re_motion_mode = re.compile("G([0123])*([^\\d]|$)")
        self._re_distance_mode = re.compile("(G9[01])([^\d]|$)")
            
        self.render()
        self.upload()
        
        
    def highlight_line(self, line_number):
        self.highlight_lines_queue.append(line_number)
        pass
        
        
    def draw(self, viewmatrix=None):
        for line_number in self.highlight_lines_queue:
            #print("highlighting line", line_number)
            stride = self.data.strides[0]
            position_size = self.data.dtype["position"].itemsize
            color_size = self.data.dtype["color"].itemsize
            
            # 2 opengl segments for each logical line, see below
            offset = 2 * line_number * stride + position_size
            
            col = np.array([1, 1, 1, 0.8], dtype=np.float32)
            
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
            glBufferSubData(GL_ARRAY_BUFFER, offset, color_size, col)
            
        del self.highlight_lines_queue[:]

        super(GcodePath, self).draw(viewmatrix)
        
        
    def render(self):
        pos = self.cwpos # current position
        col = (1, 1, 1, 1)
        cs = self.ccs # current coordinate system
        offset = self.cs_offsets[cs] # current cs offset tuple
        current_motion_mode = 0
        distance_mode = "G90"
        spindle_speed = None
        
        in_arc = False # if currently in arc
        
        colors = {
            0: (.5, .5, .6, 1),
            1: (.7, .7, 1, 1),
            2: (0.7, 1, 0.8, 1),
            3: (.9, .7, 0.9, 1),
            "arc": (0.7, 1, 0.7, 1),
            }
        diff = [0, 0, 0]
        
        # start of path
        end = np.add(offset, pos)
        self.append(tuple(end), col)
        
        for line in self.gcode:
            
            # process special comments
            m = re.match(self._re_comment_grbl, line)
            # Detect if we're currently in an arc
            if m:
                comment = m.group(1)
                # these comments are added by gerbil's preprocessor
                if "arc_begin" in comment:
                    in_arc = True
                    
                elif "arc_end" in comment:
                    in_arc = False
            
            # remove all comments
            line = re.sub(self._re_allcomments_remove, "", line)
            
            # get current motion mode G0, G1, G2, G3
            m = re.match(self._re_motion_mode, line)
            if m:
                current_motion_mode = int(m.group(1))
                if current_motion_mode == 2 or current_motion_mode == 3:
                    print("G2 and G3 not supported. Use gerbil's preprocessor to fractionize a circle into small linear segements.")
                    
                    
            # update spindle speed / laser intensity
            # select colors
            m = re.match(self._re_contains_spindle, line)
            if m:
                spindle_speed = int(m.group(1))
                print("SPINDLE {} {}".format(spindle_speed, line))
            
            if spindle_speed != None and spindle_speed > 0:
                rgb = spindle_speed / 255.0
                if in_arc == True:
                    col = (rgb, rgb * 0.5, 0, 1) # yellow/reddish
                else:
                    col = (rgb, rgb * 0.9, 0, 1) # yellow
            elif in_arc == True:
                col = colors["arc"]
            else:
                col = colors[current_motion_mode]
                print("COLOR {} {}".format(current_motion_mode, col))

            m = re.match(self._re_distance_mode, line)
            if m: distance_mode = m.group(1)
            
            # get current coordinate system G54-G59
            mcs = re.match("G(5[4-9]).*", line)
            if mcs: 
                cs = "G" + mcs.group(1)
                offset = cs_offsets[cs]

            # parse X, Y, Z axis
            for i in range(0, 3):
                axis = self.axes[i]
                cr = self._re_axis_values[i]
                m = re.match(cr, line)
                if m:
                    a = float(m.group(1)) # axis value
                    if distance_mode == "G90":
                        # absolute
                        pos[i] = a
                    else:
                        # relative
                        pos[i] += a

            start = end
            end = np.add(offset, pos)
            diff = np.subtract(end, start)
            
            # generate 2 line segments per gcode for sharper color transitions when using spindle speed
            self.append(start + diff * 0.001, col)
            self.append(start + diff, (col[0], col[1], col[2], 0.3))