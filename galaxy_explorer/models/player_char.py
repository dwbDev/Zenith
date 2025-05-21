# -*- coding: utf-8 -*-
import pygame
import traceback
from .. import settings

class PlayerCharacter(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        try:
            self.image = pygame.Surface((20, 40))
            self.image.fill(settings.GREEN)
            self.rect = self.image.get_rect(center=(settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT - 100))
        except Exception as e:
            print(f"Error creating PlayerCharacter surface/rect: {e}")
            self.image = None
            self.rect = pygame.Rect(0,0,1,1) # Placeholder
        
        self.pos = pygame.Vector2(self.rect.center)
        self.velocity = pygame.Vector2(0, 0)
        self.speed = 4
        self.jump_power = -12
        self.gravity = 0.6
        self.on_ground = False
        self.world_scroll = 0 # How much the world has scrolled left (player moved right)
        self.scroll_threshold = 250 # Screen x-pos where scrolling starts/stops

    def update(self, keys, platforms, landed_ship_rect): # dt is not used here, movement is frame-based
        if not self.image: return False # Cannot update if image failed to load

        try:
            dx = 0 # Change in world position
            if keys[pygame.K_a]: dx = -self.speed
            if keys[pygame.K_d]: dx = self.speed

            # Vertical movement
            self.velocity.y += self.gravity
            if self.velocity.y > 10: self.velocity.y = 10 # Terminal velocity

            if keys[pygame.K_SPACE] and self.on_ground:
                self.velocity.y = self.jump_power
                self.on_ground = False

            # Apply vertical movement and check for ground collision
            self.pos.y += self.velocity.y
            self.rect.centery = int(self.pos.y)
            self.on_ground = False # Assume not on ground until collision check

            ground_level = settings.SCREEN_HEIGHT - 50 # Bottom of the screen ground
            if self.rect.bottom > ground_level:
                self.rect.bottom = ground_level
                self.pos.y = self.rect.centery
                self.velocity.y = 0
                self.on_ground = True

            # Platform collision (vertical)
            # Platforms are in world coordinates, rect is in screen coordinates
            # Player's rect.x is self.pos.x + self.world_scroll
            # Player's rect.y is self.pos.y
            
            # Create a temporary rect for the player in world coordinates for collision
            player_world_rect_vertical_check = pygame.Rect(self.pos.x - self.rect.width / 2, self.rect.top, self.rect.width, self.rect.height)

            for plat_rect_world in platforms:
                if player_world_rect_vertical_check.colliderect(plat_rect_world):
                    # Check if landing on top
                    if self.velocity.y >= 0: # Moving down or still
                        # Check if player was above platform in previous frame (approx)
                        prev_bottom_approx = self.pos.y + self.rect.height/2 - self.velocity.y
                        if prev_bottom_approx <= plat_rect_world.top + 1 and self.rect.bottom >= plat_rect_world.top :
                             self.rect.bottom = plat_rect_world.top
                             self.pos.y = self.rect.centery
                             self.velocity.y = 0
                             self.on_ground = True
                             break 
                    # Check if hitting underside
                    elif self.velocity.y < 0: # Moving up
                        prev_top_approx = self.pos.y - self.rect.height/2 - self.velocity.y
                        if prev_top_approx >= plat_rect_world.bottom -1 and self.rect.top <= plat_rect_world.bottom :
                            self.rect.top = plat_rect_world.bottom
                            self.pos.y = self.rect.centery
                            self.velocity.y = 0 # Stop upward movement
                            break
            
            # Horizontal movement and scrolling
            scroll_change = 0
            next_world_x = self.pos.x + dx 
            
            # Player's potential screen position if they move and world doesn't scroll
            potential_screen_x = next_world_x + self.world_scroll 

            if dx > 0 and potential_screen_x > settings.SCREEN_WIDTH - self.scroll_threshold:
                # Player moves right, world scrolls left
                scroll_change = (settings.SCREEN_WIDTH - self.scroll_threshold) - potential_screen_x
            elif dx < 0 and potential_screen_x < self.scroll_threshold:
                # Player moves left, world scrolls right
                scroll_change = self.scroll_threshold - potential_screen_x
            
            self.pos.x = next_world_x
            self.world_scroll += scroll_change
            self.rect.centerx = int(self.pos.x + self.world_scroll) # Update screen rect x

            # Platform collision (horizontal)
            # Player's rect is now updated for screen position after horizontal move & scroll
            player_screen_rect_horizontal_check = self.rect.inflate(2,-4) # Slightly wider, shorter rect for side collision

            for plat_rect_world in platforms:
                plat_screen_rect = plat_rect_world.move(self.world_scroll, 0)
                if player_screen_rect_horizontal_check.colliderect(plat_screen_rect):
                    # Check vertical overlap to ensure it's a side collision, not top/bottom
                    vertical_overlap = min(self.rect.bottom, plat_screen_rect.bottom) - max(self.rect.top, plat_screen_rect.top)
                    if vertical_overlap > 5: # Must overlap sufficiently vertically
                        if dx > 0 and self.rect.right > plat_screen_rect.left: # Moving right, collided with left side of platform
                            self.rect.right = plat_screen_rect.left
                            self.pos.x = self.rect.centerx - self.world_scroll # Update world pos based on collision
                            # self.velocity.x = 0 # If you had x velocity
                            break
                        elif dx < 0 and self.rect.left < plat_screen_rect.right: # Moving left, collided with right side
                            self.rect.left = plat_screen_rect.right
                            self.pos.x = self.rect.centerx - self.world_scroll
                            # self.velocity.x = 0
                            break
            
            can_enter_ship = False
            if landed_ship_rect: # landed_ship_rect is in world coordinates
                shifted_ship_rect_screen = landed_ship_rect.move(self.world_scroll, 0)
                if self.rect.colliderect(shifted_ship_rect_screen):
                    can_enter_ship = True
            
            return can_enter_ship # Return whether player can enter ship

        except Exception as e:
            print(f"Error in PlayerCharacter update: {e}")
            traceback.print_exc()
            return False


    def draw(self, surface):
        if self.image:
            surface.blit(self.image, self.rect)

    def reset_position(self):
        # Initial screen position when landing/starting ground view
        initial_screen_x = self.scroll_threshold + 10 
        
        # World_scroll will be 0 initially. Player's world x = screen x.
        self.world_scroll = 0 
        self.pos = pygame.Vector2(initial_screen_x, settings.SCREEN_HEIGHT - 100) # Player's pos in world coords
        
        self.velocity = pygame.Vector2(0, 0)
        if self.image:
            self.rect.center = (int(self.pos.x + self.world_scroll), int(self.pos.y))
        self.on_ground = False