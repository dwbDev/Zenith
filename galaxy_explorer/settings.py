# -*- coding: utf-8 -*-
# Use utf-8 encoding for broader compatibility

import pygame

# ------------------------------------------------------------
# -----------------     CONSTANTS     ------------------------
# ------------------------------------------------------------
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 750
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
BLUE = (0, 0, 255)
LIGHT_BLUE = (173, 216, 230)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
GRAY = (128, 128, 128)
DARK_GRAY = (50, 50, 50) # Used for night sky
ORANGE = (255, 165, 0)
BROWN = (139, 69, 19)
PURPLE = (128, 0, 128)
PARTICLE_COLOR = (200, 200, 255) # For side thrusters

# Game States (used as keys/identifiers for state transitions)
GALAXY_VIEW = "GALAXY_VIEW"
STAR_SYSTEM_VIEW = "STAR_SYSTEM_VIEW"
PLANET_OVERHEAD_VIEW = "PLANET_OVERHEAD_VIEW"
GROUND_VIEW = "GROUND_VIEW"
HYPERSPACE_TRANSITION = "HYPERSPACE_TRANSITION"

# Game specific constants
HYPERSPACE_DURATION = 90 # frames
PLANET_OVERHEAD_SCALE = 5
NUM_TWINKLE_STARS = 180