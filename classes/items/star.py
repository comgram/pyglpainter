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