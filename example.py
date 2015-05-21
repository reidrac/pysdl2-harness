#!/usr/bin/env python
"""
Harness demo, a game example.

Tested with Python 3.4, may or may not work with Python 2!
"""

from random import randint, shuffle

from harness import Harness

game = Harness(title="pysdl2 HARNESS demo", width=240, height=240, zoom=3)

if game.has_controllers:
    # use first game controller; harness will manage this internally
    # but it's useful to keep a reference (eg, to set the keyboard mapping,
    # get the controller name, etc)
    controller = game.controllers[0]

background = game.load_resource("background.png")
title = game.load_resource("title.png")
font = game.load_bitmap_font("font.png", width=6, height=10)

# load all the sprites in just one image so they're in one big texture
tiles = game.load_resource("tiles.png")

game.set_icon("icon.png")

dance = game.load_resource("harness-dance.ogg")
dance_hurry = game.load_resource("harness-dance-hurry.ogg")
gameover = game.load_resource("gameover.ogg")
hurryup = game.load_resource("hurryup.ogg")
time = game.load_resource("time.ogg")

scenes = []
hiscore = 0

class MenuScene(object):

    # only one direction
    dragon_frames = ((0, 24, 24, 24), (24, 24, 24, 24))
    knight_frames = ((48, 48, 24, 24), (72, 48, 24, 24))

    def __init__(self):
        self.intro_channel = None
        self.counter = 2
        self.title_y = -100

        self.anim_delay = 0
        self.frame = 0

        self.dragon = [tiles.get_texture(*frames) for frames in self.dragon_frames]
        self.knight = [tiles.get_texture(*frames) for frames in self.knight_frames]

        self.boing = game.load_resource("boing.ogg")
        game.play(self.boing)

    def draw(self, renderer):
        renderer.draw(background)
        renderer.draw(title, dest_rect=(0, int(self.title_y), 240, 60))

        # wait until the title is in place
        if self.title_y >= 40:
            if 2 < self.counter < 12:
                renderer.draw_text(font, 120, 132, "Press 's' to start!", align="center")

            renderer.draw_text(font, 120, 10, "Copyright (c) 2015 usebox.net", align="center")
            renderer.draw_text(font, 120, 48, "HI: %04i" % hiscore, align="center")

            renderer.draw_text(font, 120, 196, "Use the arrows to move", align="center")
            renderer.draw_text(font, 120, 208, "and collect the goodies!", align="center")

            renderer.draw_text(font, 120, 106, "a game by @reidrac",
                    align="center", tint=(98, 100, 220, 255))

            # draw the animation cycle; frame 1 will be drawn 1 pixel higher
            renderer.draw(self.dragon[self.frame],
                          x = 12,
                          y = 192 - self.frame,
                          )
            renderer.draw(self.knight[self.frame],
                          x = 204,
                          y = 192 - self.frame,
                          )

    def update(self, dt):

        # initial animation (title falls into place)
        if self.title_y < 40:
            self.title_y += dt * 120
            return
        elif self.boing:
            # won't be used again
            game.free_resource("boing.ogg")
            self.boing = None
        elif self.intro_channel is None:
            # loop the intro music
            self.intro_channel = game.play(dance, loops=-1)

        # the "start" will blink
        self.counter += dt * 10
        if self.counter > 12:
            self.counter -= 12

        # frame animation
        self.anim_delay += dt * 10
        if self.anim_delay > 1.5:
            self.anim_delay = 0
            self.frame = 0 if self.frame else 1

        # controls
        if game.keys[game.KEY_ESCAPE]:
            game.quit()
        elif game.keys[game.KEY_S]:
            # press "s" to play
            game.stop_playback(self.intro_channel)
            self.intro_channel = None
            scenes.append(ReadyScene())
            return

class ReadyScene(object):

    def __init__(self):
        self.delay = 16

    def draw(self, renderer):
        renderer.draw(background)
        renderer.draw_text(font, 120, 100, "READY?", align="center")

    def update(self, dt):
        if self.delay > 0:
            self.delay -= dt * 10
            if self.delay <= 0:
                scenes.pop()
                scenes.append(PlayScene())

class GameOverScene(object):

    def __init__(self):
        self.delay = 80

        # play it once
        game.play(gameover)

    def draw(self, renderer):
        renderer.draw(background)
        renderer.draw_text(font, 120, 100, "GAME OVER", align="center")

    def update(self, dt):
        if self.delay > 0:
            self.delay -= dt * 10
            if self.delay <= 0:

                # back to menu
                scenes.pop()

class PlayScene(object):

    BW = 7
    BH = 7

    MAX_TILES = 10
    TILES = 8

    def __init__(self):
        self.stage = 1
        self.score = 0

        # subtextures for the board tiles
        self.tiles = [tiles.get_texture(*tuple([i * 24, 0, 24, 24])) for i in range(self.MAX_TILES)]

        self.music_channel = game.play(dance, loops=-1)
        self.next_stage()

    def next_stage(self):
        self.time = 12
        self.hurry_up = None
        self.time_tint = None
        self.game_over = None
        self.prev_time = 0

        # generate a random board
        tileset = [range(self.MAX_TILES)]
        shuffle(tileset)
        self.board = [randint(0, self.TILES - 1) for i in range(self.BW * self.BH)]

    def draw(self, renderer):
        renderer.draw(background)

        renderer.draw_text(font, 4, 4, "SCORE %04i" % self.score)
        renderer.draw_text(font, 236, 4, "STAGE %i" % self.stage, align="right")

        if self.hurry_up:
            # blink a warning when the time is running out
            if int(self.hurry_up) & 1:
                renderer.draw_text(font, 120, 9, "HURRY UP!", align="center")
        else:
            renderer.draw_text(font, 120, 9, "TIME: %02i" % int(self.time), align="center", tint=self.time_tint)

        # draw the board
        for y in range(self.BH):
            for x in range(self.BW):
                renderer.draw(self.tiles[self.board[x + y * self.BW]],
                              x=(120 - (24 * self.BW // 2)) + x * 24,
                              y=(120 - (24 * self.BH // 2)) + y * 24,
                              )

    def update(self, dt):

        # HURRY UP! delay
        if self.hurry_up:
            self.hurry_up -= dt * 10

            if self.hurry_up <= 0:
                self.hurry_up = 0
                if self.music_channel is None:
                    self.music_channel = game.play(dance_hurry, loops=-1)
            else:
                return

        self.time -= dt

        # set HURRY UP once
        if int(self.time) == 10 and self.hurry_up is None:
            self.hurry_up = 12
            self.time_tint = (255, 0, 0, 255)
            self.prev_time = 10
            game.play(hurryup)
            game.stop_playback(self.music_channel)
            self.music_channel = None
            return

        # beep on the last seconds
        if self.prev_time and int(self.time) != self.prev_time:
            self.prev_time = int(self.time)
            game.play(time)

        # set GAME OVER
        if int(self.time) == 0:

            # stop music
            if self.music_channel is not None:
                game.stop_playback(self.music_channel)

            global hiscore
            if self.score > hiscore:
                hiscore = self.score

            scenes.pop()
            scenes.append(GameOverScene())
            return

        # controls
        if game.keys[game.KEY_ESCAPE]:
            # avoid leaving the game just after
            # leaving this scene!
            game.keys[game.KEY_ESCAPE] = False

            # stop music
            if self.music_channel is not None:
                game.stop_playback(self.music_channel)

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

