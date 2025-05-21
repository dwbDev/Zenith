# File: galaxy_explorer/views/galaxy_view.py
# -*- coding: utf-8 -*-
import pygame
from .base_view import BaseView
from .. import settings
from ..core import utils

class GalaxyView(BaseView):
    def __init__(self, game_context):
        super().__init__()
        self.game_context = game_context
        self.star_systems_data = game_context['star_systems']
        self.galaxy_zoom_target = None

    def handle_event(self, event, mouse_pos, keys_pressed):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: # Left click
            for i, system_data in enumerate(self.star_systems_data):
                if self.galaxy_zoom_target is None and \
                   system_data.galaxy_pos.distance_to(pygame.Vector2(mouse_pos)) < 15:
                    
                    if i == self.game_context['current_star_system_idx']:
                        # MODIFIED: Pass 'from_galaxy_map_entry' instead of 'reset_ship'
                        # This ensures the ship is positioned at the jump gate.
                        self.next_state_request = (settings.STAR_SYSTEM_VIEW, 
                                                   {'system_idx': i, 'from_galaxy_map_entry': True})
                    else:
                        # This path goes through HyperspaceView, which correctly sets 'from_hyperspace: True'
                        self.galaxy_zoom_target = i
                        self.next_state_request = (settings.HYPERSPACE_TRANSITION, {'target_system_idx': i})
                    break

    def update(self, dt, mouse_pos, keys_pressed, frame_count):
        pass

    def render(self, screen, mouse_pos, frame_count): # MODIFIED: Signature matches BaseView
        screen.fill(settings.BLACK)
        utils.draw_text("GALAXY MAP", "main", settings.WHITE, screen, 10, 10)
        
        mouse_pos_vec = pygame.Vector2(mouse_pos) # mouse_pos is now correctly passed
        mouse_on_system_idx = -1

        for i, system_data in enumerate(self.star_systems_data):
            color = system_data.star_color
            radius = 8
            is_current = (i == self.game_context['current_star_system_idx'])
            is_hover = False

            if self.galaxy_zoom_target is None and system_data.galaxy_pos.distance_to(mouse_pos_vec) < 15:
                radius = 14
                mouse_on_system_idx = i
                is_hover = True
            
            if is_current:
                pygame.draw.circle(screen, settings.GREEN, system_data.galaxy_pos, radius + 6, 3)
            
            pygame.draw.circle(screen, color, system_data.galaxy_pos, radius)
            
            if is_hover:
                pygame.draw.circle(screen, settings.WHITE, system_data.galaxy_pos, radius // 2)

        if mouse_on_system_idx != -1:
            system_name = self.star_systems_data[mouse_on_system_idx].name
            utils.draw_text(system_name, "small", settings.WHITE, screen, mouse_pos[0] + 15, mouse_pos[1])
        
        current_system_name = self.game_context['current_star_system'].name
        utils.draw_text(f"Current: {current_system_name}", "main", settings.GREEN, screen, 10, settings.SCREEN_HEIGHT - 40)