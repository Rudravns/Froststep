import pygame
import utilities as utils
import math

class Player:
    def __init__(self, start_pos):
        # Screen init
        self.screen = pygame.display.get_surface()

        # Player attributes
        self.world_pos = pygame.Vector2(start_pos)
        self.velocity = pygame.Vector2(0, 0)
        self.player_direction = 0
        self.size = 40
        
        # Player rect and image handling
        self.rect = pygame.Rect(0, 0, self.size, self.size)
        self.fist_hitbox = pygame.Rect(self.size, 0, self.size, self.size)
        self.image = utils.SpriteSheet()
        self.player_size = (self.size + 50, self.size + 50)
        self.image.extract_single_image("Player_imgs/idle.png", self.player_size)
        self.image.extract_grid("Player_imgs/Fist.png", crop_size=(128, 128), scale=self.player_size)
        self.image_index = 0
        self.fist_animation_timer = utils.Timer(0.1)
        self.fist_animation_lenght = 5
        
        # Scaling Cache to prevent resizing images 120 times a second
        self.cached_image = None
        self.last_drawn_scale = -1
        self.last_drawn_index = -1
        self.last_drawn_rotation = -1

        # Collision
        self.collide_beacon = False
        self.fist_animation_timer.start()       

    def update(self, speed, dt, map_size, beacon_pos, beacon_radius, tree_rects, offset):
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
            target_angle = -math.degrees(math.atan2(input_vel.y, input_vel.x))
            self.__smooth_rotation(target_angle)
        else:
            mos_pos = pygame.mouse.get_pos()
            screen_pos = self.world_pos + pygame.Vector2(offset)
            deg = math.atan2(mos_pos[1] - screen_pos.y, mos_pos[0] - screen_pos.x)
            self.__smooth_rotation(int(-math.degrees(deg)))
        
        self.velocity += input_vel

        # Friction
        if self.velocity.length() > 0.1:
            self.velocity *= 0.93
        else:
            self.velocity = pygame.Vector2(0, 0)

        # Collision Handling
        self.world_pos.x += self.velocity.x
        self.rect.centerx = int(self.world_pos.x)
        if tree_rects:
            collisions = self.rect.collidelistall(tree_rects)
            for idx in collisions:
                tree_rect = tree_rects[idx]
                if self.velocity.x > 0: self.rect.right = tree_rect.left
                elif self.velocity.x < 0: self.rect.left = tree_rect.right
                self.world_pos.x = self.rect.centerx
                self.velocity.x = 0

        self.world_pos.y += self.velocity.y
        self.rect.centery = int(self.world_pos.y)
        if tree_rects:
            collisions = self.rect.collidelistall(tree_rects)
            for idx in collisions:
                tree_rect = tree_rects[idx]
                if self.velocity.y > 0: self.rect.bottom = tree_rect.top
                elif self.velocity.y < 0: self.rect.top = tree_rect.bottom
                self.world_pos.y = self.rect.centery
                self.velocity.y = 0

        self.rect.center = (int(self.world_pos.x), int(self.world_pos.y))
        
        # Beacon collision
        if self.circle_to_rect_collition(beacon_pos, beacon_radius):
            direction = self.world_pos - pygame.Vector2(beacon_pos)
            if direction.length() == 0: direction = pygame.Vector2(1, 0)
            else: direction = direction.normalize()
            self.world_pos = pygame.Vector2(beacon_pos) + direction * (beacon_radius + self.size * 0.8)
            self.rect.center = (int(self.world_pos.x), int(self.world_pos.y))

        # Clamp boundaries
        self.world_pos.x = max(self.size/2, min(self.world_pos.x, map_size[0] - self.size/2))
        self.world_pos.y = max(self.size/2, min(self.world_pos.y, map_size[1] - self.size/2))

    def __smooth_rotation(self, rot, lerp_factor=0.15):
        rot = rot % 360
        self.player_direction = self.player_direction % 360
        diff = rot - self.player_direction
        if diff > 180: diff -= 360
        elif diff < -180: diff += 360

        if abs(diff) < 0.1: self.player_direction = rot
        else: self.player_direction += diff * lerp_factor

        self.image.rotate_images(int(self.player_direction - 90))
        return self.player_direction

    def draw(self, debug, offset=(0,0), scale:dict = {"width": 1.0, "height": 1.0, "overall": 1.0}):
        img = self.image.get_image(self.image_index)

        if (self.last_drawn_scale != scale['overall'] or 
            self.last_drawn_index != self.image_index or 
            self.last_drawn_rotation != self.player_direction):
            
            new_w = int(img.get_width() * scale['overall'])
            new_h = int(img.get_height() * scale['overall'])
            self.cached_image = pygame.transform.scale(img, (new_w, new_h))
            self.last_drawn_scale = scale['overall']
            self.last_drawn_index = self.image_index
            self.last_drawn_rotation = self.player_direction

        screen_x = self.world_pos.x + offset[0]
        screen_y = self.world_pos.y + offset[1]
        
        rect = self.cached_image.get_rect(center=(screen_x, screen_y)) # pyright: ignore[reportOptionalMemberAccess]
        self.screen.blit(self.cached_image, rect) # pyright: ignore[reportArgumentType]
        
        # Fist Hitbox Logic (Always active)
        self.fist_hitbox.width = 20 * scale['overall']
        self.fist_hitbox.height = 20 * scale['overall']
        angle = math.radians(self.player_direction)
        radius = 40 * scale['overall']
        offset_x = math.cos(angle) * radius
        offset_y = math.sin(angle) * radius

        # Convert back to screen space for the collision check logic in main loop
        self.fist_hitbox.center = (screen_x + offset_x, screen_y - offset_y)

        if debug:
            hitbox = pygame.Rect(0, 0, self.size * scale['overall'], self.size * scale['overall'])
            hitbox.center = (screen_x, screen_y)
            pygame.draw.rect(self.screen, (255, 0, 0), hitbox, 2)
            pygame.draw.rect(self.screen, "green", self.fist_hitbox, 2)
    
    def circle_to_rect_collition(self, circle_pos, radius):
        closest_x = max(self.rect.left, min(circle_pos[0], self.rect.right))
        closest_y = max(self.rect.top, min(circle_pos[1], self.rect.bottom))
        closest_point = pygame.Vector2(closest_x, closest_y)
        circle_center = pygame.Vector2(circle_pos)
        self.collide_beacon = circle_center.distance_to(closest_point) < radius
        return self.collide_beacon
