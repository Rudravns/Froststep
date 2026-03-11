import pygame
import utilities as utils
import random


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
            # The image is drawn centered on self.pos. Its top-left corner in world space is:
            img_topleft_x = self.pos.x - img.get_width() / 2
            img_topleft_y = self.pos.y - img.get_height() / 2

            # The bound_rect is relative to the image's top-left.
            # So the hitbox's world position is img_topleft + bound_rect.topleft
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
            # Draw the actual world-space rect relative to camera for debugging
            debug_rect = self.rect.copy()
            debug_rect.x += offset[0]
            debug_rect.y += offset[1]
            pygame.draw.rect(self.screen, (255, 0, 0), debug_rect, 2)
    
    def get_rect(self, offset):
        # Return rect in screen coordinates for simpler click/collision checks
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
        self.cached_items = []
        """
        item: item_name(string)
        pos: vector2d(x,y)
        rect: img.get_rect()(rect)
        image: image_id(int)
        """
        # Removed deepcopy because pygame.Surface objects cannot be pickled.
        # It is better to use the reference directly or handle surface copying manually.
        self.item_texs = utils.SpriteSheet()
        self.item_texs.extract_single_image("items/twig.png", (60,60))
        self.size = size
        self.screen = pygame.display.get_surface()

    def draw(self, offset, debug):
        screen_rect = self.screen.get_rect()
        
        for item in self.cached_items:
            # .copy() and setting center is faster than recreation if we have many items
            draw_rect = item["rect"].copy()
            draw_rect.center = item["pos"] + pygame.Vector2(offset)
            #print(draw_rect, screen_rect.colliderect(draw_rect))

            # Frustum Culling: Only blit if the draw_rect is touching the screen_rect
            if screen_rect.colliderect(draw_rect):
                img = self.item_texs.get_image(item["image"])
                if img: # Safety check
                    self.screen.blit(img, draw_rect)
                
                if debug:
                    pygame.draw.rect(self.screen, (255, 0, 0), draw_rect, 2)

    def add_item(self, name, pos, image_id):
        img = self.item_texs.get_image(image_id)
        
        self.cached_items.append({
            "item": name,
            "pos": pygame.Vector2(pos),
            "image": image_id,
            "rect": img.get_rect() 
        })

    def remove_item(self, item_to_remove):
        if item_to_remove in self.cached_items:
            self.cached_items.remove(item_to_remove)

    def resize(self, scale:dict):
        # Update the texture sheet size
        new_size = int(self.size * scale['overall'])
        self.item_texs.rezize_images((new_size, new_size))
        
        # Update cached rects for all items to match new texture size
        for item in self.cached_items:
            img = self.item_texs.get_image(item["image"])
            if img:
                item["rect"] = img.get_rect()