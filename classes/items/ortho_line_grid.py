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

import OpenGL
from OpenGL.GL import *

from .base_item import BaseItem

class OrthoLineGrid(BaseItem):
    """
    Draws a grid from individual lines. It can therefore not be filled.
    
    @param lower_left
    Lower left corner in local coordinates
    
    @param upper_right
    Upper right corner in local coordinates
    
    @param origin
    The location of the lower left corner in world coordinates
    
    @param unit
    At which intervals to draw a line
    
    @param color
    4-tuple of RGBA color
    
    @param linewidth
    Line width in pixels
    """
    
    def __init__(self,
                 label,
                 prog,
                 lower_left=(0, 0),
                 upper_right=(1000, 1000),
                 origin=(0, 0, 0),
                 unit=10,
                 color=(1, 1, 1, 0.2),
                 linewidth=1
                 ):
        
        width = upper_right[0] - lower_left[0]
        height = upper_right[1] - lower_left[1]
        
        width_units = int(width / unit) + 1
        height_units = int(height / unit) + 1
        
        vertex_count = 2 * width_units + 2 * height_units
        
        super(OrthoLineGrid, self).__init__(label, prog, vertex_count)
        
        self.primitive_type = GL_LINES
        self.linewidth = linewidth
        self.color = color
        self.set_origin(origin)
        
        for wu in range(0, width_units):
            x = unit * wu
            self.append((x, 0, 0), self.color)
            self.append((x, height, 0), self.color)
            
        for hu in range(0, height_units):
            y = unit * hu
            self.append((0, y, 0), self.color)
            self.append((width, y, 0), self.color)

        self.upload()