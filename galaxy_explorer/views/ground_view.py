# -*- coding: utf-8 -*-
import pygame
import random
import math
from .base_view import BaseView
from .. import settings
from ..core import utils

class GroundView(BaseView):
    def __init__(self, game_context):
        super().__init__()
        self.game_context = game_context
        self.player_char = game_context['player_char']
        
        self.current_planet_data = None
        self.current_region_data = None
        
        self.ground_platforms = []
        self.landed_ship_rect = None
        self.biome_color = settings.BLACK
        self.parallax_mountains = []
        self._gv_star_pos_list = None # For caching star positions

    def on_enter(self, params=None):
        self.player_char.reset_position()

        current_planet_idx = self.game_context.get('current_planet_idx')
        current_region_idx = self.game_context.get('current_region_idx')
        
        valid_data = False
        if current_planet_idx is not None and current_region_idx is not None:
            star_system = self.game_context['current_star_system']
            if 0 <= current_planet_idx < len(star_system.planets):
                self.current_planet_data = star_system.planets[current_planet_idx]
                if 0 <= current_region_idx < len(self.current_planet_data['regions']):
                    self.current_region_data = self.current_planet_data['regions'][current_region_idx]
                    self.biome_color = self.current_region_data['color']
                    valid_data = True
        
        if not valid_data:
            print("Error: Invalid planet or region index for GroundView.")
            self.next_state_request = (settings.PLANET_OVERHEAD_VIEW, {})
            return

        self.ground_platforms = []
        self.parallax_mountains = []
        self._gv_star_pos_list = None # Reset star cache

        ship_world_x = self.player_char.pos.x - 100 
        ship_height = 60
        self.landed_ship_rect = pygame.Rect(ship_world_x, 
                                           settings.SCREEN_HEIGHT - 50 - ship_height,
                                           45, ship_height)

        world_width_for_elements = settings.SCREEN_WIDTH * 5

        for _p in range(random.randint(15,40)):
            plat_x_world = random.randint(int(ship_world_x - world_width_for_elements / 2), 
                                     int(ship_world_x + world_width_for_elements / 2))
            plat_y_world = random.randint(int(settings.SCREEN_HEIGHT * 0.4), 
                                     settings.SCREEN_HEIGHT - 100)
            temp_rect_world = pygame.Rect(plat_x_world, plat_y_world, 
                                         random.randint(80,250), 20)
            if not temp_rect_world.colliderect(self.landed_ship_rect.inflate(40,40)):
                self.ground_platforms.append(temp_rect_world)
        
        for _m in range(random.randint(15,40)):
            m_x_world = random.randint(int(ship_world_x - world_width_for_elements / 2), 
                                  int(ship_world_x + world_width_for_elements / 2))
            m_h = random.randint(50, settings.SCREEN_HEIGHT // 2)
            m_w = m_h * random.uniform(1.5, 3.5)
            mountain_rect_world = pygame.Rect(m_x_world, settings.SCREEN_HEIGHT - 50 - m_h, m_w, m_h)
            self.parallax_mountains.append((mountain_rect_world, random.uniform(0.1, 0.7))) 
        
        self.parallax_mountains.sort(key=lambda x: x[1], reverse=True)

    def handle_event(self, event, mouse_pos, keys_pressed):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
            if self.landed_ship_rect and self.player_char.rect.colliderect(
                self.landed_ship_rect.move(self.player_char.world_scroll, 0)):
                self.next_state_request = (settings.PLANET_OVERHEAD_VIEW, {})

    def update(self, dt, mouse_pos, keys_pressed, frame_count):
        if not self.current_planet_data or not self.current_region_data: return

        self.current_planet_data['rotation_angle'] = \
            (self.current_planet_data['rotation_angle'] + self.current_planet_data['rotation_speed']) % 360
        
        current_star_system = self.game_context.get('current_star_system')
        if current_star_system:
            current_star_system.update_orbits()

        self.player_char.update(keys_pressed, self.ground_platforms, self.landed_ship_rect)

    def render(self, screen, mouse_pos, frame_count): # MODIFIED: Signature matches BaseView
        if not self.current_planet_data or not self.current_region_data:
            utils.draw_text("Error: Ground data not loaded.", "main", settings.RED, screen, 100, 100)
            return

        sky_color = settings.DARK_GRAY
        num_stars = 0
        daylight_factor = 0.0
        
        planet_rotation_gv = self.current_planet_data['rotation_angle']
        daylight_factor = (math.cos(math.radians(planet_rotation_gv + 180)) + 1) / 2.0 
        
        sky_color = utils.lerp_color(settings.DARK_GRAY, settings.LIGHT_BLUE, daylight_factor)
        num_stars = int(150 * max(0.0, 1.0 - daylight_factor * 1.5))

        screen.fill(sky_color)

        if num_stars > 0:
            if self._gv_star_pos_list is None or len(self._gv_star_pos_list) != 150:
                 random.seed(123 + int(planet_rotation_gv) % 360) # Seed changes slightly with rotation for variation
                 self._gv_star_pos_list = [(random.randint(0,settings.SCREEN_WIDTH), random.randint(0,settings.SCREEN_HEIGHT-50)) for _ in range(150)]
                 random.seed()
            
            for i_star in range(min(num_stars, 150)):
                pygame.draw.circle(screen,settings.WHITE,self._gv_star_pos_list[i_star],random.randint(1,2))

        current_scroll_gv = self.player_char.world_scroll

        for mount_rect_world, depth_gv in self.parallax_mountains:
            final_color_factor = (0.4 + (0.6 * (1 - depth_gv))) * (0.3 + 0.7 * daylight_factor)
            mount_color = tuple(max(0,min(255,int(c * final_color_factor))) for c in self.biome_color)
            shifted_rect_m_screen = pygame.Rect(
                int(mount_rect_world.left + current_scroll_gv * (1.0 - depth_gv)),
                mount_rect_world.top,
                mount_rect_world.width,
                mount_rect_world.height
            )
            if shifted_rect_m_screen.right > 0 and shifted_rect_m_screen.left < settings.SCREEN_WIDTH:
                pygame.draw.polygon(screen, mount_color, [
                    (shifted_rect_m_screen.left, shifted_rect_m_screen.bottom),
                    (shifted_rect_m_screen.centerx, shifted_rect_m_screen.top),
                    (shifted_rect_m_screen.right, shifted_rect_m_screen.bottom)
                ])

        ground_color_gv = tuple(max(0,min(255,int(c * (0.5 + 0.5 * daylight_factor)))) for c in self.biome_color)
        pygame.draw.rect(screen, ground_color_gv, pygame.Rect(0, settings.SCREEN_HEIGHT - 50, settings.SCREEN_WIDTH, 50))

        platform_color = utils.lerp_color(settings.DARK_GRAY, settings.GRAY, daylight_factor)
        for plat_rect_world in self.ground_platforms:
            shifted_rect_p_screen = plat_rect_world.move(int(current_scroll_gv), 0)
            if shifted_rect_p_screen.colliderect(screen.get_rect()):
                pygame.draw.rect(screen, platform_color, shifted_rect_p_screen)

        if self.landed_ship_rect:
             shifted_ship_r_screen = self.landed_ship_rect.move(int(current_scroll_gv), 0)
             if shifted_ship_r_screen.colliderect(screen.get_rect()):
                  ship_body_color = utils.lerp_color((100,100,100), settings.WHITE, daylight_factor)
                  ship_outline_color = utils.lerp_color(settings.DARK_GRAY, settings.GRAY, daylight_factor)
                  ship_pts_screen = [
                      (shifted_ship_r_screen.centerx, shifted_ship_r_screen.top),
                      (shifted_ship_r_screen.left, shifted_ship_r_screen.bottom - 15),
                      (shifted_ship_r_screen.centerx - 5, shifted_ship_r_screen.bottom - 15),
                      (shifted_ship_r_screen.centerx - 5, shifted_ship_r_screen.bottom),
                      (shifted_ship_r_screen.centerx + 5, shifted_ship_r_screen.bottom),
                      (shifted_ship_r_screen.centerx + 5, shifted_ship_r_screen.bottom - 15),
                      (shifted_ship_r_screen.right, shifted_ship_r_screen.bottom - 15)
                  ]
                  pygame.draw.polygon(screen, ship_body_color, ship_pts_screen)
                  pygame.draw.polygon(screen, ship_outline_color, ship_pts_screen, 2)

        self.player_char.draw(screen)

        region_name_gv = self.current_region_data.get('name', "Unknown Region")
        utils.draw_text(f"Region: {region_name_gv}", "main", settings.WHITE, screen, 10, 10)

        if self.landed_ship_rect and self.player_char.rect.colliderect(
            self.landed_ship_rect.move(int(current_scroll_gv),0)):
            prompt_rect_screen = self.landed_ship_rect.move(int(current_scroll_gv),0)
            utils.draw_text("Press [E] to board ship", "main", settings.YELLOW, screen, 
                            prompt_rect_screen.centerx - 100, prompt_rect_screen.top - 30)