import OpenGL
from OpenGL.GL import *

from .base_item import BaseItem

class Star(BaseItem):
    def __init__(self, label, prog, scale=1, origin=(0, 0, 0)):
        
        vertex_count = 6
        super(Star, self).__init__(label, prog, vertex_count)
        
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