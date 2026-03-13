import os, math
import numpy as np
import pygame
from typing import *  # pyright: ignore[reportWildcardImportFromLibrary]
import json


pygame.init()
pygame.display.init()
pygame.font.init()




BASE_SIZE = (1100,700)
map_key = {
    0: "Empty",
    1: "Spike",
    2: "Cube",
    3: "Start",
    4: "End"
}


# ====================================================
# Screen Funcs
# ====================================================
def get_screen_size():
    return pygame.display.Info().current_w, pygame.display.Info().current_h

    
@overload
def scale(value: int | float, *, round_values: bool = False) -> int | float: ...


@overload
def scale(
        value: tuple[int | float, ...],
        *,
        round_values: bool = False
) -> tuple[int | float, ...]: ...


def scale(
        value: int | float | tuple[int | float, ...],
        *,
        round_values: bool = False
) -> int | float | tuple[int | float, ...]:
    """Scale a value or tuple of values based on the current fullscreen resolution."""
    if isinstance(value, (int, float)):
        return round(value) if round_values else value

    if isinstance(value, tuple):
        return tuple(round(v) if round_values else v for v in value)

    raise TypeError("Value must be an int, float, or tuple of int/float.")


# =====================================================
# Text rendering
# =====================================================

# Initialize font cache
_font_cache = {}

