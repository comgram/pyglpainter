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

from .item import Item

class Arc(Item):
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
    
    def __init__(self, label, prog_id, start, end, offset, radius, axis_1, axis_2, axis_linear, is_clockwise_arc, use_triangles, filled, origin=(0,0,0), scale=1, linewidth=1, color=(1,.5,1,1)):
        
        positions = self.render(list(start), end, offset, radius, axis_1, axis_2, axis_linear, is_clockwise_arc)
        vertex_count = len(positions) + 1
        
        if use_triangles:
            primitive_type = GL_TRIANGLE_FAN
        else:
            primitive_type = GL_LINE_STRIP
        
        super(Arc, self).__init__(label, prog_id, primitive_type, linewidth, origin, scale, vertex_count, filled)
        
        if use_triangles:
            center = np.add(start, offset)
            self.append_vertices([[center, color]])
        
        for pos in positions:
            self.append_vertices([[pos, color]])

        self.upload()
        

    def render(self, position, target, offset, radius, axis_0, axis_1, axis_linear, is_clockwise_arc):
        """
        This function is a direct port of Grbl's C code into Python (motion_control.c)
        with slight refactoring for Python by Michael Franzl.
        This function is copyright (c) Sungeun K. Jeon under GNU General Public License 3
        """

        center_axis0 = position[axis_0] + offset[axis_0]
        center_axis1 = position[axis_1] + offset[axis_1]
        # radius vector from center to current location
        r_axis0 = -offset[axis_0]
        r_axis1 = -offset[axis_1]
        # radius vector from target to center
        rt_axis0 = target[axis_0] - center_axis0
        rt_axis1 = target[axis_1] - center_axis1
        
        angular_travel = math.atan2(r_axis0 * rt_axis1 - r_axis1 * rt_axis0, r_axis0 * rt_axis0 + r_axis1 * rt_axis1)
        
        arc_tolerance = 0.004
        arc_angular_travel_epsilon = 0.0000005
        
        if is_clockwise_arc: # Correct atan2 output per direction
            if angular_travel >= -arc_angular_travel_epsilon: angular_travel -= 2*math.pi
        else:
            if angular_travel <= arc_angular_travel_epsilon: angular_travel += 2*math.pi
            
        segments = math.floor(math.fabs(0.5 * angular_travel * radius) / math.sqrt(arc_tolerance * (2 * radius - arc_tolerance)))
        
        #print("angular_travel:{:f}, radius:{:f}, arc_tolerance:{:f}, segments:{:d}".format(angular_travel, radius, arc_tolerance, segments))
        
        words = ["X", "Y", "Z"]
        positions = []
        positions.append(tuple(position))
        if segments:
            theta_per_segment = angular_travel / segments
            linear_per_segment = (target[axis_linear] - position[axis_linear]) / segments
            
            for i in range(1, segments):
                cos_Ti = math.cos(i * theta_per_segment);
                sin_Ti = math.sin(i * theta_per_segment);
                r_axis0 = -offset[axis_0] * cos_Ti + offset[axis_1] * sin_Ti;
                r_axis1 = -offset[axis_0] * sin_Ti - offset[axis_1] * cos_Ti;
            
                position[axis_0] = center_axis0 + r_axis0;
                position[axis_1] = center_axis1 + r_axis1;
                position[axis_linear] += linear_per_segment;
                    
                positions.append(tuple(position))
            
        
        # make sure we arrive at target
        positions.append(tuple(target))
        
        return positions