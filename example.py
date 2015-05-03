#!/usr/bin/env python

from harness import Game

game = Game(width=240, height=240)
title_tex = game.load_resource("title.bmp")

@game.draw
def draw(renderer):
    # draw your textures, optionally provide two tuples describing
    # source and destination rects
    renderer.draw(title_tex)

@game.update
def update(dt):
    # update your game logic, dt is constant Game.UPDATE_FPS
    # use game.quit() to exit the game loop

    # key state can be check in "keys" dict using KEY_* constants
    if game.keys[game.KEY_ESCAPE]:
        game.quit()

# will return when exits
game.loop()

