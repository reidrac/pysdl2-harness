#!/usr/bin/env python
"""
Harness for pysdl2,
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
from __future__ import division
import sys
import os
import ctypes

version = "0.2"

try:
    import sdl2
except ImportError as ex:
    if not hasattr(sys, "_gen_docs"):
        sys.exit("SDL2 library not found: %s" % ex)

try:
    from sdl2 import sdlmixer
except ImportError as ex:
    if not hasattr(sys, "_gen_docs"):
        sys.exit("SDL2_Mixer library not found: %s" % ex)

# loads game controller definitions
from .GameControllerDB import init_game_controller

class Harness(object):
    """
    Harness object

    Parameters:

        title: windows title.
        width: with in pixels of the draw area.
        height: height in pixels of the draw area.
        zoom: scale up the output, or use 1 to disable.

    """
    UFPS = 80
    UFPS_DT = 1.0 / 80

    FONT_MAP = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!?()@:/'., "

    AUDIO_CHANNELS = 6

    def __init__(self, title=None, width=320, height=200, zoom=1):

        self.title = title.encode() if title else b"SDL2 Harness"
        self.width = width
        self.height = height
        self.zoom = zoom

        self._quit = False
        self._update_dt = 0
        self.update_handlers = []
        self.draw_handlers = []
        self._controllers = {}

        # try to find the script directory
        if "__main__" in globals():
            main = globals().__main__
        else:
            import __main__ as main
        main_dir = os.path.dirname(os.path.realpath(getattr(main, "__file__", ".")))

        # heuristic intended to work with packaged scripts (eg, py2exe)
        while not os.path.isdir(main_dir):
            main_dir = os.path.dirname(main_dir)

        self.resource_path = [
                os.path.join(main_dir, "data"),
                ]

        self.resources = {}

        for attr in dir(sdl2):
            if attr.startswith("SDL_SCANCODE_"):
                setattr(self, attr.replace("SDL_SCANCODE_", "KEY_"), getattr(sdl2, attr))

        sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO|sdl2.SDL_INIT_AUDIO|sdl2.SDL_INIT_TIMER|sdl2.SDL_INIT_JOYSTICK)
        init_game_controller()
        sdlmixer.Mix_Init(sdlmixer.MIX_INIT_OGG)
        sdlmixer.Mix_OpenAudio(44100, sdlmixer.MIX_DEFAULT_FORMAT, self.AUDIO_CHANNELS, 1024)

        self.window = sdl2.SDL_CreateWindow(self.title,
                                            sdl2.SDL_WINDOWPOS_CENTERED,
                                            sdl2.SDL_WINDOWPOS_CENTERED,
                                            self.width * self.zoom,
                                            self.height * self.zoom,
                                            sdl2.SDL_WINDOW_HIDDEN
                                            )
        self.renderer = sdl2.SDL_CreateRenderer(self.window, -1,
                sdl2.SDL_RENDERER_ACCELERATED|sdl2.SDL_RENDERER_PRESENTVSYNC)
        self.renderer_obj = Renderer(self.renderer)

        if self.zoom != 1:
            sdl2.SDL_RenderSetScale(self.renderer, self.zoom, self.zoom)

    def set_icon(self, filename):
        """
        Sets the window icon from an image

        NOT a texture (don't use load_resource method).
        """
        from sdl2 import sdlimage

        found_path = self._find_path(filename)
        image = sdlimage.IMG_Load(found_path.encode())
        if not image:
            sys.exit("Error loading %r: %s" % (filename, sdlimage.IMG_GetError()))

        sdl2.SDL_SetWindowIcon(self.window, image)
        sdl2.SDL_FreeSurface(image)

    def _update(self, dt):

        self._update_dt += dt
        while self._update_dt > self.UFPS_DT:
            for update in self.update_handlers:
                update(self.UFPS_DT)
            self._update_dt -= self.UFPS_DT

    def _draw(self):

        for draw in self.draw_handlers:
            draw(self.renderer_obj)

    def quit(self):
        """Quits the game"""
        self._quit = True

    def loop(self):
        """The game loop!"""
        sdl2.SDL_ShowWindow(self.window)

        current = sdl2.SDL_GetPerformanceCounter()
        freq = sdl2.SDL_GetPerformanceFrequency()
        while not self._quit:

            event = sdl2.SDL_Event()
            while sdl2.SDL_PollEvent(ctypes.byref(event)) != 0:
                if event.type == sdl2.SDL_QUIT:
                    self._quit = True
                    break

            self.keys = sdl2.SDL_GetKeyboardState(None)
            for controller in self._controllers.values():
                controller.poll()

            new = sdl2.SDL_GetPerformanceCounter()
            self._update((new - current) / freq)
            current = new

            sdl2.SDL_RenderClear(self.renderer)
            self._draw()
            sdl2.SDL_RenderPresent(self.renderer)

        for resource in self.resources.copy().keys():
            self.free_resource(resource)

        for controller in list(self._controllers.values()):
            if controller.handler:
                controller.close()

        sdl2.SDL_DestroyRenderer(self.renderer)
        sdl2.SDL_HideWindow(self.window)
        sdl2.SDL_DestroyWindow(self.window)

        sdlmixer.Mix_Quit()
        sdl2.SDL_Quit()

    def remove_handler(self, fn):
        """
        Remove a draw or update handler

        Parameters:

            fn: handler to remove.
        """
        if fn in self.draw_handlers:
            self.draw_handlers.remove(fn)
        if fn in self.update_handlers:
            self.update_handlers.remove(fn)

    def draw(self, fn):
        self.draw_handlers.append(fn)
        return fn

    def update(self, fn):
        self.update_handlers.append(fn)
        return fn

    def play(self, sample, loops=0):
        """
        Plays a sample loaded with load_resource

        Parameters:

            sample: sample to play.
            loops: number of times to play the sample (-1 for infinite loop).

        """
        return sdlmixer.Mix_PlayChannel(-1, sample, loops)

    def stop_playback(self, channel=-1):
        """Stops the audio playback"""
        return sdlmixer.Mix_HaltChannel(channel)

    def free_resource(self, filename):
        """Free resources"""

        try:
            free_fn = self.resources[filename]
        except KeyError:
            return

        free_fn()
        del self.resources[filename]

    def _find_path(self, filename):
        found_path = None
        for path in self.resource_path:
            full_path = os.path.realpath(os.path.join(path, filename))
            if os.path.isfile(full_path):
                found_path = full_path
                break

        if found_path is None:
            raise OSError("Resource not found: %r" % filename)

        return found_path

    def load_resource(self, filename):
        """
        Loads resources

        Parameters:

            filename: file name of the resource to load.

        The resource is identified based on its name:

            .bmp: image (using SDL2).
            .png, .gif, .jpg: image (using SDL2_Image)
            .wav, .ogg: audio sample

        If the resource type is not identified, an open file handle
        is returned (is to the callee to close the file).
        """

        found_path = self._find_path(filename)

        if filename[-4:] == ".bmp":
            image = sdl2.SDL_LoadBMP(found_path.encode())
            if not image:
                sys.exit("Error loading %r: %s" % (filename, sdl2.SDL_GetError()))

            resource = sdl2.SDL_CreateTextureFromSurface(self.renderer, image);
            free_fn = lambda : sdl2.SDL_DestroyTexture(resource)

            sdl2.SDL_FreeSurface(image)
        elif filename[-4:] in (".png", ".gif", ".jpg"):
            from sdl2 import sdlimage

            image = sdlimage.IMG_Load(found_path.encode())
            if not image:
                sys.exit("Error loading %r: %s" % (filename, sdlimage.IMG_GetError()))

            texture = sdl2.SDL_CreateTextureFromSurface(self.renderer, image);
            free_fn = lambda : sdl2.SDL_DestroyTexture(texture)
            resource = Texture(texture, (0, 0, image.contents.w, image.contents.h))

            sdl2.SDL_FreeSurface(image)
        elif filename[-4:] in (".wav", ".ogg"):
            audio = sdlmixer.Mix_LoadWAV(found_path.encode())
            if not audio:
                sys.exit("Error loading %r: %s" % (filename, sdlmixer.Mix_GetError()))

            resource = audio
            free_fn = lambda : sdlmixer.Mix_FreeChunk(resource)
        else:
            return open(filename, "rb")

        self.resources[filename] = free_fn
        return resource

    def load_bitmap_font(self, filename, width, height, font_map=None):
        """
        Loads a bitmap font

        Parameters:

            filename: image containing the font (eg, font.png).
            width: width of a font character.
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
        return font

    @property
    def has_controllers(self):
        """True if there are game controllers available"""
        return sdl2.SDL_NumJoysticks() > 0

    @property
    def controllers(self):
        """
        Get a tuple of all detected game controllers

        By getting a controller from this list, the controller gets automatically
        enabled and ready to use.
        """
        for joy in range(sdl2.SDL_NumJoysticks()):
            if sdl2.SDL_IsGameController(joy):
                controller = Controller(joy, self)
                self._controllers[controller.name] = controller
        return tuple(self._controllers.values())

class Renderer(object):
    """Wrapper for the renderer to be used by the draw functions"""
    def __init__(self, renderer):
        self.renderer = renderer

    def _get_rect(self, texture, rect=None):
        _rect = rect

        if isinstance(texture, Texture):
            _rect = texture.sdl_rect

        if isinstance(rect, tuple):
            _rect = sdl2.SDL_Rect(*rect)

        return _rect

    def draw(self, texture, x=None, y=None, src_rect=None, dest_rect=None, tint=None):
        """
        Draws a texture

        Parameters:

            texture: texture created with Harness.load_resource or Texture.get_texture.
            x: horizontal location to draw the whole texture.
            y: vertical location to draw the whole texture.
            src_rect: tuple with the rect defining the section of the texture to draw.
            dest_rect: tuple with the rect defining the section of the destination. If
              this parameter is used, x and y are ignored.
            tint: colour the text texture, tuple with (r, g, b, alpha).
        """

        _texture = texture.texture
        src = self._get_rect(texture, src_rect)

        _dest_rect = dest_rect
        if _dest_rect is None and all([x, y]):
            _dest_rect = (x, y, texture.rect[2], texture.rect[3])
        dest = self._get_rect(texture, _dest_rect)

        if isinstance(tint, tuple) and len(tint) == 4:
            sdl2.SDL_SetTextureColorMod(_texture, *tint)
        else:
            tint = None

        sdl2.SDL_RenderCopy(self.renderer, _texture, src, dest)

        if tint:
            sdl2.SDL_SetTextureColorMod(_texture, 255, 255, 255, 255)

    def draw_text(self, font, x, y, text, align="left", tint=None):
        """
        Draws text using a bitmap font

        Parameters:

            font: font (load it first with load_bitmap_font).
            x: horizontal position on the screen.
            y: vertical position on the screen.
            text: the text to render.
            align: "left", "right" or "center" (defaults to "left").
            tint: colour the text texture, tuple with (r, g, b, alpha).
        """
        width = len(text) * font.width

        if align == "center":
            x -= width // 2
            y -= font.height // 2
        elif align == "right":
            x -= width

        src = sdl2.SDL_Rect(font.rect[0],
                            font.rect[1],
                            font.width,
                            font.height,
                            )
        dest = sdl2.SDL_Rect(0, y, font.width, font.height)

        if isinstance(tint, tuple) and len(tint) == 4:
            sdl2.SDL_SetTextureColorMod(font.texture, *tint)
        else:
            tint = None

        for i, c in enumerate(text):
            index = font.font_map.find(c)
            src.x = font.rect[0] + index * font.width
            dest.x = x + i * font.width
            sdl2.SDL_RenderCopy(self.renderer, font.texture, src, dest)

        if tint:
            sdl2.SDL_SetTextureColorMod(font.texture, 255, 255, 255, 255)

class Texture(object):
    """Wrapper for SDL textures and subtextures"""
    def __init__(self, texture, rect):
        self.texture = texture
        self.width = rect[2]
        self.height = rect[3]
        self.rect = rect
        self.sdl_rect = sdl2.SDL_Rect(*rect)

    def get_texture(self, x, y, width, height):
        """
        Returns a reference to a subtexture

        Parameters:

            x: horizontal position on the parent texture.
            y: vertical position on the parent texture.
            width: width of the subtexture.
            height: height of the subtexture.
        """
        return Texture(self.texture, (x, y, width, height))

class BitmapFont(object):
    """Bitmap font object"""
    def __init__(self, texture, width, height, font_map):
        self.texture = texture.texture
        self.rect = texture.rect
        self.sdl_rect = texture.sdl_rect
        self.width = width
        self.height = height
        self.font_map = font_map

class Controller(object):
    """Game controller"""

    DEF_KEY_MAPPING = dict(up="KEY_UP",
                           down="KEY_DOWN",
                           left="KEY_LEFT",
                           right="KEY_RIGHT",
                           a="KEY_C",
                           b="KEY_V",
                           start="KEY_S",
                           back="KEY_ESCAPE",
                           )

    MAPPING = dict(up="SDL_CONTROLLER_BUTTON_DPAD_UP",
                   down="SDL_CONTROLLER_BUTTON_DPAD_DOWN",
                   left="SDL_CONTROLLER_BUTTON_DPAD_LEFT",
                   right="SDL_CONTROLLER_BUTTON_DPAD_RIGHT",
                   a="SDL_CONTROLLER_BUTTON_A",
                   b="SDL_CONTROLLER_BUTTON_B",
                   start="SDL_CONTROLLER_BUTTON_START",
                   back="SDL_CONTROLLER_BUTTON_BACK",
                   )

    def __init__(self, joy_number, harness):
        self.key_mapping = self.DEF_KEY_MAPPING
        self.harness = harness
        self.joy_number = joy_number
        self.previous = dict((key, False) for key in self.MAPPING.keys())

        # unlikely
        if not sdl2.SDL_IsGameController(joy_number):
            raise ValueError("%r is not a support game controller" % joy_number)

        self.handler = sdl2.SDL_GameControllerOpen(self.joy_number)
        if not self.handler:
            raise ValueError("%r is not a support game controller" % joy_number)

        self.name = sdl2.SDL_GameControllerName(self.handler)

    def __repr__(self):
        return u"<Controller: %r>" % self.name

    def close(self):
        """Deactivate a game controller"""
        sdl2.SDL_GameControllerClose(self.handler)
        self.handler = None

        if self.name in self.harness._controllers:
            del self.harness._controllers[self.name]

    def set_mapping(self, **kwargs):
        """
        Maps a controller action to a key

        Takes named parameters in the form:

            action="KEY"

        Example:

            start="KEY_S"
        """
        for key, value in kwargs.items():
            if key not in self.MAPPING.keys():
                raise ValueError("%r is not a supported game controler to keyboard mapping" % key)
            self.key_mapping[getattr(sdl2, key)] = value

    def poll(self):
        if not self.handler:
            return

        for key, value in self.MAPPING.items():
            state = sdl2.SDL_GameControllerGetButton(self.handler, getattr(sdl2, value)) == 1
            if self.previous[key] != state:
                self.harness.keys[getattr(self.harness, self.key_mapping[key])] = state
            self.previous[key] = state

