# -*- coding: utf-8 -*-
import pygame
import math
import random
from .. import settings # For colors, screen dimensions etc.
from . import assets # For fonts

# --- General Utilities ---
def lerp(a, b, t):
    """Linear interpolation for numbers"""
    return a + (b - a) * t

def lerp_color(color1, color2, t):
    """Linear interpolation for colors"""
    t = max(0, min(1, t)) # Clamp t between 0 and 1
    r = int(lerp(color1[0], color2[0], t))
    g = int(lerp(color1[1], color2[1], t))
    b = int(lerp(color1[2], color2[2], t))
    r = max(0, min(255, r))
    g = max(0, min(255, g))
    b = max(0, min(255, b))
    return (r, g, b)

def get_rotated_point(center_x, center_y, angle_degrees, radius):
    """Calculate point on circle"""
    angle_radians = math.radians(angle_degrees)
    x = center_x + radius * math.cos(angle_radians)
    y = center_y + radius * math.sin(angle_radians)
    return int(x), int(y)

# --- Text Drawing ---
def draw_text(text, font_type, color, surface, x, y):
    font = None
    if font_type == "main":
        font = assets.get_main_font()
    elif font_type == "small":
        font = assets.get_small_font()
    
    if font:
        try:
            textobj = font.render(text, True, color)
            textrect = textobj.get_rect()
            textrect.topleft = (x, y)
            surface.blit(textobj, textrect)
        except Exception as e:
            print(f"Error rendering text '{text}': {e}")
    else:
        print(f"Font '{font_type}' not available for text: {text}")


# --- Star-Field Specifics ---
_TWINKLE_STARS_DATA = []

def init_twinkle_stars():
    global _TWINKLE_STARS_DATA
    if not _TWINKLE_STARS_DATA: # Initialize only once
        for _ in range(settings.NUM_TWINKLE_STARS):
            _TWINKLE_STARS_DATA.append({
                'pos'   : (random.randint(0, settings.SCREEN_WIDTH-1),
                           random.randint(0, settings.SCREEN_HEIGHT-1)),
                'size'  : random.choice([1,1,1,2]),
                'speed' : random.uniform(0.02, 0.12),
                'phase' : random.uniform(0, math.tau),
                'lo'    : random.randint(40, 90),
                'hi'    : random.randint(170, 255)
            })

def draw_twinkling_stars(surface, frame_count):
    """Draw tiny stars whose brightness oscillates sinusoidally."""
    if not _TWINKLE_STARS_DATA:
        init_twinkle_stars()
        
    for s in _TWINKLE_STARS_DATA:
        t = (math.sin(frame_count * s['speed'] + s['phase']) + 1) * 0.5
        c = int(s['lo'] + (s['hi'] - s['lo']) * t)
        pygame.draw.circle(surface, (c, c, c), s['pos'], s['size'])

# --- Planet Rendering Specifics ---
def draw_shaded_planet_simple(surface, planet_data, planet_pos):
    """ Draws a planet with simple overall radial gradient shading """
    radius = planet_data['radius']
    center_color = planet_data['color']

    if radius < 1: return

    darkening_factor = 0.3
    edge_color = (
        max(0, min(255, int(center_color[0] * darkening_factor))),
        max(0, min(255, int(center_color[1] * darkening_factor))),
        max(0, min(255, int(center_color[2] * darkening_factor)))
    )

    for current_radius in range(radius, 0, -1):
        if radius == 0: t = 0
        else: t = current_radius / radius
        interpolated_color = lerp_color(center_color, edge_color, 1.0 - t) # Invert t for correct gradient
        try:
             if radius > 5:
                 pygame.draw.circle(surface, interpolated_color, planet_pos, current_radius)
             elif current_radius % 2 == 0: # Optimization for small planets
                  pygame.draw.circle(surface, interpolated_color, planet_pos, current_radius)
        except Exception: pass # Ignore minor drawing errors if any

