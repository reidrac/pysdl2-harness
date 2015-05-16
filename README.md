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

from harness import Game

game = Game(width=320, height=240, zoom=3)

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

 1. Game loop.
 2. Resource management.
 3. Controls.
 4. Audio.

### 1. The Game loop

Harness implements a game loop with a fixed frame rate determined by the vsync
of the screen (usually 60 FPS).

The usual workflow is:

 1. Create a Game object (we'll call it `game` in the examples).
 2. Load resources.
 3. Declare the draw and update functions.
 3. Run `game.loop()`.

The game loop should be called once  and it will run until the game is quitted
(eg, using `quit()` method).

Define draw functions with the `game.draw` decorator, and update
functions with the `game.update` decorator.

The draw functions should expect a "renderer" parameter that allows to draw
textures and bitmap fonts.

Example:

```python

game = Game()

tex = game.load_resource("bitmap.bmp")

@game.draw
def draw(renderer):
    renderer.draw(tex)

game.loop()
```

The update functions should expect a "dt" parameter that provides the delta
time (time elapsed between updates); in this case fixed at UFPS_DT (1 / UFPS).

Example:

```python

game = Game()

@game.update
def update(dt):
    print("%s elapsed since last update" % dt)

game.loop()
```

Several draw and update functions can be defined and they will be run in the
same order they were defined.

The game instance can be accessed from the update function to test for key
states, quite the game, etc.

The method `game.quit()` can be used to exit the game loop.

Example:
```python

game = Game()

@game.update
def update(dt):

    if game.keys[game.KEY_ESCAPE]:
        game.quit()
        # in case we don't want to complete the update
        return

game.loop()
```

### 2. Loading resources

Resources can loaded with `game.load_resource()`. This method allows loading
resources searching for them in the paths specified in the
`game.resource_path` list.

By default this files will be searched in the "data" subdirectory at the same
level as the script running the game.

Depending on the resource some extra libraries may be required in the system
(eg, SDL\_Image).

Resources not in use can be freed using `game.free_resources()` method, but
be careful to not use any reference to the resource once it has been released.
Harness will free all resources after exiting the game loop.

#### 2.1 Bitmap fonts

`game.load_bitmap_font` can be used to load a image that will be used to draw
text with `renderer.draw_text()`. Harness will map a text string into a fixed
width and height part of the font image.

Example:
```python

game = Game()

font = game.load_bitmap_font("font.png", width=6, height=10)

@game.draw
def draw(renderer):
    renderer.draw_text(font, 10, 10, "This is a text!")

game.loop()
```

Fonts can be freed with `game.free_resources()`.

### 3. Controls

The status of the keys is exposed in `game.keys` dictionary and it
gets updated in each game loop iteration.

In `Game.KEYS_*` there are constants to test in the "keys" dictionary.

Example:
```python

game = Game()

@game.update
def update(dt):

    if game.keys[game.KEY_ESCAPE]:
        game.quit()

game.loop()
```

### 4. Audio

The method `game.play()` can be used to play a sample loaded with
`game.load_resource()`. Optionally a `loops` parameter can be provided stating
how many times the sample will be repeated (use -1 for an infinite loop).

By default .ogg and .wav files are supported (in theory it could load any
format supported by SDL\_Mixer but Harness will only identify files with the
aforementioned extensions).

`game.play()` returns the channel number used to play the sample and that
number can be used to muted the channel with `game.stop_playback()` (don't
provide a channel number to stop all channels).

By default `Game.AUDIO_CHANNELS` channels are allocated (6 channels).

## Using OOP

Harness can be used in a class to take advantage of object oriented programing
and avoid the use of global variables. Just use composition and register the
update and draw methods with `Game.update` and `Game.draw` instead of using
the decorators:

Example:
```python
from harness import Game

class MyGame(object):

    def __init__(self):
        self.harness = Game()

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

## Author

Juan J. Martinez <jjm@usebox.net>

This is free software under MIT license terms.

