#!/usr/bin/env python

from harness import Game

game = Game(title="pysdl2 HARNESS demo", width=240, height=240, zoom=3)
background = game.load_resource("background.png")
title = game.load_resource("title.png")
font = game.load_bitmap_font("font.png", width=6, height=10)

scenes = []

class MenuScene(object):

    def __init__(self):
        self.counter = 2

    def draw(self, renderer):
        renderer.draw(background)
        renderer.draw(title, dest_rect=(0, 40, 240, 60))

        if 2 < self.counter < 12:
            renderer.draw_text(font, 120, 120, "Press 's' to start!", align="center")

        renderer.draw_text(font, 120, 10, "Copyright (c) 2015 usebox.net", align="center")

        renderer.draw_text(font, 120, 200, "Use the arrows to move", align="center")
        renderer.draw_text(font, 120, 212, "and collect the goodies!", align="center")

    def update(self, dt):

        self.counter += dt * 10
        if self.counter > 12:
            self.counter -= 12

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

