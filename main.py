from re import S
import time

import pygame
import sys, os, math
import utilities as utils
import objects


class Froststep:
    def __init__(self):
        #starting app
        os.environ['SDL_VIDEO_CENTERED'] = '1'
        os.system("cls"if os.name == "nt" else "clear")


        #Initialize Pygame and set up the display
        pygame.init()
        self.full_screen_size = utils.get_screen_size()
        self.last_screen_size = utils.BASE_SIZE #<---- this is (1100,700)
        self.scale = {"width": 1.0, "height": 1.0, "overall": 1.0}
        self.screen = pygame.display.set_mode(utils.BASE_SIZE, pygame.RESIZABLE)
        pygame.display.set_caption("Froststep")
        self.clock = pygame.time.Clock()
        self.dt = 0
        
        #debug
        self.Master_debug_mode = True
        self.UI_debug_mode = True
        self.hitbox_debug = True
       


        #world
        self.map_size = (5000,5000)
        self.world_pos = pygame.Vector2(self.screen.get_size()[0] // 2, self.screen.get_size()[1] // 2)
        self.map = utils.SpriteSheet()
        self.map.extract_single_image("Textures/map_final_background.png", self.map_size)
        self.map.extract_single_image("Textures/map_bg.png", self.map_size)
        self.map_index = 0


        #screen elements/objects
       
        #beacon 
        self.beacon_img = None
        self.beacon_cap = 10
        self.beacon_storage = 0
        self.beacon_light = utils.create_gradient("yellow", (1000, 1000), radius=300, opposite=True, circular=True)

        #player
        self.player = objects.player((self.map_size[0] // 3, self.map_size[1] // 2))
        w,h = self.screen.get_size() 
        self.vision = utils.create_gradient("black", (w, h),400)

        #game features
        self.time_left = 120 #<- in seconds
        self.time_speed = 100
        self.warmth = 1

    def run(self):
        while True:
            #Reset the game state here if needed
            self.clock.tick(120)
            self.dt = self.clock.get_time() / 1000.0
            self.screen.fill((0, 0, 0))

            # Calculate camera offset (Top-Left of map relative to screen)
            offset_x = (self.screen.get_width() // 2) - self.world_pos.x
            offset_y = (self.screen.get_height() // 2) - self.world_pos.y

            #draw map
            self.screen.blit(self.map.get_image(self.map_index), (offset_x, offset_y))

            w,h = self.screen.get_size()
            self.scale_window(w,h)


            #draw UI elements here
            self.player.draw(self.hitbox_debug, (offset_x, offset_y), self.scale)
            self.draw_world((offset_x, offset_y))
            self.draw_ui()


            #update elements
            beacon_pos = (self.map_size[0] // 2, self.map_size[1] // 2)
            self.player.update(100, 400, self.dt, self.map_size, beacon_pos, 200*self.scale['overall'])
            self.update_world()


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
                    if self.Master_debug_mode:
                        if event.key == pygame.K_F1:
                                self.UI_debug_mode = not self.UI_debug_mode
                        if event.key == pygame.K_F2:
                                self.hitbox_debug = not self.hitbox_debug
                        if event.key == pygame.K_1:
                            self.map_index = 0
                        if event.key == pygame.K_2:
                            self.map_index = 1
                        if event.key == pygame.K_k:
                            self.warmth -= 0.1
                        if event.key == pygame.K_l:
                            self.warmth += 0.1



                    if event.key == pygame.K_F11:
                        if self.screen.get_size() == self.full_screen_size:
                            self.screen = pygame.display.set_mode(self.last_screen_size, pygame.RESIZABLE); self.scale_window(w,h)
                        else:
                            self.screen = pygame.display.set_mode(self.full_screen_size, pygame.RESIZABLE); self.scale_window(w,h)
                     
                    
    
            #Update game state here
            pygame.display.flip()

    
    #=====================================================
    # World
    #=====================================================
    def update_world(self):
        # Camera follows player
        target_x = self.player.world_pos.x
        target_y = self.player.world_pos.y
        
        w, h = self.screen.get_size()
        
        # Clamp camera center so view doesn't leave map
        min_x = w // 2
        max_x = self.map_size[0] - w // 2
        min_y = h // 2
        max_y = self.map_size[1] - h // 2

        self.world_pos.x = max(min_x, min(target_x, max_x))
        self.world_pos.y = max(min_y, min(target_y, max_y))

        self.time_speed = self.dt * abs(round((abs(self.player.velocity.length_squared())/10)))
        self.time_left -= self.time_speed
        
    def draw_world(self, offset):
        w,h = self.screen.get_size()
        
        offset_x = (self.screen.get_width() // 2) - self.world_pos.x
        offset_y = (self.screen.get_height() // 2) - self.world_pos.y
        beacon_pos = ((self.map_size[0] // 2) + offset_x, (self.map_size[1] // 2) + offset_y)
        radius = 200 
        
        self.vision_resize = (w*self.warmth,h*self.warmth)
        self.vision = pygame.transform.scale(self.vision, self.vision_resize)
        screen_x = self.player.world_pos.x + offset[0] - self.vision_resize[0]//2
        screen_y = self.player.world_pos.y + offset[1] - self.vision_resize[1]//2

        self.screen.blit(self.vision,(screen_x, screen_y))
        #draw black squares surrounding the vision
        pygame.draw.rect(self.screen, (0,0,0), (screen_x - self.vision_resize[0]//2, screen_y - self.vision_resize[1]//2, self.vision_resize[0], self.vision_resize[1]), 1)
        
        


       
        self.beacon_light_resize = (2000*self.scale['overall'],2000*self.scale['overall'])
        self.beacon_light = pygame.transform.scale(self.beacon_light, self.beacon_light_resize)
        self.screen.blit(self.beacon_light, (beacon_pos[0] - self.beacon_light_resize[0]//2, beacon_pos[1] - self.beacon_light_resize[1]//2))

        if self.hitbox_debug:
            pygame.draw.circle(self.screen, (255, 0, 0), beacon_pos, radius * self.scale['overall'])



    #=====================================================
    # Window elements
    #=====================================================
    def scale_window(self, w, h): 
        self.scale['width'] = w / utils.BASE_SIZE[0]
        self.scale['height'] = h / utils.BASE_SIZE[1]
        self.scale['overall'] = min(self.scale['width'], self.scale['height'])  
        if self.screen.get_size() != self.full_screen_size: self.last_screen_size = (w,h)

    def draw_ui(self):
        #Draw UI elements here
        w,h = self.screen.get_size()

        time_left_pos = (w//2-(100*self.scale['width']), 10*self.scale['height'])
        utils.draw_text(text=f"Time Left: {round(self.time_left, 1)}s", position=time_left_pos, size=40, color= "#FFFFFF")

        if self.UI_debug_mode:
            utils.draw_text(text=f"Fps:{round(self.clock.get_fps())}", position=(10*self.scale['width'], 10*self.scale['height']), size=20*self.scale['overall'], color="#FFFFFF")
            utils.draw_text(text=f"Player velocity: {self.player.velocity}, Velocity Lenght: {self.player.velocity.length_squared():.1f}", position=(10*self.scale['width'], 30*self.scale['height']), size=20*self.scale['overall'], color="#FFFFFF")
            utils.draw_text(text=f"Map pos: {self.world_pos}", position=(10*self.scale['width'], 50*self.scale['height']), size=20*self.scale['overall'], color="#FFFFFF")
            utils.draw_text(text=f"Warmth: {self.warmth}", position=(10*self.scale['width'], 70*self.scale['height']), size=20*self.scale['overall'], color="#FFFFFF")


#Entry point of the game
if __name__ == "__main__":
    game = Froststep()
    game.run()