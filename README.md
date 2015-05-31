# Harness for pysdl2

These are a set of classes to make easier to use [pysdl2](https://pysdl2.readthedocs.org).

This is a work in progress so use it at your own risk!


## Required

 - Python 3
 - pysdl2
 - SDL2 and SDL2\_Mixer installed in your system
 - Optionally SDL2\_Image (otherwise only uncompressed BMP images are supported)


## How does it looks like?

It is inspired by [pyglet](http://www.pyglet.org/) and specially focused
on 2D games.

Example:

```python
#!/usr/bin/env python

from harness import Harness

game = Harness(width=320, height=240, zoom=3)

title = game.load_resource("title.bmp")

@game.draw
def draw(renderer):
	renderer.draw(title, 10, 10)

@game.update
def update(dt):
	if game.keys[game.KEY_ESCAPE]:
		game.quit()

game.loop()
```

See `harness` module docstrings for a complete list of classes and methods.

There's an example game in `example.py` and remember that you can still use
pysdl2 directly if you need to!

## Components

Harness tries to provide a clean and simple interface to the following
components:

 1. The game loop
 2. Resource management
 3. Controls
 4. Audio

### 1. The game loop

Harness implements a game loop with a fixed frame rate determined by the vsync
of the screen (usually 60 FPS), with support for fixed updates for the game
logic (by default at 80 times per second).

The usual workflow is:

 1. Create a Harness object (we'll call it `game` in the examples).
 2. Load resources.
 3. Declare the draw and update functions.
 3. Run the `loop()` method in your Harness instance.

The game loop should be called once and it will run until the game is quitted
(eg, using `quit()` method).

Draw functions can be defined with the `draw` decorator, and update
functions with the `update` decorator.

The draw functions should expect a "renderer" parameter that allows to draw
textures, bitmap fonts, etc.

Example:

```python

game = Harness()

tex = game.load_resource("bitmap.bmp")

@game.draw
def draw(renderer):
    renderer.draw(tex)

game.loop()
```

The update function should expect a "dt" parameter that provides the delta
time (time elapsed between updates); in this case fixed at `Harness.UFPS_DT`
(1 / UFPS).

Example:

```python

game = Harness()

@game.update
def update(dt):
    print("%s elapsed since last update" % dt)

game.loop()
```

Several draw and update functions can be defined and they will be run in the
same order they were defined.

The game instance can be accessed from the update function to test for key
states, quit the game, etc.

The method `quit()` can be used to exit the game loop.

Example:
```python

game = Harness()

@game.update
def update(dt):

    if game.keys[game.KEY_ESCAPE]:
        game.quit()
        # in case we don't want to complete the update
        return

game.loop()
```

A draw or update function can be removed from the game loop with `remove_handler()`
method, passing the function to be removed as parameter.

Example:
```python

game = Harness()
debug = False

def update_debug(dt):
	print(dt)

@game.update
def update(dt):
    global debug

    if game.keys[game.KEY_D]:
        print("D was pressed!")
        if debug:
            # remove the update_debug update function
            game.remove_handler(update_debug)
        else:
            # add a new update function
            game.update(update_debug)
        debug = not debug
        # remove the key press once processed
        game.keys[game.KEY_D] = False

    if game.keys[game.KEY_ESCAPE]:
        game.quit()

game.loop()

```

### 2. Loading resources

Resources can loaded with `load_resource()` method. This method allows loading
resources searching for them in the paths specified in the `resource_path` list.

By default the files will be searched for in the "data" subdirectory at the same
level as the script running the game.

Depending on the resource some extra libraries may be required in the system
(eg, `SDL_Image`).

Resources not in use can be freed using `free_resources()` method, but
be careful to not use any reference to the resource once it has been released.

Harness will free all resources after exiting the game loop.

#### 2.1 Bitmap fonts

The method `load_bitmap_font()` can be used to load a image that will be used to draw
text with `renderer.draw_text()`. Harness will map a text string into a fixed
width and height part of the font image.

Example:
```python

game = Harness()

font = game.load_bitmap_font("font.png", width=6, height=10)

@game.draw
def draw(renderer):
    renderer.draw_text(font, 10, 10, "This is a text!")

game.loop()
```

Fonts can be freed with `free_resources()`.

### 3. Controls

The state of the keys is exposed in `keys` dictionary and it
gets updated in each game loop iteration.

In `Harness.KEY_*` there are constants to test in the "keys" dictionary. If a key
is being pressed, the value in the dictionary will be `True`.

Example:
```python

game = Harness()

@game.update
def update(dt):

    if game.keys[game.KEY_ESCAPE]:
        game.quit()

game.loop()
```

#### 3.1 Game controllers

Game controllers can be mapped into key states so the game can access to the
controller like the player was using the keyboard.

The default mapping is:

 - DPad up: up arrow key
 - DPad down: down arrow key
 - DPad left: left arrow key
 - DPad right: right arrow key
 - Button A: key c
 - Button B: key v
 - Start button: key s
 - Back button: escape key

Harness will manage the controller automatically in the game loop updating the
`keys` dictionary as needed. 

`has_controllers` property can be checked to see if any game controller was
detected. Harness includes a game controller database with definitions for most
common devices, and SDL2 functions can be used to add more. If there's no information
about a given controller, it will be silently ignored.

In order to use a controller, the `controllers` property can be accessed to
activate any detected controller.

Example:
```python

game = Harness()

# enumerate all detected controllers
for controller in game.controllers:
    print(controller.name)

```

Once the controller has been activated, it can be deactivated using `close()`
controller method.

The key mapping can be changed using the `set_mapping()` method on the controller.

Example:
```python

game = Harness()

# first controller
controller = game.controllers[0]

# remap button a to key a
controller.set_mapping(a="KEY_A")
```

The valid parameters are: up, down, left, right, a, b, start and back. Use a
string defining the key (see `Harness.KEY_*`).

The use of a controller won't disable the keyboard. If that is required, the
game controllers can be accessed using SDL2 functions directly.

### 4. Audio

The method `play()` can be used to play a sample loaded with `load_resource()`.
Optionally a `loops` parameter can be provided stating how many times the sample
will be repeated (use -1 for an infinite loop).

By default .ogg and .wav files are supported (in theory it could load any
format supported by `SDL_Mixer` but Harness will only identify files with the
aforementioned extensions).

`play()` returns the channel number used to play the sample and that
number can be used to muted the channel with `stop_playback()` (if a channel
number s not provided, it will stop all channels).

By default `Harness.AUDIO_CHANNELS` channels are allocated (6 channels).

## Using OOP

Harness can be used in a class to take advantage of object oriented programming
and avoid the use of global variables. Just use composition and register the
update and draw methods with `update()` and `draw()` instead of using the
decorators:

Example:
```python
from harness import Harness

class MyGame(object):

    def __init__(self):
        self.harness = Harness()

        # register update and draw methods
        self.harness.update(self.update)
        self.harness.draw(self.draw)

        # load some resources
        self.image = self.harness.load_resource("image.png")

    def run(self):
        self.harness.loop()

    def update(self, dt):
        if self.harness.keys[self.harness.KEY_ESCAPE]:
            self.harness.quit()

    def draw(self, renderer):
        renderer.draw(self.image)


if __name__ == "__main__":
    game = MyGame()
    game.run()
```

See `example-oop.py`.

## Author

Juan J. Martinez <jjm@usebox.net>

This is free software under MIT license terms.

