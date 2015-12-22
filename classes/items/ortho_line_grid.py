import OpenGL
from OpenGL.GL import *

from .base_item import BaseItem

class OrthoLineGrid(BaseItem):
    def __init__(self,
                 label,
                 prog,
                 ll=(0, 0),
                 ur=(1000, 1000),
                 trans=(0, 0, 0),
                 unit=10,
                 color=(1, 1, 1, 0.2),
                 linewidth=1
                 ):
        
        width = ur[0] - ll[0]
        height = ur[1] - ll[1]
        width_units = int(width / unit) + 1
        height_units = int(height / unit) + 1
        
        vertex_count = 2 * width_units + 2 * height_units
        
        super(OrthoLineGrid, self).__init__(label, prog, vertex_count)
        
        self.primitive_type = GL_LINES
        self.linewidth = linewidth
        self.color = color
        self.set_origin(trans)
        
        for wu in range(0, width_units):
            x = unit * wu
            self.append((x, 0, 0), self.color)
            self.append((x, height, 0), self.color)
            
        for hu in range(0, height_units):
            y = unit * hu
            self.append((0, y, 0), self.color)
            self.append((width, y, 0), self.color)

        self.upload()