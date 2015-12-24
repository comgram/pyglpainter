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

import re
import logging
import math

class GcodePreprocessor:
    
    def __init__(self):
        self.line = ""

        self.do_fractionize_arcs = True
        
        # state information
        self.current_distance_mode = "G90"
        self.current_motion_mode = 0
        self.current_plane_mode = "G17"
        self.position = [None, None, None] # current xyz position, i.e. self.target of last line
        self.target = [None, None, None] # xyz target of current line
        self.offset = [0, 0, 0] # offset of circle center from current xyz position
        
        self.radius = None
        self.contains_radius = False
        
        # precompile regular expressions
        self._axes_regexps = []
        self._axes_words = ["X", "Y", "Z"]
        for i in range(0, 3):
            word = self._axes_words[i]
            self._axes_regexps.append(re.compile(".*" + word + "([-.\d]+)"))
            
        self._offset_regexps = []
        self._offset_words = ["I", "J", "K"]
        for i in range(0, 3):
            word = self._offset_words[i]
            self._offset_regexps.append(re.compile(".*" + word + "([-.\d]+)"))
            
        self._re_radius = re.compile(".*R([-.\d]+)")
        self._re_spindle = re.compile(".*S([-.\d]+)")
        
        self._re_motion_mode = re.compile("G([0123])*([^\\d]|$)")
        self._re_distance_mode = re.compile("(G9[01])([^\d]|$)")
        self._re_plane_mode = re.compile("(G1[789])([^\d]|$)")
        
        # regex to remove all foreign comments except those
        # specific to this library, which begin with _gerbil.
        self._re_comment_bracket_replace = re.compile(r"\(.*?\)")
        self._re_comment_other_replace = re.compile(r"[;%](?!_gerbil.color).*") # keep only color comments
        self._re_comment_all_replace = re.compile(r"[;%].*")
        
        self._arc_count = 0
        
        # put colors in comments for visualization, keys are G modes
        self.colors = {
            0: (.5, .5, .5, 1),  # grey
            1: (.7, .7, 1, 1),   # blue/purple
            2: (1, 0.7, 0.8, 1), # redish
            3: (1, 0.9, 0.7, 1), # red/yellowish
            }
        

    def set_line(self, line):
        self.line = line
        
        
    def tidy(self):
        """
        Strips G-Code not supported by Grbl, comments, and cleans up spaces in G-Code for slightly reduced serial bandwidth. . Set line first with `set_line`. Returns the tidy line. 
        """
        self._strip_comments()
        self._strip_unsupported()
        self._strip()
        return self.line
    
    
    def parse_state(self):
        # parse G0 .. G3 and remember
        m = re.match(self._re_motion_mode, self.line)
        if m: self.current_motion_mode = int(m.group(1))
        
        # parse G90 and G91 and remember
        m = re.match(self._re_distance_mode, self.line)
        if m: self.current_distance_mode = m.group(1)
            
        # parse G17, G18 and G19 and remember
        m = re.match(self._re_plane_mode, self.line)
        if m: self.current_plane_mode = m.group(1)
        
        self._parse_distance_values()
        
        # calculate travelling distance
        self.dist = math.sqrt(self.dists[0] * self.dists[0] + self.dists[1] * self.dists[1] + self.dists[2] * self.dists[2])
        
        
    def fractionize(self):
        """
        Breaks circles into segments.
        """
        result = []
           
        if self.do_fractionize_arcs == True and (self.current_motion_mode == 2 or self.current_motion_mode == 3):
            result = self._fractionize_circular_motion()
            
        else:
            # this motion cannot be fractionized
            # return the line as it was passed in
            result = [self.line]

        return result
    
    
    def done(self):
        # remember last pos
        if not (self.current_motion_mode == 0 or self.current_motion_mode == 1):
            # only G1 and G2 can stay active
            self.current_motion_mode = None 
            
        for i in range(0, 3):
            # loop over X, Y, Z axes
            if self.target[i] != None: # keep state
                self.position[i] = self.target[i]

    
    def _strip_unsupported(self):
        # This silently strips gcode unsupported by Grbl, but ONLY those commands that are safe to strip without making the program deviate from its original purpose. For example it is  safe to strip a tool change. All other encountered unsupported commands should be sent to Grbl nevertheless so that an error is raised. The user then can make an informed decision.
        if ("T" in self.line or # tool change
            "M6" in self.line or # tool change
            re.match("#\d=.*", self.line) # var assignment
            ): 
            self.line = ""
        
        
    def _strip_comments(self):
        # strip comments
        self.line = re.sub(self._re_comment_bracket_replace, "", self.line)
        self.line = re.sub(self._re_comment_other_replace, "", self.line)


    def _strip(self):
        # Remove blank spaces and newlines from beginning and end, and remove blank spaces from the middle of the line.
        self.line = self.line.strip()
        self.line = self.line.replace(" ", "")
        
        
    
    def _fractionize_circular_motion(self):
        """
        This function is a direct port of Grbl's C code into Python (gcode.c)
        with slight refactoring for Python by Michael Franzl.
        This function is copyright (c) Sungeun K. Jeon under GNU General Public License 3
        """
    
        # implies self.current_motion_mode == 2 or self.current_motion_mode == 3
        
        if self.current_plane_mode == "G17":
            axis_0 = 0 # X axis
            axis_1 = 1 # Y axis
            axis_linear = 2 # Z axis
        elif self.current_plane_mode == "G18":
            axis_0 = 2 # Z axis
            axis_1 = 0 # X axis
            axis_linear = 1 # Y axis
        elif self.current_plane_mode == "G19":
            axis_0 = 1 # Y axis
            axis_1 = 2 # Z axis
            axis_linear = 0 # X axis
            
        is_clockwise_arc = True if self.current_motion_mode == 2 else False
            
        # deltas between target and (current) position
        x = self.target[axis_0] - self.position[axis_0]
        y = self.target[axis_1] - self.position[axis_1]
        
        if self.contains_radius:
            # RADIUS MODE
            # R given, no IJK given, self.offset must be calculated
            
            if self.target == self.position:
                self.logger.error("Arc in Radius Mode: Identical start/end {}".format(self.line))
                return [self.line]
            
            h_x2_div_d = 4.0 * self.radius * self.radius - x * x - y * y;
            
            if h_x2_div_d < 0:
                self.logger.error("Arc in Radius Mode: Radius error {}".format(self.line))
                return [self.line]

            # Finish computing h_x2_div_d.
            h_x2_div_d = -math.sqrt(h_x2_div_d) / math.sqrt(x * x + y * y);
            
            if not is_clockwise_arc:
                h_x2_div_d = -h_x2_div_d
    
            if self.radius < 0:
                h_x2_div_d = -h_x2_div_d; 
                self.radius = -self.radius;
                
            self.offset[axis_0] = 0.5*(x-(y*h_x2_div_d))
            self.offset[axis_1] = 0.5*(y+(x*h_x2_div_d))
            
        else:
            # CENTER OFFSET MODE, no R given so must be calculated
            
            if self.offset[axis_0] == None or self.offset[axis_1] == None:
                self.logger.error("Arc in Offset Mode: No offsets in plane")
                return [self.line]
            
            # Arc radius from center to target
            x -= self.offset[axis_0]
            y -= self.offset[axis_1]
            target_r = math.sqrt(x * x + y * y)
            
            # Compute arc radius for mc_arc. Defined from current location to center.
            self.radius = math.sqrt(self.offset[axis_0] * self.offset[axis_0] + self.offset[axis_1] * self.offset[axis_1])
            
            # Compute difference between current location and target radii for final error-checks.
            delta_r = math.fabs(target_r - self.radius);
            if delta_r > 0.005:
                if delta_r > 0.5:
                    self.logger.warning("Arc in Offset Mode: Invalid Target. r={:f} delta_r={:f} {}".format(self.radius, delta_r, self.line))
                if delta_r > (0.001 * self.radius):
                    self.logger.warning("Arc in Offset Mode: Invalid Target. r={:f} delta_r={:f} {}".format(self.radius, delta_r, self.line))
        
        #print("CALLING MC ARC", self.line, self.position, self.target, self.offset, self.radius, axis_0, axis_1, axis_linear, is_clockwise_arc)
        
        gcode_list = self.mc_arc(self.position, self.target, self.offset, self.radius, axis_0, axis_1, axis_linear, is_clockwise_arc)
        
        return gcode_list
        

    def mc_arc(self, position, target, offset, radius, axis_0, axis_1, axis_linear, is_clockwise_arc):
        """
        This function is a direct port of Grbl's C code into Python (motion_control.c)
        with slight refactoring for Python by Michael Franzl.
        This function is copyright (c) Sungeun K. Jeon under GNU General Public License 3
        """
        
        self._arc_count += 1
        
        gcode_list = []
        gcode_list.append(";_gerbil.arc_begin:{}".format(self.line))
        
        col = self.colors[self.current_motion_mode]
        fac = 1 if self._arc_count % 2 == 0 else 0.5
        col = tuple(c * fac for c in col)
        gcode_list.append(";_gerbil.color_begin[{:.2f},{:.2f},{:.2f}]".format(*col))
        
        do_restore_distance_mode = False
        if self.current_distance_mode == "G91":
            # it's bad to concatenate many small floating point segments due to accumulating errors
            # each arc will use G90
            do_restore_distance_mode = True
            gcode_list.append("G90")
        
        center_axis0 = position[axis_0] + offset[axis_0]
        center_axis1 = position[axis_1] + offset[axis_1]
        # radius vector from center to current location
        r_axis0 = -offset[axis_0]
        r_axis1 = -offset[axis_1]
        # radius vector from target to center
        rt_axis0 = target[axis_0] - center_axis0
        rt_axis1 = target[axis_1] - center_axis1
        
        angular_travel = math.atan2(r_axis0 * rt_axis1 - r_axis1 * rt_axis0, r_axis0 * rt_axis0 + r_axis1 * rt_axis1)
        
        arc_tolerance = 0.004
        arc_angular_travel_epsilon = 0.0000005
        
        if is_clockwise_arc: # Correct atan2 output per direction
            if angular_travel >= -arc_angular_travel_epsilon: angular_travel -= 2*math.pi
        else:
            if angular_travel <= arc_angular_travel_epsilon: angular_travel += 2*math.pi
            
       
            
        segments = math.floor(math.fabs(0.5 * angular_travel * radius) / math.sqrt(arc_tolerance * (2 * radius - arc_tolerance)))
        
        #print("angular_travel:{:f}, radius:{:f}, arc_tolerance:{:f}, segments:{:d}".format(angular_travel, radius, arc_tolerance, segments))
        
        words = ["X", "Y", "Z"]
        if segments:
            theta_per_segment = angular_travel / segments
            linear_per_segment = (target[axis_linear] - position[axis_linear]) / segments
            
            position_last = [None, None, None]
            for i in range(1, segments):
                cos_Ti = math.cos(i * theta_per_segment);
                sin_Ti = math.sin(i * theta_per_segment);
                r_axis0 = -offset[axis_0] * cos_Ti + offset[axis_1] * sin_Ti;
                r_axis1 = -offset[axis_0] * sin_Ti - offset[axis_1] * cos_Ti;
            
                position[axis_0] = center_axis0 + r_axis0;
                position[axis_1] = center_axis1 + r_axis1;
                position[axis_linear] += linear_per_segment;

                gcodeline = ""
                if i == 1:
                    gcodeline += "G1"
                    
                for a in range(0,3):
                    if position[a] != position_last[a]: # only write changes
                        txt = "{}{:0.3f}".format(words[a], position[a])
                        txt = txt.rstrip("0").rstrip(".")
                        gcodeline += txt
                        position_last[a] = position[a]
                        
                if i == 1:
                    if self.contains_spindle:
                        # only neccessary at first segment of arc
                        # gcode is a state machine
                        gcodeline += "S{:d}".format(self.spindle)
                    
                gcode_list.append(gcodeline)
            
            
        
        # make sure we arrive at target
        gcodeline = ""
        if segments <= 1:
            gcodeline += "G1"
        
        for a in range(0,3):
            if target[a] != position[a]:
                txt = "{}{:0.3f}".format(words[a], target[a])
                txt = txt.rstrip("0").rstrip(".")
                gcodeline += txt
           
        if segments <= 1 and self.contains_spindle:
            # no segments were rendered (very small arc) so we have to put S here
            gcodeline += "S{:d}".format(self.spindle)
                
        gcode_list.append(gcodeline)
        
        if do_restore_distance_mode == True:
          gcode_list.append(self.current_distance_mode)
          
        gcode_list.append(";_gerbil.color_end")
        gcode_list.append(";_gerbil.arc_end:{}".format(self.line))
        
        return gcode_list
    
       
    def _parse_distance_values(self):
        #self.target = self.position
        
        # look for spindle
        m = re.match(self._re_spindle, self.line)
        self.contains_spindle = True if m else False
        if m: self.spindle = int(m.group(1))
        
        if self.current_motion_mode == 2 or self.current_motion_mode == 3:
            self.offset = [None, None, None]
            for i in range(0, 3):
                # loop over I, J, K offsets
                regexp = self._offset_regexps[i]
                
                m = re.match(regexp, self.line)
                if m: self.offset[i] = float(m.group(1))
                    
            m = re.match(self._re_radius, self.line)
            self.contains_radius = True if m else False
            if m: self.radius = float(m.group(1))

                
        self.dists = [0, 0, 0] # distance traveled by this G-Code cmd in xyz
        for i in range(0, 3):
            # loop over X, Y, Z axes
            regexp = self._axes_regexps[i]
            
            m = re.match(regexp, self.line)
            if m:
                if self.current_distance_mode == "G90":
                    # absolute distances
                    self.target[i] = float(m.group(1))
                    # calculate distance
                    self.dists[i] = self.target[i] - self.position[i]
                else:
                    # G91 relative distances
                    self.dists[i] = float(m.group(1))
                    self.target[i] += self.dists[i]

 