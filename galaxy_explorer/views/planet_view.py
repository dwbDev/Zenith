# galaxy_explorer/views/planet_view.py
# -*- coding: utf-8 -*-
import pygame
import math
from .base_view import BaseView
from .. import settings
from ..core import utils # For assets and drawing functions

class PlanetView(BaseView): # For Planet Overhead View
    def __init__(self, game_context):
        super().__init__()
        self.game_context = game_context
        self.player_ship = game_context['player_ship']
        
        self.planet_data = None
        self.planet_overhead_texture = None
        self.texture_needs_update = True
        
        self.cached_original_ship_image_for_exit = None 
        self.hovered_region_idx = None

    def on_enter(self, params=None):
        current_planet_idx = self.game_context.get('current_planet_idx')
        current_star_system = self.game_context.get('current_star_system')

        self.hovered_region_idx = None 

        if current_star_system and current_planet_idx is not None and \
           0 <= current_planet_idx < len(current_star_system.planets):
            self.planet_data = current_star_system.planets[current_planet_idx]
            self.texture_needs_update = True 
        else:
            print(f"Error: Invalid planet index ({current_planet_idx}) or star system for PlanetView.")
            self.next_state_request = (settings.STAR_SYSTEM_VIEW, {}) # Fallback
            return

        if self.player_ship:
            self.cached_original_ship_image_for_exit = self.player_ship.image_orig
            
            original_width, original_height = self.cached_original_ship_image_for_exit.get_size()
            scaled_width, scaled_height = int(original_width * 1.5), int(original_height * 1.5)
            
            self.player_ship.image_orig = pygame.transform.scale(self.cached_original_ship_image_for_exit, (scaled_width, scaled_height))
            
            planet_center_y = settings.SCREEN_HEIGHT // 2
            planet_draw_radius = self.planet_data['radius'] * settings.PLANET_OVERHEAD_SCALE
            
            temp_rotated_image = pygame.transform.rotate(self.player_ship.image_orig, -90)
            ship_height_for_positioning = temp_rotated_image.get_height()

            ship_start_x = settings.SCREEN_WIDTH // 2
            ship_start_y = planet_center_y - planet_draw_radius - (ship_height_for_positioning / 2) - 30 

            self.player_ship.pos = pygame.Vector2(ship_start_x, ship_start_y)
            self.player_ship.angle = -90 
            self.player_ship.velocity = pygame.Vector2(0,0)

            self.player_ship.image = pygame.transform.rotate(self.player_ship.image_orig, self.player_ship.angle)
            self.player_ship.rect = self.player_ship.image.get_rect(center=self.player_ship.pos)
            self.player_ship.thrust_particles = []


    def handle_event(self, event, mouse_pos, keys_pressed):
        if not self.planet_data: return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_e: 
                if self.hovered_region_idx is not None:
                    self.next_state_request = (settings.GROUND_VIEW, {'region_idx': self.hovered_region_idx})

    def update(self, dt, mouse_pos, keys_pressed, frame_count):
        current_star_system = self.game_context.get('current_star_system')
        if not self.planet_data or not self.player_ship or not current_star_system:
            return

        current_star_system.update_orbits() 
        
        if self.texture_needs_update and self.planet_data: 
            self.planet_overhead_texture = utils.create_planet_texture(self.planet_data, settings.PLANET_OVERHEAD_SCALE)
            self.texture_needs_update = False
        
        self.player_ship.update(keys_pressed, mouse_pos, dt)

        ship_pos = self.player_ship.pos
        exited_screen = False
        if ship_pos.x == 0 or ship_pos.x == settings.SCREEN_WIDTH or \
           ship_pos.y == 0 or ship_pos.y == settings.SCREEN_HEIGHT:
            exited_screen = True
        
        if exited_screen:
            self.next_state_request = (
                settings.STAR_SYSTEM_VIEW, 
                {'from_planet_idx': self.game_context.get('current_planet_idx')}
            )
            return 

        self.hovered_region_idx = None
        planet_center_v = pygame.Vector2(settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT // 2)
        ship_pos_v = self.player_ship.pos 
        dist_from_center = ship_pos_v.distance_to(planet_center_v)
        planet_draw_radius_scaled = self.planet_data['radius'] * settings.PLANET_OVERHEAD_SCALE

        if dist_from_center < planet_draw_radius_scaled: 
            R_ccw_logical = self.planet_data['rotation_angle'] 
            ship_rel_v_screen = ship_pos_v - planet_center_v
            ship_rel_v_unrotated = ship_rel_v_screen.rotate(-R_ccw_logical) 
            ship_angle_on_texture = (math.degrees(math.atan2(ship_rel_v_unrotated.y, ship_rel_v_unrotated.x)) + 360) % 360

            for i, region in enumerate(self.planet_data['regions']):
                start_texture_angle = region['start_angle']
                end_texture_angle = region['end_angle']
                is_in_region = False

                if start_texture_angle <= end_texture_angle: 
                    if start_texture_angle <= ship_angle_on_texture < end_texture_angle:
                        is_in_region = True
                else: 
                    if ship_angle_on_texture >= start_texture_angle or \
                       ship_angle_on_texture < end_texture_angle:
                        is_in_region = True
                
                if is_in_region:
                    self.hovered_region_idx = i
                    break

    def render(self, screen, mouse_pos, frame_count): 
        screen.fill(settings.BLACK)
        utils.draw_twinkling_stars(screen, frame_count)

        if not self.planet_data:
            utils.draw_text("Error: No planet data loaded.", "main", settings.RED, screen, 100, 100)
            return

        planet_center = (settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT // 2)
        planet_draw_radius_scaled = self.planet_data['radius'] * settings.PLANET_OVERHEAD_SCALE
        
        utils.draw_planet_light_and_shadow(screen, planet_center, planet_draw_radius_scaled, self.planet_data['angle'])

        if self.planet_overhead_texture:
            R_ccw_logical = self.planet_data['rotation_angle']
            rotated_texture_surf = pygame.transform.rotate(self.planet_overhead_texture, -R_ccw_logical) 
            rotated_visual_rect = rotated_texture_surf.get_rect(center=planet_center)
            screen.blit(rotated_texture_surf, rotated_visual_rect)

            if self.hovered_region_idx is not None:
                hovered_region_data = self.planet_data['regions'][self.hovered_region_idx]
                
                highlight_surf_size = self.planet_overhead_texture.get_size()
                highlight_surf = pygame.Surface(highlight_surf_size, pygame.SRCALPHA)
                hs_center_x, hs_center_y = highlight_surf_size[0] // 2, highlight_surf_size[1] // 2
                
                radius_for_poly = planet_draw_radius_scaled 

                points_for_highlight = [(hs_center_x, hs_center_y)]
                
                start_angle_deg = hovered_region_data['start_angle']
                end_angle_deg = hovered_region_data['end_angle']
                
                angle_range_deg = (end_angle_deg - start_angle_deg + 360) % 360
                if angle_range_deg == 0 and len(self.planet_data['regions']) == 1: 
                    angle_range_deg = 360.0

                num_steps = max(5, int(angle_range_deg / 4)) 
                if num_steps == 0 and angle_range_deg > 0 : num_steps = 1

                for i_step in range(num_steps + 1):
                    angle_on_texture = start_angle_deg
                    if num_steps > 0: 
                        angle_on_texture = (start_angle_deg + (angle_range_deg * i_step / num_steps))
                    
                    angle_on_texture %= 360 
                    
                    px, py = utils.get_rotated_point(hs_center_x, hs_center_y, angle_on_texture, radius_for_poly)
                    points_for_highlight.append((px, py))

                if len(points_for_highlight) >= 3:
                    highlight_color = (settings.YELLOW[0], settings.YELLOW[1], settings.YELLOW[2], 100) 
                    pygame.draw.polygon(highlight_surf, highlight_color, points_for_highlight)

                rotated_highlight_surf = pygame.transform.rotate(highlight_surf, -R_ccw_logical)
                rotated_highlight_rect = rotated_highlight_surf.get_rect(center=planet_center)
                screen.blit(rotated_highlight_surf, rotated_highlight_rect)
        else:
            temp_planet_render_data = {'radius': int(planet_draw_radius_scaled),'color': self.planet_data.get('color', settings.GRAY)}
            utils.draw_shaded_planet_simple(screen, temp_planet_render_data, planet_center)
            utils.draw_text("Generating Texture...", "main", settings.YELLOW, screen, 
                            planet_center[0] - 100, planet_center[1] - 10)

        if self.player_ship:
            self.player_ship.draw_particles(screen)
            if self.player_ship.image: 
                 screen.blit(self.player_ship.image, self.player_ship.rect)

        # Draw Red 'X' over cursor if orientation is locked
        if self.player_ship and self.player_ship.orientation_locked:
            cursor_x_pos = mouse_pos[0]
            cursor_y_pos = mouse_pos[1]
            x_size = 10 
            line_width = 3
            
            pygame.draw.line(screen, settings.RED, 
                             (cursor_x_pos - x_size, cursor_y_pos - x_size), 
                             (cursor_x_pos + x_size, cursor_y_pos + x_size), line_width)
            pygame.draw.line(screen, settings.RED, 
                             (cursor_x_pos - x_size, cursor_y_pos + x_size), 
                             (cursor_x_pos + x_size, cursor_y_pos - x_size), line_width)

        utils.draw_text(f"Planet: {self.planet_data.get('name', 'Unnamed Planet')}", "main", settings.WHITE, screen, settings.SCREEN_WIDTH // 2 - 150, 10)

        if self.hovered_region_idx is not None:
            hovered_region = self.planet_data['regions'][self.hovered_region_idx]
            text_to_draw = f"Press [E] to land on {hovered_region['name']}"
            
            font = utils.assets.get_main_font() 
            if font:
                text_surf = font.render(text_to_draw, True, settings.YELLOW)
                text_rect = text_surf.get_rect(centerx=settings.SCREEN_WIDTH // 2, y=settings.SCREEN_HEIGHT - 70)
                screen.blit(text_surf, text_rect)
            else: 
                utils.draw_text(text_to_draw, "main", settings.YELLOW, screen, 
                                settings.SCREEN_WIDTH // 2 - 150, settings.SCREEN_HEIGHT - 70) 
        else:
            utils.draw_text("Fly over a region and press [E] to land. Fly off-screen to exit.", "small", settings.WHITE, screen,
                            settings.SCREEN_WIDTH // 2 - 200, settings.SCREEN_HEIGHT - 50) 


    def on_exit(self):
        if self.player_ship and self.cached_original_ship_image_for_exit:
            self.player_ship.image_orig = self.cached_original_ship_image_for_exit
            self.cached_original_ship_image_for_exit = None 

            self.player_ship.image = pygame.transform.rotate(self.player_ship.image_orig, self.player_ship.angle)
            self.player_ship.rect = self.player_ship.image.get_rect(center=self.player_ship.pos)
        
        self.planet_overhead_texture = None