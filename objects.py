import pygame
import numpy as np
import random
import utilities as utils

class Tree:
    def __init__(self, pos, tree_type, size):
        self.images = utils.SpriteSheet()
        self.images.extract_grid("Textures/Simple_Tree.png", crop_size=(64,64), scale=(size,size))
        self.images.remove(-1)
        self.images.extract_grid("Textures/Weird_Tree.png", crop_size=(64,64), scale=(size,size))
        self.images.remove(-1)
        
        self.ani_lenth = [5, 13]
        self.tree_type = random.randint(1,2)
        self.image_index = 0 if self.tree_type == 1 else self.ani_lenth[0]+2
        self.size = size
        self.pos = pygame.Vector2(pos) # This is the world-space CENTER of the tree
        self.rect = pygame.Rect(0, 0, self.size, self.size)
        self.rect.center = self.pos # pyright: ignore[reportAttributeAccessIssue]
        self.screen = pygame.display.get_surface()
        self.hit_timer = utils.Timer(0.5)
        self.regen_timer = utils.Timer(3)
        self.regen_timer.start()
        self.hit_timer.reset()
        self.hit_timer.start()
        self.__update_rect()

    def __update_rect(self):
        """Updates the hitbox to match the non-transparent pixels of the current frame."""
        img = self.images.get_image(self.image_index)
        if img:
            bound_rect = img.get_bounding_rect()
            img_topleft_x = self.pos.x - img.get_width() / 2
            img_topleft_y = self.pos.y - img.get_height() / 2
            self.rect.width = bound_rect.width
            self.rect.height = bound_rect.height
            self.rect.left = img_topleft_x + bound_rect.left # pyright: ignore[reportAttributeAccessIssue]
            self.rect.top = img_topleft_y + bound_rect.top # pyright: ignore[reportAttributeAccessIssue]

    def draw(self, offset, debug):
        screen_pos = self.pos + pygame.Vector2(offset)
        img = self.images.get_image(self.image_index)
        draw_rect = img.get_rect(center=screen_pos)
        self.screen.blit(img, draw_rect)
        if debug:
            debug_rect = self.rect.copy()
            debug_rect.x += offset[0]
            debug_rect.y += offset[1]
            pygame.draw.rect(self.screen, (255, 0, 0), debug_rect, 2)
    
    def get_rect(self, offset):
        screen_rect = self.rect.copy()
        screen_rect.x += offset[0]
        screen_rect.y += offset[1]
        return screen_rect
    
    def update(self):
        if self.regen_timer.has_elapsed():
            if (self.image_index in range(1,5) or self.image_index in range(8,13)):
                self.image_index -= 1
                self.__update_rect()
                self.__reset_timer()
    
    def hit(self):
        if self.hit_timer.has_elapsed():
            if self.image_index in self.ani_lenth: return True
            self.image_index += 1
            self.__update_rect()
            self.hit_timer.reset()
            self.hit_timer.start()
            self.__reset_timer()
        return False

    def resize(self, scale:dict):
        new_size = int(self.size * scale['overall'])
        self.images.rezize_images((new_size, new_size))
        self.__update_rect()

    def __reset_timer(self):
        self.regen_timer.reset()
        self.regen_timer.start()


