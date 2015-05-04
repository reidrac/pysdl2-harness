#!/usr/bin/env python
"""
harness.Game,
some simple classes to make working with pysdl2 easier.

Copyright (C) 2015 by Juan J. Martinez <jjm@usebox.net>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""
import sys
import os
import ctypes
from collections import namedtuple

try:
    import sdl2
except ImportError as ex:
    sys.exit("SDL2 library not found: %s" % ex)

BitmapFont = namedtuple("BitmapFont", ["texture", "width", "height", "font_map"])

class Renderer(object):
    """Wrapper for the renderer to be used by the draw functions"""
    def __init__(self, renderer):
        self.renderer = renderer

    def draw(self, texture, src_rect=None, dest_rect=None):
        if isinstance(src_rect, tuple):
            src = sdl2.SDL_Rect(*src_rect)
        else:
            src = None

        if isinstance(dest_rect, tuple):
            dest = sdl2.SDL_Rect(*dest_rect)
        else:
            dest = None

        sdl2.SDL_RenderCopy(self.renderer, texture, src, dest)

    def draw_text(self, font, x, y, text, align="left"):
        """
        Render text using a texture.

        Rreturns a new texture.

        Parameters:

            font: font name (load it first with load_bitmap_font).
            x: horizontal position on the screen.
            y: vertical position on the screen.
            text: the text to render.
            align: "left", "right" or "center" (defaults to "left").
        """
        width = len(text) * font.width

        if align == "center":
            x -= width // 2
            y -= font.height // 2
        elif align == "right":
            x -= width

        src = sdl2.SDL_Rect(0, 0, font.width, font.height)
        dest = sdl2.SDL_Rect(0, y, font.width, font.height)

        for i, c in enumerate(text):
            index = font.font_map.find(c)
            src.x = index * font.width
            dest.x = x + i * font.width
            sdl2.SDL_RenderCopy(self.renderer, font.texture, src, dest)

class Game(object):
    """
    Game object.

    Parameters:

        title: windows title
        width: with in pixels of the draw area
        height: height in pixels of the draw area
        zoom: scale up the output, or use 1 to disable

    The Game loop

        Call it once and it will run until the game is quitted (eg, using
        "quit()" method).

        It implements fixed draw (cap a FPS) and fixed updates.

        Define draw functions with the "game.draw" decorator, and update
        functions with the "game.update" decorator.

        The draw functions should expect a "renderer" parameter that
        allows to draw textures and bitmap fonts.

        Example:

        ```python

            game = Game()

            tex = game.load_resource("bitmap.bmp")

            @game.draw
            def draw(renderer):
                renderer.draw(tex)

            game.loop()
        ```

        The update functions should expect a "dt" parameter that provides
        the delta time (time elapsed between updates); in this case fixed
        at UPDATE_DT (1 / UPDATE_FPS).

        Example:

        ```python

            game = Game()

            @game.update
            def update(dt):
                print("%s elapsed" % dt)

            game.loop()
        ```

        Several draw and update functions can be defined and they will be
        run in the same order they were defined.

        The game instance can be accessed from the update function to
        test for key states, quite the game, etc.

    Loading resources

        This method allows loading resources searching for them
        in the paths specified in game.resource_path.

        By default this files will be searched in the "data"
        subdirectory at the same level as the script running
        the game.

        Depending on the resource some extra libraries may be
        required in the system (eg, SDL_Image).

        Resources not in use can be freed using game.free_resources(filename)
        method.

    Bitmap fonts

        game.load_bitmap_font can be used to load a image that will be
        used to draw text with rederer.draw_text.

        Example:
        ```python

            game = Game()

            font = game.load_bitmap_font("font.png", width=6, height=10)

            @game.draw
            def draw(renderer):
                renderer.draw_text(font, 10, 10, "This is a text!")

            game.loop()
        ```

        Fonts can be freed with game.free_resources.

    Useful properties

        Keyboard

        keys: updated in each update loop with the status of all the keys.
        KEY_*: constants to test in the "keys" dictionay.

        Resources

        resource_path: list of paths to search for resources.

    Useful methods

        quit(): quit the game.

        Example:
        ```python

            game = Game()

            @game.update
            def update(dt):

                if game.keys[game.KEY_ESCAPE]:
                    game.quit()

            game.loop()
        ```
    """
    # the update functions will be called a fixed number of FPS
    UPDATE_FPS = 80
    UPDATE_DT = 1.0 / UPDATE_FPS

    # draw frames per second
    FPS = 60

    FONT_MAP = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!?()@:/'., "

    def __init__(self, title=None, width=320, height=200, zoom=1):

        self.title = title.encode() or b"SDL2 Game"
        self.width = width
        self.height = height
        self.zoom = zoom

        self._quit = False
        self.dt = 0
        self.update_handlers = []
        self.draw_handlers = []
        self.resource_path = [os.path.join(os.path.dirname(os.path.realpath(__file__)), "data"),]
        self.resources = {}
        self.bitmap_fonts = {}

        for attr in dir(sdl2):
            if attr.startswith("SDL_SCANCODE_"):
                setattr(self, attr.replace("SDL_SCANCODE_", "KEY_"), getattr(sdl2, attr))

        sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO)

        self.window = sdl2.SDL_CreateWindow(self.title,
                                            sdl2.SDL_WINDOWPOS_CENTERED,
                                            sdl2.SDL_WINDOWPOS_CENTERED,
                                            self.width * self.zoom,
                                            self.height * self.zoom,
                                            sdl2.SDL_WINDOW_HIDDEN
                                            )
        self.renderer = sdl2.SDL_CreateRenderer(self.window, -1, sdl2.SDL_RENDERER_ACCELERATED)
        self.renderer_obj = Renderer(self.renderer)

        if self.zoom != 1:
            sdl2.SDL_RenderSetScale(self.renderer, self.zoom, self.zoom)

    def _update(self, dt):

        self.dt += dt
        while self.dt >= self.UPDATE_DT:
            for update in self.update_handlers:
                update(self.UPDATE_DT)
            self.dt -= dt

    def _draw(self):

        for draw in self.draw_handlers:
            draw(self.renderer_obj)

    def quit(self):
        """Quits the game"""
        self._quit = True

    def loop(self):
        """The game loop"""
        sdl2.SDL_ShowWindow(self.window)

        current = sdl2.SDL_GetTicks()
        while not self._quit:
            event = sdl2.SDL_Event()
            while sdl2.SDL_PollEvent(ctypes.byref(event)) != 0:
                if event.type == sdl2.SDL_QUIT:
                    self._quit = True
                    break

            self.keys = sdl2.SDL_GetKeyboardState(None)

            new = sdl2.SDL_GetTicks()
            self._update(new - current)

            if new - current > 1 / self.FPS:
                sdl2.SDL_RenderClear(self.renderer)
                self._draw()
                sdl2.SDL_RenderPresent(self.renderer)

            current = new

        for resource in self.resources.copy().keys():
            self.free_resource(resource)

        sdl2.SDL_DestroyRenderer(self.renderer)
        sdl2.SDL_HideWindow(self.window)
        sdl2.SDL_DestroyWindow(self.window)

        sdl2.SDL_Quit()

    def draw(self, fn):
        self.draw_handlers.append(fn)
        return fn

    def update(self, fn):
        self.update_handlers.append(fn)
        return fn

    def free_resource(self, filename):
        """Free resources"""

        try:
            free_fn = self.resources[filename]
        except KeyError:
            return

        free_fn()
        del self.resources[filename]

    def load_resource(self, filename):
        """Loads resources"""

        found_path = None
        for path in self.resource_path:
            full_path = os.path.realpath(os.path.join(path, filename))
            if os.path.isfile(full_path):
                found_path = full_path
                break

        if found_path is None:
            raise OSError("Resource not found")

        if filename[-4:] == ".bmp":
            image = sdl2.SDL_LoadBMP(found_path.encode())
            if not image:
                sys.exit("Error loading %r: %s" % (filename, sdl2.SDL_GetError()))

            resource = sdl2.SDL_CreateTextureFromSurface(self.renderer, image);
            free_fn = sdl2.SDL_DestroyTexture
            sdl2.SDL_FreeSurface(image)
        elif filename[-4:] in (".png", ".gif", ".jpg"):
            from sdl2 import sdlimage

            image = sdlimage.IMG_Load(found_path.encode())
            if not image:
                sys.exit("Error loading %r: %s" % (filename, sdlimage.IMG_GetError()))

            resource = sdl2.SDL_CreateTextureFromSurface(self.renderer, image);
            free_fn = sdl2.SDL_DestroyTexture
            sdl2.SDL_FreeSurface(image)
        elif filename[-4:] in (".wav", ".ogg"):
            # XXX: UNTESTED
            from sdl2 import sdlmixer

            audio = sdlmixer.Mix_LoadWAV(found_path.encode())
            if not audio:
                sys.exit("Error loading %r: %s" % (filename, sdlmixer.Mix_GetError()))

            resource = audio
            free_fn = sdlmixer.Mix_FreeChunk
        else:
            return open(filename, "rb")

        self.resources[filename] = lambda : free_fn(resource)
        return resource

    def load_bitmap_font(self, filename, width, height, font_map=None):
        """
        Loads a bitmap font.

        Parameters:

            filename: image containing the font (eg, font.png).
            width: wiidth of a font character.
            height: height of a font character.
            font_map: string with the order of the characters in the font.

        The default font map is:

        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!?()@:/'., "

        """
        if font_map is None:
            font_map = self.FONT_MAP

        font = BitmapFont(texture=self.load_resource(filename),
                          width=width,
                          height=height,
                          font_map=font_map,
                          )
        self.bitmap_fonts[filename] = font
        return font

