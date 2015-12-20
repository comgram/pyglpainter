import logging
import numpy as np
import ctypes
import sys
import math
import re

from PyQt5.QtCore import pyqtSignal, QPoint, Qt, QSize, QTimer
from PyQt5.QtGui import QColor, QMatrix4x4, QVector2D, QVector3D, QQuaternion
from PyQt5.QtOpenGL import QGLWidget

import OpenGL
OpenGL.ERROR_CHECKING = True
OpenGL.FULL_LOGGING = True
from OpenGL.GL import *

class Item():
    def __init__(self, label, prog, vertexcount, primitive_type=GL_LINES, filled=False, line_width=1):
        self.vbo = glGenBuffers(1)
        self.vao = glGenVertexArrays(1)
        self.program = prog
        self.label = label

        self.elementcount = 0
        
        self.primitive_type = primitive_type
        self.linewidth = line_width
        
        self.filled = filled
        
        self.scale = 1
        self.origin = QVector3D(0, 0, 0)
        self.rotation_angle = 0
        self.rotation_vector = QVector3D(0, 0, 0)
        
        self.dirty = True
        
        self.vertexcount = vertexcount
        self.data = np.zeros(self.vertexcount, [("position", np.float32, 3), ("color", np.float32, 4)])
        
        
    def __del__(self):
        print("DELETING MYSELF: {}".format(self.label))
        
    
    # simply appends to numpy data structure but neither uploads nor draws
    def append(self, pos, col=(1, 1, 1, 1)):
        self.data["position"][self.elementcount] = pos
        self.data["color"][self.elementcount] = col
        self.elementcount += 1
    
    
    # for large buffer sizes, to avoid frequently uploading the entire buffer
    # simply replace the data
    def substitute(self, vertex_nr, pos, col):
        stride = self.data.strides[0]
        position_size = self.data.dtype["position"].itemsize
        color_size = self.data.dtype["color"].itemsize
        
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        
        # replace position
        position = np.array([pos[0], pos[1], pos[2]], dtype=np.float32)
        offset = vertex_nr * stride
        glBufferSubData(GL_ARRAY_BUFFER, offset, position_size, position)
        
        # replace color
        color = np.array([col[0], col[1], col[2], col[3]], dtype=np.float32)
        offset = vertex_nr * stride + position_size
        glBufferSubData(GL_ARRAY_BUFFER, offset, color_size, color)
    
    
    def remove(self):
        glDeleteBuffers(1, [self.vbo])
        glDeleteVertexArrays(1, [self.vao])
        self.dirty = True
        print("REMOVING {}".format(self.label))
        
    def upload(self):
        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.data.nbytes, self.data, GL_DYNAMIC_DRAW)
        
        print("UPLOADING {} BYTES".format(self.data.nbytes))
        stride = self.data.strides[0]
        
        offset = ctypes.c_void_p(0)
        loc = glGetAttribLocation(self.program, "position")
        glEnableVertexAttribArray(loc)
        glVertexAttribPointer(loc, 3, GL_FLOAT, False, stride, offset)

        offset = ctypes.c_void_p(self.data.dtype["position"].itemsize)
        loc = glGetAttribLocation(self.program, "color")
        glEnableVertexAttribArray(loc)
        glVertexAttribPointer(loc, 4, GL_FLOAT, False, stride, offset)
        
        # unbind
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)
        
        
    def set_scale(self, fac):
        self.scale = fac
        
        
    def set_origin(self, tpl):
        self.origin = QVector3D(tpl[0], tpl[1], tpl[2])

        
    def draw(self):
        # upload Model Matrix
        # TODO: only draw if dirty
        mat_m = QMatrix4x4()
        mat_m.translate(self.origin)
        mat_m.scale(self.scale)
        mat_m.rotate(self.rotation_angle, self.rotation_vector)
        
        if self.filled:
            glPolygonMode( GL_FRONT_AND_BACK, GL_FILL )
        else:
            glPolygonMode( GL_FRONT_AND_BACK, GL_LINE )
        
        glUseProgram(self.program)
        
        mat_m = self.qt_mat_to_array(mat_m)
        loc_mat_m = glGetUniformLocation(self.program, "mat_m")
        glUniformMatrix4fv(loc_mat_m, 1, GL_TRUE, mat_m)
        
        # bind VBO and VAO
        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        
        # actual draw command
        glLineWidth(self.linewidth)
        glDrawArrays(self.primitive_type, 0, self.elementcount)
        
        # unbind VBO and VAO
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)
        
        self.dirty = False
    
    @staticmethod
    def qt_mat_to_array(mat):
        arr = [0] * 16
        for i in range(4):
            for j in range(4):
                idx = 4 * i + j
                arr[idx] = mat[i, j]
        return arr
        
        
        
class Star(Item):
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
        
        
class CoordSystem(Item):
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
        
        

