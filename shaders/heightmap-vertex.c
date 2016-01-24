#version 120

uniform mat4 mat_m;
uniform mat4 mat_v;
uniform mat4 mat_p;

attribute vec4 color;
attribute vec3 position;

varying vec4 v_color;

void main()
{
  gl_Position = mat_p * mat_v * mat_m * vec4(position, 1.0);
  float h = position.z;
  vec4 blah = color; //
  vec4 x = vec4(color.x, h, h, 1.0);
  v_color = x;
}