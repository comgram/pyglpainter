"""
pyglpainter - Copyright (c) 2015 Michael Franzl

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import sys
import logging
import numpy as np
import ctypes
import sys
import math
import os

from PyQt5.QtGui import QColor, QMatrix4x4, QVector2D, QVector3D, QVector4D, QQuaternion
from PyQt5.QtOpenGL import QGLWidget
from PyQt5.QtCore import pyqtSignal, QPoint, Qt, QSize, QTimer

import OpenGL
OpenGL.ERROR_CHECKING = True
OpenGL.FULL_LOGGING = True
from OpenGL.GL import *

from .items.base_item import BaseItem
from .items.coord_system import CoordSystem
from .items.ortho_line_grid import OrthoLineGrid
from .items.star import Star
from .items.text import Text
from .items.gcode_path import GcodePath


class PainterWidget(QGLWidget):
    """
    This class extends PyQt5's QGLWidget with boilerplate code neccessary
    for applications which want to build a classical orthagnoal 3D world
    in which the user can interactively navigate with the mouse via the
    classical (and expected) Pan-Zoom-Rotate paradigm implemented via a
    virtual trackball (using quaternions for rotations).
    
    This class is especially useful for technical visualizations in 3D
    space. It provides a simple Python API to draw raw OpenGL primitives
    (LINES, LINE_STRIP, TRIANGLES, etc.) as well as a number of useful
    composite primitives rendered by this class itself (Grid, Star,
    CoordSystem, Text, etc., see files in classes/items). As a bonus,
    all objects/items can either be drawn as real 3D world entities which
    optionally support "billboard" mode (fully camera-aligned or arbitrary-
    axis aligned), or as a 2D overlay.
    
    It uses the "modern", shader-based, OpenGL API rather than the
    deprecated "fixed pipeline" and was developed for Python version 3
    and Qt version 5.
    
    Model, View and Projection matrices are calculated on the CPU, and
    then utilized in the GPU.
    
    Qt has been chosen not only because it provides the GL environment
    but also vector, matrix and quaternion math. A port of this Python
    code into native Qt C++ is therefore trivial.
    
    Look at example.py, part of this project, to see how this class can
    be used. If you need more functionality, consider subclassing.
    
    Most of the time, calls to item_create() are enough to build a 3D
    world with interesting objects in it (the name for these objects here
    is "items"). This class supports items with different shaders.
    
    This project was originally created for a CNC application, but then
    extracted from this application and made multi-purpose. The author
    believes it contains the simplest and shortest code to quickly utilize
    the basic and raw powers of OpenGL. To keep code simple and short, the
    project was optimized for technical, line- and triangle based
    primitives, not the realism that game engines strive for. The simple
    shaders included in this project will draw aliased lines and the
    output therefore will look more like computer graphics of the 80's.
    But "modern" OpenGL moves all of the realism algorithms into shaders
    which cannot therefore be part of the CPU application supplying raw
    vertex attributes.
    
    This class can either be used for teaching purposes, experimentation,
    or as a visualization backend for production-class applications.
    
    Mouse Navigation:
    
    Left Button drag left/right/up/down: Rotate camera left/right/up/down
    Middle Button drag left/right/up/down: Move camera left/right/up/down
    Wheel rotate up/down: Move camera ahead/back
    Right Button drag up/down: Move camera ahead/back (same as wheel)
    
    The FOV (Field of View) is held constant. "Zooming" is rather moving
    the camera ahead, which is more natural than changing the FOV of the 
    camera. Even cameras in movies and TV series very, very rarely zoom
    any more.
    
    TODO:
    * Circle and Arc compound primitive made up from line segments
    * TRIANGLE_STRIP-based surface compund primitive
    * Support of more OpenGL features (textures, lights, etc.)
    """
    
    __version__ = "0.1.0"
    
    def __init__(self, parent=None):
        super(PainterWidget, self).__init__(parent)
        
        self.mat_v = QMatrix4x4() # the current View matrix
        self.mat_v_inverted = QMatrix4x4() # the current inverse View matrix
        
        self.mat_p = QMatrix4x4() # the current Projection matrix
        
        self.cam_right = QVector3D() # the current camera right direction
        self.cam_up = QVector3D() # the current camera up direction
        self.cam_look = QVector3D() # the current camera look direction
        self.cam_pos = QVector3D() # the current camera position
        
        self.fov = 90 # the current field of view for the projection matrix

        # The width and height of the window. resizeGL() will set them.
        self.width = None
        self.height = None
        
        # This will contain instances of class Item (objects) in the scene
        self.items = {}
        
        # Rather than repainting the scene on each mouse event,
        # we repaint at fixed timer intervals.
        self.dirty = True
        
        
        # Setup our only and main timer
        self._timer = QTimer()
        self._timer.timeout.connect(self._timer_timeout)

        # contains OpenGL "programs" of different shaders
        self._programs = {}
                
        # Setup inital world Rotation states
        self._rotation_quat = QQuaternion() # to rotate the View matrix
        self._rotation_quat_start = None # state for mouse click
        self._mouse_rotation_start_vec = None # state for mouse click
        
        # Setup initial world Translation states
        self._translation_vec = QVector3D(-150, -150, -350) # to translate the View matrix
        self._translation_vec_start = None # state for mouse click

        self._mouse_fov_start = None # state for mouse click
    

    def initializeGL(self):
        """
        This function is called once on application startup. See Qt Docs.
        """
        print("initializeGL called")
        
        # output some useful information
        print("OPENGL EXTENSIONS", glGetString(GL_EXTENSIONS))
        print("OPENGL VERSION", glGetString(GL_VERSION))
        print("OPENGL VENDOR", glGetString(GL_VENDOR))
        print("OPENGL RENDERER", glGetString(GL_RENDERER))
        print("OPENGL GLSL VERSION", glGetString(GL_SHADING_LANGUAGE_VERSION))
        
        # some global OpenGL settings
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        # Try smooth lines. this only works on some GPUs.
        # The only reliable way to have smooth lines nowadays is to 
        # write appropriate shaders for it
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_DONT_CARE)
        
        # the world background color
        glClearColor(0, 0, 0, 1.0)

        # fire the timer every 10 milliseconds, yielding a maximum of 100 fps
        # this will re-draw the scene if self.dirty is True
        self._timer.start(10)


    def program_create(self, label, vertex_filepath, fragment_filepath):
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
        prog_id = glCreateProgram()
        
        # create vertex and fragment shaders which are temporary
        vertex_id   = glCreateShader(GL_VERTEX_SHADER)
        fragment_id = glCreateShader(GL_FRAGMENT_SHADER)
        
        # set the GLSL sources
        with open(vertex_filepath, "r") as f: vertex_code = f.read()
        with open(fragment_filepath, "r") as f: fragment_code = f.read()
        
        glShaderSource(vertex_id, vertex_code)
        glShaderSource(fragment_id, fragment_code)
        
        # compile shaders
        glCompileShader(vertex_id)
        glCompileShader(fragment_id)
        
        # associate the shaders with the program
        glAttachShader(prog_id, vertex_id)
        glAttachShader(prog_id, fragment_id)
        
        # link the program
        glLinkProgram(prog_id)
        
        # once compiled and linked, the shaders are in the firmware
        # and can be discarded from the application context
        glDetachShader(prog_id, vertex_id)
        glDetachShader(prog_id, fragment_id)
        
        # remember the program id for later
        self._programs[label] = prog_id
        
        
    def item_create(self, class_name, label, program_name, *args):
        """ Creates an item and returns the object for further manipulation.
        
        @param class_name
        A string of the class name that should be instantiated and drawn.
        e.g. "Star", "CoordSystem" etc. See item.py for available classes.
        
        @param label
        A string containing the unique label for this item.
        
        @param program_name
        A string containing the label of a previously created program.
        The item will be rendered using this program/shaders.
        
        @param *args
        Arguments to pass to the initialization method of the given
        `class_name`. See item.py for the required arguments.
        """
        if not label in self.items:
            # create
            prog = self._programs[program_name]
            klss = self.str_to_class(class_name)
            item = klss(label, prog, *args)
            self.items[label] = item
        else:
            item = self.items[label]
        return item
    
    
    def item_remove(self, label):
        """ Removes a previously created item. It will disappear from the
        scene.
        
        @param label
        A string containing the unique label of the previously create item.
        """
        if label in self.items:
            item = self.items[label]
            item.remove()
            del self.items[label]
        

    def paintGL(self):
        """ This function is automatially called by the Qt libraries
        whenever updateGL() has been called. This happens for example
        when the window is resized or moved or when it is marked as
        'dirty' by the window manager. It also fires during mouse
        interactivity.
        
        paintGL() traditionally is structured in the following way, see
        also OpenGL documentation:
        
        1. Call to glClear()
        2. Uploading of per-frame CPU-calculated data if they have changed
           since the last call. This can include:
           a. Projection and View matrices
           b. For each object in the scene:
               - Model Matrix (translation, scale, rotation of object)
        3. For each object in the scene:
           a. Binding the data buffers of the object
           b. Drawing of the object
        """
        #print("paintGL called")
        
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # loop over all programs/shaders
        # first switch to that program (expensive operation)
        # then draw all items belonging to that program
        for key, prog_id in self._programs.items():
            glUseProgram(prog_id)
            
            # ======= VIEW MATRIX BEGIN ==========
            # start with an empty matrix
            self.mat_v = QMatrix4x4()
            
            # rotate the world
            self.mat_v.rotate(self._rotation_quat) # math is done by Qt!
            
            # translate the world
            self.mat_v.translate(self._translation_vec) # math is done by Qt!
            
            # calculate inverse view matrix which contains
            # camera right, up, look directions, and camera position
            # Items in "billboard" mode will need this to know where the camera is
            self.mat_v_inverted = self.mat_v.inverted()[0]
            
            # the right direction of the camera
            cam_right = self.mat_v_inverted * QVector4D(1,0,0,0) # extract 1st column
            self.cam_right = QVector3D(cam_right[0], cam_right[1], cam_right[2])
            
            # the up direction of the camera
            cam_up = self.mat_v_inverted * QVector4D(0,1,0,0) # extract 2nd column
            self.cam_up = QVector3D(cam_up[0], cam_up[1], cam_up[2])
            
            # the look direction of the camera
            cam_look = self.mat_v_inverted * QVector4D(0,0,1,0) # extract 3rd column
            self.cam_look = QVector3D(cam_look[0], cam_look[1], cam_look[2])
            
            # the postion of the camera
            cam_pos = self.mat_v_inverted * QVector4D(0,0,0,1) # extract 4th column
            self.cam_pos = QVector3D(cam_pos[0], cam_pos[1], cam_pos[2])
            
            # upload the View matrix into the GPU,
            # accessible to the vertex shader under the variable name "mat_v"
            mat_v_list = PainterWidget.qt_mat_to_list(self.mat_v) # Transform Qt object to Python list
            loc_mat_v = glGetUniformLocation(prog_id, "mat_v")
            glUniformMatrix4fv(loc_mat_v, 1, GL_TRUE, mat_v_list)
            # ======= VIEW MATRIX END ==========
            
            
            # ======= PROJECTION MATRIX BEGIN ==========
            self.mat_p = QMatrix4x4() # start with an empty matrix
            self.mat_p.perspective(self.fov, self.aspect, 0.1, 100000) # math is done by Qt!
            # ======= PROJECTION MATRIX END ==========
            
            
            # upload the Projection matrix into the GPU,
            # accessible to the vertex shader under the variable name "mat_p"
            mat_p_list = PainterWidget.qt_mat_to_list(self.mat_p) #Transform Qt object to Python list
            loc_mat_p = glGetUniformLocation(prog_id, "mat_p")
            glUniformMatrix4fv(loc_mat_p, 1, GL_TRUE, mat_p_list)
            # ======= PROJECTION MATRIX END ==========
            
            
            # Draw items belonging to this program
            for key, item in self.items.items():
                if item.program_id == prog_id:
                    # a draw call usually consists of
                    #   1. upload Model matrix to GPU
                    #   2. call glBindVertexArray()
                    #   3. call glBindBuffer()
                    #   4. call glDraw...()
                    
                    # "billboard" items need camera coordinates which are stored
                    # in the inverted View matrix
                    item.draw(self.mat_v_inverted)
      
        # nothing more to do here!
        # Swapping the OpenGL buffer is done automatically by Qt.


    def resizeGL(self, width, height):
        """ Called by the Qt libraries whenever the window is resized
        """
        print("resizeGL called")
        self.width = width
        self.height = height
        self.aspect = width / height
        glViewport(0, 0, width, height)


    def mousePressEvent(self, event):
        """ Called by the Qt libraries whenever the window receives a mouse click.
        
        For info on mouse navigation see comments for this class above.
        
        Note that this method simply sets the "starting" values before
        the mouse is moved. The actual translation and rotation vectors
        are calculated in mouseMoveEvent().
        """
        btns = event.buttons()
        x = event.localPos().x()
        y = event.localPos().y()
        
        if btns & Qt.LeftButton:
            self._mouse_rotation_start_vec = self._find_trackball_vector(x, y)
            self._rotation_quat_start = self._rotation_quat
            
        elif btns & (Qt.MidButton):
            self._mouse_translation_start_vec = QVector3D(x, y, 0)
            self._translation_vec_start = self._translation_vec
            
        elif btns & (Qt.RightButton):
            self._mouse_camforward_start = y
            self._translation_vec_start = self._translation_vec
        
        
    def wheelEvent(self, event):
        """
        Called by the Qt libraries whenever the window receives a mouse wheel change.
        
        This is used for zooming, or rather moving the camera ahead.
        """
        delta = event.angleDelta().y()
        
        # move in look direction of camera
        self._translation_vec += self.cam_look * delta / 15
        
        # re-paint at the next timer tick
        self.dirty = True
            

    def mouseReleaseEvent(self, event):
        # nothing to be done here.
        pass


    def mouseMoveEvent(self, event):
        """
        Called by the Qt libraries whenever the window receives a mouse
        move/drag event.
        """
        btns = event.buttons()
        
        # pixel coordinates relative to the window
        x = event.localPos().x()
        y = event.localPos().y()
        
        if btns & Qt.LeftButton:
            # Rotation via emulated trackball using quaternions.
            # For method employed see:
            # https://en.wikipedia.org/wiki/Quaternions_and_spatial_rotation
            
            # get current vector from sphere/trackball center to surface
            mouse_rotation_current_vec = self._find_trackball_vector(x, y)
            
            # get the angle between the vector which was stored at the
            # time of mouse click and the current vector
            angle_between = PainterWidget.angle_between(
                mouse_rotation_current_vec,
                self._mouse_rotation_start_vec)
            
            angle_between *= 20 # arbitrary amplification for faster rotation
            
            # get the rotation axis which is perpendicular to both vectors
            rotation_axis = QVector3D.crossProduct(
                self._mouse_rotation_start_vec,
                mouse_rotation_current_vec)
            
            # create a rotated normalized quaternion corresponding to the
            # drag distance travelled by the mouse since the click
            delta = QQuaternion.fromAxisAndAngle(rotation_axis, angle_between)
            delta.normalize()
            
            # rotate self._rotation_quat (used to rotate the View matrix)
            self._rotation_quat = delta * self._rotation_quat_start
            self._rotation_quat.normalize()
            
        elif btns & Qt.MidButton:
            # Translation left/right and up/down depending on camera orientation
            diff = QVector3D(x, y, 0) - self._mouse_translation_start_vec
            diff_x = diff[0]
            diff_y = diff[1]
            
            self._translation_vec = self._translation_vec_start - self.cam_right * diff_x * 2 + self.cam_up * diff_y * 2
            
        elif btns & Qt.RightButton:
            # Translation forward/backward depending on camera orientation
            diff_y = y - self._mouse_camforward_start
            self._translation_vec = self._translation_vec_start - self.cam_look * diff_y * 2
            
        
        # re-draw at next timer tick
        self.dirty = True
        
        
    def _find_trackball_vector(self, px, py):
        """
        Emulate a track ball. Find a vector from center of virtual sphere
        to its surface. If outside of sphere, find a vector to surface of
        a hyperbolic sheet to avoid discontinuities in rotation.
        
        It follows the principles outlined here:
        https://www.opengl.org/wiki/Object_Mouse_Trackball
        
        @param px
        Integer horizontal pixel coordinate relative to the window
        
        @param px
        Integer vertical pixel coordinate relative to the window
        """
        
        # Calculate the normalized -1..1 (x,y) coords of the mouse in the window.
        # The center of the window has the coordinates (0,0).
        x = px / (self.width / 2) - 1
        y = 1 - py / (self.height / 2)
        
        r = 0.8 # the radius of the virtual trackball
        
        """
        definition of trackball sphere:
            (1) x**2 + y**2 + z**2 = r**2
        
        rewriting (1) to get explicit form of trackball sphere:
            (2) z = sqrt(r**2 - (x**2 + y**2))
            
        explicit form of hyperbola that tangentially touches the trackball sphere:
            (4) z = r**2 / ( 2 * sqrt(x**2 + y**2))
            
        intersection of sphere and hyperbola is defined by the circle ...
            (5) x**2 + y**2 = r**2 / 2
            
        from (5) get radius of intersection circle by setting y to zero:
                x**2 + 0 = r**2 / 2
                with r_transition = x
            (6) r_transition = sqrt(r**2 / 2)
        """
        
        # hypotenuse of x and y coordinates
        hypotenuse = math.sqrt(x**2 + y**2)
        
        # transition radius delimiting sphere and hyperbola, from (6)
        r_transition = math.sqrt(r**2 / 2)

        if hypotenuse < r_transition:
            # mouse is within sphere radius
            # get z on surface of sphere
            z = math.sqrt(r**2 - (x**2 + y**2))
        else:
            # mouse is outside sphere
            # get z on surface of hyperbola
            z = r**2 / (2 * math.sqrt(x**2 + y**2))
            
        # vector from center of sphere to whatever surface has been selected
        vec = QVector3D(x, y, z)
        vec.normalize()
        return vec


    def _timer_timeout(self):
        """
        called regularly from timer
        """
        if self.dirty:
            self.updateGL()
            self.dirty = False
            

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
    def str_to_class(str):
        return getattr(sys.modules[__name__], str)
    

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