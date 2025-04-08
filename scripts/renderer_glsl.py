"""Utility to do a full-screen pass using a GLSL shader."""

import os

import glfw
import OpenGL.GL as gl
import numpy as np


shader_dir = os.path.abspath(os.path.join(__file__, "..", "..", "glsl"))

VERTEX_SHADER = """
#version 330 core
layout (location = 0) in vec2 aPos;
void main() {
    gl_Position = vec4(aPos, 0.0, 1.0);
}
"""

FRAGMENT_SHADER = """
#version 330 core
out vec4 FragColor;
uniform sampler2D inputTexture;

AA_SHADER

void main() {
    ivec2 resolution = textureSize(inputTexture, 0).xy; // 0 = mip level
    FragColor = aa_shader(inputTexture, gl_FragCoord.xy);
}

"""


class GlslFullscreenRenderer:
    SHADER = "noaa.glsl"  # filename of the shader to invoke

    def __init__(self):
        self.shader_program = None
        self.texture = None
        self.width = 0
        self.height = 0

    def compile_shader(self, source, shader_type):
        shader = gl.glCreateShader(shader_type)
        gl.glShaderSource(shader, source)
        gl.glCompileShader(shader)
        if not gl.glGetShaderiv(shader, gl.GL_COMPILE_STATUS):
            error = gl.glGetShaderInfoLog(shader)
            raise RuntimeError(f"Shader compilation failed: {error}")
        return shader

    def create_shader_program(self):
        vertex_code = VERTEX_SHADER
        aa_code = open(os.path.join(shader_dir, self.SHADER), "rb").read().decode()
        fragment_code = FRAGMENT_SHADER.replace("AA_SHADER", aa_code)

        vertex_shader = self.compile_shader(vertex_code, gl.GL_VERTEX_SHADER)
        fragment_shader = self.compile_shader(fragment_code, gl.GL_FRAGMENT_SHADER)
        program = gl.glCreateProgram()
        gl.glAttachShader(program, vertex_shader)
        gl.glAttachShader(program, fragment_shader)
        gl.glLinkProgram(program)
        if not gl.glGetProgramiv(program, gl.GL_LINK_STATUS):
            error = gl.glGetProgramInfoLog(program)
            raise RuntimeError(f"Shader linking failed: {error}")
        gl.glDeleteShader(vertex_shader)
        gl.glDeleteShader(fragment_shader)
        return program

    def create_texture(self, image):
        self.width, self.height = image.shape[1], image.shape[0]
        texture = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, texture)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
        gl.glTexImage2D(
            gl.GL_TEXTURE_2D,
            0,
            gl.GL_RGBA,
            self.width,
            self.height,
            0,
            gl.GL_RGBA,
            gl.GL_UNSIGNED_BYTE,
            image,
        )
        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
        return texture

    def render(self, image):
        if not glfw.init():
            raise RuntimeError("Failed to initialize GLFW")

        glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

        window = glfw.create_window(800, 600, "Offscreen", None, None)
        if not window:
            glfw.terminate()
            raise RuntimeError("Failed to create GLFW window")

        glfw.make_context_current(window)
        self.texture = self.create_texture(image)
        self.shader_program = self.create_shader_program()

        quad_vertices = np.array(
            [
                -1.0,
                -1.0,
                0.0,
                0.0,
                1.0,
                -1.0,
                1.0,
                0.0,
                -1.0,
                1.0,
                0.0,
                1.0,
                -1.0,
                1.0,
                0.0,
                1.0,
                1.0,
                -1.0,
                1.0,
                0.0,
                1.0,
                1.0,
                1.0,
                1.0,
            ],
            dtype=np.float32,
        )

        vao = gl.glGenVertexArrays(1)
        vbo = gl.glGenBuffers(1)
        gl.glBindVertexArray(vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo)
        gl.glBufferData(
            gl.GL_ARRAY_BUFFER, quad_vertices.nbytes, quad_vertices, gl.GL_STATIC_DRAW
        )
        gl.glVertexAttribPointer(
            0,
            2,
            gl.GL_FLOAT,
            gl.GL_FALSE,
            4 * quad_vertices.itemsize,
            gl.ctypes.c_void_p(0),
        )
        gl.glEnableVertexAttribArray(0)
        # gl.glVertexAttribPointer(1, 2, gl.GL_FLOAT, gl.GL_FALSE, 4 * quad_vertices.itemsize, gl.ctypes.c_void_p(2 * quad_vertices.itemsize))
        # gl.glEnableVertexAttribArray(1)

        fbo = gl.glGenFramebuffers(1)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, fbo)
        output_texture = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, output_texture)
        gl.glTexImage2D(
            gl.GL_TEXTURE_2D,
            0,
            gl.GL_RGBA,
            self.width,
            self.height,
            0,
            gl.GL_RGBA,
            gl.GL_UNSIGNED_BYTE,
            None,
        )
        gl.glFramebufferTexture2D(
            gl.GL_FRAMEBUFFER,
            gl.GL_COLOR_ATTACHMENT0,
            gl.GL_TEXTURE_2D,
            output_texture,
            0,
        )

        gl.glViewport(0, 0, self.width, self.height)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glUseProgram(self.shader_program)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture)
        gl.glBindVertexArray(vao)
        gl.glDrawArrays(gl.GL_TRIANGLES, 0, 6)

        result = gl.glReadPixels(
            0, 0, self.width, self.height, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE
        )
        result_image = np.frombuffer(result, dtype=np.uint8).reshape(
            (self.height, self.width, 4)
        )

        gl.glDeleteFramebuffers(1, [fbo])
        gl.glDeleteTextures(1, [output_texture])
        glfw.terminate()

        return result_image
