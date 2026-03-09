"""File for the enemy AI"""

import pygame
import math
import random
import utilities as utils

class Enemy:
    def __init__(self, start_pos, size=40):
        self.screen = pygame.display.get_surface()
        self.world_pos = pygame.Vector2(start_pos)
        self.velocity = pygame.Vector2(0, 0)
        self.direction = 0
        self.size = size
        self.speed = 70 # Pixels per second
        
        # Hitbox (World Space)
        self.rect = pygame.Rect(0, 0, self.size, self.size)
        
        # Visuals
        self.images = utils.SpriteSheet()
        self.enemy_size = (self.size + 40, self.size + 40)
        # Assuming you have an enemy sheet or reuse player logic
        self.images.extract_single_image("Enemy_imgs/Spider/idle.png", self.enemy_size)
        self.image_index = 0
        
        # Behavior States
        self.state = "WANDER" # WANDER, CHASE, ATTACK
        self.detection_radius = 300
        self.attack_radius = 50
        
        # Wander logic
        self.wander_target = self.__get_new_wander_pos()
        self.wander_timer = utils.Timer(random.uniform(2, 5))
        self.wander_timer.start()

    def __get_new_wander_pos(self):
        # Pick a random spot near the current position
        angle = random.uniform(0, math.pi * 2)
        dist = random.uniform(100, 200)
        return self.world_pos + pygame.Vector2(math.cos(angle) * dist, math.sin(angle) * dist)

    def update(self, dt, player_world_pos, time_speed, map_size, tree_rects):
        dist_to_player = self.world_pos.distance_to(player_world_pos)
        
        # 1. State Switching Logic
        if dist_to_player < self.attack_radius:
            self.state = "ATTACK"
        elif dist_to_player < self.detection_radius:
            self.state = "CHASE"
        else:
            self.state = "WANDER"

        # 2. Movement Logic based on State
        move_vec = pygame.Vector2(0, 0)

        if self.state == "CHASE":
            if dist_to_player > 0:
                move_vec = (player_world_pos - self.world_pos).normalize()
        
        elif self.state == "WANDER":
            # Only update the timer based on the world's time_speed
            # If time_speed is 0 (player not moving/warmth low), the wander target doesn't change
            if self.world_pos.distance_to(self.wander_target) < 10 or self.wander_timer.has_elapsed():
                self.wander_target = self.__get_new_wander_pos()
                self.wander_timer.reset()
                self.wander_timer.start()
            
            if self.world_pos.distance_to(self.wander_target) > 0:
                move_vec = (self.wander_target - self.world_pos).normalize()
        
        elif self.state == "ATTACK":
            # Just face the player, don't move forward
            move_vec = pygame.Vector2(0,0)
            target_deg = -math.degrees(math.atan2(player_world_pos.y - self.world_pos.y, player_world_pos.x - self.world_pos.x)) + 90
            self.direction = target_deg % 360

        # 3. Apply Movement & Rotation based on time_speed
        if move_vec.length_squared() > 0:
            # The speed is multiplied by your custom time_speed variable
            self.velocity = move_vec * self.speed * time_speed
            
            # Update visual rotation
            if self.state != "ATTACK":
                target_deg = -math.degrees(math.atan2(move_vec.y, move_vec.x)) + 90
                self.direction = target_deg % 360
        else:
            self.velocity = pygame.Vector2(0, 0)
        
        # 4. Simple Tree/Map Collision (X then Y like your Player)
        # Movement X
        self.world_pos.x += self.velocity.x
        self.rect.centerx = int(self.world_pos.x)
        if tree_rects:
            for tree in tree_rects:
                if self.rect.colliderect(tree):
                    if self.velocity.x > 0: self.rect.right = tree.left
                    elif self.velocity.x < 0: self.rect.left = tree.right
                    self.world_pos.x = self.rect.centerx
                    if self.state == "WANDER":
                        self.wander_target = self.__get_new_wander_pos()
                        self.wander_timer.reset()
                        self.wander_timer.start()   

        # Movement Y
        self.world_pos.y += self.velocity.y
        self.rect.centery = int(self.world_pos.y)
        if tree_rects:
            for tree in tree_rects:
                if self.rect.colliderect(tree):
                    if self.velocity.y > 0: self.rect.bottom = tree.top
                    elif self.velocity.y < 0: self.rect.top = tree.bottom
                    self.world_pos.y = self.rect.centery

                    if self.state == "WANDER":
                        self.wander_target = self.__get_new_wander_pos()
                        self.wander_timer.reset()
                        self.wander_timer.start()   

        # Clamp to Map boundaries
        self.world_pos.x = max(self.size/2, min(self.world_pos.x, map_size[0] - self.size/2))
        self.world_pos.y = max(self.size/2, min(self.world_pos.y, map_size[1] - self.size/2))

    def draw(self, offset, debug):
        screen_pos = self.world_pos + pygame.Vector2(offset)
        
        # Get and rotate image (similar to player)
        img = self.images.get_image(self.image_index)
        if img:
            rotated_img = pygame.transform.rotate(img, self.direction - 90)
            draw_rect = rotated_img.get_rect(center=(screen_pos.x, screen_pos.y))
            self.screen.blit(rotated_img, draw_rect)

        if debug:
            # Draw detection and attack ranges
            pygame.draw.circle(self.screen, (255, 255, 0), (int(screen_pos.x), int(screen_pos.y)), self.detection_radius, 1)
            pygame.draw.circle(self.screen, (255, 0, 0), (int(screen_pos.x), int(screen_pos.y)), self.attack_radius, 1)
            # Draw hitbox
            debug_rect = self.rect.copy()
            debug_rect.center = (int(screen_pos.x), int(screen_pos.y))
            pygame.draw.rect(self.screen, (255, 0, 0), debug_rect, 2)