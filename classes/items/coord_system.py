import OpenGL
from OpenGL.GL import *

from .base_item import BaseItem

class CoordSystem(BaseItem):
    """
    Draws a classical XYZ coordinate system with colors RGB.
    
    @param label
    A string containing a unique name for this object
        
    @param prog_id
    OpenGL program ID (determines shaders to use) to use for this object
    
    @param scale
    The axes of the CS are length 1. Use `scale` to scale
    
    @param origin
    The position of the CS in world coordinates
    
    @param linewidth
    The line width in pixels
    
    @param hilight
    Set to True to make a gradient towards white, towards the center
    """
    def __init__(self, label, prog_id, scale=1, origin=(0, 0, 0), linewidth=1, hilight=False):
        
        vertex_count = 6
        super(CoordSystem, self).__init__(label, prog_id, vertex_count)
        
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