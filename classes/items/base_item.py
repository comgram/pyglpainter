"""
pyglpainter - Copyright (c) 2015 Michael Franzl

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""


import logging
import numpy as np
import ctypes
import sys
import math

from PyQt5.QtGui import QColor, QMatrix4x4, QVector2D, QVector3D, QVector4D, QQuaternion

import OpenGL
from OpenGL.GL import *

class BaseItem():
    """
    This class represents a separate object in 3D space.
    
    It implements OpenGL per-object boilerplate functions.
    
    Most importantly, a Base Item has its own relative coordinate system
    with local (0,0,0) located at global self.origin.
    
    It also has its own units of measurement determined by self.scale.
    
    It can be rotated around its own origin by self.rotation_angle and
    self.rotation_vector.
    
    An instance of this class knows how to
      * add CPU vertex data (color and position) as simple tuples
      * manage all vertex data in numpy format
      * upload CPU vertex data into the GPU fully or in part (substitute)
      * draw itself
      * remove itself
      * calculate it's own Model matrix (optionally in "billboard" mode)
      
    You can use this class as it is for drawing raw OpenGL primitives.
    
    You can subclass to implement composite primitives (see other classes
    in this directory).
    """
    
    def __init__(self, label, prog_id, vertexcount, primitive_type=GL_LINES, filled=False, line_width=1):
        """
        @param label
        A string containing a unique name for this object
        
        @param prog_id
        OpenGL program ID (determines shaders to use) to use for this object
        
        @param vertexcount
        The maximum number of vertices to reserve for the CPU und GPU data buffers.
        You may append only a part of that via `append()`
        
        @param primitive_type
        An integer constant GL_LINES, GL_LINE_STRIP, GL_TRINAGLES, GL_TRINAGLE_STRIP
        etc.
        
        @param filled
        True or False. Determines if drawn triangles will be filled with color.
        
        @param line_width
        An integer giving the line width in pixels.
        """
        
        self.vbo = glGenBuffers(1) # VertexBuffer ID
        self.vao = glGenVertexArrays(1) # VertexArray ID
        
        self.program_id = prog_id # the program/shader to use
        self.label = label

        self.vertexcount = vertexcount # maximum number of vertices
        self.elementcount = 0 # current number of appended/used vertices

        self.primitive_type = primitive_type
        self.linewidth = line_width
        self.filled = filled # if a triangle should be drawn filled
        
        # billboard mode
        self.billboard = False # set to True to always face camera
        self.billboard_axis = None # must be strings "X", "Y", or "Z"
        
        self.scale = 1 # 1 local unit corresponds to 1 world unit
        
        # by default congruent with world origin
        self.origin = QVector3D(0, 0, 0) 
        
        # by default not rotated
        self.rotation_angle = 0 
        self.rotation_vector = QVector3D(0, 1, 0) # default rotation around Y
        
        self.dirty = True

        # The CPU vertex data buffer is managed with numpy
        self.data = np.zeros(self.vertexcount, [("position", np.float32, 3), ("color", np.float32, 4)])
        
        
    def __del__(self):
        print("Item {}: deleting myself.".format(self.label))
        
    
    def append(self, pos, col=(1, 1, 1, 1)):
        """
        Appends one vertex with position and color to CPU data storage
        but neither uploads nor draws.
        
        @param pos
        3-tuple of floats for position
        
        @param col
        4-tuple of floats for color RGBA
        """
        self.data["position"][self.elementcount] = pos
        self.data["color"][self.elementcount] = col
        self.elementcount += 1
    
    
    def substitute(self, vertex_nr, pos, col):
        """
        If your object contains a very large vertex count, it may be more
        efficient to substitute data directly on the GPU instead of
        re-uploading everything. Use this to modify data.
        
        @param vertex_nr
        Number of vertex to substitute
        
        @param pos
        3-tuple of floats. Position to substitue for specified vertex
        
        @params col
        4-tuple of RGBA color. Color to substitute for specified vertex
        
        """
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
        """
        Removes self from the scene. The object will disappear.
        """
        glDeleteBuffers(1, [self.vbo])
        glDeleteVertexArrays(1, [self.vao])
        self.dirty = True
        print("Item {}: removing myself.".format(self.label))
        
        
    def upload(self):
        """
        This method will upload the entire CPU vertex data to the GPU.
        
        Call this once after all the CPU data have been set with append().
        """
        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.data.nbytes, self.data, GL_DYNAMIC_DRAW)
        
        print("Item {}: uploading {} bytes.".format(self.label, self.data.nbytes))
        stride = self.data.strides[0]
        
        offset = ctypes.c_void_p(0)
        loc = glGetAttribLocation(self.program_id, "position")
        glEnableVertexAttribArray(loc)
        glVertexAttribPointer(loc, 3, GL_FLOAT, False, stride, offset)

        offset = ctypes.c_void_p(self.data.dtype["position"].itemsize)
        loc = glGetAttribLocation(self.program_id, "color")
        glEnableVertexAttribArray(loc)
        glVertexAttribPointer(loc, 4, GL_FLOAT, False, stride, offset)
        
        # unbind (not strictly neccessary)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)
        
        
    def set_scale(self, fac):
        """
        Alternative method to set scale.
        
        @param fac
        Scale factor
        """
        self.scale = fac
        
        
    def set_origin(self, tpl):
        """
        Alternative method to set origin.
        
        @param tpl
        Origin of self in world coordinates as 3-tuple
        """
        self.origin = QVector3D(*tpl)

        
    def draw(self, viewmatrix_inverted=None):
        """
        Draws this object. Call this from within paintGL().
        
        @param viewmatrix_inverted
        The inverted View matrix. It contains Camera position and angles.
        Mandatory only when self.billboard == True
        """
        
        # Calculate the Model matrix
        mat_m = self.calculate_model_matrix(viewmatrix_inverted)

        if self.filled:
            glPolygonMode( GL_FRONT_AND_BACK, GL_FILL )
        else:
            glPolygonMode( GL_FRONT_AND_BACK, GL_LINE )
        
        # this determines which shaders will be used
        glUseProgram(self.program_id)
        
        # upload Model matrix, accessible in the shader as variable mat_m
        mat_m = self.qt_mat_to_list(mat_m)
        loc_mat_m = glGetUniformLocation(self.program_id, "mat_m")
        glUniformMatrix4fv(loc_mat_m, 1, GL_TRUE, mat_m)
        
        # bind VBO and VAO
        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        
        # actual draw command
        glLineWidth(self.linewidth)
        glDrawArrays(self.primitive_type, 0, self.elementcount)
        
        # unbind VBO and VAO, not strictly neccessary
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)
        
        self.dirty = False
        
        
    def calculate_model_matrix(self, viewmatrix_inv=None):
        """
        Calculates the Model matrix based upon self.origin and self.scale.
        
        If self.billboard == False, the Model matrix will also be rotated
        determined by self.rotation_angle and self.rotation_axis.
        
        If self.billboard == True and self.billboard_axis == None
        the Model matrix will also be rotated so that the local Z axis
        will face the camera and the local Y axis will be parallel to
        the camera up axis.
        
        If self.billboard == True and self.billboard_axis is either "X",
        "Y", or "Z", the local Z axis will always face the camera, but
        the rotation will be restricted to billboard_axis.
        
        @param viewmatrix_inv
        The inverted View matrix as class QMatrix4x4. Mandatory when
        self.billboard == True, otherwise optional.
        """
        mat_m = QMatrix4x4()
        mat_m.translate(self.origin)
        
        if self.billboard:
            # billboard calulation based on excellent tutorial:
            # http://nehe.gamedev.net/article/billboarding_how_to/18011/
            
            # extract 2nd column which is camera up vector
            cam_up = viewmatrix_inv * QVector4D(0,1,0,0)
            cam_up = QVector3D(cam_up[0], cam_up[1], cam_up[2])
            cam_up.normalize()
            
            # extract 4th column which is camera position
            cam_pos = viewmatrix_inv * QVector4D(0,0,0,1)
            cam_pos = QVector3D(cam_pos[0], cam_pos[1], cam_pos[2])
            
            # calculate self look vector (vector from self.origin to camera)
            bill_look = cam_pos - self.origin
            bill_look.normalize()
            
            if self.billboard_axis == None:
                # Fully aligned billboard, not restricted in axis
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
            
            # View and Model matrices are actually nicely structured!
            # 1st column: right vector
            # 2nd column: up vector
            # 3rd column: look vector
            # 4th column: position
            
            # here we only overwrite right, up and look.
            # Position is already there, and we don't have to change it.
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