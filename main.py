import time
import pygame
import sys, os, math
import utilities as utils
import objects

class Froststep:
    def __init__(self):
        #starting app
        os.environ['SDL_VIDEO_CENTERED'] = '1'
        os.system("cls" if os.name == "nt" else "clear")

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
        self.map_size = (5000, 5000)
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
        
        # We only need the base image for the light. 
        self.beacon_light_base = utils.create_gradient("yellow", (1000, 1000), radius=300, opposite=True, circular=True)
        self.cached_beacon_light = None
        self.last_scale_overall = -1 # Used to check if we need to rescale the light

        #player
        self.player = objects.player((self.map_size[0] // 3, self.map_size[1] // 2))
        w, h = self.screen.get_size() 
        self.vision_base = utils.create_gradient("black", (1500, 1500), 400, opposite=True)
        
        # Create the fog surface ONCE, not every frame
        self.fog = pygame.Surface((w, h), pygame.SRCALPHA)
        
        # Cache the vision scaling so we don't scale it 120 times a second
        self.cached_vision_surf = None
        self.last_warmth = -1 

        #game features
        self.time_left = 120 #<- in seconds
        self.time_speed = 100
        self.warmth = 1
        
        # Trigger an initial scale setup
        self.scale_window(w, h)

    def run(self):
        while True:
            #Reset the game state here if needed
            self.dt = self.clock.tick(120) / 1000.0
            self.screen.fill((0, 0, 0))

            # Calculate camera offset (Top-Left of map relative to screen). Use integers for drawing.
            offset_x = (self.screen.get_width() // 2) - int(self.world_pos.x)
            offset_y = (self.screen.get_height() // 2) - int(self.world_pos.y)

            #draw map
            self.screen.blit(self.map.get_image(self.map_index), (offset_x, offset_y))

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

                # Handle window resizing properly here, instead of every frame
                if event.type == pygame.VIDEORESIZE:
                    w, h = event.w, event.h
                    self.fog = pygame.Surface((w, h), pygame.SRCALPHA) # Recreate fog to fit new screen
                    self.scale_window(w, h)

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
                            w, h = self.last_screen_size
                            self.screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)
                        else:
                            self.last_screen_size = self.screen.get_size()
                            w, h = self.full_screen_size
                            self.screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)
                        
                        # Apply new settings
                        self.fog = pygame.Surface((w, h), pygame.SRCALPHA)
                        self.scale_window(w, h)
                        
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
        w, h = self.screen.get_size()
        
        offset_x = (w // 2) - int(self.world_pos.x)
        offset_y = (h // 2) - int(self.world_pos.y)
        beacon_pos = ((self.map_size[0] // 2) + offset_x, (self.map_size[1] // 2) + offset_y)
        radius = 200 
        
        # Fog System Optimization: Clear the existing surface instead of creating a new one
        self.fog.fill((0, 0, 0, 255))
        
        safe_warmth = max(0.05, self.warmth)
        
        # CACHE CHECK: Only scale the image if the warmth ACTUALLY changed
        if safe_warmth != self.last_warmth:
            vision_size = (int(1500 * safe_warmth), int(1500 * safe_warmth))
            self.cached_vision_surf = pygame.transform.scale(self.vision_base, vision_size)
            self.last_warmth = safe_warmth
        
        vision_rect = self.cached_vision_surf.get_rect() # pyright: ignore[reportOptionalMemberAccess]
        screen_x = int(self.player.world_pos.x + offset[0] - vision_rect.width // 2)
        screen_y = int(self.player.world_pos.y + offset[1] - vision_rect.height // 2)
        
        self.fog.blit(self.cached_vision_surf, (screen_x, screen_y), special_flags=pygame.BLEND_RGBA_SUB)  # pyright: ignore[reportArgumentType]
        self.screen.blit(self.fog, (0, 0))

        # CACHE CHECK: Only scale the beacon light if the screen was resized
        if self.scale['overall'] != self.last_scale_overall or self.cached_beacon_light is None:
            self.cached_beacon_light = pygame.transform.scale(self.beacon_light_base, self.beacon_light_resize)
            self.last_scale_overall = self.scale['overall']

        # Get rect to easily center the image
        beacon_rect = self.cached_beacon_light.get_rect(center=beacon_pos)
        self.screen.blit(self.cached_beacon_light, beacon_rect.topleft)

        if self.hitbox_debug:
            pygame.draw.circle(self.screen, (255, 0, 0), beacon_pos, int(radius * self.scale['overall']))

    #=====================================================
    # Window elements
    #=====================================================
    def scale_window(self, w, h): 
        self.scale['width'] = w / utils.BASE_SIZE[0]
        self.scale['height'] = h / utils.BASE_SIZE[1]
        self.scale['overall'] = min(self.scale['width'], self.scale['height'])  

        # Pre-calculate integers for transforms
        self.beacon_light_resize = (int(2000 * self.scale['overall']), int(2000 * self.scale['overall']))
        
        if self.screen.get_size() != self.full_screen_size: 
            self.last_screen_size = (w, h)

    def draw_ui(self):
        #Draw UI elements here
        w, h = self.screen.get_size()

        time_left_pos = (w // 2 - int(100 * self.scale['width']), int(10 * self.scale['height']))
        utils.draw_text(text=f"Time Left: {round(self.time_left, 1)}s", position=time_left_pos, size=40, color="#FFFFFF")

        if self.UI_debug_mode:
            utils.draw_text(text=f"Fps:{round(self.clock.get_fps())}", position=(int(10*self.scale['width']), int(10*self.scale['height'])), size=int(20*self.scale['overall']), color="#FFFFFF")
            utils.draw_text(text=f"Player velocity: {self.player.velocity}, Velocity Length: {self.player.velocity.length_squared():.1f}", position=(int(10*self.scale['width']), int(30*self.scale['height'])), size=int(20*self.scale['overall']), color="#FFFFFF")
            utils.draw_text(text=f"Map pos: {self.world_pos}", position=(int(10*self.scale['width']), int(50*self.scale['height'])), size=int(20*self.scale['overall']), color="#FFFFFF")
            utils.draw_text(text=f"Warmth: {self.warmth:.2f}", position=(int(10*self.scale['width']), int(70*self.scale['height'])), size=int(20*self.scale['overall']), color="#FFFFFF")

#Entry point of the game
if __name__ == "__main__":
    game = Froststep()
    game.run()