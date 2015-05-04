#!/usr/bin/env python

from harness import Game

game = Game(title="pysdl2 HARNESS demo", width=240, height=240, zoom=3)
title = game.load_resource("title.png")
font = game.load_bitmap_font("font.png", width=6, height=10)

scenes = []

class MenuScene(object):

    def __init__(self):
        self.counter = 2

    def draw(self, renderer):
        renderer.draw(title)

        if 2 < self.counter < 10:
            renderer.draw_text(font, 120, 120, "Press 's' to start!", align="center")

    def update(self, dt):

        self.counter += dt * 10
        if self.counter > 10:
            self.counter -= 10

        if game.keys[game.KEY_ESCAPE]:
            game.quit()
        elif game.keys[game.KEY_S]:
            # press "s" to play
            scenes.append(PlayScene())
            return

class PlayScene(object):

    def draw(self, renderer):
        pass

    def update(self, dt):
        if game.keys[game.KEY_ESCAPE]:
            # avoid leaving the game just after
            # leaving this scene!
            game.keys[game.KEY_ESCAPE] = False

            # go to previous scene
            scenes.pop()
            return

@game.draw
def draw(renderer):
    # draw last scene
    scenes[-1].draw(renderer)

@game.update
def update(dt):
    # uddate last scene
    scenes[-1].update(dt)

scenes.append(MenuScene())

game.loop()

