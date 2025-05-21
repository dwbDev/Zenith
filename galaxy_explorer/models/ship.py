# -*- coding: utf-8 -*-
import pygame
import math
import random
import traceback
from .. import settings

class PlayerShip(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image_orig = pygame.Surface((30, 20), pygame.SRCALPHA)
        pygame.draw.polygon(self.image_orig, settings.WHITE, [(0, 0), (30, 10), (0, 20)])
        pygame.draw.rect(self.image_orig, settings.RED, (25, 8, 5, 4))
        self.image = self.image_orig
        self.rect = self.image.get_rect(center=(settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT // 2))
        self.pos = pygame.Vector2(self.rect.center)
        self.velocity = pygame.Vector2(0, 0)
        self.angle = 0
        self.max_speed = 5
        self.acceleration = 0.2
        self.strafe_acceleration = 0.15
        self.rotation_speed = 4
        self.thrust_particles = []
        self.orientation_locked = False # True if shift is held, ship won't orient to mouse

    def update(self, keys, mouse_pos, dt): # dt added for particles
        try:
            # Determine if orientation should be locked (Shift key pressed)
            self.orientation_locked = (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT])

            if not self.orientation_locked:
                dx_mouse = mouse_pos[0] - self.pos.x
                dy_mouse = mouse_pos[1] - self.pos.y
                target_angle = math.degrees(math.atan2(-dy_mouse, dx_mouse)) # Pygame y is inverted

                angle_diff = (target_angle - self.angle + 180) % 360 - 180
                if abs(angle_diff) < 0.5: # Snap if very close
                     self.angle = target_angle
                elif abs(angle_diff) <= self.rotation_speed:
                     self.angle = target_angle
                else:
                     self.angle += math.copysign(self.rotation_speed, angle_diff)
                self.angle %= 360
            # If orientation_locked is True, self.angle remains unchanged from the previous frame

            self.image = pygame.transform.rotate(self.image_orig, self.angle)
            self.rect = self.image.get_rect(center=self.pos)

            # Note: Pygame's rotation is clockwise for positive angles.
            # Vector2.rotate expects counter-clockwise.
            # If self.angle is visual (CW), then for vectors use -self.angle.
            forward = pygame.Vector2(1, 0).rotate(-self.angle)
            right = pygame.Vector2(0, -1).rotate(-self.angle) # Points out ship's left flank
            left = -right # Points out ship's right flank

            thrusting_forward = False
            strafing_left = False # Corresponds to 'd' key (ship moves to its own right)
            strafing_right = False # Corresponds to 'a' key (ship moves to its own left)

            accel_vec = pygame.Vector2(0, 0)
            if keys[pygame.K_w]:
                accel_vec += forward * self.acceleration
                thrusting_forward = True
            if keys[pygame.K_s]:
                accel_vec -= forward * self.acceleration * 0.7 # Slower reverse

            # Original: K_a for Strafe RIGHT (actual: ship moves its left), K_d for Strafe LEFT (actual: ship moves its right)
            if keys[pygame.K_a]: # Ship moves towards its own left
                accel_vec += right * self.strafe_acceleration
                strafing_right = True # Particle effect from right nozzle, pushing ship left
            if keys[pygame.K_d]: # Ship moves towards its own right
                accel_vec += left * self.strafe_acceleration
                strafing_left = True # Particle effect from left nozzle, pushing ship right


            self.velocity += accel_vec
            if self.velocity.length_squared() > self.max_speed**2:
                self.velocity.scale_to_length(self.max_speed)

            # Apply friction/drag if no thrust keys are pressed for that direction
            if not (thrusting_forward or keys[pygame.K_s] or strafing_left or strafing_right):
                 self.velocity *= 0.98 # General drag if no input

            self.pos += self.velocity

            # Screen wrapping
            if self.pos.x < 0: self.pos.x = settings.SCREEN_WIDTH
            if self.pos.x > settings.SCREEN_WIDTH: self.pos.x = 0
            if self.pos.y < 0: self.pos.y = settings.SCREEN_HEIGHT
            if self.pos.y > settings.SCREEN_HEIGHT: self.pos.y = 0
            self.rect.center = self.pos

            # Particle Update (using dt now)
            dt_particles = dt
            if thrusting_forward:
                nozzle_offset = pygame.Vector2(-15, 0).rotate(-self.angle) # Back of the ship
                particle_pos_base = self.pos + nozzle_offset
                particle_vel_base = -forward # Opposite to ship's forward
                for _ in range(2):
                    # Spread particles slightly and give them velocity away from nozzle
                    particle_vel = particle_vel_base.rotate(random.uniform(-15, 15)) * random.uniform(1.5, 3.0) * 60 # Scale speed
                    self.thrust_particles.append({
                        'pos': particle_pos_base + pygame.Vector2(random.uniform(-2,2), random.uniform(-2,2)),
                        'vel': particle_vel,
                        'life': random.uniform(0.3, 0.8),
                        'color': random.choice([settings.ORANGE, settings.YELLOW, settings.WHITE])
                    })

            if strafing_left: # 'd' key, ship moves right, thrust from left nozzle
                nozzle_offset = pygame.Vector2(5, -10).rotate(-self.angle) # Assumed left side nozzle (top-ish for triangle)
                particle_pos_base = self.pos + nozzle_offset
                particle_vel_base = right # Thrust is to the ship's right to move ship right
                for _ in range(1):
                    particle_vel = particle_vel_base.rotate(random.uniform(-20, 20)) * random.uniform(1.0, 2.0) * 60
                    self.thrust_particles.append({
                        'pos': particle_pos_base + pygame.Vector2(random.uniform(-1,1), random.uniform(-1,1)),
                        'vel': particle_vel,
                        'life': random.uniform(0.2, 0.5),
                        'color': settings.PARTICLE_COLOR
                    })
            if strafing_right: # 'a' key, ship moves left, thrust from right nozzle
                nozzle_offset = pygame.Vector2(5, 10).rotate(-self.angle) # Assumed right side nozzle (bottom-ish for triangle)
                particle_pos_base = self.pos + nozzle_offset
                particle_vel_base = left # Thrust is to the ship's left to move ship left
                for _ in range(1):
                    particle_vel = particle_vel_base.rotate(random.uniform(-20, 20)) * random.uniform(1.0, 2.0) * 60
                    self.thrust_particles.append({
                        'pos': particle_pos_base + pygame.Vector2(random.uniform(-1,1), random.uniform(-1,1)),
                        'vel': particle_vel,
                        'life': random.uniform(0.2, 0.5),
                        'color': settings.PARTICLE_COLOR
                    })


            new_particles = []
            for p in self.thrust_particles:
                p['pos'] += p['vel'] * dt_particles
                p['life'] -= dt_particles
                if p['life'] > 0:
                    new_particles.append(p)
            self.thrust_particles = new_particles

        except Exception as e:
            print(f"Error in PlayerShip update: {e}")
            traceback.print_exc()

    def draw_particles(self, surface):
         for p in self.thrust_particles:
             size = max(1, int(p['life'] * 4 + 1)) # Size based on remaining life
             pygame.draw.circle(surface, p['color'], p['pos'], size)

    def reset_position(self, current_star_system): # Takes current_star_system now
        if current_star_system:
            safe_dist = current_star_system.star_radius + 100
            start_pos = pygame.Vector2(settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT // 2 + safe_dist)

            # Ensure not spawning on jump gate
            gate_rect = pygame.Rect(0, 0, 60, 80)
            gate_rect.center = current_star_system.jump_gate_pos
            attempts = 0
            while gate_rect.collidepoint(start_pos) and attempts < 20:
                start_pos.y += 20 # Move further down if colliding
                attempts += 1

            self.pos = start_pos
        else: # Fallback if no system info
            self.pos = pygame.Vector2(settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT - 150)

        self.velocity = pygame.Vector2(0, 0)
        self.angle = -90 # Pointing "up"
        self.rect.center = self.pos
        self.orientation_locked = False # Reset this state too