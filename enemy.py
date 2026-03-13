"""File for the enemy AI"""

import pygame
import math
import random
import utilities as utils

class Spider:
    def __init__(self, start_pos, size=50):
        self.screen = pygame.display.get_surface()
        self.world_pos = pygame.Vector2(start_pos)
        self.velocity = pygame.Vector2(0, 0)
        self.direction = 0
        self.size = size
        self.base_speed = 70 # Pixels per second
        
        # Stats
        self.hp = 100
        self.max_hp = 100
        self.is_dead = False
        
        # Hitbox (World Space)
        self.rect = pygame.Rect(0, 0, self.size, self.size)
        
        # Visuals
        self.images = utils.SpriteSheet()
        self.enemy_size = (self.size + 50, self.size + 50)
        self.images.extract_grid("Enemy_imgs/Spider/moving(1).png", crop_size=(60,60), scale=self.enemy_size)
        self.image_index = 0
        self.animation_timer = utils.Timer(.0625)
        self.animation_timer.start()

        # HP Bar UI Logic
        self.hp_visible_timer = utils.Timer(3.0) # Show HP for 3 seconds after hit
        self.hp_alpha = 0 # For fading effect

        # Behavior States
        self.state = "WANDER" # WANDER, CHASE, ATTACK
        self.detection_radius = 300
        self.attack_radius = 50
        self.attack_timer = utils.Timer(1.5) # Attacks every 1.5s
        self.damage = 10
        
        self.wander_target = self.__get_new_wander_pos()
        self.wander_timer = utils.Timer(random.uniform(2, 5))
        self.wander_timer.start()

    def __get_new_wander_pos(self):
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(100, 300)
        return self.world_pos + pygame.Vector2(math.cos(angle) * dist, math.sin(angle) * dist)

    def hit(self, dmg):
        """Called when the player attacks the spider."""
        if self.is_dead: return
        
        self.hp -= dmg
        self.hp_visible_timer.reset()
        self.hp_visible_timer.start()
        
        if self.hp <= 0:
            self.hp = 0
            self.is_dead = True
            return self.die()
        return None

    def die(self):
        """Returns the items dropped upon death."""
        # Drop 1-3 membranes (Weighted: 1 is common, 3 is rare)
        # Weights: 1 (70%), 2 (20%), 3 (10%)
        drop_count = random.choices([1, 2, 3], weights=[70, 20, 10], k=1)[0]
        return {"membrane": drop_count}

    def update(self, dt, player_pos, map_size, tree_rects, other_enemies=[], player_warmth=1.0):
        if self.is_dead: return 0

        # Spiders are faster in the warmth, slower in the cold.
        # Clamp warmth so they don't stop or go backwards.
        speed_modifier = max(0.5, player_warmth) 
        current_speed = self.base_speed * speed_modifier

        dist_to_player = self.world_pos.distance_to(player_pos)
        move_vec = pygame.Vector2(0, 0)
        damage_dealt = 0

        # 1. Behavior State Machine
        if dist_to_player < self.attack_radius:
            self.state = "ATTACK"
        elif dist_to_player < self.detection_radius:
            self.state = "CHASE"
        else:
            self.state = "WANDER"
        
        # Reset attack timer if not in attack range
        if self.state != "ATTACK" and self.attack_timer.start_time:
            self.attack_timer.reset()

        # 2. Movement Logic based on State
        if self.state == "ATTACK":
            # Stop moving and face the player to attack
            move_vec = pygame.Vector2(0, 0)

            # Explicitly face the player when attacking
            face_vec = player_pos - self.world_pos
            if face_vec.length_squared() > 0:
                self.direction = math.degrees(math.atan2(-face_vec.y, face_vec.x))

            if not self.attack_timer.start_time: self.attack_timer.start()
            if self.attack_timer.has_elapsed():
                damage_dealt = self.damage
                self.attack_timer.restart()
        elif self.state == "CHASE":
            move_vec = (player_pos - self.world_pos).normalize()
        elif self.state == "WANDER":
            if self.wander_timer.has_elapsed():
                self.wander_target = self.__get_new_wander_pos()
                self.wander_timer.reset()
                self.wander_timer.start()
            
            if self.world_pos.distance_to(self.wander_target) > 10:
                move_vec = (self.wander_target - self.world_pos).normalize()

        # 3. ANTI-STACKING (Soft Collision with other spiders)
        # This makes them feel more like a swarm and less like one glitched entity
        if self.state != "ATTACK":
            for other in other_enemies:
                if other is self or other.is_dead: continue
                dist = self.world_pos.distance_to(other.world_pos)
                if dist < self.size: # If overlapping
                    push_away = (self.world_pos - other.world_pos)
                    if push_away.length() == 0: # Exactly on top? push random direction
                        push_away = pygame.Vector2(random.uniform(-1,1), random.uniform(-1,1))
                    move_vec += push_away.normalize() * 0.5 # Add a separation force

        # 4. Apply Movement
        if move_vec.length() > 0:
            move_vec = move_vec.normalize()
            self.velocity = move_vec * current_speed

            # --- Tree Collision (like player) ---
            # Move X
            self.world_pos.x += self.velocity.x * dt
            self.rect.centerx = int(self.world_pos.x)
            if tree_rects:
                collisions = self.rect.collidelistall(tree_rects)
                for idx in collisions:
                    tree_rect = tree_rects[idx]
                    if self.velocity.x > 0: self.rect.right = tree_rect.left
                    elif self.velocity.x < 0: self.rect.left = tree_rect.right
                    self.world_pos.x = self.rect.centerx
            
            # Move Y
            self.world_pos.y += self.velocity.y * dt
            self.rect.centery = int(self.world_pos.y)
            if tree_rects:
                collisions = self.rect.collidelistall(tree_rects)
                for idx in collisions:
                    tree_rect = tree_rects[idx]
                    if self.velocity.y > 0: self.rect.bottom = tree_rect.top
                    elif self.velocity.y < 0: self.rect.top = tree_rect.bottom
                    self.world_pos.y = self.rect.centery

            # Update rotation
            self.direction = math.degrees(math.atan2(-self.velocity.y, self.velocity.x))
            
            # Animation
            if self.animation_timer.has_elapsed():
                self.image_index = (self.image_index + 1) % self.images.images.__len__()
                self.animation_timer.reset()
                self.animation_timer.start()

        # Update Rect
        self.rect.center = self.world_pos # pyright: ignore[reportAttributeAccessIssue]

        # Clamp to Map boundaries
        self.world_pos.x = max(self.size/2, min(self.world_pos.x, map_size[0] - self.size/2))
        self.world_pos.y = max(self.size/2, min(self.world_pos.y, map_size[1] - self.size/2))
        
        return damage_dealt

    def draw(self, offset, debug):
        if self.is_dead: return
        
        screen_pos = self.world_pos + pygame.Vector2(offset)
        
        # 1. Draw Spider
        img = self.images.get_image(self.image_index)
        if img:
            rotated_img = pygame.transform.rotate(img, self.direction )
            draw_rect = rotated_img.get_rect(center=(screen_pos.x, screen_pos.y))
            self.screen.blit(rotated_img, draw_rect)

        # 2. Draw Health Bar with fading logic
        if not self.hp_visible_timer.has_elapsed():
            # Fade calculation: fade in quickly, stay, fade out at the very end
            time_left = self.hp_visible_timer.get_time_left()
            if time_left < 0.5: # Fade out in last 0.5s
                alpha = int((time_left / 0.5) * 255)
            else:
                alpha = 255
                
            self._draw_hp_bar(screen_pos, alpha)

        if debug:
            # Draw detection and attack ranges
            pygame.draw.circle(self.screen, (255, 255, 0), (int(screen_pos.x), int(screen_pos.y)), self.detection_radius, 1)
            pygame.draw.circle(self.screen, (255, 0, 0), (int(screen_pos.x), int(screen_pos.y)), self.attack_radius, 1)
            debug_rect = self.rect.copy()
            debug_rect.center = screen_pos # pyright: ignore[reportAttributeAccessIssue]
            pygame.draw.rect(self.screen, (0, 255, 0), debug_rect, 1)

    def _draw_hp_bar(self, screen_pos, alpha):
        bar_width = 40
        bar_height = 6
        bar_x = screen_pos.x - bar_width // 2
        bar_y = screen_pos.y - self.size // 2 - 15
        
        # Calculate health width
        health_fill = (self.hp / self.max_hp) * bar_width
        
        # We use a temporary surface for alpha fading
        hp_surf = pygame.Surface((bar_width, bar_height), pygame.SRCALPHA)
        
        # Background (Dark Red/Black)
        pygame.draw.rect(hp_surf, (30, 0, 0, alpha), (0, 0, bar_width, bar_height))
        # Foreground (Bright Red)
        pygame.draw.rect(hp_surf, (200, 0, 0, alpha), (0, 0, health_fill, bar_height))
        # Border
        pygame.draw.rect(hp_surf, (0, 0, 0, alpha), (0, 0, bar_width, bar_height), 1)
        
        self.screen.blit(hp_surf, (bar_x, bar_y))

    def resize(self, new_size):
        self.images.rezize_images(new_size)
        self.rect.size = (int(new_size[0]), int(new_size[1]))
        self.rect.center = (int(self.world_pos.x), int(self.world_pos.y))
        self.size = new_size[0]

    def __str__(self):
        return "Spider"