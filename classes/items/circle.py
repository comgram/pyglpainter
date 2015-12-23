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

import math
import numpy as np
import OpenGL
from OpenGL.GL import *

from .arc import Arc

class Circle(Arc):
    """
    xxx
    
    @param label
    A string containing a unique name for this object
        
    @param prog_id
    OpenGL program ID (determines shaders to use) to use for this object
    
    xxx
    
    @param origin
    Origin of item in world coordinates.
    
    @param scale
    Scale of item.
    """
    
    def __init__(self, label, prog_id, radius, use_triangles, filled, origin=(0,0,0), scale=1, linewidth=1, color=(1,.5,.5,1)):
        
        start = (-radius,0,0)
        end = start
        offset = (radius,0,0)
        
        super(Circle, self).__init__(label, prog_id, start, end, offset, radius, 0, 1, 2, True, use_triangles, filled, origin, scale, linewidth, color)