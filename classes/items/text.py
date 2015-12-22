import OpenGL
from OpenGL.GL import *

from .base_item import BaseItem
from .fonts import font_dutch_blunt as font

class Text(BaseItem):
    def __init__(self, label, prog, txt):
        
        charnum = len(txt)
        
        firstcharidx = 24
        
        vertexcount_total = 0
        for char in txt:
            j = ord(char) - firstcharidx
            #if j < 33 or j > 127: continue # this includes \n but reserving a few bytes more doesn't matter
            vertexcount_total += font.sizes[j]
            
        super(Text, self).__init__(label, prog, vertexcount_total, GL_TRIANGLES, True)
        
        letterpos = 0
        letterspacing = 1
        linepos = 0
        linespacing = 6
        
        col = (1, 1, 1, 0.6)
        
        for char in txt:
            j = ord(char) - firstcharidx
            
            if char == "\n":
                linepos -= linespacing
                letterpos = 0
                
                continue
            
            vertexcount = font.sizes[j] * 2
            offset = font.vdataoffsets[j] * 2
            for i in range(offset, offset + vertexcount, 2):
                x = font.vdata[i]
                y = font.vdata[i + 1]
                w = font.widths[j]
                
                x += letterpos
                y += linepos
                self.append((x, y, 0), col)
            letterpos += w
            letterpos += letterspacing
                
                
        self.upload()