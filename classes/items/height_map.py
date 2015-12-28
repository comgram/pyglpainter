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

import numpy as np

from .item import Item

class HeightMap(Item):
    """
    xxx
    """
    
    def __init__(self, label, prog,
                 nodes_x, nodes_y, pos_col,
                 origin=(0,0,0), scale=1, linewidth=1, color=(1,1,1,0.2)):
        """
        @param label
        A string containing a unique name for this item.
            
        @param prog_id
        OpenGL program ID (determines shaders to use) to use for this item.
        
        @param positions
        List of 3-tuples of node positions
        
        @param origin
        Origin of this item in world space.
        
        @param scale
        Scale of this item in world space.
        
        @param linewidth
        Width of rendered lines in pixels.
        
        @param color
        Color of this item.
        """

        self.nodes_x = nodes_x
        self.nodes_y = nodes_y
        
        super(HeightMap, self).__init__(label, prog, GL_TRIANGLE_STRIP, linewidth, origin, scale, 0)
        
        glPrimitiveRestartIndex(self.nodes_x * self.nodes_y)
        
        self.calculate_indices(nodes_x, nodes_y)
        print("XXXXXXXXXXXXXXXXXX", self.vdata_indices)
        
        self.vdata_pos_col = pos_col
        self.elementcount = pos_col.size


    def calculate_indices(self, nx, ny):
        size = 2 * nx * (ny-1) + ny - 2
        self.vdata_indices = np.zeros(size, dtype=np.int32)
        
        j = 0
        for y in range(0, ny - 1):
            for x in range(0, nx):
                self.vdata_indices[j] = y * nx + x
                j += 1
                self.vdata_indices[j] = (y + 1) * nx + x
                j += 1
            if y < (ny - 2):
                self.vdata_indices[j] = nx * ny
                j += 1
        
        
