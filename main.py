import pygame
import sys, os, math, random
from enemy import *
import utilities as utils
import objects, player, ui
from Beacon import Beacon
import Sound

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
        self.mode = "menu"
        self.stage = "Running"
        self.running = False
        
        #debug
        self.Master_debug_mode = True
        self.UI_debug_mode = False
        self.hitbox_debug = False
        self.console_debug = False

        #world
        self.map_size = (5000, 5000)
        self.world_pos = pygame.Vector2(self.screen.get_size()[0] // 2, self.screen.get_size()[1] // 2)
        self.map = utils.SpriteSheet()
        self.map.extract_single_image("Textures/map_final_background.png", self.map_size)
        self.map.extract_single_image("Textures/map_bg.png", self.map_size)
        self.map_index = 0

        #screen elements/objects
        self.popout = ui.TextPopout()


        #beacon
        self.beacon = Beacon((self.map_size[0] // 2, self.map_size[1] // 2), size=484)

        #player
        self.player = player.Player((self.map_size[0] // 3, self.map_size[1] // 2))
        w, h = self.screen.get_size() 
        self.vision_base = utils.create_gradient("black", (1500, 1500),400, opposite=True)
        self.inventory = {
            "membrane" : 4,
            "wood" : 4,
            "apple" : 4.
        } if self.Master_debug_mode else {}
        """
        current items avalible:
        wood
        membrane
        apple
        """

        #items
        self.items_tex = utils.SpriteSheet()
        self.items_tex.extract_single_image("items/twig.png", (60,60))
        self.items_tex.extract_single_image("items/membrane.png", (60,60))
        self.items_tex.extract_single_image("items/apple.png", (60,60))
        self.slot = 1
        self.items = objects.Items(50) #droped items class NOT the slot UI items
        #self.items.add_item("stick", (500,500), 0)#test item
        self.pickup_timer = utils.Timer(0.3)
        self.pickup_timer.start()
        
        #enemys
       # Spawn some Spiders
        self.enemies = []
        for _ in range(12):
            ex = random.randint(0, self.map_size[0])
            ey = random.randint(0, self.map_size[1])
            self.enemies.append(Spider((ex, ey)))
            


        # Create the fog surface ONCE, not every frame
        self.fog = pygame.Surface((w, h), pygame.SRCALPHA)
        
        # Cache the vision scaling so we don't scale it 120 times a second
        self.cached_vision_surf = None
        self.last_warmth = -1 
        
        self.has_won = False
        self.win_circle_radius = 0
        self.win_flash_alpha = 0

        #game features
        self.time_left = 12#<- in seconds
        self.time_speed = 100
        self.warmth = 1

        #objects 
        self.trees = []
        self.tree_rects = [] # Optimized list for Pygame C-level collisions
        self.create_map()

        #warmth meter
        self.warmth_bar = ui.WarmthBar((960, 490), image_path="Assets/Textures/Thermometer.png", size= (150,190))

        #buttons
        self.menu_buttons = [] # Will be created in menu()
        self.game_over_buttons = [
            utils.Button(pos=(w/2, h/2 + 100), size=(250, 60), text="Restart", center=True, callback=self.restart_game),
            utils.Button(pos=(w/2, h/2 + 180), size=(250, 60), text="Exit to Main Menu", center=True, callback=self.go_to_menu)
        ]
        self.win_buttons = [
            utils.Button(pos=(utils.BASE_SIZE[0] - 120, 50), size=(200, 60), text="Exit", center=True, callback=self.go_to_menu)
        ]
        
        #sound stuff
        self.sound = Sound.SoundManager()
        self.sound.load_sfx("Hit", "hitHurt.wav")
        self.sound.load_sfx("Tree Broken", "Tree_broken.wav")
        self.sound.load_sfx("Tree Hit", "Tree_hit.wav")
        self.sound.load_sfx("DEATH", "Death.wav")
        self.sound.load_sfx("beacon upgrade", "Beacon upgrade.wav")
        self.sound.load_sfx("beacon add feul", "beacon_feul.wav")
        self.sound.load_music("main menu music", "glacial_ambient.wav")

        
        self.tree_hit_sound_timer = utils.Timer(0.1)
        self.tree_hit_sound_timer.start()
        

        # Trigger an initial scale setup
        self.scale_window(w, h)

       



    def run(self):  
        self.sound.stop_music()
        self.stage = "Running"
        self.running = True
        while self.running:
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

            # --- Drawing (unconditional) ---
            for enemy in self.enemies:
                enemy.draw((offset_x, offset_y), self.hitbox_debug)
            self.player.draw(self.hitbox_debug, (offset_x, offset_y), self.scale)
            self.items.draw((offset_x, offset_y), self.hitbox_debug)
            self.draw_world((offset_x, offset_y), self.stage)
            self.draw_ui(pygame.Vector2((offset_x, offset_y)))
            self.draw_inv()

            if self.has_won:
                for bts in self.win_buttons:
                    bts.update()
                    bts.draw()

            # --- Updates (conditional on stage) ---
            if self.stage == "Running":
                # Enemy updates
                for enemy in self.enemies[:]: # Iterate over a copy to allow removal
                    damage_dealt = enemy.update(self.dt, self.player.world_pos, self.map_size, self.tree_rects, self.enemies, player_warmth=self.warmth)
                    if damage_dealt > 0:
                        if self.player.hit(damage_dealt):
                            pass # Game over is handled below
                        self.popout.add_bottom_pop_out(f"-{damage_dealt}", pygame.Vector2(50,100), 1.0, rise_by=60, center=True, color="red", size = 30)

                    # Player attacking enemy
                    enemy_screen_rect = enemy.rect.move(offset_x, offset_y)
                    if (self.player.is_attacking() and 
                        enemy not in self.player.hit_this_swing and 
                        self.player.fist_hitbox.colliderect(enemy_screen_rect)):
                        
                        self.player.hit_this_swing.add(enemy)
                        drops = enemy.hit(25) # Example damage
                        self.sound.play_sfx("Hit")
                        if drops:
                            for _ in range(drops['membrane']):
                                drop_pos = enemy.world_pos + pygame.Vector2(random.randint(-20, 20), random.randint(-20, 20))
                                self.items.add_item("membrane", drop_pos, 1)
                            self.enemies.remove(enemy)

                # World and player updates
                self.update_world()
                self.player.update(100 * self.warmth, self.dt, self.map_size, self.beacon.pos, self.beacon.get_radius(), self.tree_rects, (offset_x, offset_y))

            # --- Game Over Check ---
            if (self.player.is_dead or self.time_left <= 0 or self.warmth <= 0) and self.stage == "Running":
                self.stage = "Dead"
                self.sound.play_sfx("DEATH")
            
            if self.stage == "Dead":
                self.death(w,h)
                for bts in self.game_over_buttons:
                    bts.update()
                    bts.draw()
            elif self.stage == "Running":
                # check if the items could be picked up or not
                player_rect = self.player.get_rect((offset_x, offset_y), self.scale)
                world_player_rect = player_rect.copy()
                world_player_rect.x -= offset_x
                world_player_rect.y -= offset_y
                
                checked_itms = self.items.check_can_remove(world_player_rect)
                can_deposit = self.beacon.check_deposit_rad(self.player.rect)
                
                if checked_itms:
                    if self.console_debug: print(f"Standing on items at indices: {checked_itms}")
                    utils.draw_text(text=f"Press [e] to pick up item", color=(255,255,255), 
                                    position=(w//2, 580*self.scale['height']), 
                                    size=50*self.scale['overall'], centered=True)
                elif can_deposit:
                    utils.draw_text(text=f"Press [e] to deposit item", color=(255,255,255), 
                                    position=(w//2, 580*self.scale['height']), 
                                    size=50*self.scale['overall'], centered=True)
            
            #Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit_game()
                if self.stage == "Dead":
                    for bts in self.game_over_buttons:
                        bts.handle_event(event)
                
                if self.has_won:
                    for bts in self.win_buttons:
                        bts.handle_event(event)

                # Handle window resizing properly here, instead of every frame
                if event.type == pygame.VIDEORESIZE:
                    if self.console_debug: print(f"Resized to {event.w, event.h}")
                    w, h = event.w, event.h
                    self.scale_window(w, h)

                if event.type == pygame.KEYDOWN:
                    if self.stage == "Running":
                        if event.key == pygame.K_ESCAPE:
                            self.go_to_menu()

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

                        if event.key == pygame.K_e:
                            if checked_itms:
                                self.popout.add_top_pop_out(f"Picked up {self.items.names[checked_itms[0]]}",pygame.Vector2(w//2, 80), 1, center=True)
                                match self.items.names[checked_itms[0]]:
                                    case "twig" if self.add("wood", 1): self.items.remove_item(checked_itms[0]) 
                                    case "membrane" if self.add("membrane", 1): self.items.remove_item(checked_itms[0])
                                    case "apple" if self.add("apple", 1): self.items.remove_item(checked_itms[0]) 
                                    case _: pass
                            elif can_deposit:
                                
                                inv_items = list(self.inventory.items())
                                # Check if the currently selected slot actually has an item
                                if self.slot - 1 < len(inv_items):
                                    item_name = inv_items[self.slot - 1][0]
                                    fuel_val = 0
                                    
                                    match item_name:
                                        case "wood": fuel_val = 1
                                        case "membrane": fuel_val = 3
                                        case "apple": 
                                            self.popout.add_top_pop_out(f"Cannot use {item_name} as fuel", pygame.Vector2(w//2, 80), 0.5, center=True)
                                        case _: pass
                                    
                                    if fuel_val > 0:
                                        self.inventory[item_name] -= 1
                                        if self.inventory[item_name] <= 0: del self.inventory[item_name]
                                        
                                        upgraded = self.beacon.add_fuel(fuel_val)
                                        self.popout.add_top_pop_out(f"Deposited 1 {item_name}", pygame.Vector2(w//2, 80), 0.5, center=True)
                                        self.sound.play_sfx("beacon add feul")
                                        if upgraded: self.sound.play_sfx("beacon upgrade")
                                        if self.beacon.stage < self.beacon.max_stage:
                                            self.popout.add_top_pop_out(f"Need {self.beacon.fuel_requirements[self.beacon.stage]-self.beacon.fuel} more to advance",pygame.Vector2(w//2, 80), 0.5, center=True)
                                else:
                                    self.popout.add_top_pop_out(f"This inventory slot has nothing",pygame.Vector2(w//2, 80), 0.5, center=True)

                        if event.key == pygame.K_q:
                            inv_items = list(self.inventory.items())
                            # Check if the currently selected slot actually has an item
                            if self.slot - 1 < len(inv_items):
                                item_name = inv_items[self.slot - 1][0]
                                
                                # Decrease count
                                self.inventory[item_name] -= 1

                                match item_name:
                                    case "wood": self.items.add_item("twig", self.world_pos, 0)
                                    case "membrane": self.items.add_item("membrane", self.world_pos, 1)
                                    case "apple":  self.items.add_item("apple", self.world_pos, 2)
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
                        self.scale_window(w, h)
                    
                elif event.type == pygame.MOUSEWHEEL:
                    current_index = self.slot - 1
                    new_index = (current_index + event.y) % 3
                    self.slot = new_index + 1

            # --- WIN STATE CHECK & UPDATE ---
            if self.beacon.stage >= self.beacon.max_stage and not self.has_won:
                self.has_won = True
                self.win_circle_radius = self.beacon.get_radius()
                self.win_flash_alpha = 255 # Start the white flash at full brightness
                self.enemies.clear()

            if self.has_won:
                self.warmth = 1.4 # Permanent warmth!
                self.win_circle_radius += 3000 * self.dt # Expand out to clear the fog rapidly
                self.win_flash_alpha = max(0, self.win_flash_alpha - 150 * self.dt) # Fade out the bright flash
            elif self.stage == "Running":
                # Only decrement timer if player hasn't won
                self.time_left -= self.dt

            #Update game state here
            pygame.display.flip()

    def menu(self): 
        
        self.mode = "menu"

        self.menu_buttons = []
        
        cx = utils.BASE_SIZE[0] // 2
        cy = utils.BASE_SIZE[1] // 2
        
        # Play Button
        play_btn = utils.Button(
            pos=(cx, cy), 
            size=(220, 65), 
            text="Play Game", 
            color=(50, 140, 70), 
            hover_color=(70, 170, 90), 
            press_color=(40, 110, 50),
            callback=self.start_game, 
            center=True,
            font="Rajdhani-Bold",
            radius=12
        )
        
        # Quit Button
        quit_btn = utils.Button(
            pos=(cx, cy + 90), 
            size=(220, 65), 
            text="Quit", 
            color=(180, 60, 60), 
            hover_color=(210, 80, 80), 
            press_color=(140, 40, 40),
            callback=self.quit_game, 
            center=True,
            font="Rajdhani-Bold",
            radius=12
        )
        
        self.menu_buttons.extend([play_btn, quit_btn])
        
        for bts in self.menu_buttons:
            bts.resize(self.scale)
        
        for bts in self.game_over_buttons:
            bts.resize(self.scale)
            
        for bts in self.win_buttons:
            bts.resize(self.scale)

        self.sound.play_music("main menu music")
        while True:
            w,h =  self.screen.get_size()
            self.dt = self.clock.tick(60) / 1000.0
            self.screen.fill( (21, 20, 67))
            
            #draw main Text
            utils.draw_text("FROSTSTEP", (w/2, 100*self.scale['height']), 200*self.scale['overall'],(255//2,255//2,255//2) , centered=True, font="Rajdhani-Bold", bold=True, italic=True)
            utils.draw_text("FROSTSTEP", (w/2, 110*self.scale['height']), 210*self.scale['overall'], (255,255,255), centered=True, font="Rajdhani-Bold", bold=True, italic=True)

           

            # -------- EVENTS --------
            for event in pygame.event.get():

                if event.type == pygame.QUIT:
                    self.quit_game()
                    

                if event.type == pygame.VIDEORESIZE:
                    if self.console_debug: print(f"Resized to {event.w, event.h}")
                    w, h = event.w, event.h
                    self.scale_window(w, h)


                if event.type == pygame.KEYDOWN:

                    if event.key == pygame.K_ESCAPE:
                        self.quit_game()
                        

                    if event.key == pygame.K_F11:

                        if self.screen.get_size() == self.full_screen_size:
                            w, h = self.last_screen_size
                            self.screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)
                        else:
                            self.last_screen_size = self.screen.get_size()
                            w, h = self.full_screen_size
                            self.screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)

                        self.scale_window(w, h)

               
                for bts in self.menu_buttons:
                    bts.handle_event(event)

            # -------- UPDATE --------
            for bts in self.menu_buttons:
                bts.update()

            # -------- DRAW --------
            for bts in self.menu_buttons:
                bts.draw()

            pygame.display.flip()


    #====================================================
    # inventory
    #====================================================
    def add(self, item, amt):

        #1. if timer has not passed exit
        if not self.pickup_timer.has_elapsed():
            return False
        
        #2. if timer PASSED then reset and procceed
        self.pickup_timer.restart()
        
        #3. assign vars
        items = list(self.inventory.items())
        slots = 3

        #4. create the list loop checking if item exist or not
        for stored, stored_amt in items:

            #5. If exist add and close this func
            if stored == item:
                self.inventory[stored] += amt
                return True #marks stored
        
        #6. create a new slot for this if the lenth is <= max slots
        if len(items) < slots:
            self.inventory[item] = amt
            return True
        
        #7. Doesn't exist and cannot be added to inv so just say can't add
        return False

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
                    case "membrane":
                        # Assuming coal is index 1 in your sprite sheet
                        self.screen.blit(self.items_tex.get_image(1), (x_pos, y_pos))
                    case "apple":
                        self.screen.blit(self.items_tex.get_image(2), (x_pos, y_pos))
                    case _:
                        pass
                
                # Draw the amount text
                utils.draw_text(
                    text=str(int(item_amt)), 
                    position=(x_pos + 5, y_pos + 5), 
                    size=int(20 * self.scale['overall']), 
                    color="#FFFFFF"
                )


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

        self.time_speed = self.dt * abs(round((abs(self.player.velocity.length_squared())*(self.warmth*0.01))))
        self.time_left -= self.time_speed
        
        dist = self.beacon.get_distance_from(self.player.world_pos)
        if dist <= 1000 and self.warmth <= 1.4:
            self.warmth += ((dist/10000) + 0.1) * self.dt
            self.time_left += 0.1 * self.dt
        elif self.warmth >= 0.39: 
            self.warmth -= 0.039 * self.dt
     
    def draw_world(self, offset, stage):
        w, h = self.screen.get_size()
        offset_x, offset_y = offset
        
        # OPTIMIZATION: Camera Culling. Only draw and update trees that are within the screen!
        camera_rect = pygame.Rect(-offset_x, -offset_y, w, h)
        camera_rect.inflate_ip(200, 200) # Expand slightly so trees don't pop in abruptly at the edges

        if stage == "Running":
            mouse_pressed = pygame.mouse.get_pressed()[0] # Call ONCE per frame

            for tree in self.trees[:]:
                if camera_rect.colliderect(tree.rect):
                    tree.update()
                    tree.draw(offset, self.hitbox_debug)

                    if mouse_pressed:
                        if self.player.fist_hitbox.colliderect(tree.get_rect(offset)):
                            if tree.hit():
                                if self.tree_hit_sound_timer.has_elapsed(): self.sound.play_sfx("Tree Hit", 0.5); self.tree_hit_sound_timer.restart()
                                self.items.add_item("twig", tree.pos, 0)
                                self.trees.remove(tree)
                                self.update_tree_data()
                            else:
                                self.sound.play_sfx("Tree Broken", 1.5)
        else: # Just draw if not running
            for tree in self.trees:
                if camera_rect.colliderect(tree.rect):
                    tree.draw(offset, self.hitbox_debug)

        # Fog System Optimization: Clear the existing surface instead of creating a new one
        safe_warmth = max(0.05, self.warmth)
        
        # CACHE CHECK: Only scale the image if the warmth ACTUALLY changed
        if safe_warmth != self.last_warmth:
            vision_size = (int(1500 * safe_warmth), int(1500 * safe_warmth))
            self.cached_vision_surf = pygame.transform.scale(self.vision_base, vision_size)
            self.last_warmth = safe_warmth
        
        vision_rect = self.cached_vision_surf.get_rect() # pyright: ignore[reportOptionalMemberAccess]
        screen_x = int(self.player.world_pos.x + offset[0] - vision_rect.width // 2)
        screen_y = int(self.player.world_pos.y + offset[1] - vision_rect.height // 2)
        
        if not self.has_won:
            # Normal Fog behavior
            self.fog.fill((0, 0, 0, 240))
            beacon_screen_pos = self.beacon.pos + pygame.Vector2(offset)
            
            # Punch hole for beacon
            pygame.draw.circle(self.fog, (0, 0, 0, 0), (int(beacon_screen_pos.x), int(beacon_screen_pos.y)), self.beacon.get_radius())
            # Punch hole for player vision by subtracting the vignette alpha
            self.fog.blit(self.cached_vision_surf, (screen_x, screen_y), special_flags=pygame.BLEND_RGBA_SUB) # pyright: ignore[reportArgumentType]
            self.screen.blit(self.fog, (0, 0))
        else:
            # FOG IS GONE! Draw the white expanding bright flash transition
            if self.win_flash_alpha > 0:
                flash_surf = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
                beacon_screen_pos = self.beacon.pos + pygame.Vector2(offset)
                
                # Draw a white circle with fading alpha
                flash_color = (255, 255, 255, int(self.win_flash_alpha))
                pygame.draw.circle(flash_surf, flash_color, (int(beacon_screen_pos.x), int(beacon_screen_pos.y)), int(self.win_circle_radius))
                self.screen.blit(flash_surf, (0, 0))
        self.beacon.draw(offset, self.hitbox_debug)
    #=====================================================
    # Window elements
    #=====================================================
    def scale_window(self, w, h): 
        self.scale['width'] = w / utils.BASE_SIZE[0]
        self.scale['height'] = h / utils.BASE_SIZE[1]
        self.scale['overall'] = min(self.scale['width'], self.scale['height'])  
        
        # Recreate the fog surface to match the new screen dimensions
        self.fog = pygame.Surface((w, h), pygame.SRCALPHA)
    
        for bts in self.menu_buttons:
            bts.resize(self.scale)

        
        
        

        self.beacon.resize(self.scale)
        for tree in self.trees:
            tree.resize(self.scale)

        for enemy in self.enemies:
            enemy.resize((100*self.scale['overall'], 100*self.scale['overall']))

        self.items_tex.rezize_images((60 *self.scale['overall'],  60 *self.scale['overall']))
        self.items.resize(self.scale)
        self.warmth_bar.resize(self.scale)
        self.popout.resize(self.scale)



        self.update_tree_data()
 
        if self.screen.get_size() != self.full_screen_size: 
            self.last_screen_size = (w, h)

    def draw_ui(self, offset):
        #Draw UI elements here
        w, h = self.screen.get_size()

        if self.has_won:
            # WIN Text overrides the timer
            utils.draw_text(text="You WIN", 
                            position=(w // 2, int(50 * self.scale['height'])), 
                            size=int(80 * self.scale['overall']), 
                            color="#FFFFFF", 
                            centered=True)
        else:
            # Normal Timer Text
            time_left_pos = (w // 2 , int(50 * self.scale['height']))
            utils.draw_text(text=f"Time Left: {round(self.time_left, 1)}s", position=time_left_pos, size=40, color="#FFFFFF", centered=True)

        self.draw_player_hp()

        self.warmth_bar.draw(self.screen, self.warmth, 2)

        self.popout.draw_all(self.dt)

        if self.UI_debug_mode:

            utils.draw_text(text=f"Fps:{round(self.clock.get_fps())}", position=(int(10*self.scale['width']), int(10*self.scale['height'])), size=int(20*self.scale['overall']), color="#FFFFFF")
            utils.draw_text(text=f"Player velocity: {self.player.velocity}, Velocity Length: {self.player.velocity.length_squared():.1f}", position=(int(10*self.scale['width']), int(30*self.scale['height'])), size=int(20*self.scale['overall']), color="#FFFFFF")
            utils.draw_text(text=f"Map pos: {self.world_pos}", position=(int(10*self.scale['width']), int(50*self.scale['height'])), size=int(20*self.scale['overall']), color="#FFFFFF")
            utils.draw_text(text=f"Warmth: {self.warmth:.2f}", position=(int(10*self.scale['width']), int(70*self.scale['height'])), size=int(20*self.scale['overall']), color="#FFFFFF")
            utils.draw_text(text=f"Mouse World Pos: {pygame.Vector2(pygame.mouse.get_pos())-offset}", position=(int(10*self.scale['width']), int(90*self.scale['height'])), size=int(20*self.scale['overall']), color="#FFFFFF")
            utils.draw_text(text=f"Distance to player: {self.beacon.get_distance_from(self.player.world_pos)}", position=(int(10*self.scale['width']), int(110*self.scale['height'])), size=int(20*self.scale['overall']), color="#FFFFFF")
    
    def draw_player_hp(self):
        """Draws the player's health bar in the top-left corner."""
        bar_width = 250 * self.scale['overall']
        bar_height = 25 * self.scale['overall']
        bar_x = 20 * self.scale['width']
        bar_y = 20 * self.scale['height']

        # Calculate health ratio
        health_ratio = self.player.hp / self.player.max_hp
        fill_width = bar_width * health_ratio

        # Background (dark red)
        pygame.draw.rect(self.screen, (80, 20, 20), (bar_x, bar_y, bar_width, bar_height), border_radius=5)
        
        # Health fill (bright red)
        if fill_width > 0:
            pygame.draw.rect(self.screen, (210, 40, 40), (bar_x, bar_y, fill_width, bar_height), border_radius=5)

        # Border (white)
        pygame.draw.rect(self.screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 2, border_radius=5)

    #creation funcs
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

    def reset_game(self):
        """Resets all game-related states to their initial values for a new game."""
        # Reset player
        self.player = player.Player((self.map_size[0] // 3, self.map_size[1] // 2))
        
        # Reset beacon
        self.beacon = Beacon((self.map_size[0] // 2, self.map_size[1] // 2), size=484)
        
        # Reset inventory
        self.inventory = {
            "membrane" : 20,
            "wood" : 4,
        } if self.Master_debug_mode else {}
        self.slot = 1
        
        # Reset world items and timers
        self.items = objects.Items(50)
        self.pickup_timer.restart()
        
        # Reset enemies
        self.enemies = []
        center_x, center_y = self.map_size[0] // 2, self.map_size[1] // 2
        for _ in range(12):
            ex = random.randint(0, self.map_size[0])
            ey = random.randint(0, self.map_size[1])
            # Prevent spawning too close to the beacon
            while math.hypot(ex - center_x, ey - center_y) < 800:
                ex = random.randint(0, self.map_size[0])
                ey = random.randint(0, self.map_size[1])
            self.enemies.append(Spider((ex, ey)))
            
        # Reset game state variables
        self.time_left = 1
        self.warmth = 1
        self.has_won = False
        
        # Reset world objects (trees)
        self.trees = []
        self.create_map() # This also calls self.update_tree_data()
        
        # Reset UI elements
        self.popout = ui.TextPopout()

    #callback funcs
    def start_game(self):
        self.reset_game()
        self.scale_window(*self.screen.get_size())
        self.run()
        # After run() finishes, control returns to menu() loop
        
    def quit_game(self):
        pygame.quit()
        sys.exit()

    #Win/Lose funcs
    def death(self,w,h):
        utils.draw_text("YOU DIED", (w/2, h/2), 150 * self.scale['overall'], "darkred", centered=True, font="Rajdhani-Bold")
        
        return

    def restart_game(self):
        self.reset_game()
        self.stage = "Running"

    def go_to_menu(self):
        self.running = False

#Entry point of the game
if __name__ == "__main__":
    game = Froststep() 
    game.menu()