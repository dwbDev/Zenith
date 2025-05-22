# -*- coding: utf-8 -*-
import pygame
import sys
import traceback

from . import settings
from .core import assets, utils
from .models.world import StarSystem
from .models.ship import PlayerShip
from .models.player_char import PlayerCharacter
from .views.galaxy_view import GalaxyView
from .views.star_system_view import StarSystemView
from .views.planet_view import PlanetView
from .views.ground_view import GroundView
from .views.hyperspace_view import HyperspaceView


class Game:
    def __init__(self):
        print("Initializing Pygame...")
        try:
            pygame.init()
            print("Pygame Initialized.")
        except Exception as e:
            print(f"!!!!!!!!!!!!!!!!! Pygame Init Failed: {e} !!!!!!!!!!!!!!!!!")
            traceback.print_exc()
            sys.exit()

        print("Initializing Font Module via core.assets...")
        if not assets.load_fonts():
             pass

        print("Setting Display Mode...")
        try:
            self.screen = pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
            pygame.display.set_caption("Galaxy Explorer")
            print("Display Mode Set.")
        except Exception as e:
            print(f"!!!!!!!!!!!!!!!!! Pygame Set Mode Failed: {e} !!!!!!!!!!!!!!!!!")
            traceback.print_exc()
            pygame.quit()
            sys.exit()

        print("Setting up Clock...")
        self.clock = pygame.time.Clock()
        print("Clock Setup.")

        self.running = True
        self.frame_count = 0

        print("Initializing Game Context...")
        self.game_context = {
            'player_ship': PlayerShip(),
            'player_char': PlayerCharacter(),
            'star_systems': self._generate_star_systems(),
            'current_star_system_idx': 0,
            'current_planet_idx': None,
            'current_region_idx': None,
        }
        self.game_context['current_star_system'] = \
            self.game_context['star_systems'][self.game_context['current_star_system_idx']]
        print("Game Context Initialized.")

        print("Setting initial game view...")
        self.current_view = GalaxyView(self.game_context)
        self.current_view.on_enter()
        print(f"Initial view set to: {type(self.current_view).__name__}")


    def _generate_star_systems(self):
        print("Creating Star Systems...")
        try:
            systems = [
                StarSystem("Solara Prime", (150, 200), settings.YELLOW, 4),
                StarSystem("Cygnus X-1", (600, 150), settings.BLUE, 2),
                StarSystem("Kepler-186f System", (300, 500), settings.RED, 5),
                StarSystem("Andromeda Gateway", (700, 450), settings.WHITE, 3),
                StarSystem("Nebula Core", (450, 300), settings.PURPLE, 6),
            ]
            print(f"Star Systems Created ({len(systems)} systems).")
            return systems
        except Exception as e:
            print(f"!!!!!!!!!!!!!!!!! Error Creating Star Systems: {e} !!!!!!!!!!!!!!!!!")
            traceback.print_exc()
            pygame.quit()
            sys.exit()

    def _handle_intro_events(self):
        """Handle events during the intro. Returns True if intro should be skipped."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return True
        return False

    def play_intro(self, fade_in_time=1.5, fade_out_time=1.5, game_fade_in_time=1.5, triangle_time=1.0):
        """Display a starting intro with optional fade durations and intro music."""
        fade_in_frames = int(fade_in_time * settings.FPS)
        fade_out_frames = int(fade_out_time * settings.FPS)
        game_fade_frames = int(game_fade_in_time * settings.FPS)
        triangle_frames = int(triangle_time * settings.FPS)

        # Attempt to play the intro music if available
        try:
            pygame.mixer.music.load("intro.mp3")
            pygame.mixer.music.play()
        except Exception as e:
            print(f"Failed to play intro music: {e}")

        big_font = pygame.font.SysFont(None, 120)
        text_surf = big_font.render("Zenith", True, settings.WHITE).convert_alpha()
        text_rect = text_surf.get_rect(center=(settings.SCREEN_WIDTH // 2,
                                              settings.SCREEN_HEIGHT // 2))

        triangle_size = min(settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT) // 2
        center = (settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT // 2)

        for i in range(triangle_frames):
            if self._handle_intro_events():
                pygame.mixer.music.stop()
                return
            alpha = int(255 * (i / triangle_frames))
            self.screen.fill(settings.BLACK)
            utils.draw_shiny_triangle(self.screen, center, triangle_size,
                                      i / triangle_frames, alpha)
            pygame.display.flip()
            self.clock.tick(settings.FPS)

        for i in range(fade_in_frames):
            if self._handle_intro_events():
                pygame.mixer.music.stop()
                return
            alpha = int(255 * (i / fade_in_frames))
            tri_alpha = int(255 * (1 - i / fade_in_frames))
            text_surf.set_alpha(alpha)
            self.screen.fill(settings.BLACK)
            utils.draw_shiny_triangle(self.screen, center, triangle_size,
                                      i / fade_in_frames, tri_alpha)
            self.screen.blit(text_surf, text_rect)
            pygame.display.flip()
            self.clock.tick(settings.FPS)

        for i in range(fade_out_frames):
            if self._handle_intro_events():
                pygame.mixer.music.stop()
                return
            alpha = int(255 * (1 - i / fade_out_frames))
            text_surf.set_alpha(alpha)
            self.screen.fill(settings.BLACK)
            self.screen.blit(text_surf, text_rect)
            pygame.display.flip()
            self.clock.tick(settings.FPS)

        overlay = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
        overlay.fill(settings.BLACK)
        for i in range(game_fade_frames):
            if self._handle_intro_events():
                pygame.mixer.music.stop()
                return
            if self.current_view:
                self.current_view.update(0, pygame.mouse.get_pos(),
                                        pygame.key.get_pressed(), self.frame_count)
                self.current_view.render(self.screen, pygame.mouse.get_pos(),
                                         self.frame_count)
            alpha = int(255 * (1 - i / game_fade_frames))
            overlay.set_alpha(alpha)
            self.screen.blit(overlay, (0, 0))
            pygame.display.flip()
            self.clock.tick(settings.FPS)
            self.frame_count += 1

        pygame.mixer.music.stop()

    def run(self):
        self.play_intro()
        print("Entering Main Game Loop...")
        while self.running:
            dt = self.clock.tick(settings.FPS) / 1000.0
            self.frame_count += 1
            
            mouse_pos = pygame.mouse.get_pos()
            keys_pressed = pygame.key.get_pressed()

            try:
                events = pygame.event.get()
                for event in events:
                    if event.type == pygame.QUIT:
                        self.running = False
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self.running = False
                    
                    if self.current_view:
                        self.current_view.handle_event(event, mouse_pos, keys_pressed)
            except Exception as e:
                print(f"Event Handling Error: {e}"); traceback.print_exc(); self.running = False

            try:
                if self.current_view:
                    self.current_view.update(dt, mouse_pos, keys_pressed, self.frame_count)
            except Exception as e:
                print(f"Update Logic Error ({type(self.current_view).__name__}): {e}"); traceback.print_exc(); self.running = False

            try:
                if self.current_view:
                    self.current_view.render(self.screen, mouse_pos, self.frame_count) # MODIFIED: Passed mouse_pos
                pygame.display.flip()
            except Exception as e:
                print(f"Drawing/Flip Error ({type(self.current_view).__name__}): {e}"); traceback.print_exc(); self.running = False

            if self.current_view and self.current_view.next_state_request:
                next_state_name, params = self.current_view.next_state_request
                self.current_view.next_state_request = None
                self.transition_to_state(next_state_name, params)
        
        print("Exiting game loop.")
        pygame.quit()
        print("Pygame quit successfully.")
        sys.exit()

    def transition_to_state(self, next_state_name, params):
        if self.current_view:
            self.current_view.on_exit()

        print(f"Transitioning from {type(self.current_view).__name__} to {next_state_name} with params {params}")

        if 'system_idx' in params and (next_state_name == settings.STAR_SYSTEM_VIEW):
            self.game_context['current_star_system_idx'] = params['system_idx']
            self.game_context['current_star_system'] = \
                self.game_context['star_systems'][params['system_idx']]
        
        if 'planet_idx' in params and (next_state_name == settings.PLANET_OVERHEAD_VIEW): # Removed ground view from this condition as it gets it from context
             self.game_context['current_planet_idx'] = params['planet_idx']
        
        if 'region_idx' in params and next_state_name == settings.GROUND_VIEW:
            self.game_context['current_region_idx'] = params['region_idx']

        if next_state_name == settings.GALAXY_VIEW:
            self.current_view = GalaxyView(self.game_context)
        elif next_state_name == settings.STAR_SYSTEM_VIEW:
            self.current_view = StarSystemView(self.game_context)
        elif next_state_name == settings.PLANET_OVERHEAD_VIEW:
            self.current_view = PlanetView(self.game_context)
        elif next_state_name == settings.GROUND_VIEW:
            self.current_view = GroundView(self.game_context)
        elif next_state_name == settings.HYPERSPACE_TRANSITION:
            target_idx = params.get('target_system_idx')
            self.current_view = HyperspaceView(self.game_context, target_idx)
        else:
            print(f"Error: Unknown state name '{next_state_name}' for transition.")
            self.current_view = GalaxyView(self.game_context)

        if self.current_view:
            self.current_view.on_enter(params)
        print(f"Transition complete. Current view: {type(self.current_view).__name__}")

if __name__ == '__main__':
    game = Game()
    game.run()