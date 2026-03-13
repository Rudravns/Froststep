import pygame
import utilities as utils

class Beacon:
    def __init__(self, pos, size=248):
        self.pos = pygame.Vector2(pos)
        self.size = size
        self.original_size = size
        self.scale_factor = 1.0
        self.rect = pygame.Rect(0, 0, size, size)
        self.rect.center = self.pos # pyright: ignore[reportAttributeAccessIssue]
        self.screen = pygame.display.get_surface()
        
        # --- Visuals ---
        self.images = utils.SpriteSheet()
        # Extracts the 6 images from the beacon sprite sheet
        self.images.extract_grid("Textures/Beacon.png", crop_size=(64, 64), scale=(size, size))
        
        # --- Stage & Upgrade Mechanics ---
        self.stage = 0
        self.max_stage = 5 # 0 through 5 = 6 total images
        
        self.fuel = 0
        # Fuel required to reach the NEXT stage (Stage 1 requires 3, Stage 2 requires 5, etc.)
        self.fuel_requirements = [3, 5, 8, 12, 15, 25] 
        
        # The warmth/light radius for each of the 6 stages
        self.radii = [150+size, 250+size, 350+size, 450+size, 600+size, 800+size]
        
        # Cache the light surface so we don't recalculate transparent circles every single frame
        self.light_surf = None
        self._update_light_surface()

    def _update_light_surface(self):
        """Pre-renders the glowing light circle based on the current stage's radius."""
        radius = self.radii[self.stage] * self.scale_factor
        # Create a surface twice the radius to hold the full circle, with per-pixel alpha
        self.light_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        
        # Draw a multi-layered gradient for a smooth, warm glowing effect
        pygame.draw.circle(self.light_surf, (255, 120, 0, 20), (radius, radius), radius)
        pygame.draw.circle(self.light_surf, (255, 150, 30, 40), (radius, radius), int(radius * 0.7))
        pygame.draw.circle(self.light_surf, (255, 180, 80, 60), (radius, radius), int(radius * 0.4))
        pygame.draw.circle(self.light_surf, (255, 220, 120, 100), (radius, radius), int(radius * 0.15))

    def add_fuel(self, amount):
        """Adds fuel to the beacon. Returns True if the beacon leveled up."""
        if self.stage < self.max_stage:
            self.fuel += amount
            if self.fuel >= self.fuel_requirements[self.stage]:
                self.fuel -= self.fuel_requirements[self.stage]
                self.stage += 1
                self._update_light_surface() # Re-render the light glow with the new, bigger radius
                return True # Upgraded!
        return False

    def get_radius(self):
        """Returns the current warmth/light radius based on the stage."""
        return self.images.get_image(self.stage).get_width()//2 * self.scale_factor

    def check_deposit_rad(self, player_world_rect: pygame.Rect):
        """Checks for collision with the player in world coordinates."""
        return self.rect.colliderect(player_world_rect)

    def draw(self, offset, debug=False):
        """Draws the beacon and its light radius to the screen."""
        screen_pos = self.pos + pygame.Vector2(offset)
        radius = self.radii[self.stage] * self.scale_factor
        
        # 1. Draw the glowing light (drawn first so it's under the beacon)
        if self.light_surf:
            self.screen.blit(self.light_surf, (screen_pos.x - radius, screen_pos.y - radius))
        
        # 2. Draw the Beacon Sprite
        img = self.images.get_image(self.stage)
        if img:
            draw_rect = img.get_rect(center=(screen_pos.x, screen_pos.y))
            self.screen.blit(img, draw_rect)
        else:
            # Fallback drawing just in case the image fails to load
            pygame.draw.rect(self.screen, (150, 75, 0), (screen_pos.x - 30, screen_pos.y - 30, 60, 60))

        # 3. Draw Debug Boundaries
        if debug:
            pygame.draw.rect(self.screen, (0, 255, 0), self.rect.move(offset[0], offset[1]), 2)
            pygame.draw.circle(self.screen, (255, 0, 0), (int(screen_pos.x), int(screen_pos.y)), radius, 1)

    def get_distance_from(self, pos:pygame.Vector2):
        return round(self.pos.distance_to(pos),1)


    def resize(self, scale):
        self.scale_factor = scale['overall']
        new_size = int(self.original_size * self.scale_factor)
        self.images.rezize_images((new_size, new_size))
        self._update_light_surface()


if __name__ == "__main__":
    from main import Froststep
    Froststep().run()