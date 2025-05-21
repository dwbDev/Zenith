# File: galaxy_explorer/views/star_system_view.py
# -*- coding: utf-8 -*-
import pygame
from .base_view import BaseView
from .. import settings
from ..core import utils

class StarSystemView(BaseView):
    def __init__(self, game_context):
        super().__init__()
        self.game_context = game_context
        self.player_ship = game_context['player_ship']
        self.current_star_system = game_context['current_star_system'] # Initial sync
        
        self.hovered_planet_idx = None
        self.hovered_gate = False
        
        # View-specific flags for on_enter logic
        self._entered_once_flag_sv = False 
        self._last_system_name_viewed_sv = None

    def on_enter(self, params=None):
        # Ensure current_star_system is up-to-date from game_context at the moment of entry
        self.current_star_system = self.game_context['current_star_system']
        
        self.hovered_planet_idx = None
        self.hovered_gate = False
        if self.player_ship: # Ensure player_ship exists
            self.player_ship.thrust_particles = [] # Clear particles on view entry

        should_do_default_reset = False
        positioned_specifically = False

        if params and self.player_ship: # Only proceed if params and player_ship exist
            # MODIFIED: Check for 'from_hyperspace' OR 'from_galaxy_map_entry'
            # Both indicate arrival at the system's jump gate.
            arriving_at_jump_gate = params.get('from_hyperspace') or params.get('from_galaxy_map_entry')

            if arriving_at_jump_gate:
                # Position ship at the jump gate
                gate_pos = self.current_star_system.jump_gate_pos
                self.player_ship.pos = pygame.Vector2(gate_pos)
                self.player_ship.velocity = pygame.Vector2(0, 0)
                self.player_ship.angle = -90 # Pointing "up" screen
                # Force immediate update of image and rect for first render
                self.player_ship.image = pygame.transform.rotate(self.player_ship.image_orig, self.player_ship.angle)
                self.player_ship.rect = self.player_ship.image.get_rect(center=self.player_ship.pos)
                positioned_specifically = True

            elif 'from_planet_idx' in params:
                # Arriving from a planet
                planet_idx = params['from_planet_idx']
                if 0 <= planet_idx < len(self.current_star_system.planets):
                    planet_data = self.current_star_system.planets[planet_idx]
                    planet_screen_pos_tuple = self.current_star_system.get_planet_position(planet_idx)
                    planet_screen_pos = pygame.Vector2(planet_screen_pos_tuple)
                    
                    offset_distance = planet_data['radius'] + (self.player_ship.rect.height / 2) + 20 # 20px gap
                    self.player_ship.pos = pygame.Vector2(planet_screen_pos.x, planet_screen_pos.y - offset_distance)
                    
                    self.player_ship.velocity = pygame.Vector2(0, 0)
                    self.player_ship.angle = -90 # Pointing "up" screen
                    self.player_ship.image = pygame.transform.rotate(self.player_ship.image_orig, self.player_ship.angle)
                    self.player_ship.rect = self.player_ship.image.get_rect(center=self.player_ship.pos)
                    positioned_specifically = True
                else:
                    should_do_default_reset = True # Fallback if planet_idx is bad
            
            if not positioned_specifically and params.get('reset_ship', False):
                should_do_default_reset = True

        if not positioned_specifically:
            if not self._entered_once_flag_sv or \
               (self._last_system_name_viewed_sv is not None and self._last_system_name_viewed_sv != self.current_star_system.name):
                should_do_default_reset = True
        
        if self.player_ship:
            if should_do_default_reset and not positioned_specifically :
                self.player_ship.reset_position(self.current_star_system)
            elif not positioned_specifically and not should_do_default_reset:
                self.player_ship.image = pygame.transform.rotate(self.player_ship.image_orig, self.player_ship.angle)
                self.player_ship.rect = self.player_ship.image.get_rect(center=self.player_ship.pos)

        self._last_system_name_viewed_sv = self.current_star_system.name
        self._entered_once_flag_sv = True

    def handle_event(self, event, mouse_pos, keys_pressed):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
            if self.hovered_planet_idx is not None:
                self.next_state_request = (settings.PLANET_OVERHEAD_VIEW, {'planet_idx': self.hovered_planet_idx})
            elif self.hovered_gate:
                self.next_state_request = (settings.GALAXY_VIEW, {})

    def update(self, dt, mouse_pos, keys_pressed, frame_count):
        if not self.player_ship or not self.current_star_system : return

        self.player_ship.update(keys_pressed, mouse_pos, dt)
        self.current_star_system.update_orbits()

        self.hovered_planet_idx = None
        self.hovered_gate = False

        ship_rect = self.player_ship.rect 

        for i, planet_data in enumerate(self.current_star_system.planets):
            planet_pos_vec = pygame.Vector2(self.current_star_system.get_planet_position(i))
            dist_sq = self.player_ship.pos.distance_squared_to(planet_pos_vec)
            hover_radius = planet_data['radius'] + max(ship_rect.width, ship_rect.height) / 1.5 + 10
            if dist_sq < hover_radius**2:
                self.hovered_planet_idx = i
                break 

        if self.hovered_planet_idx is None:
            gate_interaction_rect = pygame.Rect(0,0,40,60) 
            gate_interaction_rect.center = self.current_star_system.jump_gate_pos
            if ship_rect.colliderect(gate_interaction_rect):
                self.hovered_gate = True

    def render(self, screen, mouse_pos, frame_count):
        if not self.current_star_system: 
            screen.fill(settings.BLACK)
            utils.draw_text("Error: No star system data.", "main", settings.RED, screen, 100, 100)
            return

        screen.fill(settings.BLACK)
        utils.draw_twinkling_stars(screen, frame_count)
        
        star_center_pos = (settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT // 2)
        
        star_render_data = {
            'radius': self.current_star_system.star_radius,
            'color': self.current_star_system.star_color
        }
        utils.draw_shaded_planet_simple(screen, star_render_data, star_center_pos)
        
        star_glow_radius = int(self.current_star_system.star_radius * 1.5)
        if star_glow_radius > 0:
            star_glow_surf = pygame.Surface((star_glow_radius * 2, star_glow_radius * 2), pygame.SRCALPHA)
            for i_glow in range(star_glow_radius, 0, -2):
                t = i_glow / star_glow_radius 
                alpha_factor = (1 - t**0.5) 
                alpha = int(120 * alpha_factor) 
                alpha = max(0, min(255, alpha))
                glow_edge_color = utils.lerp_color(self.current_star_system.star_color, settings.WHITE, 0.3)
                current_glow_color = utils.lerp_color(self.current_star_system.star_color, glow_edge_color, 1 - (i_glow / star_glow_radius))
                pygame.draw.circle(star_glow_surf, (*current_glow_color, alpha),
                                   (star_glow_radius, star_glow_radius), i_glow)
            screen.blit(star_glow_surf, 
                        (star_center_pos[0] - star_glow_radius, star_center_pos[1] - star_glow_radius),
                        special_flags=pygame.BLEND_RGBA_ADD)

        for i, planet_data in enumerate(self.current_star_system.planets):
            planet_pos = self.current_star_system.get_planet_position(i)
            pygame.draw.circle(screen, settings.DARK_GRAY, star_center_pos, 
                               planet_data['orbit_radius'], 1) 
            
            is_hovered = (i == self.hovered_planet_idx)
            if is_hovered: 
                pygame.draw.circle(screen, settings.YELLOW, planet_pos, planet_data['radius'] + 7, 3)
            
            utils.draw_shaded_planet_simple(screen, planet_data, planet_pos)

        gate_render_rect = pygame.Rect(0,0,40,60)
        gate_render_rect.center = self.current_star_system.jump_gate_pos
        
        gate_color = settings.PURPLE
        outline_color = settings.WHITE
        if self.hovered_gate: 
            gate_color = settings.LIGHT_BLUE 
            outline_color = settings.YELLOW
            pygame.draw.rect(screen, outline_color, gate_render_rect.inflate(6,6), 3) 

        pygame.draw.rect(screen, gate_color, gate_render_rect)
        pygame.draw.rect(screen, outline_color, gate_render_rect, 2)
        utils.draw_text("EXIT", "small", settings.WHITE, screen, 
                        gate_render_rect.centerx - 15, gate_render_rect.centery - 8)

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

        utils.draw_text(f"System: {self.current_star_system.name}", "main", settings.WHITE, screen, 10, 10)

        if self.hovered_planet_idx is not None or self.hovered_gate:
            utils.draw_text("Press [E] to interact", "small", settings.YELLOW, screen, 
                            settings.SCREEN_WIDTH // 2 - 70, settings.SCREEN_HEIGHT - 30)