class Items:
    def __init__(self, size) -> None:
        self.item_texs = utils.SpriteSheet()
        self.item_texs.extract_single_image("items/twig.png", (size,size))
        self.item_texs.extract_single_image("items/membrane.png", (size,size))
        self.size = size
        self.screen = pygame.display.get_surface()

        # --- Vectorized Data Structures ---
        self.names = []
        self.image_ids = []
        
        # Keep track of world-space centers for easy resizing (N, 2 array)
        self.centers = np.empty((0, 2), dtype=np.float32)
        
        # Keep track of world-space Top-Left bounding boxes (N, 4 array)
        self.rect_data = np.empty((0, 4), dtype=np.float32)
        
        # Link it to our fast VectorizedRects wrapper!
        self.v_rects = utils.VectorizedRects(self.rect_data)

    def draw(self, offset, debug):
        if len(self.names) == 0:
            return
            
        screen_rect = self.screen.get_rect()
        
        # --- Vectorized Frustum Culling ---
        # 1. Apply offset to all rects instantly to simulate screen-space
        screen_x = self.v_rects.x + offset[0]
        screen_y = self.v_rects.y + offset[1]
        right = screen_x + self.v_rects.w
        bottom = screen_y + self.v_rects.h
        
        # 2. Vectorized check: Which rects are inside the screen boundaries?
        # Returns a boolean mask
        is_visible = (right > 0) & (screen_x < screen_rect.w) & \
                     (bottom > 0) & (screen_y < screen_rect.h)
                     
        # 3. Extract only the indices of items that are on-screen
        visible_indices = np.nonzero(is_visible)[0]

        # 4. Loop ONLY through items that are actually on screen
        for i in visible_indices:
            img = self.item_texs.get_image(self.image_ids[i])
            if img:
                # Cast the NumPy scalar types to standard Python ints for Pygame
                x = int(screen_x[i])
                y = int(screen_y[i])
                w = int(self.v_rects.w[i])
                h = int(self.v_rects.h[i])
                
                draw_rect = pygame.Rect(x, y, w, h)
                self.screen.blit(img, draw_rect)
                
                if debug:
                    pygame.draw.rect(self.screen, (255, 0, 0), draw_rect, 2)

    def check_can_remove(self, player_rect:pygame.Rect) -> list:
        """
        Replaces the traditional for-loop collision with one massive C-level check.
        Returns a list of indices representing items the player is touching.
        """
        if len(self.names) == 0:
            return []
            
        # One fast math operation checks the player against ALL items
        collisions = self.v_rects.colliderect(player_rect)
        
        # Get the indices of the items we collided with
        collided_indices = np.nonzero(collisions)[0].tolist()
        
        return collided_indices

    def add_item(self, name, pos, image_id):
        img = self.item_texs.get_image(image_id)
        rect = img.get_rect()
        
        self.names.append(name)
        self.image_ids.append(image_id)
        
        # Add center pos to centers array
        new_center = np.array([[pos[0], pos[1]]], dtype=np.float32)
        if self.centers.size == 0:
            self.centers = new_center
        else:
            self.centers = np.vstack((self.centers, new_center))
        
        # Calculate Top-Left world space from the center pos
        w, h = rect.width, rect.height
        x = pos[0] - w / 2
        y = pos[1] - h / 2
        
        # Add rect to rects array
        new_rect = np.array([[x, y, w, h]], dtype=np.float32)
        if self.rect_data.size == 0:
            self.rect_data = new_rect
        else:
            self.rect_data = np.vstack((self.rect_data, new_rect))
            
        # Update the math wrapper
        self.v_rects.data = self.rect_data

    def remove_item(self, index_to_remove):
        """Pass the index returned by check_can_remove() to delete it instantly."""
        if 0 <= index_to_remove < len(self.names):
            self.names.pop(index_to_remove)
            self.image_ids.pop(index_to_remove)
            
            # Remove from numpy arrays instantly
            self.centers = np.delete(self.centers, index_to_remove, axis=0)
            self.rect_data = np.delete(self.rect_data, index_to_remove, axis=0)
            self.v_rects.data = self.rect_data

    def resize(self, scale:dict):
        if len(self.names) == 0:
            return
            
        new_size = int(self.size * scale['overall'])
        self.item_texs.rezize_images((new_size, new_size))
        
        # Re-calculate all Top-Left bounds based on the fixed world centers
        for i, image_id in enumerate(self.image_ids):
            img = self.item_texs.get_image(image_id)
            if img:
                w, h = img.get_width(), img.get_height()
                cx, cy = self.centers[i]
                self.rect_data[i] = [cx - w / 2, cy - h / 2, w, h]
                
        self.v_rects.data = self.rect_data