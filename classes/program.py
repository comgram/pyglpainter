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
    
    def __init__(self, label, vertex_filepath, fragment_filepath, shader_opts):
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
        self.label = label
        self.shader_vertex = Shader(GL_VERTEX_SHADER, vertex_filepath)
        self.shader_fragment = Shader(GL_FRAGMENT_SHADER, fragment_filepath)
        
        self.shader_opts = shader_opts
        
        glAttachShader(self.id, self.shader_vertex.id)
        glAttachShader(self.id, self.shader_fragment.id)
        
        # link
        glLinkProgram(self.id)
        link_result = glGetProgramiv(self.id, GL_LINK_STATUS)
        if (link_result == 0):
            raise RuntimeError("Error in LINKING")
        #print("SHADER LINK", link_result)
        
        # once compiled and linked, the shaders are in the firmware
        # and can be discarded from the application context
        glDetachShader(self.id, self.shader_vertex.id)
        glDetachShader(self.id, self.shader_fragment.id)
        
        self.locations = {
            "uniforms": {},
            "attributes": {}
            }
        
        self.uniform_function_dispatcher = {
            "Matrix4fv": glUniformMatrix4fv,
            "1f": glUniform1f,
            }
        
        for varname, tpe in shader_opts["uniforms"].items():
            self.locations["uniforms"][varname] = glGetUniformLocation(self.id, varname)
            
        for varname, tpe in shader_opts["attributes"].items():
            self.locations["attributes"][varname] = glGetAttribLocation(self.id, varname)
        
        self.items = {}
        
        
    def item_create(self, class_name, item_label, *args):
        if not item_label in self.items:
            # create
            klss = self.str_to_class(class_name)
            item = klss(item_label, self, *args)
            self.items[item_label] = item
            
            item.setup_vao(self.locations)
            item.upload()
        else:
            item = self.items[item_label]
            
        return item
        
        
    def set_uniform(self, key, val):
        if key in self.locations["uniforms"]:
            function_string = self.shader_opts["uniforms"][key]
            location = self.locations["uniforms"][key]
            function = self.uniform_function_dispatcher[function_string]
            
            # see https://www.opengl.org/sdk/docs/man/html/glUniform.xhtml
            if "Matrix" in function_string:
                count = 1
                transpose = GL_TRUE
                function(location, count, transpose, val)
            elif "v" in function_string:
                function(location, count, val)
            else:
                print("set_uniform", key, val)
                function(location, *val)
                
            
        else:
          print("Warning: set_uniform(): Uniform {} is not used in the shader.".format(key))


    def items_draw(self, mat_v_inverted):
        for label, item in self.items.items():
            item.draw(mat_v_inverted)


    @staticmethod
    def str_to_class(str):
        return getattr(sys.modules[__name__], str)