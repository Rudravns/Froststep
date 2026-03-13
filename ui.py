import pygame
import os
import utilities

class WarmthBar:
    def __init__(self, position, size=(40, 200), image_path=None):
        self.original_pos = pygame.Vector2(position)
        self.original_size = size
        self.position = list(position)
        self.size = size
        # Hex #89b063 is exactly (137, 176, 99)
        self.target_color = (137, 176, 99) 
        self.image_path = image_path
        
        # 1. Load the thermometer image
        self._load_image()
        
        # 2. Create the internal fill mask AND punch a hole in the image
        self.fill_mask = self._create_fill_mask()
        
        # 3. Create the full-sized gradient background
        self.gradient = self._create_gradient()

    def _load_image(self):
        if self.image_path and os.path.exists(self.image_path):
            original_image = pygame.image.load(self.image_path).convert_alpha()
            self.image = pygame.transform.scale(original_image, self.size)
        else:
            # Fallback: Create a pill shape with a gray border and GREEN inside
            self.image = pygame.Surface(self.size, pygame.SRCALPHA)
            # Draw outer border (gray)
            pygame.draw.rect(self.image, (150, 150, 150, 255), (0, 0, *self.size), border_radius=20)
            # Draw inner fill (target green) so the mask detects it!
            inner_rect = pygame.Rect(4, 4, self.size[0]-8, self.size[1]-8)
            pygame.draw.rect(self.image, self.target_color, inner_rect, border_radius=16)

    def _create_fill_mask(self):
        """Creates the mask and erases the green from the original image."""
        mask_surf = pygame.Surface(self.size, pygame.SRCALPHA)
        
        # Use PixelArray for faster processing
        px_array = pygame.PixelArray(self.image)
        
        # Increased tolerance to 20 to easily catch slight image compression artifacts
        tolerance = 20 
        
        for x in range(self.size[0]):
            for y in range(self.size[1]):
                # Get the pixel color
                pixel_val = px_array[x, y]  # pyright: ignore[reportIndexIssue]
                r, g, b, a = self.image.unmap_rgb(pixel_val)
                
                # Check if the pixel matches the target green
                if (abs(r - self.target_color[0]) <= tolerance and 
                    abs(g - self.target_color[1]) <= tolerance and 
                    abs(b - self.target_color[2]) <= tolerance):
                    
                    # 1. Register this spot on the mask so the gradient shows here
                    mask_surf.set_at((x, y), (255, 255, 255, 255))
                    
                    # 2. ERASING STEP: Punch a hole in the image! 
                    px_array[x, y] = self.image.map_rgb((0, 0, 0, 0)) # pyright: ignore[reportIndexIssue]
                else:
                    # Not green, keep it blocked off
                    mask_surf.set_at((x, y), (0, 0, 0, 0))
        
        px_array.close()
        return mask_surf

    def _create_gradient(self):
        width, height = self.size
        # Create a tiny 1x2 surface for the colors
        color_surf = pygame.Surface((1, 2), pygame.SRCALPHA)
        color_surf.set_at((0, 0), (255, 0, 0, 255))   # Top: Warm Red
        color_surf.set_at((0, 1), (0, 0, 255, 255))   # Bottom: Cold Blue
        
        # Scale it up to create a smooth vertical transition
        return pygame.transform.smoothscale(color_surf, (width, height))

    def draw(self, screen, current_warmth, max_warmth=100):
        x, y = self.position
        width, height = self.size
        
        # Calculate visibility ratio (0.0 to 1.0)
        ratio = max(0.0, min(1.0, current_warmth / max_warmth))
        visible_height = int(height * ratio)
        
        # Calculate Y offset so it shrinks from the top down
        crop_y = height - visible_height
        
        # 1. Create a workspace surface
        temp_surface = pygame.Surface(self.size, pygame.SRCALPHA)
        
        # 2. Draw the visible part of the gradient
        if visible_height > 0:
            crop_rect = pygame.Rect(0, crop_y, width, visible_height)
            temp_surface.blit(self.gradient, (0, crop_y), crop_rect)
        
        # 3. MASKING STEP: 
        temp_surface.blit(self.fill_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        
        # 4. Draw to the screen
        screen.blit(temp_surface, (x, y))
        screen.blit(self.image, (x, y))

    def resize(self, scale):
        # Update current size and position based on original values and scale
        self.size = (int(self.original_size[0] * scale["overall"]), int(self.original_size[1] * scale["overall"]))
        self.position = (int(self.original_pos.x * scale["width"]), int(self.original_pos.y * scale["height"]))
        
        # Reload/Regenerate everything to ensure crisp textures and correct masks
        self._load_image()
        self.fill_mask = self._create_fill_mask()
        self.gradient = self._create_gradient()


class TextPopout:
    def __init__(self):
        # Changed from {} to [] to act as a queue
        self.top_queue = [] 
        self.bottom_queue = [] 
        self.screen = pygame.display.get_surface()

    def add_top_pop_out(self, text:str, pos:pygame.Vector2, time:float, fall_by:float = 30.0, center:bool = False, color = "White", size = 50):
        # We store all info in a dict and append it to the end of the line
        # Note: We do NOT call timer.start() here
        self.top_queue.append({
            "text": text,
            "timer": utilities.Timer(time),
            "original_pos": pygame.Vector2(pos),
            "pos": pygame.Vector2(pos), # This will be the scaled position
            "original_fall_by": fall_by,
            "fall_by": fall_by, # This will be the scaled value
            "center": center,
            "started": False,
            "color": color,
            "original_size": size,
            "size": size # This will be the scaled size
        })
    
    def add_bottom_pop_out(self, text:str, pos:pygame.Vector2, time:float, rise_by:float = 30.0, center:bool = False, color = "White", size = 50):
        self.bottom_queue.append({
            "text": text,
            "timer": utilities.Timer(time),
            "original_pos": pygame.Vector2(pos),
            "pos": pygame.Vector2(pos), # Scaled position
            "original_rise_by": rise_by,
            "rise_by": rise_by, # Scaled value
            "center": center,
            "started": False,
            "color": color,
            "original_size": size,
            "size": size, # Scaled size
        })

    def draw_bottom_pop_out(self, dt:float):
        if not self.bottom_queue:
            return

        # Only process the first item in the queue
        current = self.bottom_queue[0]
        timer = current["timer"]

        # Start the timer ONLY when this item reaches the front of the queue
        if not current["started"]:
            timer.start()
            current["started"] = True

        if timer.has_elapsed():
            self.bottom_queue.pop(0) # Remove and move to next
        else:
            progress = timer.get_time_left() / timer.duration
            pos = current["pos"]
            current_pos = pygame.Vector2(pos.x, pos.y - (current["rise_by"] * progress))
            utilities.draw_text(current["text"], (current_pos.x,current_pos.y), size=current["size"], color=current["color"], centered=current["center"])

    def draw_top_pop_out(self, dt:float):
        if not self.top_queue:
            return

        current = self.top_queue[0]
        timer = current["timer"]

        if not current["started"]:
            timer.start()
            current["started"] = True

        if timer.has_elapsed():
            self.top_queue.pop(0)
        else:
            progress = timer.get_time_left() / timer.duration
            pos = current["pos"]
            current_pos = pygame.Vector2(pos.x, pos.y + (current["fall_by"] * progress))
            utilities.draw_text(current["text"], (current_pos.x, current_pos.y), size=current["size"], color=current["color"], centered=current["center"])

    def draw_all(self, dt:float):
        self.draw_top_pop_out(dt)
        self.draw_bottom_pop_out(dt)

    def resize(self, scale):
        # Update positions for everything waiting in the top queue
        for item in self.top_queue:
            item["pos"].x = item["original_pos"].x * scale["width"]
            item["pos"].y = item["original_pos"].y * scale["height"]
            item["fall_by"] = item["original_fall_by"] * scale["overall"]
            item["size"] = item["original_size"] * scale["overall"]

        # Update positions for everything waiting in the bottom queue
        for item in self.bottom_queue:
            item["pos"].x = item["original_pos"].x * scale["width"]
            item["pos"].y = item["original_pos"].y * scale["height"]
            item["rise_by"] = item["original_rise_by"] * scale["overall"]
            item["size"] = item["original_size"] * scale["overall"]