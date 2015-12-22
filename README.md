# pyglpainter - Python OpenGL Painter

Minimalistic but modern OpenGL drawing for technical applications

This module includes the class PainterWidget, extending
PyQt5's QGLWidget with boilerplate code neccessary
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

Most of the time, calls to `item_create()` are enough to build a 3D
world with interesting objects in it (the name for these objects here
is "items"). Items can be rendered with different shaders.

This project was originally created for a CNC application, but then
extracted from this application and made multi-purpose. The author
believes it contains the simplest and shortest code to quickly utilize
the basic and raw powers of OpenGL. To keep code simple and short, the
project was optimized for technical, line- and triangle based
primitives, not the realism that game engines strive for. The simple
shaders included in this project will draw aliased lines and the
output therefore will look more like computer graphics of the 80's.
But "modern" OpenGL offloads many things into shaders anyway.

This class can either be used for teaching purposes, experimentation,
or as a visualization backend for production-class applications.

## Mouse Navigation

Left Button drag left/right/up/down: Rotate camera left/right/up/down

Middle Button drag left/right/up/down: Move camera left/right/up/down

Wheel rotate up/down: Move camera ahead/back

Right Button drag up/down: Move camera ahead/back (same as wheel)

The FOV (Field of View) is held constant. "Zooming" is rather moving
the camera forward alongs its look axis, which is more natural than
changing the FOV of the camera. Even cameras in movies and TV series
nowadays very, very rarely zoom.

## Installation

Clone this git repository

Then install some dependencies (tested on Debian Jessie)

    apt-get install python3-numpy python3-pyqt5 python3-pyqt5.qtopengl python3-opengl
    
I may have forgotten other dependencies. Please let me know if something is missing.


## Example

All features of pyglpainter are shown in an OpenGL window (install dependencies
first):

    python3 ./example.py
    
#### Individual steps

You first need to create a PyQt5 window, then add to it a PainterWidget
instance (for working code see example.py). Let's say this PainterWidget
instance is the variable `painter`. You then can simply draw a coordinate system:

    mycs1 = painter.item_create("CoordSystem", "mycs1", "simple3d", 12, (0, 0, 0))
    
This means: Painter, create an item of class CoordSystem called "mycs1"
with the program called "simple3d". Scale it by 12 and put its origin to
the world coordinates (0,0,0).
    

## TODO:

* Turn this project into a standards-compliant Python module/package
* Circle and Arc compound primitive made up from line segments
* TRIANGLE_STRIP-based surface compund primitive
* Support of more OpenGL features (textures, lights, etc.)

## License

Copyright (c) 2015 Michael Franzl

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.