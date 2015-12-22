import OpenGL
from OpenGL.GL import *

from .base_item import BaseItem

class CoordSystem(BaseItem):
    def __init__(self, label, prog, scale=1, origin=(0, 0, 0), linewidth=1, hilight=False):
        
        vertex_count = 6
        super(CoordSystem, self).__init__(label, prog, vertex_count)
        
        self.primitive_type = GL_LINES
        self.linewidth = linewidth
        self.set_scale(scale)
        self.set_origin(origin)
        
        self.append((00, 00, 00), (.6, .0, .0, 1.0))
        self.append((10, 00, 00), (.6, .0, .0, 1.0))
        self.append((00, 00, 00), (.0, .6, .0, 1.0))
        self.append((00, 10, 00), (.0, .6, .0, 1.0))
        self.append((00, 00, 00), (.0, .0, .6, 1.0))
        self.append((00, 00, 10), (.0, .0, .6, 1.0))
            
        self.upload()
        
        self.highlight(hilight)
        

    def highlight(self, val):
        self.hilight = val
        for x in range(0,3):
            col = self.data["color"][x * 2 + 1]
            if self.hilight == True:
                newcol = (1, 1, 1, 1)
            else:
                newcol = (0, 0, 0, 1)
                
            self.data["color"][x * 2] = newcol

        self.upload()
        self.dirty = True