# -*- coding: utf-8 -*-
import pygame
import sys
import traceback

# Global font storage
_FONT = None
_SMALL_FONT = None

def load_fonts():
    global _FONT, _SMALL_FONT
    print("Loading Fonts...")
    try:
        _FONT = pygame.font.SysFont(None, 30)
        _SMALL_FONT = pygame.font.SysFont(None, 20)
        print("Fonts Loaded.")
        return True
    except Exception as e:
        print(f"!!!!!!!!!!!!!!!!! Font Loading Failed: {e} !!!!!!!!!!!!!!!!!")
        print("Attempting to continue without custom fonts might fail later.")
        traceback.print_exc()
        # Mark as failed by leaving them None
        return False

def get_main_font():
    if _FONT is None:
        # Fallback if not loaded, though load_fonts should be called at init
        try:
            return pygame.font.SysFont(None, 30)
        except: return None # Should not happen if pygame.font.init() worked
    return _FONT

def get_small_font():
    if _SMALL_FONT is None:
        try:
            return pygame.font.SysFont(None, 20)
        except: return None
    return _SMALL_FONT

# Placeholder for other asset loading (images, sounds)
# Example:
# _images_cache = {}
# def load_image(name, colorkey=None):
#     if name in _images_cache:
#         return _images_cache[name]
#     # fullname = os.path.join('assets/images', name)
#     # try:
#     #     image = pygame.image.load(fullname)
#     # except pygame.error as message:
#     #     print('Cannot load image:', fullname)
#     #     raise SystemExit(message)
#     # image = image.convert()
#     # if colorkey is not None:
#     #     if colorkey == -1:
#     #         colorkey = image.get_at((0,0))
#     #     image.set_colorkey(colorkey, pygame.RLEACCEL)
#     # _images_cache[name] = image
#     # return image