def draw_planet_light_and_shadow(surface, center, planet_draw_radius, orbit_angle_deg):
    glow_color   = (255, 250, 230)
    peak_alpha   = 180
    falloff_pow  = 1.6
    step         = 4

    max_radius = int(math.hypot(settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
    light_surface = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA)

    for r in range(max_radius, 0, -step):
        t = r / max_radius
        alpha = int(peak_alpha * (t ** falloff_pow))
        if alpha <= 0:
            continue
        pygame.draw.circle(light_surface, (*glow_color, alpha), center, r)

    star_to_planet = pygame.Vector2(
        math.cos(math.radians(orbit_angle_deg)),
        math.sin(math.radians(orbit_angle_deg))
    )
    if star_to_planet.length_squared() > 0: # Avoid division by zero if orbit_angle makes it zero vector
        star_to_planet.normalize_ip()

    shadow_dir = star_to_planet
    left  = pygame.Vector2(-shadow_dir.y,  shadow_dir.x)
    if left.length_squared() > 0: left.normalize_ip()
    right = -left
    
    wedge_len = max_radius
    wedge_w   = planet_draw_radius
    p0   = pygame.Vector2(center)
    pts  = [p0,
            p0 + left  * wedge_w,
            p0 + left  * wedge_w + shadow_dir * wedge_len,
            p0 + right * wedge_w + shadow_dir * wedge_len,
            p0 + right * wedge_w]
    
    # Ensure points are integer tuples for pygame.draw.polygon
    int_pts = [(int(p.x), int(p.y)) for p in pts]
    if len(int_pts) >= 3: # Polygon needs at least 3 points
        pygame.draw.polygon(light_surface, (0, 0, 0, 0), int_pts)


    pygame.draw.circle(light_surface, (0, 0, 0, 0), center, planet_draw_radius)
    surface.blit(light_surface, (0, 0))


# --- Planet Texture Generation Specifics ---
def create_planet_texture(planet_data, scale):
    radius = planet_data['radius'] * scale
    diameter = int(radius * 2)
    tex_size = int(diameter * 1.1) if diameter > 0 else 10 # Ensure tex_size is reasonable
    planet_surf = pygame.Surface((tex_size, tex_size), pygame.SRCALPHA)
    surf_center_x = tex_size // 2
    surf_center_y = tex_size // 2
    surf_center = (surf_center_x, surf_center_y)

    if radius < 1: return planet_surf

    for region in planet_data['regions']:
        center_color = region['color']
        darkening_factor = 0.25
        edge_color = (
            max(0, min(255, int(center_color[0] * darkening_factor))),
            max(0, min(255, int(center_color[1] * darkening_factor))),
            max(0, min(255, int(center_color[2] * darkening_factor)))
        )

        gradient_surf = pygame.Surface((tex_size, tex_size), pygame.SRCALPHA)
        for current_radius_iter in range(int(radius), 0, -1):
            t = current_radius_iter / radius if radius > 0 else 0
            interpolated_color = lerp_color(center_color, edge_color, 1.0 - t) # Invert t
            pygame.draw.circle(gradient_surf, interpolated_color, surf_center, current_radius_iter)

        mask_surf = pygame.Surface((tex_size, tex_size), pygame.SRCALPHA)
        points = [surf_center]
        angle_range = (region['end_angle'] - region['start_angle'] + 360) % 360
        if angle_range == 0 and len(planet_data['regions']) == 1: angle_range = 360
        
        steps = max(5, int(angle_range / 4)) # Ensure at least a few steps for small angles
        if steps == 0 and angle_range > 0 : steps = 1 # if angle_range is very small e.g. 1 degree

        for step in range(steps + 1):
            angle = (region['start_angle'] + (angle_range * step / steps)) % 360 if steps > 0 else region['start_angle']
            points.append(get_rotated_point(surf_center_x, surf_center_y, angle, radius))
        
        if len(points) >= 3:
            pygame.draw.polygon(mask_surf, settings.WHITE, points) # Use settings.WHITE

        try:
            gradient_surf.blit(mask_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        except pygame.error as e:
            print(f"Warning: BLEND_RGBA_MULT failed for region mask: {e}. Drawing flat region.")
            if len(points) >= 3:
                 pygame.draw.polygon(planet_surf, region['color'], points) # Draw on main surface
            continue # Skip blitting this region's gradient_surf
        planet_surf.blit(gradient_surf, (0, 0))
    return planet_surf