def load_font(name: str, size: int, bold: bool = False) -> pygame.font.Font:
    """
    Load a font from disk based on the family name and style.
    Automatically grabs the -Bold.ttf variant if bold=True.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    BASE_DIR = os.path.abspath(
        os.path.join(script_dir, "Assets", "Fonts")
    )

    # Determine which file variant to load based on the bold flag
    style = "Bold" if bold else "Regular"
    filename = f"{name}-{style}.ttf"

    # 1st try: Look inside a subfolder (e.g., Assets/Fonts/Rajdhani/Rajdhani-Regular.ttf)
    font_path = os.path.join(BASE_DIR, name, filename)

    # 2nd try: Look in the main Fonts folder (e.g., Assets/Fonts/Rajdhani-Regular.ttf)
    if not os.path.exists(font_path):
        font_path = os.path.join(BASE_DIR, filename)
        
    try:
        return pygame.font.Font(font_path, size)
    except Exception as e:
        print(f"Warning: Unable to load custom font '{filename}': {e}. Falling back to Arial.")
        # Fallback to standard system font
        sys_font = pygame.font.SysFont("Arial", size)
        sys_font.set_bold(bold)
        return sys_font

def draw_text(
        text: str,
        position,
        size: int|float = 50,
        color: str | pygame.Color | tuple[int, int, int] = "#000000",
        font: Optional[str | pygame.font.Font] = None,
        bold: bool = False,
        italic: bool = False,
        underline: bool = False,
        draw: bool = True,
        centered: bool = False,
        surface: Optional[pygame.Surface] = None
) -> Tuple[pygame.Surface, pygame.Rect]:
    """Render text to the active display surface."""

    if surface:
        screen = surface
    else:
        screen = pygame.display.get_surface()

    if screen is None and draw:
        raise RuntimeError("Display surface not initialized. Call pygame.display.set_mode().")

    # Assuming `scale()` is defined elsewhere in your utilities
    # If not, you might need to adjust this depending on how you import `scale`
    scaled_size = int(scale(size)) if 'scale' in globals() else int(size)

    # 1. Determine font object or string name
    if isinstance(font, pygame.font.Font):
        font_obj = font
        # Apply pseudo-styles directly to an existing font object
        font_obj.set_bold(bold)
        font_obj.set_italic(italic)
        font_obj.set_underline(underline)
    else:
        # Default to Arial if no font is specified
        font_name = font if font is not None else "Arial"
        
        # Unique cache key based on all styling parameters
        key = (font_name, scaled_size, bold, italic, underline)
        
        if key not in _font_cache:
            # Check if it's one of our custom downloaded fonts
            if font_name in ["Rajdhani", "Silkscreen"]:
                # Load the custom file (handles bold internally by picking correct .ttf)
                new_font = load_font(font_name, scaled_size, bold) # pyright: ignore[reportCallIssue]
                new_font.set_italic(italic)
                new_font.set_underline(underline)
            else:
                # Load standard system font
                new_font = pygame.font.SysFont(font_name, scaled_size)
                new_font.set_bold(bold)
                new_font.set_italic(italic)
                new_font.set_underline(underline)
                
            _font_cache[key] = new_font
        
        font_obj = _font_cache[key]

    # 2. Convert color string to pygame.Color
    if isinstance(color, str):
        color = pygame.Color(color)  # type: ignore

    # 3. Render text
    text_surface = font_obj.render(str(text), True, color) # pyright: ignore[reportOptionalMemberAccess]
    
    scaled_pos = scale(position) if 'scale' in globals() else position
    
    if centered:
        text_rect = text_surface.get_rect(center=scaled_pos)
    else:
        text_rect = text_surface.get_rect(topleft=scaled_pos)
    
    if draw:
        screen.blit(text_surface, text_rect)

    return text_surface, text_rect

# =====================================================
# Loading / Saving Files
# =====================================================
def load_image(path: str) -> pygame.Surface:
    """Load an image from disk with alpha support."""
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        BASE_DIR = os.path.abspath(
            os.path.join(script_dir, "Assets")
        )
        image = pygame.image.load(os.path.join(BASE_DIR, path))
        return image
    except pygame.error as e:
        raise FileNotFoundError(f"Unable to load image at '{path}': {e}") from e


def load_sound(filename: str) -> pygame.mixer.Sound:
    """Load a sound from disk."""
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        BASE_DIR = os.path.abspath(
            os.path.join(script_dir, "Assets", "Sounds", "SFX")
        )
        full_path = os.path.join(BASE_DIR, filename)
        
        # We check existence here after the path is actually built
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found at: {full_path}")
            
        return pygame.mixer.Sound(full_path)
    except pygame.error as e:
        raise FileNotFoundError(f"Unable to load sound at '{full_path}': {e}") from e



# =====================================================
# Sprite Sheets
# =====================================================
class SpriteSheet:
    def __init__(self):
        #only init
        self.sprite_sheet = None
        self.sprite_sheet_rect = None
        self.images: List[pygame.Surface] = []
        self.original_image: List[pygame.Surface] = []
        
    # ---------------------------------------------------------
    # Method 1: Extract using a list of Rects
    # ---------------------------------------------------------
    def extract_from_rects(
        self,
        path: str,
        rects: List[pygame.Rect],
        scale: Tuple[int, int],
        alpha: int = 255,
        convert_alpha: bool = True
    ) :
        self.sprite_sheet = load_image(path)
        if convert_alpha:
            self.sprite_sheet = self.sprite_sheet.convert_alpha()
       
        self.sprite_sheet_rect = self.sprite_sheet.get_rect()
        images: List[pygame.Surface] = []

        for rect in rects:
            image = pygame.Surface(rect.size, pygame.SRCALPHA)
            image.blit(self.sprite_sheet, (0, 0), rect)
            image = pygame.transform.scale(image, scale)
            image.set_alpha(alpha)
            images.append(image)

        self.images.extend(images)
        self.original_image.extend(images)


    # ---------------------------------------------------------
    # Method 2: Extract grid-style
    # ---------------------------------------------------------
    def extract_grid(
        self,
        path: str,
        crop_size: Tuple[int, int],
        start: Tuple[int, int] = (0, 0),
        scale: Tuple[int, int] | None = None,
        alpha: int = 255,
        convert_alpha: bool = True
    ):

        self.sprite_sheet = load_image(path)
        if convert_alpha:
            self.sprite_sheet = self.sprite_sheet.convert_alpha()
        self.sprite_sheet_rect = self.sprite_sheet.get_rect()
        images: List[pygame.Surface] = []
        
        w_crop, h_crop = crop_size
        x_start, y_start = start

        for y in range(y_start, self.sprite_sheet_rect.height, h_crop):
            for x in range(x_start, self.sprite_sheet_rect.width, w_crop):
                rect = pygame.Rect(x, y, w_crop, h_crop)

                image = pygame.Surface(rect.size, pygame.SRCALPHA)
                image.blit(self.sprite_sheet, (0, 0), rect)

                if scale:
                    image = pygame.transform.scale(image, scale)

                image.set_alpha(alpha)
                images.append(image)
                self.original_image.append(image)

        self.images.extend(images)

    def extract_single_image(self, path: str, scale: Tuple[int, int], alpha: int = 255, convert_alpha: bool = True):
        image = load_image(path)
        image = pygame.transform.scale(image, scale)
        if convert_alpha:
            image = image.convert_alpha()
        else:   image = image.convert()
        image.set_alpha(alpha)
        self.images.append(image)
        self.original_image.append(image)

#   all the init of @overload functions are in the SpriteSheet class, so that we can use it to rotate and scale images easily. We can also use it to extract images from a sprite sheet easily. The @overload functions are just for type hinting and do not have any implementation. The actual implementation is in the functions below them. This way we can have multiple ways to rotate and scale images without having to write multiple functions for each case.
    @overload
    def rotate_images(self, angle: int) -> None: ...

    @overload 
    def rotate_images(self, angle: int, index: int) -> None: ...

    @overload
    def rezize_images(self, size: Tuple[int, int]) -> None: ...

    @overload
    def rezize_images(self, size: Tuple[int, int], index: int) -> None: ...

   
#   The actual implementation of the above functions. The index parameter is optional, if it is provided, only the image at that index will be rotated or resized, otherwise all images will be rotated or resized.

    def rezize_images(self, size: Tuple[int, int], index: Optional[int] = None) -> None:
        if index is not None:
            self.images[index] = pygame.transform.scale(self.original_image[index], size)
            return
        else:
            for i in range(len(self.images)):
                self.images[i] = pygame.transform.scale(self.original_image[i], size)
            return

    def rotate_images(self, angle: int, index: int | None = None) -> None:
        if index is not None:
            self.images[index] = pygame.transform.rotate(self.original_image[index], angle)
            return
        else:
            for i in range(len(self.images)):
                self.images[i] = pygame.transform.rotate(self.original_image[i], angle)
            return
        


    # ---------------------------------------------------------
    def get_image(self, index: int) -> pygame.Surface:
        return self.images[index]
    
    def remove(self, index:int):
        self.images.pop(index)
    

# timer class

class Timer:
    def __init__(self, duration: float, speed: int = 100):
        """
        This class measures duration in seconds and will tell you how much time is left.

        :duration: in seconds
        """
        self.duration = duration
        self.start_time = None
        self.saved_time = duration
        self.speed = speed
        self.stoped = False

    def start(self):
        self.start_time = pygame.time.get_ticks()

    def has_elapsed(self) -> bool:
        if self.stoped:
            return True
        if self.start_time is None:
            return False
        
        elapsed_time = ((pygame.time.get_ticks() - self.start_time) / 1000) * (self.speed / 100)
        return elapsed_time >= self.duration
    
    def get_time_left(self) -> float:
        if self.start_time is None:
            return self.duration
        return self.duration - ((pygame.time.get_ticks() - self.start_time) / 1000) * (self.speed / 100)

    
    def reset(self):
        self.start_time = None

    def change_duration(self, new_duration: float):
        self.duration = new_duration
        self.reset()

    def pause(self):
        if self.start_time is not None: # if it is running
            self.duration = self.get_time_left() # Save remaining time
            self.start_time = None # Mark as paused

    def stop(self):
        self.stoped = True
        self.pause()

    def resume(self):
        if self.start_time is None and not self.stoped: # if it is paused
            self.start_time = pygame.time.get_ticks()
            self.stoped = False

    def restart(self):
        self.reset() 
        self.start()

    def __str__(self):
        return f"Time Left: {self.duration - ((pygame.time.get_ticks() - self.start_time) / 1000) * (self.speed / 100)}" # pyright: ignore[reportOperatorIssue]


def create_gradient(color: str, size: tuple[int, int], radius: int = None, opposite: bool = False, circular: bool = False):  # pyright: ignore[reportArgumentType]
    """
    Creates a gradient surface. Optimized with NumPy for vectorization.
    :color: Color of the gradient
    :size: size of the surface
    
    :circular: If True, pixels outside the radius are transparent.

    """
    width, height = size
    
    # Create the surface with SRCALPHA
    gradient = pygame.Surface(size, pygame.SRCALPHA)
    
    # Fill the entire surface with the target color but 0 alpha initially.
    # This completely avoids needing to set the R, G, B values pixel-by-pixel.
    color_obj = pygame.Color(color)
    gradient.fill((color_obj.r, color_obj.g, color_obj.b, 0))

    center_x, center_y = width // 2, height // 2
    max_dist = radius if radius is not None else math.sqrt(center_x**2 + center_y**2)
    
    # Prevent division by zero if radius is 0
    max_dist = max(max_dist, 0.001)

    # 1. Create a vectorized grid of X and Y coordinates 
    # np.ogrid creates 1D arrays that broadcast to a 2D grid matching Pygame's (width, height)
    X, Y = np.ogrid[:width, :height]

    # 2. Calculate distances from center for ALL pixels at once using NumPy broadcasting
    dist = np.sqrt((X - center_x)**2 + (Y - center_y)**2)

    # 3. Calculate the gradient ratio (clamped between 0 and 1) for the entire array
    ratio = np.clip(dist / max_dist, 0.0, 1.0)

    # 4. Calculate alpha values across the whole grid
    if opposite:
        alpha = (1.0 - ratio) * 255  # Solid center -> Transparent edge
    else:
        alpha = ratio * 255          # Transparent center -> Solid edge

    # 5. Apply circular clipping if required
    if circular:
        alpha[dist > max_dist] = 0

    # 6. Apply the calculated alpha array directly to the Pygame surface's memory
    alpha_array = pygame.surfarray.pixels_alpha(gradient)
    alpha_array[:] = alpha.astype(np.uint8)
    
    # IMPORTANT: Delete the reference to unlock the surface memory so Pygame can use it
    del alpha_array

    return gradient


class VectorizedRects:
    """
    A NumPy-backed class to handle thousands of Pygame Rects simultaneously.
    Stores rects as an (N, 4) float/int array: [x, y, width, height].
    """
    def __init__(self, rect_data):
        self.data = np.array(rect_data, dtype=np.float32)

    @classmethod
    def from_pygame_rects(cls, rect_list):
        data = [[r.x, r.y, r.w, r.h] for r in rect_list]
        return cls(data)

    @property
    def x(self): return self.data[:, 0]
    @x.setter
    def x(self, val): self.data[:, 0] = val

    @property
    def y(self): return self.data[:, 1]
    @y.setter
    def y(self, val): self.data[:, 1] = val

    @property
    def w(self): return self.data[:, 2]
    @property
    def h(self): return self.data[:, 3]
    @property
    def left(self): return self.x
    @property
    def right(self): return self.x + self.w
    @property
    def top(self): return self.y
    @property
    def bottom(self): return self.y + self.h

    def move_ip(self, dx, dy):
        self.data[:, 0] += dx
        self.data[:, 1] += dy

    def collidepoint(self, px, py):
        return (self.x <= px) & (px < self.right) & \
               (self.y <= py) & (py < self.bottom)

    def colliderect(self, other_rect):
        if isinstance(other_rect, pygame.Rect):
            ox, oy, ow, oh = other_rect.x, other_rect.y, other_rect.w, other_rect.h
        else:
            ox, oy, ow, oh = other_rect

        oright = ox + ow
        obottom = oy + oh
        return (self.left < oright) & (self.right > ox) & \
               (self.top < obottom) & (self.bottom > oy)
    

class Button:

    def __init__(
        self,
        pos,
        size,
        text="",
        color=(60, 60, 60),
        hover_color=(100, 100, 100),
        press_color=(150, 150, 150),
        text_color=(255, 255, 255),
        border_color=None,
        border_width=0,
        radius=8,
        font = None,
        callback=None,
        center=False,
        enabled=True
    ):

        self.screen = pygame.display.get_surface()

        self.pos = list(pos)
        self.size = list(size)
        
    
        self.rect = pygame.Rect(0, 0, *size)
        if center:
            self.rect.center = pos
        else:
            self.rect.topleft = pos

        self.text = text
        self.text_color = text_color

        self.color = color
        self.hover_color = hover_color
        self.press_color = press_color

        self.border_color = border_color
        self.border_width = border_width
        self.radius = radius

        self.callback = callback
        self.enabled = enabled

        self.hovered = False
        self.pressed = False

        self.font_size = int(size[1] * 0.6)
        self.font = font

        # animation
        self.scale = 1
        self.target_scale = 1

        self.center_anchor = center
        self.anchor = self.rect.center if center else self.rect.topleft
        self.center = center
        

        


        self.org_size = list(size)
        self.org_pos = pos
        self.base_render_size = [
            int(self.org_size[0]),
            int(self.org_size[1])
        ]

    def handle_event(self, event):

        if not self.enabled:
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.hovered:
                self.pressed = True

        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                if self.pressed and self.hovered:
                    if self.callback:
                        self.callback()
                self.pressed = False

    def update(self):

        mouse = pygame.mouse.get_pos()
        self.hovered = self.rect.collidepoint(mouse)

        if self.pressed:
            self.target_scale = 0.95
        elif self.hovered:
            self.target_scale = 1.08
        else:
            self.target_scale = 1

        # smooth animation
        self.scale += (self.target_scale - self.scale) * 0.2

        new_w = int(self.base_render_size[0] * self.scale)
        new_h = int(self.base_render_size[1] * self.scale)

        self.rect.size = (new_w, new_h)

        if self.center_anchor:
            self.rect.center = self.anchor
        else:
            self.rect.topleft = self.anchor

        self.font_size = int(self.rect.height * 0.55)

    def draw(self):

        if not self.enabled:
            draw_color = (110,110,110)
        elif self.pressed:
            draw_color = self.press_color
        elif self.hovered:
            draw_color = self.hover_color
        else:
            draw_color = self.color

        pygame.draw.rect(
            self.screen,
            draw_color,
            self.rect,
            border_radius=self.radius
        )

        if self.border_width > 0 and self.border_color:
            pygame.draw.rect(
                self.screen,
                self.border_color,
                self.rect,
                self.border_width,
                border_radius=self.radius
            )

        # draw text using YOUR function
        if self.text:
            draw_text(
                self.text,
                self.rect.center,
                self.font_size,
                color=self.text_color,
                centered=True,
                surface=self.screen,
                font=self.font
            )

    def resize(self, scale):

        self.base_render_size = [
            int(self.org_size[0] * scale["overall"]),
            int(self.org_size[1] * scale["overall"])
        ]

        new_x = int(self.org_pos[0] * scale["width"])
        new_y = int(self.org_pos[1] * scale["height"])

        self.anchor = (new_x, new_y)

        self.rect.size = tuple(self.base_render_size) # pyright: ignore[reportAttributeAccessIssue]