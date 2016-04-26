#!/usr/bin/python3

"""
pyglp - Copyright (c) 2015 Michael Franzl

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

import os
import random
import sys
import math

import numpy as np
from scipy.interpolate import griddata


from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QVector3D

import numpy as np
from scipy.interpolate import griddata

import time

import OpenGL
from OpenGL.GL import *

from mainwindow import MainWindow

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    p = window.painter
    
    # ============= CREATE PROGRAMS BEGIN =============
    path = os.path.dirname(os.path.realpath(__file__)) + "/shaders/"
    opts = {
        "uniforms": {
            "mat_m": "Matrix4fv",
            "mat_v": "Matrix4fv",
            "mat_p": "Matrix4fv",
            },
        "attributes": {
            "color": "vec4",
            "position": "vec3",
            }
        }
    p.program_create("simple3d", path + "simple3d-vertex.c", path + "simple3d-fragment.c", opts)
    
    opts = {
        "uniforms": {
            "mat_m": "Matrix4fv",
            },
        "attributes": {
            "color": "vec4",
            "position": "vec3",
            }
        }
    p.program_create("simple2d", path + "simple2d-vertex.c", path + "simple2d-fragment.c", opts)
    
    opts = {
        "uniforms": {
            "mat_m": "Matrix4fv",
            "mat_v": "Matrix4fv",
            "mat_p": "Matrix4fv",
            "height_min": "1f",
            "height_max": "1f",
            },
        "attributes": {
            "position": "vec3",
            }
        }
    p.program_create("heightmap", path + "heightmap-vertex.c", path + "heightmap-fragment.c", opts)
    # ============= CREATE PROGRAMS END =============
    

    # ============= CREATE COMPOUND PRIMITIVES BEGIN =============
    
    # create a "ground" for better orientation
    grid = p.item_create("OrthoLineGrid", "mygrid1", "simple3d", (0,0), (1000,1000), 10)
    

    # Create static 2D overlay text at bottom left corder of window
    i = p.item_create("Text", "mytext2", "simple2d", "pyglpainter (c) 2015 Michael Franzl", (-0.95,-0.95,0), 0.01)
    
    # create the main coordinate system with label
    p.item_create("CoordSystem", "mycs1", "simple3d", (0,0,0), 100, 4)
    
    mycs2 = p.item_create("CoordSystem", "mycs2", "simple3d", (100,300,0), 50, 2)
    mycs2.highlight(True)
    i = p.item_create("Text", "mycslabel", "simple3d", "class CoordSystem", (0, 0, 0), 1)
    i.billboard = True
    i.billboard_axis = "Z"
    
    
    # Draw a "mexican hat" function
    #grid_x = 30
    #grid_y = 10
    
    #dat = np.zeros(grid_x * grid_y, [("position", np.float32, 3), ("color", np.float32, 4)])
    
    #for y in range(0, grid_y):
        #for x in range(0, grid_x):
            #idx = y * grid_x + x
            #i = grid_x/2 - x
            #j = grid_y/2 - y
            #z = 1 * math.sin(math.sqrt(i**2 + j**2)) / (math.sqrt(i**2 + j**2) + 0.1)
            #dat["position"][idx] = (x, y, z)
            #dat["color"][idx] = (1, 1, 1, 1)

    #i = p.item_create("HeightMap", "myheightmap1", "heightmap", grid_x, grid_y, dat, True, (100,400,1), 10)
    
    
    
    grid_x = 100
    grid_y = 100
    
    def func(x, y):
        return x*(1-x)*np.cos(4*np.pi*x) * np.sin(4*np.pi*y**2)**2
    
    gx, gy = np.mgrid[0:1:100j, 0:1:100j]

    dat = np.zeros(100 * 100, [("position", np.float32, 3), ("color", np.float32, 4)])
    i = p.item_create("HeightMap", "myheightmap2", "heightmap", 100, 100, dat, False, (0,0,0), 2)
    
    
    for animation in range(0,10):
        points = np.random.rand(20, 2)
        values = func(points[:,0], points[:,1])
        gz = griddata(points, values, (gx, gy), method='cubic', fill_value=0)
        
        for y in range(0, grid_y):
            for x in range(0, grid_x):
                idx = y * grid_x + x
                dat["position"][idx] = (x, y, 2 + gz[x][y])
                #print(dat["position"][idx])
                dat["color"][idx] = (1, 1, 1, 1)
                
        i.set_data(dat)
        print(animation)
        time.sleep(1)

    

    # ============= CREATE RAW OPENGL PRIMITIVES END =============
   
    
    sys.exit(app.exec_())
    
if __name__ == "__main__":
    main()