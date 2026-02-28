import os, math
import re
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
_font_cache = {}
def draw_text(
        text: str,
        position,
        size: int|float = 50,
        color: str | pygame.Color | tuple[int, int, int] = "#000000",
        font: Optional[pygame.font.Font] = None,
        bold: bool = False,
        italic: bool = False,
        underline: bool = False,
        draw: bool = True,
        surface: Optional[pygame.Surface] = None
) -> Tuple[pygame.Surface, pygame.Rect]:
    """Render text to the active display surface."""

    if surface:
        screen = surface
    else:
        screen = pygame.display.get_surface()

    if screen is None and draw:
        raise RuntimeError("Display surface not initialized. Call pygame.display.set_mode().")

    # Create font if none provided
    if font is None:
        key = ("Arial", int(scale(size)))
        if key not in _font_cache:
            _font_cache[key] = pygame.font.SysFont("Arial", int(scale(size)))
        font = _font_cache[key]

    # Convert color string to pygame.Color
    if isinstance(color, str):
        color = pygame.Color(color)  # type: ignore

    # Apply font styles
    font.set_bold(bold) # pyright: ignore[reportOptionalMemberAccess]
    font.set_italic(italic) # pyright: ignore[reportOptionalMemberAccess]
    font.set_underline(underline)   # pyright: ignore[reportOptionalMemberAccess]

    # Render text
    text_surface = font.render(str(text), True, color) # pyright: ignore[reportOptionalMemberAccess]
    text_rect = text_surface.get_rect(topleft=scale(position))

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


def load_font(path: str, size: int) -> pygame.font.Font:
    """Load a font from disk."""
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        BASE_DIR = os.path.abspath(
            os.path.join(script_dir, "Assets", "Fonts")
        )
        
        return pygame.font.Font(os.path.join(BASE_DIR, path), size)
    except IOError as e:
        raise FileNotFoundError(f"Unable to load font at '{path}': {e}") from e


def load_sound(path: str) -> pygame.mixer.Sound:
    """Load a sound from disk."""
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        BASE_DIR = os.path.abspath(
            os.path.join(script_dir, "Assets", "Sounds")
        )
        path = os.path.join(BASE_DIR, path)
            
        return pygame.mixer.Sound(path)
    except pygame.error as e:
        raise FileNotFoundError(f"Unable to load sound at '{path}': {e}") from e



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
            self.images[index] = pygame.transform.scale(self.images[index], size)
            return
        else:
            for i in range(len(self.images)):
                self.images[i] = pygame.transform.scale(self.images[i], size)
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
    

# timer class

class Timer:
    def __init__(self, duration: float, speed: int = 100):
        """
        This class measures duration in ms and will tell you how much time is left.

        :duration: in miliseconds
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


def create_gradient(color: str, size: tuple[int, int], radius: int = None, opposite = False, circular = False): # pyright: ignore[reportArgumentType]
    """
    Creates a gradient surface. 
    If circular=True, pixels outside the radius are transparent.
    """
    gradient = pygame.Surface(size, pygame.SRCALPHA)
    color_obj = pygame.Color(color)
    color_rgb = (color_obj.r, color_obj.g, color_obj.b)

    width, height = size
    center_x, center_y = width // 2, height // 2
    
    # If no radius is provided, use the distance to the corner
    max_dist = radius if radius is not None else math.sqrt(center_x**2 + center_y**2)

    for x in range(width):
        for y in range(height):
            # Calculate distance from center
            distance = math.sqrt((x - center_x)**2 + (y - center_y)**2)
            
            # 1. Check if we should clip to a circle shape
            if circular and distance > max_dist:
                alpha = 0
            else:
                # 2. Calculate the gradient ratio (clamped between 0 and 1)
                ratio = min(distance / max_dist, 1.0)
                
                if opposite:
                    alpha = int((1.0 - ratio) * 255) # Solid center -> Transparent edge
                else:
                    alpha = int(ratio * 255)         # Transparent center -> Solid edge
            
            gradient.set_at((x, y), (*color_rgb, alpha))

    return gradient