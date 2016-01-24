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

import logging
import numpy as np
import ctypes
import sys
import math

from PyQt5.QtGui import QColor, QMatrix4x4, QVector2D, QVector3D, QVector4D, QQuaternion

import OpenGL
from OpenGL.GL import *

from .items.item import Item
from .items.coord_system import CoordSystem
from .items.ortho_line_grid import OrthoLineGrid
from .items.star import Star
from .items.text import Text
from .items.arc import Arc
from .items.circle import Circle
from .items.gcode_path import GcodePath
from .items.height_map import HeightMap

from .shader import Shader

class Program():
    """
    This class represents an OpenGL program.
    """
    
    def __init__(self, label, vertex_filepath, fragment_filepath):
        """
        Create a named OpenGL program, attach shaders to it, and remember.
        
        @param label
        A string containing a unique label for the program that can be
        passed into the item_create() funtion call, which tells the Item
        which shaders to use for its drawing.
        
        @param vertex_filepath
        A string containing the absolute filepath of the GLSL vertex shader
        source code.
        
        @param fragment_filepath
        A string containing the absolute filepath of the GLSL fragment shader
        source code.
        """
        self.id = glCreateProgram()
        self.shader_vertex = Shader(GL_VERTEX_SHADER, vertex_filepath)
        self.shader_fragment = Shader(GL_FRAGMENT_SHADER, fragment_filepath)
        
        glAttachShader(self.id, self.shader_vertex.id)
        glAttachShader(self.id, self.shader_fragment.id)
        
        # link
        glLinkProgram(self.id)
        # TODO: use glGetProgramiv to detect linker errors
        
        # once compiled and linked, the shaders are in the firmware
        # and can be discarded from the application context
        glDetachShader(self.id, self.shader_vertex.id)
        glDetachShader(self.id, self.shader_fragment.id)
        
        self.loc_mat_v = glGetUniformLocation(self.id, "mat_v")
        self.loc_mat_p = glGetUniformLocation(self.id, "mat_p")
        
        self.items = {}
        
        
    def item_create(self, class_name, item_label, *args):
        if not item_label in self.items:
            # create
            klss = self.str_to_class(class_name)
            item = klss(item_label, self.id, *args)
            self.items[item_label] = item
        else:
            item = self.items[item_label]
            
        return item
        
    def items_draw(self, mat_v_inverted):
        for label, item in self.items.items():
            # a draw call usually consists of
            #   1. upload Model matrix to GPU
            #   2. call glBindVertexArray()
            #   3. call glBindBuffer()
            #   4. call glDraw...()
            
            # "billboard" items need camera coordinates which are stored
            # in the inverted View matrix
            item.draw(mat_v_inverted)


    @staticmethod
    def str_to_class(str):
        return getattr(sys.modules[__name__], str)