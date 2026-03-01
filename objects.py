from re import S

import pygame
import utilities as utils
import math
import numpy as np

class player:
    def __init__(self, start_pos):
        #screen init
        self.screen = pygame.display.get_surface()

        #player attr
        self.world_pos = pygame.Vector2(start_pos)
        self.velocity = pygame.Vector2(0, 0)
        self.player_direction = 0
        self.size = 40
        
        #player rect and image handling
        self.rect = pygame.Rect(0, 0, self.size, self.size)
        self.image = utils.SpriteSheet()
        self.player_size = (self.size + 50, self.size + 50)
        self.image.extract_single_image("Player_imgs/idle.png",self.player_size )
        self.image.extract_grid("Player_imgs/Fist.png", crop_size=(128, 128), scale=self.player_size)
        self.image_index = 0
        self.fist_animation_timer = utils.Timer(0.1)
        self.fist_animation_lenght = 5

        #collition
        self.collide_beacon = False
        self.fist_animation_timer.start()       




    def update(self, speed, dt, map_size, beacon_pos, beacon_radius, tree_data, offset):

        mouse_down = pygame.mouse.get_pressed()
        if mouse_down[0]:
            if self.image_index == 0:
                self.image_index = 1
                self.fist_animation_timer.start()
            
            if self.fist_animation_timer.has_elapsed():
                self.image_index += 1
                if self.image_index > self.fist_animation_lenght:
                    self.image_index = 1
                self.fist_animation_timer.reset()
                self.fist_animation_timer.start()
        else:
            self.image_index = 0





        # Movement Logic
        input_vel = pygame.Vector2(0, 0)
        
        keys = pygame.key.get_pressed()
        
        # Accumulate input first
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            input_vel.x -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            input_vel.x += 1
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            input_vel.y -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            input_vel.y += 1
        
        # Handle Rotation and Movement
        if input_vel.length_squared() > 0:
            input_vel = input_vel.normalize() * speed * dt
            
            # Calculate target angle from velocity vector (matches your previous cardinal direction logic)
            # Right(0), Up(90), Left(180), Down(270) -> corresponds to -degrees(atan2(y, x))
            target_angle = -math.degrees(math.atan2(input_vel.y, input_vel.x))
            self.__smooth_rotation(target_angle)
        else:
            #update rotation    
            mos_pos = pygame.mouse.get_pos()
            # Calculate player screen position using the camera offset
            screen_pos = self.world_pos + pygame.Vector2(offset)
            
            deg = math.atan2(mos_pos[1] - screen_pos.y, mos_pos[0] - screen_pos.x)
            self.__smooth_rotation(int(-math.degrees(deg)))
        
        self.velocity += input_vel

        # Friction
        if self.velocity.length() > 0.1:
            self.velocity *= 0.93
        else:
            self.velocity = pygame.Vector2(0, 0)

        # --- Tree Collision using Pre-calculated Vector Data ---
        if len(tree_data) > 0:
            tree_lefts = tree_data[:, 0]  
            tree_rights = tree_lefts + tree_data[:, 2]
            tree_tops = tree_data[:, 1]
            tree_bottoms = tree_tops + tree_data[:, 3]

            # --- X-AXIS MOVEMENT & COLLISION ---
            self.world_pos.x += self.velocity.x
            self.rect.centerx = int(self.world_pos.x)

            # Vectorized collision check for X-axis movement
            player_rect = self.rect
            x_collision_mask = (player_rect.right > tree_lefts) & \
                               (player_rect.left < tree_rights) & \
                               (player_rect.bottom > tree_tops) & \
                               (player_rect.top < tree_bottoms)
            
            if np.any(x_collision_mask):
                if self.velocity.x > 0:  # Moving right
                    self.rect.right = np.min(tree_lefts[x_collision_mask])
                elif self.velocity.x < 0:  # Moving left
                    self.rect.left = np.max(tree_rights[x_collision_mask])
                self.world_pos.x = self.rect.centerx
                self.velocity.x = 0 # Stop horizontal movement to prevent sticking

            # --- Y-AXIS MOVEMENT & COLLISION ---
            self.world_pos.y += self.velocity.y
            self.rect.centery = int(self.world_pos.y)

            # Vectorized collision check for Y-axis movement
            player_rect = self.rect # Player rect might have moved on X axis
            y_collision_mask = (player_rect.right > tree_lefts) & \
                               (player_rect.left < tree_rights) & \
                               (player_rect.bottom > tree_tops) & \
                               (player_rect.top < tree_bottoms)

            if np.any(y_collision_mask):
                if self.velocity.y > 0:  # Moving down
                    self.rect.bottom = np.min(tree_tops[y_collision_mask])
                elif self.velocity.y < 0:  # Moving up
                    self.rect.top = np.max(tree_bottoms[y_collision_mask])
                self.world_pos.y = self.rect.centery
                self.velocity.y = 0 # Stop vertical movement to prevent sticking
        else:
            # No trees, just move the player
            self.world_pos.x += self.velocity.x
            self.world_pos.y += self.velocity.y

        self.rect.center = (int(self.world_pos.x), int(self.world_pos.y))
        
        if self.circle_to_rect_collition(beacon_pos, beacon_radius):
            direction = self.world_pos - pygame.Vector2(beacon_pos)
            if direction.length() == 0:
                direction = pygame.Vector2(1, 0)
            else:
                direction = direction.normalize()
            
            self.world_pos = pygame.Vector2(beacon_pos) + direction * (beacon_radius + self.size * 0.8)
            self.rect.center = (int(self.world_pos.x), int(self.world_pos.y))


        # Clamp to map boundaries
        self.world_pos.x = max(self.size/2, min(self.world_pos.x, map_size[0] - self.size/2))
        self.world_pos.y = max(self.size/2, min(self.world_pos.y, map_size[1] - self.size/2))

    def __smooth_rotation(self, rot, lerp_factor=0.15):
        # 1. Normalize angles to 0-360
        rot = rot % 360
        self.player_direction = self.player_direction % 360

        # 2. Find the shortest distance between current and target angle
        diff = rot - self.player_direction
        if diff > 180:
            diff -= 360
        elif diff < -180:
            diff += 360

        # 3. Apply Lerp: Move a percentage of the distance
        # If the distance is very small, just snap to avoid microscopic jitter
        if abs(diff) < 0.1:
            self.player_direction = rot
        else:
            self.player_direction += diff * lerp_factor

        # 4. Update image
        self.image.rotate_images(int(self.player_direction - 90))
        return self.player_direction

    def draw(self, debug, offset=(0,0), scale:dict = {"width": 1.0, "height": 1.0, "overall": 1.0}):
        
        img = self.image.get_image(self.image_index)

        #scale
        new_w = int(img.get_width() * scale['overall'])
        new_h = int(img.get_height() * scale['overall'])
        img = pygame.transform.scale(img, (new_w, new_h))

        # Calculate screen position based on world pos and camera offset
        screen_x = self.world_pos.x + offset[0]
        screen_y = self.world_pos.y + offset[1]
        
        rect = img.get_rect(center=(screen_x, screen_y))
        self.screen.blit(img, rect)
        if debug:
            hitbox = pygame.Rect(0, 0, self.size * scale['overall'], self.size * scale['overall'])
            hitbox.center = (screen_x, screen_y)
            pygame.draw.rect(self.screen, (255, 0, 0), hitbox, 2)
    
    def circle_to_rect_collition(self, circle_pos, radius):

        closest_x = max(self.rect.left, min(circle_pos[0], self.rect.right))
        closest_y = max(self.rect.top, min(circle_pos[1], self.rect.bottom))
        
        # Calculate distance using pygame's Vector2 for simplicity
        closest_point = pygame.Vector2(closest_x, closest_y)
        circle_center = pygame.Vector2(circle_pos)
        
        self.collide_beacon = circle_center.distance_to(closest_point) < radius

        return self.collide_beacon

            


class Tree:
    def __init__(self, pos, tree_type, size):
        #init 
        self.images = utils.SpriteSheet()
        self.images.extract_grid("Textures/Trees.png",(64,64), scale= (size,size))
        self.image_index = tree_type
        self.size = size
        self.pos = pygame.Vector2(pos)
        self.rect = pygame.Rect(self.pos.x, self.pos.y, self.size, self.size)
        self.screen = pygame.display.get_surface()


    def draw(self, offset, debug):
        screen_pos = self.pos + pygame.Vector2(offset)
        self.screen.blit(self.images.get_image(self.image_index), screen_pos)
        if debug:
            pygame.draw.rect(self.screen, (255, 0, 0), self.get_rect(offset), 2)
    
    def get_rect(self, offset):
        screen_pos = self.pos + pygame.Vector2(offset)
        return self.images.get_image(self.image_index).get_rect(topleft=screen_pos)