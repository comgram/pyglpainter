#!/usr/bin/python3

# copyright Michael Franzl
# MIT License

import sys
from PyQt5.QtWidgets import QApplication

import OpenGL
from OpenGL.GL import *

from classes.mainwindow import MainWindow

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    
    painter = window.painter
    

    # ============= CREATE ITEMS BEGIN =============
    # draw_item() receives arguments: class_name, label, *class_args
    
    
    # CoordSystem class_args: scale, offset, hilight -------
    mycs1 = painter.item_create("CoordSystem", "mycs1", "simple3d", 12, (0, 0, 0))
    
    mycs2 = painter.item_create("CoordSystem", "mycs2", "simple3d", 12, (400, 400, 0), 2, True)
    
    
    # Grid class_args: (x1,y1), (x2,y2), offset, unit ------
    mygrid1 = painter.item_create("Grid", "mygrid1", "simple3d", (0, 0), (1000, 1000), (0, 0, 0), 10) 
    
    
    # Star class_args: scale, origin -----------------------
    mystar1 = painter.item_create("Star", "mystar1", "simple3d", 15, (10, 0, 0))
    mystar2 = painter.item_create("Star", "mystar2", "simple3d", 15, (100, 100, 10))
    
    
    # Plot CNC G-code relative to mycs2 ------------------------
    gcodes = []
    gcodes.append("G0 X20 Y20")
    gcodes.append("G1 X30")
    gcodes.append("G1 X40")
    gcodes.append("G1 X50 Y25")
    coordinate_system_2_origin = (mycs2.origin[0], mycs2.origin[1], mycs2.origin[2])
    cs_offsets = {"G54": coordinate_system_2_origin}
    cs = "G54"
    mygcode1 = painter.item_create("GcodePath", "mygcode1", "simple3d", gcodes, (0,0,0), "G54", cs_offsets)
    
    
    
    
    # === Create arbitrary items ===
    
    # Create an arbitrary line strip -----------------------
    vertexcount = 4
    mylinestrip1 = painter.item_create("Item", "mylinestrip1", "simple3d", vertexcount, GL_LINE_STRIP)
    color = (0.7, 0.2, 0.2, 1)
    mylinestrip1.append((100,100,1), color)
    mylinestrip1.append((150,150,1), color)
    mylinestrip1.append((220,150,1), color)
    mylinestrip1.append((130,100,1), color)
    mylinestrip1.upload()
    
    # Create arbitrary lines -------------------------------
    vertexcount = 4
    mylines2 = painter.item_create("Item", "mylines2", "simple3d", vertexcount, GL_LINES)
    color = (0.2, 0.7, 0.2, 1)
    mylines2.append((200,100,1), color)
    mylines2.append((250,150,1), color)
    mylines2.append((320,150,1), color)
    mylines2.append((230,100,1), color)
    mylines2.upload()
    
    # Create a fully aligned billboard
    vertexcount = 4
    myquad1 = painter.item_create("Item", "myquad1", "simple3d", vertexcount, GL_TRIANGLE_STRIP, False, 2)
    myquad1.billboard = True
    myquad1.billboard_axis = None
    col = (0.2, 0.7, 0.2, 1)
    myquad1.append((0,0,0), col)
    myquad1.append((0,50,0), col)
    myquad1.append((50,0,0), col)
    myquad1.append((50,50,0), col)
    myquad1.set_origin((350, 100, 0))
    myquad1.upload()
    
    # Create a Z-axis aligned billboard
    vertexcount = 4
    myquad2 = painter.item_create("Item", "myquad2", "simple3d", vertexcount, GL_TRIANGLE_STRIP, False, 2)
    myquad2.billboard = True
    myquad2.billboard_axis = "Z"
    col = (0.7, 0.2, 0.7, 1)
    myquad2.append((0,0,0), col)
    myquad2.append((0,50,0), col)
    myquad2.append((50,0,0), col)
    myquad2.append((50,50,0), col)
    myquad2.set_origin((350, 200, 0))
    myquad2.upload()
    
    
    # Create an arbitrary filled triangle with smooth colors
    vertexcount = 4
    mytriangle2 = painter.item_create("Item", "mytriangle2", "simple3d", vertexcount, GL_TRIANGLE_STRIP, True)
    mytriangle2.append((400,100,1), (0.2, 0.7, 0.2, 1))
    mytriangle2.append((450,150,1), (0.7, 0.2, 0.2, 1))
    mytriangle2.append((520,150,1), (0.2, 0.2, 0.7, 1))
    mytriangle2.append((520,150,70), (1, 1, 1, 0.2))
    mytriangle2.upload()
    
    # Create an "overlay" triangle. It uses a different shader and does not rotate with the world.
    vertexcount = 3
    mytriangle3 = painter.item_create("Item", "mytriangle3", "simple2d", vertexcount, GL_TRIANGLES, False, 4)
    mytriangle3.append((-0.9,-0.9,0), (1, 1, 1, 0.5))
    mytriangle3.append((-0.8,-0.8,0), (1, 1, 1, 0.5))
    mytriangle3.append((-0.8,-0.7,0), (1, 1, 1, 0.5))
    mytriangle3.upload()
    # ============= CREATE ITEMS END =============
    
    
    
    # ===== UPDATE ITEMS (OPTIONAL) =====
    # move mystar1
    mystar1.set_origin((50,50,50))
    mystar2.set_scale(100)
    
    mygcode1.highlight_line(2)
    mygcode1.draw()
    
    
    # ===== DELETE ITEMS (OPTIONAL) =====
    painter.item_remove("mystar2")
    
    sys.exit(app.exec_())
    
if __name__ == "__main__":
    main()