# galaxy_explorer/views/hyperspace_view.py
# -*- coding: utf-8 -*-
import pygame
import math
import random
from .base_view import BaseView
from .. import settings
from ..core import utils

class HyperspaceView(BaseView):
    def __init__(self, game_context, target_system_idx):
        super().__init__()
        self.game_context = game_context
        self.target_system_idx = target_system_idx
        self.hyperspace_timer = 0

    def on_enter(self, params=None):
        self.hyperspace_timer = 0
        # target_system_idx is set at __init__ or can be overridden if passed in params
        if params and 'target_system_idx' in params: 
            self.target_system_idx = params['target_system_idx']

    def update(self, dt, mouse_pos, keys_pressed, frame_count):
        self.hyperspace_timer += 1
        if self.hyperspace_timer >= settings.HYPERSPACE_DURATION:
            if self.target_system_idx is not None and \
               0 <= self.target_system_idx < len(self.game_context['star_systems']):
                self.next_state_request = (settings.STAR_SYSTEM_VIEW, 
                                           {
                                               'system_idx': self.target_system_idx, 
                                               'reset_ship': True, # General reset flag for ship's state
                                               'from_hyperspace': True # Specific flag for positioning
                                           })
            else:
                # Fallback if target system is invalid
                self.next_state_request = (settings.GALAXY_VIEW, {})
    
    def render(self, screen, mouse_pos, frame_count): # MODIFIED: Signature matches BaseView
        screen.fill(settings.BLACK)
        
        progress = self.hyperspace_timer / settings.HYPERSPACE_DURATION
        anim_progress = (1 - math.cos(progress * math.pi)) / 2 

        overlay_alpha = int(math.sin(progress * math.pi) * 150)
        overlay = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, overlay_alpha))
        
        center_v = pygame.Vector2(settings.SCREEN_WIDTH / 2, settings.SCREEN_HEIGHT / 2)

        for _ in range(150):
            start_offset_factor = (1 - anim_progress)
            angle = random.uniform(0, 360)
            direction = pygame.Vector2(1,0).rotate(angle)
            # Ensure start_dist_from_center doesn't become negative if anim_progress > 1 (it shouldn't)
            start_dist_from_center = max(0, start_offset_factor * random.uniform(0, settings.SCREEN_WIDTH*0.1))
            start_pos = center_v + direction * start_dist_from_center
            current_length = anim_progress * settings.SCREEN_WIDTH * 1.5 * random.uniform(0.1, 1.0)
            
            if current_length > 2:
                end_pos = start_pos + direction * current_length
                line_width = int(anim_progress * 3 + 1)
                # Ensure line_width is at least 1 if anim_progress is very small
                line_width = max(1, line_width) 
                line_color = random.choice([settings.WHITE, settings.LIGHT_BLUE, (200,200,255)])
                pygame.draw.line(screen, line_color, start_pos, end_pos, line_width)
        
        screen.blit(overlay, (0,0))
        
        utils.draw_text("HYPERSPACE TRAVEL", "main", settings.WHITE, screen, 
                        settings.SCREEN_WIDTH // 2 - 100, settings.SCREEN_HEIGHT // 2 - 20)