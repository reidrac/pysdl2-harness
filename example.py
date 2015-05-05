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

# load all the sprites in just one image so they're in one big texture
tiles = game.load_resource("tiles.png")

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
            renderer.draw(tiles,
                          src_rect=self.dragon_frames[self.frame],
                          dest_rect=(12, 192 - self.frame, 24, 24),
                          )
            renderer.draw(tiles,
                          src_rect=self.knight_frames[self.frame],
                          dest_rect=(204, 192 - self.frame, 24, 24)
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

        # the "start" will blnk
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
            scenes.append(PlayScene())
            return

class PlayScene(object):

    def __init__(self):
        self.score = 0

        # stage 1
        self.stage = 0
        self.next_stage()

    def next_stage(self):
        self.stage += 1
        self.ready_delay = 16
        self.time = 99
        self.music_channel = None
        self.hurry_up = None
        self.time_tint = None
        self.game_over = None
        self.prev_time = 0

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
            if self.ready_delay <= 0 and self.music_channel is None:
                self.music_channel = game.play(dance, loops=-1)
            return

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
            self.game_over = 80

            # stop music
            if self.music_channel is not None:
                game.stop_playback(self.music_channel)

            # play it once
            game.play(gameover)

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