class Grid(Item):
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
        
        super(Grid, self).__init__(label, prog, vertex_count)
        
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
        
        
class GcodePath(Item):
    def __init__(self, label, prog, gcode, cwpos, ccs, cs_offsets):
        vertex_count = 2 * (len(gcode) + 1)
        super(GcodePath, self).__init__(label, prog, vertex_count)
        
        self.primitive_type = GL_LINE_STRIP
        self.linewidth = 2
        
        self.gcode = gcode
        self.cwpos = list(cwpos)
        self.ccs = ccs
        self.cs_offsets = cs_offsets
        
        self.highlight_lines_queue = []
        
        self.axes = ["X", "Y", "Z"]
        
        self._re_axis_values = []
        for i in range(0, 3):
            axis = self.axes[i]
            self._re_axis_values.append(re.compile(".*" + axis + "([-.\d]+)"))
            
        self._re_contains_spindle = re.compile(".*S(\d+)")
        self._re_comment_grbl = re.compile(".*;(?:_gerbil)\.(.*)")
        self._re_allcomments_remove = re.compile(";.*")
        self._re_motion_mode = re.compile("G([0123])*([^\\d]|$)")
        self._re_distance_mode = re.compile("(G9[01])([^\d]|$)")
            
        self.render()
        self.upload()
        
        
    def highlight_line(self, line_number):
        self.highlight_lines_queue.append(line_number)
        pass
        
        
    def draw(self):
        for line_number in self.highlight_lines_queue:
            #print("highlighting line", line_number)
            stride = self.data.strides[0]
            position_size = self.data.dtype["position"].itemsize
            color_size = self.data.dtype["color"].itemsize
            
            # 2 opengl segments for each logical line, see below
            offset = 2 * line_number * stride + position_size
            
            col = np.array([1, 1, 1, 0.8], dtype=np.float32)
            
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
            glBufferSubData(GL_ARRAY_BUFFER, offset, color_size, col)
            
        del self.highlight_lines_queue[:]
        
        super(GcodePath, self).draw()
        
        
    def render(self):
        pos = self.cwpos # current position
        col = (1, 1, 1, 1)
        cs = self.ccs # current coordinate system
        offset = self.cs_offsets[cs] # current cs offset tuple
        current_motion_mode = 0
        distance_mode = "G90"
        spindle_speed = None
        
        in_arc = False # if currently in arc
        
        colors = {
            0: (.5, .5, .6, 1),
            1: (.7, .7, 1, 1),
            2: (0.7, 1, 0.8, 1),
            3: (.9, .7, 0.9, 1),
            "arc": (0.7, 1, 0.7, 1),
            }
        diff = [0, 0, 0]
        
        # start of path
        end = np.add(offset, pos)
        self.append(tuple(end), col)
        
        for line in self.gcode:
            
            # process special comments
            m = re.match(self._re_comment_grbl, line)
            # Detect if we're currently in an arc
            if m:
                comment = m.group(1)
                # these comments are added by gerbil's preprocessor
                if "arc_begin" in comment:
                    in_arc = True
                    
                elif "arc_end" in comment:
                    in_arc = False
            
            # remove all comments
            line = re.sub(self._re_allcomments_remove, "", line)
            
            # get current motion mode G0, G1, G2, G3
            m = re.match(self._re_motion_mode, line)
            if m:
                current_motion_mode = int(m.group(1))
                if current_motion_mode == 2 or current_motion_mode == 3:
                    print("G2 and G3 not supported. Use gerbil's preprocessor to fractionize a circle into small linear segements.")
                    
                    
            # update spindle speed / laser intensity
            # select colors
            m = re.match(self._re_contains_spindle, line)
            if m:
                spindle_speed = int(m.group(1))
                print("SPINDLE {} {}".format(spindle_speed, line))
            
            if spindle_speed != None and spindle_speed > 0:
                rgb = spindle_speed / 255.0
                if in_arc == True:
                    col = (rgb, rgb * 0.5, 0, 1) # yellow/reddish
                else:
                    col = (rgb, rgb * 0.9, 0, 1) # yellow
            elif in_arc == True:
                col = colors["arc"]
            else:
                col = colors[current_motion_mode]
                print("COLOR {} {}".format(current_motion_mode, col))

            m = re.match(self._re_distance_mode, line)
            if m: distance_mode = m.group(1)
            
            # get current coordinate system G54-G59
            mcs = re.match("G(5[4-9]).*", line)
            if mcs: 
                cs = "G" + mcs.group(1)
                offset = cs_offsets[cs]

            # parse X, Y, Z axis
            for i in range(0, 3):
                axis = self.axes[i]
                cr = self._re_axis_values[i]
                m = re.match(cr, line)
                if m:
                    a = float(m.group(1)) # axis value
                    if distance_mode == "G90":
                        # absolute
                        pos[i] = a
                    else:
                        # relative
                        pos[i] += a

            start = end
            end = np.add(offset, pos)
            diff = np.subtract(end, start)
            
            # generate 2 line segments per gcode for sharper color transitions when using spindle speed
            self.append(start + diff * 0.001, col)
            self.append(start + diff, (col[0], col[1], col[2], 0.3))
            