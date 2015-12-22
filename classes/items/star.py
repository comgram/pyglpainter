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

class Star(BaseItem):
    """
    Draws a simple 3-dimensional cross, which appears as a star when
    viewed from a non-orthogonal direction.
    
    @param label
    A string containing a unique name for this object
        
    @param prog_id
    OpenGL program ID (determines shaders to use) to use for this object
    
    @param scale
    Default size of star is 1. Use this to modify.
    
    @param origin
    Origin of star in world coordinates.
    """
    
    def __init__(self, label, prog_id, scale=1, origin=(0, 0, 0)):
        
        vertex_count = 6
        super(Star, self).__init__(label, prog_id, vertex_count)
        
        self.primitive_type = GL_LINES
        self.linewidth = 2
        self.set_scale(scale)
        self.set_origin(origin)
        
        col = (1, 1, .5, 1)
        
        self.append((-1, 0, 0), col)
        self.append((1, 0, 0), col)
        self.append((0, -1, 0), col)
        self.append((0, 1, 0), col)
        self.append((0, 0, -1), col)
        self.append((0, 0, 1), col)
        
        self.upload()