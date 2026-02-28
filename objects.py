import pygame
import utilities as utils
import math

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
        self.image.extract_single_image("Player_imgs/place_holder.png", (self.size, self.size))
        
        #collition
        self.collide_beacon = False



    def update(self, speed, sensitivity, dt, map_size, beacon_pos, beacon_radius):

        #update rotation
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.player_direction = (self.player_direction + (sensitivity*dt)) % 360
            self.image.rotate_images(self.player_direction, 0)

        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.player_direction = (self.player_direction - (sensitivity*dt)) % 360
            self.image.rotate_images(self.player_direction, 0)
        
        # Movement Logic
        rad = math.radians(self.player_direction)
        input_vel = pygame.Vector2(0, 0)
        
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            input_vel.x += math.sin(rad) * speed * dt
            input_vel.y += math.cos(rad) * speed * dt

        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            input_vel.x -= math.sin(rad) * speed * dt
            input_vel.y -= math.cos(rad) * speed * dt

        self.velocity += input_vel

        # Friction
        if self.velocity.length() > 0.1:
            self.velocity *= 0.93
        else:
            self.velocity = pygame.Vector2(0, 0)

        self.world_pos.x -= self.velocity.x
        self.world_pos.y -= self.velocity.y

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

    def draw(self, debug, offset=(0,0), scale:dict = {"width": 1.0, "height": 1.0, "overall": 1.0}):
        
        img = self.image.get_image(0)

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