import pygame
import sys, os, math, random
from enemy import *
import utilities as utils
import objects, player

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
        self.console_debug = True

        #world
        self.map_size = (5000, 5000)
        self.world_pos = pygame.Vector2(self.screen.get_size()[0] // 2, self.screen.get_size()[1] // 2)
        self.map = utils.SpriteSheet()
        self.map.extract_single_image("Textures/map_final_background.png", self.map_size)
        self.map.extract_single_image("Textures/map_bg.png", self.map_size)
        self.map_index = 0

        #screen elements/objects
        
        #beacon 
        self.beacon_img = utils.SpriteSheet()
        self.beacon_img.extract_grid("Textures\\Beacon.png", crop_size=(64,64), scale=(400,400))
        self.beacon_img_index = 0
        self.beacon_cap = 10
        self.beacon_storage = 0
        
        # We only need the base image for the light. 
        self.beacon_light_radius = 200
        self.beacon_light_base = utils.create_gradient("white", (1000, 1000), radius=self.beacon_light_radius, opposite=True, circular=True)
        self.cached_beacon_light = None
        self.last_scale_overall = -1 # Used to check if we need to rescale the light

        #player
        self.player = player.Player((self.map_size[0] // 3, self.map_size[1] // 2))
        w, h = self.screen.get_size() 
        self.vision_base = utils.create_gradient("black", (1500, 1500), 400, opposite=True)
        self.inventory = {
            "wood" : 2,
        }
        """
        current items avalible:
        wood
        """

        #items
        self.items_tex = utils.SpriteSheet()
        self.items_tex.extract_single_image("items/twig.png", (60,60))
        self.slot = 1
        self.items = objects.Items(50) #droped items class NOT the slot UI items
        #self.items.add_item("stick", (500,500), 0)#test item
        
        #enemys
        self.enemies = [Spider((500, 500))]


        # Create the fog surface ONCE, not every frame
        self.fog = pygame.Surface((w, h), pygame.SRCALPHA)
        
        # Cache the vision scaling so we don't scale it 120 times a second
        self.cached_vision_surf = None
        self.last_warmth = -1 

        #game features
        self.time_left = 120 #<- in seconds
        self.time_speed = 100
        self.warmth = 1

        #objects 
        self.trees = []
        self.tree_rects = [] # Optimized list for Pygame C-level collisions
        self.create_map()

        # Trigger an initial scale setup
        self.scale_window(w, h)

    def run(self):
        while True:
            #Reset the game state here if needed
            self.dt = self.clock.tick(60) / 1000.0
            self.screen.fill((0, 0, 0))

            # Calculate camera offset (Top-Left of map relative to screen). Use integers for drawing.
            offset_x = (self.screen.get_width() // 2) - int(self.world_pos.x)
            offset_y = (self.screen.get_height() // 2) - int(self.world_pos.y)

            # OPTIMIZATION: Subsurface Map Blitting. 
            # Only extracts and blits the visible portion of the 5000x5000 map.
            w, h = self.screen.get_size()
            view_rect = pygame.Rect(-offset_x, -offset_y, w, h)
            map_image = self.map.get_image(self.map_index)
            view_rect.clamp_ip(map_image.get_rect()) # Ensure we don't look outside the map
            self.screen.blit(map_image, (0, 0), area=view_rect)

            #update enemy first
            time_speed = 0.1 #self.dt * abs(round((abs(self.player.velocity.length_squared())*(self.warmth*0.1))))
            for enemy in self.enemies:
                enemy.update(self.dt, self.player.world_pos, time_speed, self.map_size, [t.rect for t in self.trees])
                enemy.draw((offset_x, offset_y), self.hitbox_debug)


            #draw UI elements here
            self.player.draw(self.hitbox_debug, (offset_x, offset_y), self.scale)
            self.items.draw((offset_x, offset_y), self.hitbox_debug)
            self.draw_world((offset_x, offset_y))
            self.draw_ui(pygame.Vector2((offset_x, offset_y)))

            #update elements
            beacon_pos = (self.map_size[0] // 2, self.map_size[1] // 2)
            self.player.update(100, self.dt, self.map_size, beacon_pos, 200*self.scale['overall'], self.tree_rects, (offset_x, offset_y))
            self.update_world()
            self.draw_inv()
            
            #Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                # Handle window resizing properly here, instead of every frame
                if event.type == pygame.VIDEORESIZE:
                    if self.console_debug: print(f"Resized to {event.w, event.h}")
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
                        if event.key == pygame.K_F3:
                            self.console_debug = not self.console_debug
                        if event.key == pygame.K_1:
                            self.map_index = 0
                        if event.key == pygame.K_2:
                            self.map_index = 1
                        if event.key == pygame.K_k:
                            self.warmth -= 0.1
                        if event.key == pygame.K_l:
                            self.warmth += 0.1

                        if event.key == pygame.K_q:
                            inv_items = list(self.inventory.items())
                            # Check if the currently selected slot actually has an item
                            if self.slot - 1 < len(inv_items):
                                item_name = inv_items[self.slot - 1][0]
                                
                                # Decrease count
                                self.inventory[item_name] -= 1

                                match item_name:
                                    case "wood": self.items.add_item("twig", self.world_pos, 0)
                                    case _: pass
                                
                                # Remove from dictionary if count hits zero
                                if self.inventory[item_name] <= 0:
                                    del self.inventory[item_name]


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
                    
                elif event.type == pygame.MOUSEWHEEL:
                    current_index = self.slot - 1
                    new_index = (current_index + event.y) % 3
                    self.slot = new_index + 1

            

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

        self.time_speed = self.dt * abs(round((abs(self.player.velocity.length_squared())*(self.warmth*0.1))))
        self.time_left -= self.time_speed
        
    def draw_world(self, offset):
        w, h = self.screen.get_size()
        offset_x, offset_y = offset
        
        # OPTIMIZATION: Camera Culling. Only draw and update trees that are within the screen!
        camera_rect = pygame.Rect(-offset_x, -offset_y, w, h)
        camera_rect.inflate_ip(200, 200) # Expand slightly so trees don't pop in abruptly at the edges

        mouse_pressed = pygame.mouse.get_pressed()[0] # Call ONCE per frame

        for tree in self.trees[:]:
            if camera_rect.colliderect(tree.rect):
                tree.update()
                tree.draw(offset, self.hitbox_debug)

                if mouse_pressed:
                    if self.player.fist_hitbox.colliderect(tree.get_rect(offset)):
                        if tree.hit():
                            self.trees.remove(tree)
                            self.update_tree_data()

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

        rsize =  int(radius * self.scale['overall'])
        self.screen.blit(self.beacon_img.get_image(self.beacon_img_index), (beacon_pos[0] - rsize, beacon_pos[1] - rsize))


        if self.hitbox_debug:
            pygame.draw.circle(self.screen, (255, 0, 0), beacon_pos, int(radius * self.scale['overall']),3)
    #=====================================================
    # Window elements
    #=====================================================
    def scale_window(self, w, h): 
        self.scale['width'] = w / utils.BASE_SIZE[0]
        self.scale['height'] = h / utils.BASE_SIZE[1]
        self.scale['overall'] = min(self.scale['width'], self.scale['height'])  

        # Pre-calculate integers for transforms
        self.beacon_light_resize = (int(2000 * self.scale['overall']), int(2000 * self.scale['overall']))
        self.beacon_img.rezize_images((400*self.scale['overall'], 400*self.scale['overall']))
        for tree in self.trees:
            tree.resize(self.scale)

        for enemy in self.enemies:
            enemy.resize((100*self.scale['overall'], 100*self.scale['overall']))

        self.items_tex.rezize_images((60 *self.scale['overall'],  60 *self.scale['overall']))
        self.items.resize(self.scale)

        self.update_tree_data()
 
        if self.screen.get_size() != self.full_screen_size: 
            self.last_screen_size = (w, h)

    def draw_ui(self, offset):
        #Draw UI elements here
        w, h = self.screen.get_size()

        time_left_pos = (w // 2 , int(30 * self.scale['height']))
        utils.draw_text(text=f"Time Left: {round(self.time_left, 1)}s", position=time_left_pos, size=40, color="#FFFFFF", centered=True)

        if self.UI_debug_mode:

            utils.draw_text(text=f"Fps:{round(self.clock.get_fps())}", position=(int(10*self.scale['width']), int(10*self.scale['height'])), size=int(20*self.scale['overall']), color="#FFFFFF")
            utils.draw_text(text=f"Player velocity: {self.player.velocity}, Velocity Length: {self.player.velocity.length_squared():.1f}", position=(int(10*self.scale['width']), int(30*self.scale['height'])), size=int(20*self.scale['overall']), color="#FFFFFF")
            utils.draw_text(text=f"Map pos: {self.world_pos}", position=(int(10*self.scale['width']), int(50*self.scale['height'])), size=int(20*self.scale['overall']), color="#FFFFFF")
            utils.draw_text(text=f"Warmth: {self.warmth:.2f}", position=(int(10*self.scale['width']), int(70*self.scale['height'])), size=int(20*self.scale['overall']), color="#FFFFFF")
            utils.draw_text(text=f"Mouse World Pos: {pygame.Vector2(pygame.mouse.get_pos())-offset}", position=(int(10*self.scale['width']), int(90*self.scale['height'])), size=int(20*self.scale['overall']), color="#FFFFFF")
    
    def draw_inv(self):
        slots = 3
        slot_size = 60 * self.scale['overall']
        padding = 10 * self.scale['overall']
        total_width = (slot_size * slots) + (padding * (slots - 1))
        
        screen = pygame.display.get_surface()
        screen_rect = screen.get_rect()

        # Get inventory items as a list of tuples: [("wood", 2), ("coal", 4)]
        inven_items = list(self.inventory.items())

        for i in range(slots):
            # 1. Calculate horizontal position to center the whole bar
            start_x = screen_rect.centerx - (total_width // 2)
            x_pos = start_x + (i * (slot_size + padding))
            y_pos = screen_rect.bottom - slot_size - 20
            
            # 2. Draw the background slot box (Always draw this!)
            slot_surf = pygame.Surface((slot_size, slot_size), pygame.SRCALPHA)
            slot_surf.fill((255, 255, 255, 100)) 
            screen.blit(slot_surf, (x_pos, y_pos))

            # 3. Draw Selected slot highlight (Always check this!)
            if self.slot - 1 == i: 
                pygame.draw.rect(self.screen, "Red", (x_pos, y_pos, slot_size, slot_size), 4)

            # 4. Only draw item details if this index exists in our inventory list
            if i < len(inven_items):
                item_name = inven_items[i][0]
                item_amt = inven_items[i][1]

                # Draw the specific item texture
                match item_name:
                    case "wood": 
                        self.screen.blit(self.items_tex.get_image(0), (x_pos, y_pos))
                    case "coal":
                        # Assuming coal is index 1 in your sprite sheet
                        self.screen.blit(self.items_tex.get_image(1), (x_pos, y_pos))
                    case _:
                        pass
                
                # Draw the amount text
                utils.draw_text(
                    text=str(item_amt), 
                    position=(x_pos + 5, y_pos + 5), 
                    size=int(20 * self.scale['overall']), 
                    color="#FFFFFF"
                )


    def create_map(self, size=100):
        center_x, center_y = self.map_size[0] // 2, self.map_size[1] // 2
        for i in range(self.map_size[0] // size):
            for j in range(self.map_size[1] // size):
                x, y = (i * size) + (size // 2), (j * size) + (size // 2)
                #MAKING SURE THERE IS DISTANCE BEWTTWEN THE BEACON AND THE TREE
                if math.hypot(x - center_x, y - center_y) < 600:
                    continue

                chance = random.uniform(0, 1)
                if chance < 0.05:
                    self.trees.append(objects.Tree((x, y), 1, size))
                elif chance < 0.1:
                    self.trees.append(objects.Tree((x, y), 0, size))

        self.update_tree_data()

    def update_tree_data(self):
        # OPTIMIZATION: Simple native Pygame Rect list. 
        # Collisions are checked in heavily optimized native C code via Pygame instead of NumPy.
        self.tree_rects = [t.rect for t in self.trees]

#Entry point of the game
if __name__ == "__main__":
    game = Froststep() 
    game.run()