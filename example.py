#!/usr/bin/env python
"""
Harness demo, a game example.

Tested with Python 3.4, may or may not work with Python 2!
"""

from harness import Game

game = Game(title="pysdl2 HARNESS demo", width=240, height=240, zoom=3)
background = game.load_resource("background.png")
title = game.load_resource("title.png")
font = game.load_bitmap_font("font.png", width=6, height=10)

scenes = []
hiscore = 0

class MenuScene(object):

    def __init__(self):
        self.counter = 2
        self.title_y = -100

    def draw(self, renderer):
        renderer.draw(background)
        renderer.draw(title, dest_rect=(0, int(self.title_y), 240, 60))

        # wait until the title is in place
        if self.title_y >= 40:
            if 2 < self.counter < 12:
                renderer.draw_text(font, 120, 120, "Press 's' to start!", align="center")

            renderer.draw_text(font, 120, 10, "Copyright (c) 2015 usebox.net", align="center")
            renderer.draw_text(font, 120, 48, "HI: %04i" % hiscore, align="center")

            renderer.draw_text(font, 120, 196, "Use the arrows to move", align="center")
            renderer.draw_text(font, 120, 208, "and collect the goodies!", align="center")

    def update(self, dt):

        if self.title_y < 40:
            self.title_y += dt * 120
            return

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

    def __init__(self):
        self.score = 0
        self.stage = 1
        self.time = 20
        self.ready_delay = 16
        self.hurry_up = None
        self.game_over = None
        self.time_tint = None

    def draw(self, renderer):
        renderer.draw(background)

        renderer.draw_text(font, 4, 4, "SCORE %04i" % self.score)
        renderer.draw_text(font, 236, 4, "STAGE %i" % self.stage, align="right")
        renderer.draw_text(font, 120, 9, "TIME: %02i" % int(self.time), align="center", tint=self.time_tint)

        # show READY? before starting
        if self.ready_delay > 0:
            renderer.draw_text(font, 120, 100, "READY?", align="center")
            return

        # blink a warning when the time is running out
        if self.hurry_up and int(self.hurry_up) & 1:
            renderer.draw_text(font, 120, 100, "HURRY UP!", align="center")
            return

        # game over
        if self.game_over:
            renderer.draw_text(font, 120, 100, "GAME OVER", align="center")
            return

    def update(self, dt):

        # GAME OVER
        if self.game_over:
            self.game_over -= dt * 10

            if self.game_over <= 0:
                global hiscore
                if self.score > hiscore:
                    hiscore = self.score

                # back to menu
                scenes.pop()
            return

        # READY? delay
        if self.ready_delay > 0:
            self.ready_delay -= dt * 10
            return

        # HURRY UP! delay
        if self.hurry_up:
            self.hurry_up -= dt * 10

            if self.hurry_up <= 0:
                self.hurry_up = 0
            else:
                return

        self.time -= dt

        # set HURRY UP once
        if int(self.time) == 10 and self.hurry_up is None:
            self.hurry_up = 12
            self.time_tint = (255, 0, 0, 255)

        # set GAME OVER
        if int(self.time) == 0:
            self.game_over = 60

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

