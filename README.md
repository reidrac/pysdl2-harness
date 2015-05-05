Harness for pysdl2
==================

These are a set of classes to make easier to use [pysdl2](https://pysdl2.readthedocs.org).

This is a work in progress so use it at your own risk!


Required
--------

 - Python 3
 - pysdl2
 - SDL2 and SDL2\_Mixer installed in your system
 - Optionally SDL2\_Image (otherwise only uncompressed BMP images are supported)


How it looks like
-----------------

Example:

```python
#!/usr/bin/env python

from harness import Game

game = Game(width=320, height=240)

# by default resources are loaded for a "data" subdirectory at
# the same level of the script bein run
title = game.load_resource("title.bmp")

@game.draw
def draw(renderer):
	# draw your textures, optionally provide two tuples describing
	# source and destination rects
	renderer.draw(title)

@game.update
def update(dt):
	# update your game logic, dt is constant 1 / Game.UPDATE_FPS
	# use game.quit() to exit the game loop

	# key state can be checked in "keys" dict using KEY_* constants
	if game.keys[game.KEY_ESCAPE]:
		game.quit()

# will return when the game is quitted
game.loop()
```
See `harness.py` docstrings for further information. There's an example
game in `example.py`.


Author
------

Juan J. Martinez <jjm@usebox.net>

This is free software under MIT license terms.

