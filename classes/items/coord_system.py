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

from .item import Item

class CoordSystem(Item):
    """
    Draws a classical XYZ coordinate system with colors RGB.
    
    @param label
    A string containing a unique name for this object
        
    @param prog_id
    OpenGL program ID (determines shaders to use) to use for this object
    
    @param origin
    The position of the CS in world coordinates
    
    @param scale
    The axes of the CS are length 1. Use `scale` to scale
    
    @param linewidth
    The line width in pixels
    """
    def __init__(self, label, prog_id, origin=(0,0,0), scale=10, linewidth=1):
        
        vertex_count = 6
        super(CoordSystem, self).__init__(label, prog_id, GL_LINES, linewidth, origin, scale, vertex_count)
        
        self.append_vertices([[(0, 0, 0), (.6, .0, .0, 1.0)]])
        self.append_vertices([[(1, 0, 0), (.6, .0, .0, 1.0)]])
        self.append_vertices([[(0, 0, 0), (.0, .6, .0, 1.0)]])
        self.append_vertices([[(0, 1, 0), (.0, .6, .0, 1.0)]])
        self.append_vertices([[(0, 0, 0), (.0, .0, .6, 1.0)]])
        self.append_vertices([[(0, 0, 1), (.0, .0, .6, 1.0)]])
            
        self.upload()
        

    def highlight(self, val):
        """
        Make a gradient towards white, towards the center
        
        @val
        True or False
        """
        for x in range(0,3):
            col = self.data["color"][x * 2 + 1]
            if val == True:
                newcol = (1, 1, 1, 1)
            else:
                newcol = (0, 0, 0, 1)
                
            self.data["color"][x * 2] = newcol

        self.upload()
        self.dirty = True