import sys
import logging
import numpy as np
import ctypes
import sys
import math
import os

import OpenGL
OpenGL.ERROR_CHECKING = True
OpenGL.FULL_LOGGING = True
from OpenGL.GL import *

from .item import *


class PainterWidget(QGLWidget):
    """
    This Qt Widget implements an OpenGL viewport providing mouse
    interactivity in the classical zoom-rotate-pan fashion via the
    trackball (arcball) model, providing reusable 'boilerplate' code
    neccessary for developing simple to complex OpenGL applications.
    
    It uses Qt classes rather than Glut because Qt provides
    many advanced math functions neccessary for convenient mouse
    interactions involving quaternions.
    
    You should create a subclass that draws objects in the OpenGL scene
    by instantiating objects from the Item class, which is also part
    of this project.
    
    This class has been kept as simple and concise as possible, but can
    nevertheless be the basis of simple as well as advanced OpenGl projects.
    
    It has been developed and tested with Qt5 and Python3 in Debian Jessie.
    """
    
    __version__ = "0.1.0"
    
    def __init__(self, parent=None):
        """ Initialization of translate, rotate, zoom states.
        """
        super(PainterWidget, self).__init__(parent)
        print(glGetString(GL_EXTENSIONS))
        
        # Setup inital world Rotation state
        self._mouse_rotation_start_vec = QVector3D()
        self._rotation_quat = QQuaternion()
        self._rotation_quat_start = self._rotation_quat
        self._rotation_axis = QVector3D()
        
        # Setup initial world Translation state
        self._translation_vec = QVector3D(-150, -150, -350) # looking down the Z axis
        self._translation_vec_start = self._translation_vec
        
        # Setup inital Zoom state
        self._zoom = 3

        # The width and height of the window. resizeGL() will set them.
        self.width = None
        self.height = None
        
        # Rather than repainting the scene on each mouse event, we repaint at fixed timer intervals.
        self.dirty = True
        
        # Setup our only and main timer
        self.timer = QTimer()
        self.timer.timeout.connect(self._timer_timeout)

        self.programs = {}
        
        # This will contain all items (3D objects) in the scene
        self.items = {}
        
        
    

    def initializeGL(self):
        """
        This function is called once on application startup. See Qt Docs.
        """
        print("initializeGL called")
        
        print("OPENGL VERSION", glGetString(GL_VERSION))
        print("OPENGL VENDOR", glGetString(GL_VENDOR))
        print("OPENGL RENDERER", glGetString(GL_RENDERER))
        print("OPENGL GLSL VERSION", glGetString(GL_SHADING_LANGUAGE_VERSION))
        
        self.create_program("simple3d", "simple3d-vertex.c", "simple3d-fragment.c")
        self.create_program("simple2d", "simple2d-vertex.c", "simple2d-fragment.c")
        #glUseProgram(self.programs["simple3d"])
        
        # some global OpenGL settings
        glEnable(GL_DEPTH_TEST)
        glEnable (GL_BLEND)
        glBlendFunc (GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        # Try smooth lines. this only works on some GPUs.
        # The only reliable way to have smooth lines nowadays is to 
        # write appropriate shaders for it
        glEnable (GL_LINE_SMOOTH)
        glHint (GL_LINE_SMOOTH_HINT, GL_DONT_CARE)
        
        glClearColor(0, 0, 0, 1.0)

        # fire the timer every 10 milliseconds
        # this will re-draw the scene if self.dirty is True
        self.timer.start(10)


    def create_program(self, label, vertex_filename, fragment_filename):
        prog = glCreateProgram()
        
        # create vertex and fragment shaders which are temporary
        vertex   = glCreateShader(GL_VERTEX_SHADER)
        fragment = glCreateShader(GL_FRAGMENT_SHADER)
        
        # set the GLSL sources
        with open(os.path.dirname(os.path.realpath(__file__)) + "/shaders/" + vertex_filename, "r") as f: vertex_code = f.read()
        with open(os.path.dirname(os.path.realpath(__file__)) + "/shaders/" + fragment_filename, "r") as f: fragment_code = f.read()
        glShaderSource(vertex, vertex_code)
        glShaderSource(fragment, fragment_code)
        
        # compile shaders
        glCompileShader(vertex)
        glCompileShader(fragment)
        
        # associate the shaders with the program
        glAttachShader(prog, vertex)
        glAttachShader(prog, fragment)
        
        # link the program
        glLinkProgram(prog)
        
        # once compiled and linked, the shaders are in the firmware
        # and can be discarded from the application context
        glDetachShader(prog, vertex)
        glDetachShader(prog, fragment)
        
        self.programs[label] = prog
        
        
    def remove_item(self, label):
        """ delete a previously created scene item
        """
        if label in self.items:
            self.items[label].remove()
            del self.items[label]
            self.dirty = True
        

    def paintGL(self):
        """ This function is automatially called by the Qt libraries
        whenever updateGL() has been called. This happens for example
        when the window is resized or moved or when it is marked as
        'dirty' by the window manager. It also fires during mouse
        interactivity.
        
        paintGL() traditionally is structured in the following way:
        
        1. Call to glClear()
        2. Uploading of View and Projection matrices, controlling the 
           position and rotation of the actually non-existing "camera"
           in the scene.
        3. For each object in the scene:
            a. Uploading of Model matrix controlling the translation,
            scale, and rotation of the object
            b. Binding the data of the object
            c. Drawing the data of the object
        """
        print("paintGL called")
        
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        for key, prog in self.programs.items():
            glUseProgram(prog)
            
            # ======= VIEW MATRIX BEGIN ==========
            # rotate and translate the View matrix by mouse controlled vectors
            mat_v = QMatrix4x4() # start with a unity matrix
            
            # the order of translate and rotate is significant!
            # here we do traslate/rotate/translate for subjectively good mouse interaction
            mat_v.translate(self._translation_vec) # math is done by Qt!
            mat_v.rotate(self._rotation_quat) # math is done by Qt!
            mat_v.translate(self._translation_vec) # math is done by Qt!
            
            
            mat_v = Item.qt_mat_to_array(mat_v) # Transform Qt object to Python list
            
            # make the View matrix accessible to the vertex shader as the variable name "mat_v"
            loc_mat_v = glGetUniformLocation(prog, "mat_v")
            # copy the data into the "mat_v" GPU variable
            glUniformMatrix4fv(loc_mat_v, 1, GL_TRUE, mat_v)
            # ======= PROJECTION MATRIX END ==========
            
            
            # ======= PROJECTION MATRIX BEGIN ==========
            # calculate the aspect ratio of the window
            
            mat_p = QMatrix4x4() # start with a unity matrix
            mat_p.perspective(90, self.aspect, 0.1, 100000) # math is done by Qt!
            
            mat_p = Item.qt_mat_to_array(mat_p) #Transform Qt object to Python list
            
            # make the View matrix accessible to the vertex shader as the variable name "mat_p"
            loc_mat_p = glGetUniformLocation(prog, "mat_p")
            # copy the data into the "mat_p" GPU variable
            glUniformMatrix4fv(loc_mat_p, 1, GL_TRUE, mat_p)
            # ======= PROJECTION MATRIX END ==========
            
            
            # Each Item knows how to draw() itself (see step 3 in comment above)
            for key, item in self.items.items():
                if item.program == prog:
                    item.draw()
      
        # Swapping the OpenGL buffer is done automatically by Qt.


    def resizeGL(self, width, height):
        """ Called by the Qt libraries whenever the window is resized
        """
        print("resizeGL called")
        self.width = width
        self.height = height
        self.aspect = width / height
        glViewport(0, 0, width, height)


    """ Called by the Qt libraries whenever the window receives a mouse click.
    Left button is used to rotate. Middle button is used to pan/translate.
    Note that this simply sets the "starting" values before the mouse is moved.
    The actual changes of the translation and rotation vectors are calculated in
    mouseMoveEvent()
    """
    def mousePressEvent(self, event):
        btns = event.buttons()
        x = event.localPos().x()
        y = event.localPos().y()
        
        if btns & Qt.LeftButton:
            self._mouse_rotation_start_vec = self._find_trackball_vector(x, y)
            self._rotation_quat_start = self._rotation_quat
            
        elif btns & (Qt.MidButton):
            self._mouse_translation_vec_current = QVector3D(x, -y, 0)
            self._translation_vec_start = self._translation_vec
        
        
    """ Called by the Qt libraries whenever the window receives a mouse wheel change.
    This is used for zooming.
    """
    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        
        if delta > 0:
            # zoom in
            self._zoom = self._zoom * 1.02
        else:
            # zoom out
            self._zoom = self._zoom * 0.98
            
        print("Zoom: {}".format(self._zoom))
        
        # We use the zoom value not for actual zooming like a camera, but to
        # translate the Z axis of the translation vector for the View matrix.
        # This is, in my opinion, more natural, because in reality you would
        # translate your eyes towards an object to see more details.

        self._translation_vec = QVector3D(
            self._translation_vec[0],
            self._translation_vec[1],
            self._translation_vec[2] + delta / (2 * self._zoom))
        
        # re-paint at the next timer tick
        self.dirty = True
            

    def mouseReleaseEvent(self, event):
        # nothing to be done here.
        pass


    def mouseMoveEvent(self, event):
        btns = event.buttons()
        x = event.localPos().x()
        y = event.localPos().y()
        
        if btns & Qt.LeftButton:
            # rotation via quaternions, see
            # https://en.wikipedia.org/wiki/Quaternions_and_spatial_rotation
            
            # get current vector from sphere/trackball center to surface
            mouse_rotation_current_vec = self._find_trackball_vector(x, y)
            
            # get the angle between the vector at mouse click
            # and the current vector
            angle_between = PainterWidget.angle_between(mouse_rotation_current_vec, self._mouse_rotation_start_vec)
            
            angle_between *= 20 # arbitrary amplification for faster rotation
            
            # get the rotation axis which is perpendicular to both vectors
            rotation_axis = QVector3D.crossProduct(
                self._mouse_rotation_start_vec,
                mouse_rotation_current_vec)
            
            # create a rotated normalized quaternion
            delta = QQuaternion.fromAxisAndAngle(rotation_axis, angle_between)
            delta.normalize()
            
            # rotate self._rotation_quat (used to rotate the View matrix)
            self._rotation_quat = delta * self._rotation_quat_start
            self._rotation_quat.normalize()
            
        elif btns & Qt.MidButton:
            # simple X-Y translation, sensitivity depending on zoom
            self._translation_vec = self._translation_vec_start + (QVector3D(x, -y, 0) - self._mouse_translation_vec_current) / self._zoom * 2
        
        # re-draw at next timer tick
        self.dirty = True
        
        
    def _find_trackball_vector(self, px, py):
        """
        Emulate a track ball. Find a vector from center of virtual sphere
        to its surface. If outside of sphere, find a vector to surface of
        a hyperbolic sheet to avoid discontinuities in rotation.
        
        It follows the principles outlined here:
        https://www.opengl.org/wiki/Object_Mouse_Trackball
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
    
    
    def item_create(self, class_name, label, program_name, *args):
        if not label in self.items:
            # create
            prog = self.programs[program_name]
            klss = self.str_to_class(class_name)
            item = klss(label, prog, *args)
            self.items[label] = item
        else:
            item = self.items[label]
        return item
    
    
    def item_remove(self, label):
        item = None
        if label in self.items:
            item = self.items[label]
            item.remove()
            del self.items[label]
        return item
    

    @staticmethod
    def angle_between(v1, v2):
        return math.acos(QVector3D.dotProduct(v1, v2) / (v1.length() * v2.length()))
    
    
    @staticmethod
    def str_to_class(str):
        return getattr(sys.modules[__name__], str)