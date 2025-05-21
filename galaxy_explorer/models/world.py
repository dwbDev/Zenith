# galaxy_explorer/models/world.py
# -*- coding: utf-8 -*-
import pygame
import math
import random
from .. import settings
from ..core import utils

class StarSystem:
    def __init__(self, name, galaxy_pos, star_color, num_planets):
        self.name = name
        self.galaxy_pos = pygame.Vector2(galaxy_pos)
        self.star_color = star_color
        # MODIFIED: Star radius made smaller
        self.star_radius = random.randint(30, 45) 
        self.planets = []

        attempts = 0
        max_attempts_gate = 500
        center_v = pygame.Vector2(settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT // 2)
        
        # Jump Gate Position
        self.jump_gate_pos = pygame.Vector2(random.randint(100, settings.SCREEN_WIDTH - 100),
                                            random.randint(100, settings.SCREEN_HEIGHT - 100))
        
        min_dist_from_star_for_gate = self.star_radius + 280 # Increased slightly due to potentially larger orbits
        
        gate_placement_attempts = 0
        while self.jump_gate_pos.distance_to(center_v) < min_dist_from_star_for_gate and gate_placement_attempts < 100:
            self.jump_gate_pos = pygame.Vector2(random.randint(100, settings.SCREEN_WIDTH - 100),
                                              random.randint(100, settings.SCREEN_HEIGHT - 100))
            gate_placement_attempts += 1
        if gate_placement_attempts >= 100:
             print(f"  Warning: Could not place jump gate optimally for {name}. Using last position.")


        used_radii = {self.star_radius} 
        # MODIFIED: min_orbit increased for larger average orbital radius
        min_orbit = self.star_radius + 90  # Was star_radius + 50
        max_orbit = min(settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT // 2) - 40 # Slightly reduce max orbit to keep planets well on screen
        
        # MODIFIED: planet_separation increased
        planet_separation = 60 # Was 50 

        available_orbit_space = max_orbit - min_orbit
        max_possible_planets = max(0, int(available_orbit_space / planet_separation)) if planet_separation > 0 else 0
        
        num_planets_to_create = min(num_planets, max_possible_planets)
        if num_planets_to_create == 0 and max_possible_planets > 0 and num_planets > 0: 
            num_planets_to_create = 1 
        elif max_possible_planets <= 0: # Use <= 0 to catch cases where available_orbit_space is negative
            if num_planets > 0 : # Only print warning if planets were requested
                print(f"  Warning: No possible orbit range for {name} (min_orbit: {min_orbit}, max_orbit: {max_orbit}). Skipping planets.")
            num_planets_to_create = 0
        
        placed_planets = 0
        current_orbit_try = min_orbit
        total_placement_attempts = 0
        max_total_placement_attempts = max(num_planets_to_create * 150, 500)

        # Sort available orbit positions to try and fill from inner to outer
        potential_orbit_slots = []
        if max_possible_planets > 0 and num_planets_to_create > 0:
            for i in range(max_possible_planets):
                potential_orbit_slots.append(min_orbit + i * planet_separation)
        random.shuffle(potential_orbit_slots) # Shuffle to make placement less predictable

        for i_planet in range(num_planets_to_create):
            if not potential_orbit_slots: # No more slots left
                print(f"  Warning: Ran out of pre-calculated orbit slots for {name}. Placed {placed_planets}/{num_planets_to_create}.")
                break

            # Use a slot and add some randomness to it
            base_orbit_r = potential_orbit_slots.pop(0)
            orbit_r = base_orbit_r + random.randint(0, int(planet_separation * 0.6)) - int(planet_separation * 0.3)
            orbit_r = max(min_orbit, min(orbit_r, max_orbit)) # Clamp to valid range

            # Ensure this randomized orbit_r doesn't clash *too* badly with already used_radii (less strict check now)
            is_valid_enough = True
            for r_used in used_radii:
                if abs(orbit_r - r_used) < planet_separation * 0.75: # Allow a bit closer than full separation
                    is_valid_enough = False
                    break
            
            if is_valid_enough and orbit_r not in used_radii : # Check direct collision too
                used_radii.add(orbit_r)
                planet_radius = random.randint(10, 25) # Planets can be slightly smaller on average too
                start_angle = random.uniform(0, 360)
                orbit_speed = random.uniform(0.008, 0.04) * random.choice([-1, 1]) # Slightly slower orbits
                color = random.choice([settings.BLUE, settings.GREEN, settings.RED, settings.ORANGE, settings.BROWN, settings.GRAY, settings.PURPLE])
                num_regions = random.randint(2, 5) # Fewer regions for smaller planets
                rotation_angle = random.uniform(0, 360)
                rotation_speed = random.uniform(0.05, 0.4) * random.choice([-1, 1])

                self.planets.append({
                    'radius': planet_radius,
                    'orbit_radius': orbit_r,
                    'angle': start_angle,
                    'speed': orbit_speed,
                    'color': color, 
                    'num_regions': num_regions,
                    'regions': self._generate_regions(num_regions),
                    'rotation_angle': rotation_angle,
                    'rotation_speed': rotation_speed,
                })
                placed_planets += 1
            else:
                # Could not place this planet easily, try to re-add a generic slot if any left, or just skip
                # This simplifies the complex loop structure from before
                if potential_orbit_slots : potential_orbit_slots.append(base_orbit_r + planet_separation) # Try to add a new slot further out
                print(f"  Note: Skipped placing a planet for {name} due to orbit conflict or invalid radius. Attempt {i_planet+1}.")


        if placed_planets < num_planets_to_create:
            print(f"  Warning: Only placed {placed_planets}/{num_planets_to_create} planets for {name} due to space/attempts.")
        
        # Ensure planets are sorted by orbit_radius for consistent drawing or logic if needed later
        self.planets.sort(key=lambda p: p['orbit_radius'])


    def _generate_regions(self, num_regions):
        regions = []
        if num_regions <= 0: return regions
        
        angle_step = 360.0 / num_regions
        
        biome_colors = {
            "Forest": settings.GREEN, "Desert": settings.YELLOW, "Ocean": settings.BLUE,
            "Mountain": settings.GRAY, "Tundra": settings.WHITE, "Volcanic": settings.RED,
            "Plains": (144, 238, 144), "Swamp": (85, 107, 47)
        }
        available_biomes = list(biome_colors.keys())
        if not available_biomes: return regions

        last_biome_name = None
        current_angle = 0
        for i in range(num_regions):
            start_angle = current_angle
            # Add some variation to region sizes
            angle_slice = angle_step + random.uniform(-angle_step * 0.2, angle_step * 0.2)
            if i == num_regions -1 : # Ensure last region fills up to 360
                end_angle = 360.0
            else:
                end_angle = start_angle + angle_slice
            
            current_angle = end_angle # for next iteration
            
            chosen_biome_name = random.choice(available_biomes)
            if len(available_biomes) > 1 and chosen_biome_name == last_biome_name:
                temp_available = [b for b in available_biomes if b != last_biome_name]
                if temp_available:
                    chosen_biome_name = random.choice(temp_available)
            
            regions.append({
                'name': chosen_biome_name,
                'color': biome_colors[chosen_biome_name],
                'start_angle': start_angle % 360, # Ensure angles are wrapped
                'end_angle': end_angle % 360 if end_angle % 360 != 0 else 360.0, # Handle 0/360 consistency
            })
            last_biome_name = chosen_biome_name
        
        # Correct potential overlaps or gaps due to randomization, ensure full 360 coverage
        if regions:
            total_angle_span = 0
            for i_reg, region in enumerate(regions):
                if i_reg > 0:
                    regions[i_reg]['start_angle'] = regions[i_reg-1]['end_angle'] % 360
                
                # Recalculate span for this region
                span = (regions[i_reg]['end_angle'] - regions[i_reg]['start_angle'] + 360) % 360
                if span == 0 and regions[i_reg]['start_angle'] == regions[i_reg]['end_angle'] and num_regions == 1:
                     span = 360 # Full circle for single region
                
                # Ensure end_angle is properly set if it was based on random slice
                if i_reg < num_regions -1 :
                    regions[i_reg]['end_angle'] = (regions[i_reg]['start_angle'] + angle_step) % 360 # Use average step for non-last
                    if regions[i_reg]['end_angle'] == 0 and regions[i_reg]['start_angle'] != 0 : regions[i_reg]['end_angle'] = 360.0
                else: # Last region
                    regions[i_reg]['end_angle'] = 360.0
            
            # Final check to make last region's end_angle 360 and first start_angle 0 if it's very close
            if regions[-1]['end_angle'] > 359.9 and regions[-1]['end_angle'] < 360.01: regions[-1]['end_angle'] = 360.0
            if regions[0]['start_angle'] > -0.01 and regions[0]['start_angle'] < 0.01 : regions[0]['start_angle'] = 0.0


        return regions

    def update_orbits(self):
        for planet in self.planets:
            planet['angle'] = (planet['angle'] + planet['speed']) % 360
            planet['rotation_angle'] = (planet['rotation_angle'] + planet['rotation_speed']) % 360

    def get_planet_position(self, planet_index):
        if 0 <= planet_index < len(self.planets):
            planet = self.planets[planet_index]
            return utils.get_rotated_point(settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT // 2,
                                     planet['angle'], planet['orbit_radius'])
        return (0,0) 