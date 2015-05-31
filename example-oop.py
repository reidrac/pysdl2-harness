#!/usr/bin/env python
from harness import Harness

class MyGame(object):

    def __init__(self):
        self.harness = Harness(width=240, height=240, zoom=3)

        # register update and draw methods
        self.harness.update(self.update)
        self.harness.draw(self.draw)

        # load some resources
        self.font = self.harness.load_bitmap_font("font.png", width=6, height=10)

        self.debug = False

    def run(self):
        self.harness.loop()

    def update_debug(self, dt):
        print(dt)

    def update(self, dt):
        if self.harness.keys[self.harness.KEY_D]:
            print("***")
            self.harness.keys[self.harness.KEY_D] = False
            self.debug = not self.debug
            if self.debug:
                self.harness.update(self.update_debug)
            else:
                self.harness.remove_handler(self.update_debug)

        if self.harness.keys[self.harness.KEY_ESCAPE]:
            self.harness.quit()

    def draw(self, renderer):
        renderer.draw_text(self.font, 120, 120, "Press d to toggle debug update,", align="center")
        renderer.draw_text(self.font, 120, 130, "ESC to quit", align="center")


if __name__ == "__main__":
    game = MyGame()
    game.run()

