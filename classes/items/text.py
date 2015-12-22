"""
pyglpainter - Copyright (c) 2015 Michael Franzl

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import OpenGL
from OpenGL.GL import *

from .base_item import BaseItem
from .fonts import font_dutch_blunt as font

class Text(BaseItem):
    """
    Renders text with a triangle-only font. See font_dutch_blunt.py for 
    more information.
    
    @param label
    A string containing a unique name for this object
        
    @param prog_id
    OpenGL program ID (determines shaders to use) to use for this object
    
    @param txt
    Text to be rendered. A string which should only contain ASCII
    characters from 24-127 plus \n
    """
    def __init__(self, label, prog_id, txt):
        
        charnum = len(txt)
        
        firstcharidx = 24
        
        vertexcount_total = 0
        for char in txt:
            j = ord(char) - firstcharidx
            vertexcount_total += font.sizes[j]
            
        super(Text, self).__init__(label, prog_id, vertexcount_total, GL_TRIANGLES, True)
        
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