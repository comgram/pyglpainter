import logging
import numpy as np
import ctypes
import sys
import math


from PyQt5.QtGui import QColor, QMatrix4x4, QVector2D, QVector3D, QVector4D, QQuaternion


import OpenGL
from OpenGL.GL import *

class BaseItem():
    def __init__(self, label, prog, vertexcount, primitive_type=GL_LINES, filled=False, line_width=1):
        self.vbo = glGenBuffers(1)
        self.vao = glGenVertexArrays(1)
        self.program_id = prog
        self.label = label

        self.elementcount = 0
        
        self.primitive_type = primitive_type
        self.linewidth = line_width
        
        self.filled = filled
        
        self.billboard = False
        self.billboard_axis = None
        
        self.scale = 1
        self.origin = QVector3D(0, 0, 0)
        self.rotation_angle = 0
        self.rotation_vector = QVector3D(0, 1, 0)
        
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
        loc = glGetAttribLocation(self.program_id, "position")
        glEnableVertexAttribArray(loc)
        glVertexAttribPointer(loc, 3, GL_FLOAT, False, stride, offset)

        offset = ctypes.c_void_p(self.data.dtype["position"].itemsize)
        loc = glGetAttribLocation(self.program_id, "color")
        glEnableVertexAttribArray(loc)
        glVertexAttribPointer(loc, 4, GL_FLOAT, False, stride, offset)
        
        # unbind
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)
        
        
    def set_scale(self, fac):
        self.scale = fac
        
        
    def set_origin(self, tpl):
        self.origin = QVector3D(*tpl)

        
    def draw(self, viewmatrix=None):
        # upload Model Matrix
        mat_m = self.calculate_model_matrix(viewmatrix)

        if self.filled:
            glPolygonMode( GL_FRONT_AND_BACK, GL_FILL )
        else:
            glPolygonMode( GL_FRONT_AND_BACK, GL_LINE )
        
        glUseProgram(self.program_id)
        
        mat_m = self.qt_mat_to_list(mat_m)
        loc_mat_m = glGetUniformLocation(self.program_id, "mat_m")
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
        
        
    def calculate_model_matrix(self, viewmatrix_inv=None):
        mat_m = QMatrix4x4()
        mat_m.translate(self.origin)
        
        if self.billboard:
            # based on excellent tutorial:
            # http://nehe.gamedev.net/article/billboarding_how_to/18011/
            
            # extract 2nd column which is camera up vector
            cam_up = viewmatrix_inv * QVector4D(0,1,0,0)
            cam_up = QVector3D(cam_up[0], cam_up[1], cam_up[2])
            cam_up.normalize()
            
            # extract 3rd column which is camera look vector
            cam_look = viewmatrix_inv * QVector4D(0,0,1,0)
            cam_look = QVector3D(cam_look[0], cam_look[1], cam_look[2])
            cam_look.normalize()
            
            # extract 4th column which is camera position
            cam_pos = viewmatrix_inv * QVector4D(0,0,0,1)
            cam_pos = QVector3D(cam_pos[0], cam_pos[1], cam_pos[2])
            
            # calculate self look vector (self to camera)
            bill_look = cam_pos - self.origin
            bill_look.normalize()
            
            if self.billboard_axis == None:
                # Fully aligned billboard
                # calculate new self right vector based upon self look and camera up
                bill_right = QVector3D.crossProduct(cam_up, bill_look)
                
                # calculate self up vector based on self look and self right
                bill_up = QVector3D.crossProduct(bill_look, bill_right)
                
            else:
                axis_words = ["X", "Y", "Z"]
                axis = axis_words.index(self.billboard_axis)
                
                bill_up = [0]*3
                for i in range(0,3):
                    bill_up[i] = 1 if i == axis else 0
                bill_up = QVector3D(*bill_up)
                
                bill_look_zeroed = [0]*3
                for i in range(0,3):
                    bill_look_zeroed[i] = 0 if i == axis else bill_look[i]
                bill_look = QVector3D(*bill_look_zeroed)
                bill_look.normalize()
                
                bill_right = QVector3D.crossProduct(bill_up, bill_look)
            
            # view and model matrices are actually nicely structured
            # 1st column: right vector
            # 2nd column: up vector
            # 3rd column: look vector
            # 4th column: position
            # here we only overwrite right, up and look. Position is already there.
            mat_m[0,0] = bill_right[0]
            mat_m[1,0] = bill_right[1]
            mat_m[2,0] = bill_right[2]
            
            mat_m[0,1] = bill_up[0]
            mat_m[1,1] = bill_up[1]
            mat_m[2,1] = bill_up[2]
            
            mat_m[0,2] = bill_look[0]
            mat_m[1,2] = bill_look[1]
            mat_m[2,2] = bill_look[2]
            
        else:
            mat_m.rotate(self.rotation_angle, self.rotation_vector)
        
        mat_m.scale(self.scale)
        
        return mat_m
        
        
    @staticmethod
    def angle_between(v1, v2):
        """
        Returns angle in radians between vector v1 and vector v2.
        
        @param v1
        Vector 1 of class QVector3D
        
        @param v2
        Vector 2 of class QVector3D
        """
        return math.acos(QVector3D.dotProduct(v1, v2) / (v1.length() * v2.length()))
    
    @staticmethod
    def qt_mat_to_list(mat):
        """
        Transforms a QMatrix4x4 into a one-dimensional Python list
        in row-major order.
        
        @param mat
        Matrix of type QMatrix4x4
        """
        arr = [0] * 16
        for i in range(4):
            for j in range(4):
                idx = 4 * i + j
                arr[idx] = mat[i, j]
        return arr