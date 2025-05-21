# -*- coding: utf-8 -*-
import pygame

class BaseView:
    def __init__(self):
        self.next_state_request = None  # Tuple: (STATE_NAME_CONSTANT, params_dict)

    def handle_event(self, event, mouse_pos, keys_pressed):
        """Handles a single Pygame event."""
        pass

    def update(self, dt, mouse_pos, keys_pressed, frame_count):
        """Updates the view's logic. dt is delta time in seconds."""
        pass

    def render(self, screen, mouse_pos, frame_count): # MODIFIED: Added mouse_pos
        """Renders the view to the screen."""
        pass
    
    def on_enter(self, params=None):
        """Called when this view becomes active. Params are from the transition."""
        pass

    def on_exit(self):
        """Called when this view is being exited."""
        pass