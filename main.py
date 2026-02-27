import pygame
import sys,os,random
import utilities as utils


class Froststep:
    def __init__(self):
        #starting app
        os.environ['SDL_VIDEO_CENTERED'] = '1'
        os.system("cls"if os.name == "nt" else "clear")


        #Initialize Pygame and set up the display
        pygame.init()
        self.full_screen_size = utils.get_screen_size()
        self.last_screen_size = utils.BASE_SIZE
        self.scale = {"width": 1.0, "height": 1.0, "overall": 1.0}
        self.screen = pygame.display.set_mode(utils.BASE_SIZE, pygame.RESIZABLE)
        pygame.display.set_caption("Froststep")
        self.clock = pygame.time.Clock()
        self.dt = 0
        
        #debug
        self.UI_debug_mode = True


    def run(self):
        while True:
            #Reset the game state here if needed
            self.clock.tick(0)
            self.dt = self.clock.get_time() / 1000.0
            self.screen.fill((0, 0, 0))

            #Update scale
            w,h = self.screen.get_size()
            if w != self.last_screen_size[0] or h != self.last_screen_size[1]:
                print(f"Screen size changed to: {w}x{h}")
                self.scale['width'] = w/utils.BASE_SIZE[0]
                self.scale['height'] = h/utils.BASE_SIZE[1]
                self.scale['overall'] = min(self.scale['width'], self.scale['height'])
                if self.screen.get_size() != self.full_screen_size:
                    self.last_screen_size = (w,h)


            #draw UI elements here
            self.draw_ui()


            #Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()

                    #turn on/off bools
                    if event.key == pygame.K_F3:
                        self.UI_debug_mode = not self.UI_debug_mode
                    
                    if event.key == pygame.K_F11:
                        if self.screen.get_size() == self.full_screen_size:
                            self.screen = pygame.display.set_mode(self.last_screen_size, pygame.RESIZABLE)
                        else:
                            self.screen = pygame.display.set_mode(self.full_screen_size)
                    
    
            #Update game state here
            pygame.display.flip()


    def draw_ui(self):
        #Draw UI elements here
        if self.UI_debug_mode:
            utils.draw_text(text=f"Fps:{round(self.clock.get_fps())}", position=(10*self.scale['width'], 10*self.scale['height']), size=20*self.scale['overall'], color=(255, 255, 255))

#Entry point of the game
if __name__ == "__main__":
    game = Froststep()
    game.run()