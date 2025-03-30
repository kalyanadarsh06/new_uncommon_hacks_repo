import os
import random
import math
import time
import sys
from enum import Enum

# Initialize Pygame with error handling
try:
    import pygame
    pygame.init()
    print(f"Using Pygame version: {pygame.version.ver}")
    print(f"Display driver: {pygame.display.get_driver()}")
except ImportError as e:
    print(f"Error importing Pygame: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Error initializing Pygame: {e}")
    sys.exit(1)

# Game constants
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
TILE_SIZE = 40  # Adjusted size between 32 and 48
PLAYER_SIZE = 40  # Adjusted size between 32 and 48
FPS = 60

# Colors
COLORS = {
    'black': (0, 0, 0),
    'white': (255, 255, 255),
    'red': (255, 0, 0),
    'green': (0, 255, 0),
    'blue': (0, 0, 255),
    'brown': (139, 69, 19),
    'dark_brown': (101, 67, 33),
    'light_brown': (181, 101, 29),     # Light brown for floor
    'very_light_brown': (205, 133, 63), # Even lighter brown for floor highlights
    'yellow': (255, 255, 0),
    'orange': (255, 165, 0),
    'dark_red': (139, 0, 0),
    'obsidian': (41, 42, 45),
    'poison': (44, 85, 48),
    'poison_dark': (27, 52, 29),
    'poison_light': (64, 116, 68),
    'very_dark_gray': (30, 30, 30)
}

class GameState(Enum):
    COMBAT = 1
    TRANSITION = 2
    GAME_OVER = 3

class PowerUpType(Enum):
    HEALTH_POTION = 1
    MAGIC_STAFF = 2

class Arrow:
    def __init__(self, x, y, direction):
        self.rect = pygame.Rect(x, y, 8, 8)  # Small arrow
        self.direction = direction  # (dx, dy)
        self.speed = 15
        self.damage = 20
        self.active = True
    
    def update(self, walls):
        new_rect = self.rect.copy()
        new_rect.x += self.direction[0] * self.speed
        new_rect.y += self.direction[1] * self.speed
        
        # Check wall collisions
        for wall in walls:
            if new_rect.colliderect(wall):
                self.active = False
                return
        
        self.rect = new_rect
    
    def draw(self, screen):
        pygame.draw.rect(screen, COLORS['yellow'], self.rect)

class Sprite:
    def __init__(self, image_path, size=None):
        self.image = pygame.image.load(image_path).convert_alpha()
        if size:
            self.image = pygame.transform.scale(self.image, (size, size))
        self.rect = self.image.get_rect()

class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

class PowerUp:
    def __init__(self, x, y, power_up_type):
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.type = power_up_type
        self.creation_time = time.time()
        
        # Load appropriate sprite based on type
        if power_up_type == PowerUpType.HEALTH_POTION:
            self.sprite = Sprite(os.path.join('..', 'assets', 'images', 'sprites', 'potion.png'), TILE_SIZE)
        else:  # MAGIC_STAFF
            self.sprite = Sprite(os.path.join('..', 'assets', 'images', 'sprites', 'staff.png'), TILE_SIZE)
            
        # Special effect properties for staff
        self.effect_radius = 0
        self.max_radius = TILE_SIZE * 5
        self.effect_active = False
        
    def draw(self, screen):
        self.sprite.rect.x = self.rect.x
        self.sprite.rect.y = self.rect.y
        screen.blit(self.sprite.image, self.sprite.rect)
        
        # Draw staff effect if active
        if self.effect_active:
            if self.effect_radius < self.max_radius:
                self.effect_radius += 5
                effect_surface = pygame.Surface((self.effect_radius * 2, self.effect_radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(effect_surface, (255, 255, 255, 100), 
                                 (self.effect_radius, self.effect_radius), self.effect_radius)
                screen.blit(effect_surface, 
                           (self.rect.centerx - self.effect_radius, 
                            self.rect.centery - self.effect_radius))
            else:
                self.effect_active = False
                self.effect_radius = 0

class Player:
    def __init__(self, x, y):
        self.sprite = Sprite('../assets/images/sprites/player.png', PLAYER_SIZE)
        self.rect = pygame.Rect(x, y, PLAYER_SIZE, PLAYER_SIZE)
        self.grid_move_size = TILE_SIZE  # Move 1 tile at a time
        self.health = 100
        self.max_health = 100
        self.arrows = []  # List of active arrows
        self.last_shot_time = 0
        self.shoot_delay = 500  # Milliseconds between shots
        self.facing = Direction.RIGHT  # Default facing direction
        self.invulnerable = False
        self.invulnerable_time = 0
        self.invulnerable_duration = 500  # 0.5 seconds of invulnerability after taking damage
        self.is_moving = False  # Track if currently in a move
        self.damage_multiplier = 1.0  # For magic staff power-up
        
    def move(self, dx, dy, walls):
        if self.is_moving:
            return False  # Don't start a new move if one is in progress
            
        self.is_moving = True
        
        # Try to move by grid_move_size in the given direction
        new_x = self.rect.x + dx * self.grid_move_size
        new_y = self.rect.y + dy * self.grid_move_size
        
        # Create a test rectangle for the new position
        new_rect = pygame.Rect(new_x, new_y, self.rect.width, self.rect.height)
        
        # Clamp position to screen boundaries
        new_x = max(0, min(new_x, WINDOW_WIDTH - self.rect.width))
        new_y = max(0, min(new_y, WINDOW_HEIGHT - self.rect.height))
        new_rect = pygame.Rect(new_x, new_y, self.rect.width, self.rect.height)
        
        # Check wall collisions
        can_move = True
        for wall in walls:
            if new_rect.colliderect(wall):
                can_move = False
                break
        
        if can_move:
            self.rect.x = new_x
            self.rect.y = new_y
        else:
            # Try moving by one tile if full movement is blocked
            new_x = self.rect.x + dx * TILE_SIZE
            new_y = self.rect.y + dy * TILE_SIZE
            new_rect = pygame.Rect(new_x, new_y, self.rect.width, self.rect.height)
            
            can_move = True
            for wall in walls:
                if new_rect.colliderect(wall):
                    can_move = False
                    break
            
            if can_move:
                self.rect.x = new_x
                self.rect.y = new_y
        
        self.is_moving = False
        return True

    def shoot(self, direction):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_shot_time >= self.shoot_delay:
            # Create new arrow at player position
            arrow = Arrow(self.rect.centerx, self.rect.centery, direction)
            self.arrows.append(arrow)
            self.last_shot_time = current_time
    
    def draw(self, screen):
        # Draw player
        screen.blit(self.sprite.image, self.rect)
        
        # Draw direction indicator
        indicator_color = COLORS['yellow']
        if self.facing == Direction.UP:
            pygame.draw.rect(screen, indicator_color, (self.rect.centerx - 2, self.rect.top - 5, 4, 4))
        elif self.facing == Direction.DOWN:
            pygame.draw.rect(screen, indicator_color, (self.rect.centerx - 2, self.rect.bottom + 1, 4, 4))
        elif self.facing == Direction.LEFT:
            pygame.draw.rect(screen, indicator_color, (self.rect.left - 5, self.rect.centery - 2, 4, 4))
        elif self.facing == Direction.RIGHT:
            pygame.draw.rect(screen, indicator_color, (self.rect.right + 1, self.rect.centery - 2, 4, 4))
        
        # Draw arrows
        for arrow in self.arrows:
            arrow.draw(screen)
        
        # Draw health bar
        pygame.draw.rect(screen, COLORS['red'], (10, 10, 200, 20))
        pygame.draw.rect(screen, COLORS['green'], 
                        (10, 10, 200 * (self.health / self.max_health), 20))

class Enemy:
    def __init__(self, x, y, level=1):
        self.sprite = Sprite('../assets/images/sprites/enemy.png', PLAYER_SIZE)
        self.rect = pygame.Rect(x, y, PLAYER_SIZE, PLAYER_SIZE)
        self.speed = 1.5  # Increased for smoother movement
        # Increase health for level 2
        health_multiplier = 1.2 if level == 2 else 1.0
        self.health = int(60 * health_multiplier)
        self.max_health = int(60 * health_multiplier)
        self.last_damage_time = 0  # Track when enemy last damaged player
        self.damage_cooldown = 1000  # 1 second between damage ticks
        self.last_move_time = pygame.time.get_ticks()
        self.move_delay = 16  # ~60 FPS movement update
        self.damage = 15  # Base damage
    
    def draw(self, screen):
        # Draw enemy sprite
        screen.blit(self.sprite.image, self.rect)
        
        # Draw health bar
        health_width = int((self.health / self.max_health) * self.rect.width)
        health_height = 5
        health_y = self.rect.y - 10
        
        # Draw background (red)
        pygame.draw.rect(screen, COLORS['red'],
                        (self.rect.x, health_y, self.rect.width, health_height))
        # Draw foreground (green)
        pygame.draw.rect(screen, COLORS['green'],
                        (self.rect.x, health_y, health_width, health_height))
    
    def move_towards(self, target, walls, other_enemies, lava_tiles, fire_pillars):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_move_time < self.move_delay:
            return
        
        # Calculate direction to player
        dx = target.rect.centerx - self.rect.centerx
        dy = target.rect.centery - self.rect.centery
        
        # Normalize direction
        distance = math.sqrt(dx * dx + dy * dy)
        if distance == 0:
            return
        
        dx = (dx / distance) * self.speed
        dy = (dy / distance) * self.speed
        
        # Try moving in both x and y directions
        new_rect = self.rect.copy()
        new_rect.x += dx
        new_rect.y += dy
        
        # In Level 3, enemies can move freely but need to avoid poison
        is_level_3 = hasattr(target, 'current_level') and target.current_level == 3
        if is_level_3:
            # First check if the new position would be too close to poison
            can_move = True
            for pillar in fire_pillars:
                if hasattr(pillar, 'colors') and pillar.colors[0] == COLORS['poison']:
                    # Check if we're getting too close to poison
                    poison_center_x = pillar.rect.centerx
                    poison_center_y = pillar.rect.centery
                    new_center_x = new_rect.centerx
                    new_center_y = new_rect.centery
                    
                    # Calculate distance to poison tile
                    distance = ((poison_center_x - new_center_x) ** 2 + 
                               (poison_center_y - new_center_y) ** 2) ** 0.5
                    
                    # If we're too close to poison, try to move away
                    if distance < TILE_SIZE * 1.5:  # Keep 1.5 tiles away from poison
                        can_move = False
                        break
            
            if can_move:
                self.rect = new_rect
                self.last_move_time = current_time
            return
        
        # For other levels, check all collisions
        can_move = True
        
        # Check wall collisions
        for wall in walls:
            if new_rect.colliderect(wall):
                can_move = False
                break
        
        # Check fire pillar collisions
        for pillar in fire_pillars:
            if new_rect.colliderect(pillar.rect):
                can_move = False
                break
        
        # Check lava tile collisions
        for lava in lava_tiles:
            if new_rect.colliderect(lava):
                can_move = False
                break
        
        # Check other enemy collisions
        for other in other_enemies:
            if other != self and new_rect.colliderect(other.rect):
                can_move = False
                break
        
        # If we can move, update position
        if can_move:
            self.rect = new_rect
        
        self.last_move_time = current_time

class Boss(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, level=3)
        # Boss uses same size but different color
        self.sprite = Sprite('../assets/images/sprites/enemy.png', PLAYER_SIZE)
        # Create a copy of the surface to modify
        original_surface = self.sprite.image
        self.sprite.image = pygame.Surface(original_surface.get_size(), pygame.SRCALPHA)
        # Fill with black
        self.sprite.image.fill((0, 0, 0, 255))
        # Add red eyes (small rectangles)
        eye_color = (255, 0, 0)  # Red
        eye_width = PLAYER_SIZE // 8
        eye_height = PLAYER_SIZE // 8
        eye_y = PLAYER_SIZE // 3
        # Left eye
        pygame.draw.rect(self.sprite.image, eye_color, 
                        (PLAYER_SIZE//4 - eye_width//2, eye_y, eye_width, eye_height))
        # Right eye
        pygame.draw.rect(self.sprite.image, eye_color,
                        (3*PLAYER_SIZE//4 - eye_width//2, eye_y, eye_width, eye_height))
        self.rect = pygame.Rect(x, y, PLAYER_SIZE, PLAYER_SIZE)
        self.speed = 1.7  
        self.health = 120  # 2x normal enemy health (60 * 2)
        self.max_health = 120
        self.damage = 50  # Double enemy damage (15 * 2)
        
    def move_towards(self, target, walls, other_enemies, lava_tiles, fire_pillars):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_move_time < self.move_delay:
            return
            
        self.last_move_time = current_time
        
        dx = target.rect.x - self.rect.x
        dy = target.rect.y - self.rect.y
        dist = math.sqrt(dx * dx + dy * dy)
        
        if dist == 0:
            return
            
        # Normalize direction vector
        dx = dx / dist
        dy = dy / dist
        
        # Check if near a wall
        near_wall = False
        wall_check_rect = self.rect.inflate(20, 20)  # Slightly larger rect to check wall proximity
        for wall in walls:
            if wall_check_rect.colliderect(wall):
                near_wall = True
                break
        
        # Create movement options with weighted preference for direct path
        directions = [
            (dx, dy),      # Direct path
            (dx, dy),      # Try direct path again
            (dx * 0.866, dy * 0.5),  # 30 degree offset
            (dx * 0.5, dy * 0.866),  # 60 degree offset
            (-dx * 0.5, dy * 0.866),  # -60 degree offset
            (dx * 0.866, -dy * 0.5),  # Alternate 30 degree
            (1, 0), (-1, 0), (0, 1), (0, -1),  # Cardinal directions
            (0.707, 0.707), (-0.707, 0.707),    # 45 degree angles
            (0.707, -0.707), (-0.707, -0.707)   # More 45 degree angles
        ]
        
        # If near a wall, try more varied movements
        if near_wall:
            directions.extend([
                (-dx, -dy),  # Try opposite direction
                (-dx * 0.866, -dy * 0.5),  # Opposite 30 degree
                (-dx * 0.5, -dy * 0.866),  # Opposite 60 degree
                (dy, -dx), (-dy, dx)  # Perpendicular directions
            ])
        
        # Try each direction with increasingly smaller steps
        for direction in directions:
            base_speed = self.speed * random.uniform(0.8, 1.0)  # Slight speed variation
            
            # Try different step sizes, use smaller steps when near walls
            step_sizes = [0.5, 0.25, 0.125] if near_wall else [1.0, 0.75, 0.5, 0.25]
            for step_size in step_sizes:
                move_dx = direction[0] * base_speed * step_size
                move_dy = direction[1] * base_speed * step_size
                
                # Test the movement
                test_rect = self.rect.copy()
                test_rect.x += move_dx
                test_rect.y += move_dy
                
                # Check boundaries with some padding
                padding = TILE_SIZE // 2
                if (test_rect.left < padding or 
                    test_rect.right > WINDOW_WIDTH - padding or
                    test_rect.top < padding or 
                    test_rect.bottom > WINDOW_HEIGHT - padding):
                    continue
                
                # Check for collisions with a small buffer
                test_rect.inflate_ip(4, 4)  # Add buffer
                
                # Quick collision checks
                collision = False
                
                # Check walls
                for wall in walls:
                    if test_rect.colliderect(wall):
                        collision = True
                        break
                if collision:
                    continue
                
                # Check hazards (lava and fire pillars)
                for hazard in lava_tiles + [p.rect for p in fire_pillars]:
                    if test_rect.colliderect(hazard):
                        collision = True
                        break
                if collision:
                    continue
                
                # Check other enemies with reduced buffer
                test_rect.inflate_ip(-2, -2)
                for enemy in other_enemies:
                    if enemy != self and test_rect.colliderect(enemy.rect):
                        collision = True
                        break
                if collision:
                    continue
                
                # Movement is valid, apply it with slight smoothing
                self.rect.x += move_dx
                self.rect.y += move_dy
                return True
        
        return False



    def draw(self, screen):
        # Draw the enemy sprite
        screen.blit(self.sprite.image, self.rect)
        
        # Draw health bar
        if self.health < self.max_health:
            bar_width = 30
            bar_height = 4
            health_ratio = self.health / self.max_health
            health_width = int(bar_width * health_ratio)
            
            # Background (red)
            pygame.draw.rect(screen, (255, 0, 0),
                           (self.rect.centerx - bar_width//2,
                            self.rect.top - 8,
                            bar_width, bar_height))
            # Foreground (green)
            pygame.draw.rect(screen, (0, 255, 0),
                           (self.rect.centerx - bar_width//2,
                            self.rect.top - 8,
                            health_width, bar_height))



class FirePillar:
    def __init__(self, x, y, is_poison=False):
        self.x = x
        self.y = y
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.pixels = []
        self.next_update = 0
        self.update_delay = 400  # Slower updates (was 150)
        if is_poison:
            self.colors = [COLORS['poison'], COLORS['poison_light'], COLORS['poison_dark'], COLORS['obsidian']]
            # For poison, use a solid color instead of pixels
            self.fixed_pattern = [(i, j) for i in range(4) for j in range(4)]
        else:
            self.colors = [COLORS['dark_red'], COLORS['red'], COLORS['orange']]
            # Generate a fixed pattern for lava tile
            self.fixed_pattern = [(i, j) for i in range(4) for j in range(4) 
                                 if random.random() > 0.2]  # 80% chance of pixel
        self.generate_pixels()
    
    def generate_pixels(self):
        # Use the fixed pattern but randomize colors
        self.pixels = []
        pixel_size = TILE_SIZE // 4  # 4x4 grid
        
        for i, j in self.fixed_pattern:
            self.pixels.append({
                'x': self.x + i * pixel_size,
                'y': self.y + j * pixel_size,
                'size': pixel_size,
                'color': random.choice(self.colors)
            })
    
    def update(self):
        current_time = pygame.time.get_ticks()
        if current_time > self.next_update:
            self.generate_pixels()
            self.next_update = current_time + self.update_delay
    
    def draw(self, screen):
        # Draw base
        pygame.draw.rect(screen, COLORS['dark_red'], self.rect)
        
        # Draw retro pixel pattern
        for pixel in self.pixels:
            pygame.draw.rect(screen, pixel['color'],
                           (pixel['x'], pixel['y'], 
                            pixel['size'], pixel['size']))

class Level:
    def __init__(self, level_number):
        self.level_number = level_number
        self.walls = []  # Initialize walls list first
        self.fire_pillars = []
        self.lava_tiles = []  # Track lava tile positions
        self.tiles = {
            'floor': [Sprite(f'../assets/images/tiles/floor_{i}.png', TILE_SIZE) for i in range(3)],
            'wall': [Sprite(f'../assets/images/tiles/wall_{i}.png', TILE_SIZE) for i in range(3)]
        }
        # For level 3, use dark red floor tiles
        if level_number == 3:
            self.floor_color = COLORS['dark_red']
            self.is_poison_level = True
        else:
            self.floor_color = COLORS['light_brown']
            self.is_poison_level = False
        self.tilemap = self.generate_tilemap()
        
    def is_accessible(self, tilemap, start_x, start_y):
        width = len(tilemap[0])
        height = len(tilemap)
        visited = set()
        
        def flood_fill(x, y):
            if (x, y) in visited:
                return
            if (x < 0 or x >= width or y < 0 or y >= height):
                return
            if tilemap[y][x][0] == 'wall':
                return
            visited.add((x, y))
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                flood_fill(x + dx, y + dy)
        
        # Start flood fill from given position
        flood_fill(start_x, start_y)
        
        # Check if all floor tiles are reachable
        for y in range(height):
            for x in range(width):
                if tilemap[y][x][0] == 'floor' and (x, y) not in visited:
                    return False
        return True
    
    def generate_tilemap(self):
        width = WINDOW_WIDTH // TILE_SIZE
        height = WINDOW_HEIGHT // TILE_SIZE
        tilemap = []
        self.walls = []
        self.fire_pillars = []
        
        # Create empty tilemap with floor tiles
        for y in range(height):
            row = []
            for x in range(width):
                variant = random.randint(0, 2)
                row.append(('floor', variant))
            tilemap.append(row)
        
        if self.level_number == 3:
            # Level 3: Create maze-like pattern of poison pools
            num_pools = random.randint(6, 8)  # Number of poison pool clusters
            for _ in range(num_pools):
                x = random.randint(2, width-3)
                y = random.randint(2, height-3)
                size = random.randint(3, 4)  # Size of each poison pool cluster
                
                # Create temporary map to test accessibility
                temp_tilemap = [row[:] for row in tilemap]
                
                # Try to add poison pool cluster
                for i in range(size):
                    for j in range(size):
                        if random.random() < 0.7:  # 70% chance to add a poison pool in the cluster
                            if 0 <= y+i < height-1 and 0 <= x+j < width-1:
                                temp_tilemap[y+i][x+j] = ('poison', 0)
                
                # Check if map is still accessible
                start_x = start_y = None
                for test_y in range(1, height-1):
                    for test_x in range(1, width-1):
                        if temp_tilemap[test_y][test_x][0] == 'floor':
                            start_x = test_x
                            start_y = test_y
                            break
                    if start_x is not None:
                        break
                
                if start_x is not None and self.is_accessible(temp_tilemap, start_x, start_y):
                    # If accessible, apply changes and add poison pillars
                    for i in range(size):
                        for j in range(size):
                            if 0 <= y+i < height-1 and 0 <= x+j < width-1:
                                if temp_tilemap[y+i][x+j][0] == 'poison':
                                    px = (x+j) * TILE_SIZE
                                    py = (y+i) * TILE_SIZE
                                    self.fire_pillars.append(FirePillar(px, py, is_poison=True))
                                    self.lava_tiles.append(pygame.Rect(px, py, TILE_SIZE, TILE_SIZE))
        else:
            # Level 1 and 2: Regular walls and fire
            # Add walls around edges
            for x in range(width):
                variant = random.randint(0, 2)
                tilemap[0][x] = ('wall', variant)
                tilemap[height-1][x] = ('wall', variant)
                self.walls.append(pygame.Rect(x * TILE_SIZE, 0, TILE_SIZE, TILE_SIZE))
                self.walls.append(pygame.Rect(x * TILE_SIZE, (height-1) * TILE_SIZE, TILE_SIZE, TILE_SIZE))
                
                # Add continuous fire along top and bottom
                if x > 0 and x < width-1:
                    self.fire_pillars.append(FirePillar(x * TILE_SIZE, TILE_SIZE))
                    self.fire_pillars.append(FirePillar(x * TILE_SIZE, (height-2) * TILE_SIZE))
            
            for y in range(height):
                variant = random.randint(0, 2)
                tilemap[y][0] = ('wall', variant)
                tilemap[y][width-1] = ('wall', variant)
                self.walls.append(pygame.Rect(0, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))
                self.walls.append(pygame.Rect((width-1) * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))
                
                # Add continuous fire along left and right
                if y > 0 and y < height-1:
                    self.fire_pillars.append(FirePillar(TILE_SIZE, y * TILE_SIZE))
                    self.fire_pillars.append(FirePillar((width-2) * TILE_SIZE, y * TILE_SIZE))
            
            # Add random obstacles with validation
            num_obstacles = random.randint(5, 8)  # Reduced max obstacles
            for _ in range(num_obstacles):
                x = random.randint(2, width-3)
                y = random.randint(2, height-3)
                size = random.randint(2, 3)  # Reduced max size
                
                # Create temporary map to test accessibility
                temp_tilemap = [row[:] for row in tilemap]
                
                # Try to add obstacle
                for i in range(size):
                    for j in range(size):
                        if 0 <= y+i < height and 0 <= x+j < width:
                            temp_tilemap[y+i][x+j] = ('wall', random.randint(0, 2))
                
                # Check if map is still accessible
                start_x = start_y = None
                for test_y in range(1, height-1):
                    for test_x in range(1, width-1):
                        if temp_tilemap[test_y][test_x][0] == 'floor':
                            start_x = test_x
                            start_y = test_y
                            break
                    if start_x is not None:
                        break
                
                if start_x is not None and self.is_accessible(temp_tilemap, start_x, start_y):
                    # If accessible, apply changes to real tilemap
                    for i in range(size):
                        for j in range(size):
                            if 0 <= y+i < height and 0 <= x+j < width:
                                tilemap[y+i][x+j] = temp_tilemap[y+i][x+j]
                                self.walls.append(pygame.Rect((x+j) * TILE_SIZE, (y+i) * TILE_SIZE, TILE_SIZE, TILE_SIZE))
        
        # Validate final map
        start_x = start_y = None
        for y in range(1, height-1):
            for x in range(1, width-1):
                if tilemap[y][x][0] == 'floor':
                    start_x = x
                    start_y = y
                    break
            if start_x is not None:
                break
        
        if start_x is not None and self.is_accessible(tilemap, start_x, start_y):
            return tilemap
        
        # If map is not accessible, return an empty map
        return [[('floor', random.randint(0, 2)) for _ in range(width)] for _ in range(height)]
    
    def update(self):
        # Update fire pillars
        for pillar in self.fire_pillars:
            pillar.update()
    
    def draw(self, screen):
        # Draw base tiles
        for y, row in enumerate(self.tilemap):
            for x, (tile_type, variant) in enumerate(row):
                screen_x = x * TILE_SIZE
                screen_y = y * TILE_SIZE
                
                if self.level_number == 3:
                    # Level 3: Draw obsidian floor
                    if tile_type == 'floor':
                        pygame.draw.rect(screen, COLORS['obsidian'], (screen_x, screen_y, TILE_SIZE, TILE_SIZE))
                        # Add slight variation to create texture
                        for _ in range(2):
                            px = screen_x + random.randint(2, TILE_SIZE-4)
                            py = screen_y + random.randint(2, TILE_SIZE-4)
                            pygame.draw.circle(screen, COLORS['very_dark_gray'], (px, py), 2)
                else:
                    # Other levels: Draw normal floor
                    pygame.draw.rect(screen, COLORS['light_brown'], (screen_x, screen_y, TILE_SIZE, TILE_SIZE))
                    pygame.draw.rect(screen, COLORS['very_light_brown'], 
                                   (screen_x + 2, screen_y + 2, TILE_SIZE - 4, TILE_SIZE - 4))
                
                # Draw walls with muddy appearance
                if tile_type == 'wall':
                    pygame.draw.rect(screen, COLORS['dark_brown'], (screen_x, screen_y, TILE_SIZE, TILE_SIZE))
                    
                    # Use deterministic seed for consistent cracks
                    crack_seed = hash(f"{screen_x},{screen_y}") # Hash based on position
                    random.seed(crack_seed)
                    
                    # Add fixed mud cracks
                    for _ in range(3):  # 3 cracks per tile
                        # Start point of crack
                        start_x = screen_x + random.randint(5, TILE_SIZE-5)
                        start_y = screen_y + random.randint(5, TILE_SIZE-5)
                        
                        # Create 2-3 segments per crack
                        for _ in range(random.randint(2, 3)):
                            end_x = start_x + random.randint(-8, 8)
                            end_y = start_y + random.randint(-8, 8)
                            
                            # Keep crack within tile bounds
                            end_x = max(screen_x + 2, min(screen_x + TILE_SIZE - 2, end_x))
                            end_y = max(screen_y + 2, min(screen_y + TILE_SIZE - 2, end_y))
                            
                            pygame.draw.line(screen, COLORS['black'],
                                           (start_x, start_y), (end_x, end_y), 2)
                            
                            start_x, start_y = end_x, end_y
                    
                    # Restore the random seed
                    random.seed()
        
        # Draw fire pillars
        for pillar in self.fire_pillars:
            pillar.draw(screen)
            # Store lava tile positions for collision detection
            self.lava_tiles.append(pillar.rect)

class Game:
    def __init__(self):
        # Initialize display with a basic configuration first
        try:
            self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.HWSURFACE | pygame.DOUBLEBUF)
            pygame.display.set_caption("AI Dungeon")
        except pygame.error as e:
            print(f"Could not initialize display with hardware surface, trying software: {e}")
            try:
                self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SWSURFACE)
                pygame.display.set_caption("AI Dungeon")
            except pygame.error as e:
                print(f"Could not initialize display at all: {e}")
                pygame.quit()
                exit(1)
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = GameState.COMBAT
        self.current_level = 3  # Temporarily set to level 3 for testing
        self.level = Level(self.current_level)
        
        # Find safe spawn for player
        spawn_x, spawn_y = self.find_safe_spawn()
        self.player = Player(spawn_x, spawn_y)
        
        self.enemies = self.create_enemies()
        
        # Power-up management
        self.power_ups = []
        self.last_potion_spawn = time.time()
        self.last_staff_spawn = time.time()
        # Base intervals that will be modified by level
        self.base_potion_interval = 10  # seconds
        self.base_staff_interval = 20  # seconds
        # Current intervals (will be adjusted based on level)
        self.potion_spawn_interval = self.base_potion_interval
        self.staff_spawn_interval = self.base_staff_interval
    
    def find_safe_spawn(self):
        # Get all valid floor positions
        valid_positions = []
        
        # Start a bit away from the edges
        for y in range(TILE_SIZE * 2, WINDOW_HEIGHT - TILE_SIZE * 2, TILE_SIZE):
            for x in range(TILE_SIZE * 2, WINDOW_WIDTH - TILE_SIZE * 2, TILE_SIZE):
                # First check if this position is on a floor tile
                tile_x = x // TILE_SIZE
                tile_y = y // TILE_SIZE
                
                if (tile_y < len(self.level.tilemap) and 
                    tile_x < len(self.level.tilemap[tile_y]) and 
                    self.level.tilemap[tile_y][tile_x][0] != 'wall'):
                    
                    # Then check for wall collisions with the actual player rect
                    test_rect = pygame.Rect(x - PLAYER_SIZE//2, y - PLAYER_SIZE//2, 
                                           PLAYER_SIZE, PLAYER_SIZE)
                    collision = False
                    
                    # Check wall collisions
                    for wall in self.level.walls:
                        if test_rect.colliderect(wall):
                            collision = True
                            break
                    
                    # Check fire pillar collisions
                    for pillar in self.level.fire_pillars:
                        if test_rect.colliderect(pillar.rect):
                            collision = True
                            break
                    
                    if not collision:
                        valid_positions.append((x, y))
        
        if valid_positions:
            # Choose a random valid position away from center
            center_x = WINDOW_WIDTH // 2
            center_y = WINDOW_HEIGHT // 2
            
            # Sort positions by distance from center (furthest first)
            valid_positions.sort(key=lambda pos: -((pos[0] - center_x)**2 + (pos[1] - center_y)**2))
            
            # Take one of the first 3 positions (they'll be furthest from center)
            return random.choice(valid_positions[:3])
        
        # If no valid positions found, try the center as last resort
        return WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2
    
    def is_valid_spawn_position(self, x, y):
        # Create a test rect for collision checking
        test_rect = pygame.Rect(x - PLAYER_SIZE//2, y - PLAYER_SIZE//2, 
                                PLAYER_SIZE, PLAYER_SIZE)
        
        # Check wall collisions
        for wall in self.level.walls:
            if test_rect.colliderect(wall):
                return False

        # Check boundaries (reduced buffer)
        buffer = TILE_SIZE
        if (x < buffer or x > WINDOW_WIDTH - buffer or 
            y < buffer or y > WINDOW_HEIGHT - buffer):
            return False

        # In level 3, check for poison tiles and adjacent poison tiles
        if self.current_level == 3:
            # Check if current tile is a poison tile
            for pillar in self.level.fire_pillars:
                if pillar.rect.collidepoint(x + PLAYER_SIZE//2, y + PLAYER_SIZE//2):
                    return False
                    
            # Check adjacent tiles (including diagonals)
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    check_x = x + dx * TILE_SIZE
                    check_y = y + dy * TILE_SIZE
                    for pillar in self.level.fire_pillars:
                        if pillar.rect.collidepoint(check_x + PLAYER_SIZE//2, check_y + PLAYER_SIZE//2):
                            return False
        
        # Get tile coordinates
        tile_x = x // TILE_SIZE
        tile_y = y // TILE_SIZE
        
        # Basic tile check
        if (tile_y >= len(self.level.tilemap) or
            tile_x >= len(self.level.tilemap[tile_y]) or
            self.level.tilemap[tile_y][tile_x][0] == 'wall'):
            return False
        
        return True
        
    def is_valid_position(self, x, y):
        # Create a test rect
        test_rect = pygame.Rect(x, y, PLAYER_SIZE, PLAYER_SIZE)
        
        # In Level 3, only check distance from player
        if self.current_level == 3:
            player_dist = math.sqrt((x - self.player.rect.x)**2 + (y - self.player.rect.y)**2)
            return player_dist >= 200  # Minimum distance from player
        
        # For other levels, check all collisions
        # Check wall collisions
        for wall in self.level.walls:
            if test_rect.colliderect(wall):
                return False
        
        # Make sure it's not too close to player
        player_dist = math.sqrt((x - self.player.rect.x)**2 + (y - self.player.rect.y)**2)
        if player_dist < 200:  # Minimum distance from player
            return False
            
        return True
    
    def create_enemies(self):
        print("Starting enemy creation...")
        enemies = []
        
        if self.current_level == 3:
            print("Creating level 3 enemies...")
            # Level 3: Try to spawn boss first
            center_x = ((WINDOW_WIDTH // TILE_SIZE) // 2) * TILE_SIZE
            center_y = ((WINDOW_HEIGHT // TILE_SIZE) // 2) * TILE_SIZE
            
            # Try to spawn boss
            boss_spawned = False
            if self.is_valid_spawn_position(center_x, center_y):
                enemies.append(Boss(center_x, center_y))
                boss_spawned = True
                print("Boss spawned in center")
            else:
                print("Trying alternative boss positions...")
                for _ in range(10):  # Reduced attempts
                    x = random.randint(4, (WINDOW_WIDTH // TILE_SIZE) - 4) * TILE_SIZE
                    y = random.randint(4, (WINDOW_HEIGHT // TILE_SIZE) - 4) * TILE_SIZE
                    if self.is_valid_spawn_position(x, y):
                        enemies.append(Boss(x, y))
                        boss_spawned = True
                        print("Boss spawned in alternative position")
                        break
            
            if not boss_spawned:
                print("Warning: Could not spawn boss")
                return enemies
            
            # Add normal enemies with relaxed constraints
            print("Spawning normal enemies...")
            enemies_spawned = 0
            max_attempts = 50  # Reduced from 100
            
            while enemies_spawned < 6:
                x = random.randint(3, (WINDOW_WIDTH // TILE_SIZE) - 3) * TILE_SIZE
                y = random.randint(3, (WINDOW_HEIGHT // TILE_SIZE) - 3) * TILE_SIZE
                
                if self.is_valid_spawn_position(x, y):
                    # Simplified distance checks
                    player_dist = math.sqrt((x - self.player.rect.centerx)**2 + 
                                           (y - self.player.rect.centery)**2)
                    
                    if player_dist >= TILE_SIZE * 4:  # Reduced from 6
                        enemies.append(Enemy(x, y, self.current_level))
                        enemies_spawned += 1
                        print(f"Spawned enemy {enemies_spawned}/6")
                
                max_attempts -= 1
                if max_attempts <= 0:
                    print(f"Warning: Could only spawn {enemies_spawned} enemies")
                    break
        else:
            # Level 1 and 2: Regular enemies
            num_enemies = 6 if self.current_level == 2 else 3  # Exactly 3 enemies for level 1
            for _ in range(num_enemies):
                attempts = 0
                while attempts < 100:
                    x = random.randint(TILE_SIZE * 3, WINDOW_WIDTH - TILE_SIZE * 3)
                    y = random.randint(TILE_SIZE * 3, WINDOW_HEIGHT - TILE_SIZE * 3)
                    
                    if self.is_valid_spawn_position(x, y):
                        player_dist = math.sqrt((x - self.player.rect.centerx)**2 + 
                                              (y - self.player.rect.centery)**2)
                        
                        too_close = False
                        # Check distance from other enemies
                        for enemy in enemies:
                            enemy_dist = math.sqrt((x - enemy.rect.centerx)**2 + 
                                                  (y - enemy.rect.centery)**2)
                            if enemy_dist < TILE_SIZE * 4:  # Keep enemies spread out
                                too_close = True
                                break
                        if player_dist < TILE_SIZE * 6:
                            too_close = True
                        
                        for enemy in enemies:
                            enemy_dist = math.sqrt((x - enemy.rect.centerx)**2 + 
                                                  (y - enemy.rect.centery)**2)
                            if enemy_dist < TILE_SIZE * 4:
                                too_close = True
                                break
                        
                        if not too_close:
                            enemies.append(Enemy(x, y, self.current_level))
                            break
                    
                    attempts += 1
        
        return enemies
    
    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and self.state == GameState.GAME_OVER:
                # Check for button clicks in game over screen
                mouse_pos = pygame.mouse.get_pos()
                if self.restart_button.collidepoint(mouse_pos):
                    # Reset game
                    self.__init__()
                    self.state = GameState.COMBAT
                elif self.exit_button.collidepoint(mouse_pos):
                    self.running = False
            elif event.type == pygame.KEYDOWN and self.state == GameState.COMBAT:  # Only handle key press when alive
                if event.key == pygame.K_a:
                    self.player.facing = Direction.LEFT
                    self.player.move(-1, 0, self.level.walls)
                elif event.key == pygame.K_d:
                    self.player.facing = Direction.RIGHT
                    self.player.move(1, 0, self.level.walls)
                elif event.key == pygame.K_w:
                    self.player.facing = Direction.UP
                    self.player.move(0, -1, self.level.walls)
                elif event.key == pygame.K_s:
                    self.player.facing = Direction.DOWN
                    self.player.move(0, 1, self.level.walls)
                elif event.key == pygame.K_SPACE:
                    self.player.shoot(self.player.facing.value)
    
    def find_power_up_position(self):
        while True:
            x = random.randint(TILE_SIZE, WINDOW_WIDTH - TILE_SIZE)
            y = random.randint(TILE_SIZE, WINDOW_HEIGHT - TILE_SIZE)
            tile_x = x // TILE_SIZE
            tile_y = y // TILE_SIZE
            
            # Check if position is on a floor tile
            if (tile_y < len(self.level.tilemap) and
                tile_x < len(self.level.tilemap[tile_y]) and
                self.level.tilemap[tile_y][tile_x][0] == 'floor'):
                
                # Align to grid
                x = tile_x * TILE_SIZE
                y = tile_y * TILE_SIZE
                
                # Check for collisions with walls and other objects
                test_rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
                collision = False
                
                # Check wall collisions
                for wall in self.level.walls:
                    if test_rect.colliderect(wall):
                        collision = True
                        break
                
                # Check lava collisions
                for pillar in self.level.fire_pillars:
                    if test_rect.colliderect(pillar.rect):
                        collision = True
                        break
                
                # Check other power-ups
                for power_up in self.power_ups:
                    if test_rect.colliderect(power_up.rect):
                        collision = True
                        break
                
                # Check if too close to player
                player_dist = math.sqrt((x - self.player.rect.centerx)**2 + 
                                      (y - self.player.rect.centery)**2)
                if player_dist < TILE_SIZE * 3:  # At least 3 tiles from player
                    collision = True
                
                if not collision:
                    return x, y
    
    def update(self):
        current_time = time.time()
        
        # Spawn health potion
        if current_time - self.last_potion_spawn >= self.potion_spawn_interval:
            x, y = self.find_power_up_position()
            self.power_ups.append(PowerUp(x, y, PowerUpType.HEALTH_POTION))
            self.last_potion_spawn = current_time
        
        # Spawn magic staff
        staff_interval = self.staff_spawn_interval
        if self.player.health < self.player.max_health * 0.2:  # Below 20% health
            staff_interval = 10  # Spawn more frequently
            
        if current_time - self.last_staff_spawn >= staff_interval:
            x, y = self.find_power_up_position()
            self.power_ups.append(PowerUp(x, y, PowerUpType.MAGIC_STAFF))
            self.last_staff_spawn = current_time
        
        # Clear lava tiles list before updating
        self.level.lava_tiles = []
        
        # Update level
        self.level.update()
        
        # Update enemies and track which ones are touching player
        current_time = pygame.time.get_ticks()
        
        # In Level 3, check if player is touching poison (instant death)
        if self.current_level == 3:
            for pillar in self.level.fire_pillars:
                if self.player.rect.colliderect(pillar.rect):
                    self.player.health = 0
                    self.state = GameState.GAME_OVER
                    return
        
        # Check if invulnerability has expired
        if self.player.invulnerable and current_time - self.player.invulnerable_time >= self.player.invulnerable_duration:
            self.player.invulnerable = False
        
        touching_enemies = []
        
        for enemy in self.enemies:
            enemy.move_towards(self.player, self.level.walls, self.enemies, 
                             self.level.lava_tiles, self.level.fire_pillars)
            if self.player.rect.colliderect(enemy.rect):
                touching_enemies.append(enemy)
        
        # Apply damage from touching enemies
        if touching_enemies and not self.player.invulnerable:
            # Check if enough time has passed since last damage
            if current_time - touching_enemies[0].last_damage_time >= touching_enemies[0].damage_cooldown:
                # Base damage is 15, multiplied by number of touching enemies
                damage = 15 * len(touching_enemies)
                self.player.health -= damage
                self.player.invulnerable = True
                self.player.invulnerable_time = current_time
                # Reset damage cooldown for all touching enemies
                for enemy in touching_enemies:
                    enemy.last_damage_time = current_time
                    
                # Check if player died from the damage
                if self.player.health <= 0:
                    self.player.health = 0
                    self.state = GameState.GAME_OVER
        
        # Check if player is in lava
        for pillar in self.level.fire_pillars:
            if self.player.rect.colliderect(pillar.rect):
                self.player.health = 0  # Instant death in lava
                self.state = GameState.GAME_OVER
                break  # No need to check other lava tiles
        # Also check lava tiles
        for lava in self.level.lava_tiles:
            if self.player.rect.colliderect(lava):
                self.player.health = 0  # Instant death in lava
                self.state = GameState.GAME_OVER
                break  # No need to check other lava tiles
                
        # Check power-up collisions
        for power_up in self.power_ups[:]:
            if self.player.rect.colliderect(power_up.rect):
                if power_up.type == PowerUpType.HEALTH_POTION:
                    self.player.health = min(self.player.max_health, 
                                           self.player.health + 15)
                else:  # MAGIC_STAFF
                    self.player.damage_multiplier = 1.5
                    power_up.effect_active = True
                    # Apply damage to all enemies on screen
                    for enemy in self.enemies[:]:
                        enemy.health -= 20  # Base damage multiplied by 1.5
                        if enemy.health <= 0:
                            self.enemies.remove(enemy)
                            # Check if all enemies are defeated
                            if not self.enemies:
                                if self.current_level < 3:  # Allow progression to level 3
                                    # Advance to next level
                                    self.current_level += 1
                                    self.level = Level(self.current_level)
                                    # Reset player position but keep health
                                    current_health = self.player.health
                                    spawn_x, spawn_y = self.find_safe_spawn()
                                    self.player = Player(spawn_x, spawn_y)
                                    self.player.health = current_health
                                    # Create new enemies
                                    self.enemies = self.create_enemies()
                                    # Reset power-ups for new level
                                    self.power_ups = []
                                    # Adjust power-up spawn intervals based on level
                                    if self.current_level == 2:
                                        self.potion_spawn_interval = self.base_potion_interval * 0.8
                                        self.staff_spawn_interval = self.base_staff_interval * 0.8
                                    elif self.current_level == 3:
                                        self.potion_spawn_interval = self.base_potion_interval * 0.6
                                        self.staff_spawn_interval = self.base_staff_interval * 0.6
                self.power_ups.remove(power_up)

        # Update arrows
        for arrow in self.player.arrows[:]:  # Use slice copy to safely remove while iterating
            arrow.update(self.level.walls)
            if not arrow.active:
                self.player.arrows.remove(arrow)
                continue
                
            # Check enemy collisions
            for enemy in self.enemies[:]:  # Use slice copy to safely remove while iterating
                if arrow.rect.colliderect(enemy.rect):
                    enemy.health -= arrow.damage * self.player.damage_multiplier
                    arrow.active = False
                    self.player.arrows.remove(arrow)
                    
                    if enemy.health <= 0:
                        self.enemies.remove(enemy)
                        # Check if all enemies are defeated
                        if not self.enemies:
                            if self.current_level < 3:  # Allow progression to level 3
                                # Advance to next level
                                self.current_level += 1
                                self.level = Level(self.current_level)
                                # Reset player position but keep health
                                current_health = self.player.health
                                spawn_x, spawn_y = self.find_safe_spawn()
                                self.player = Player(spawn_x, spawn_y)
                                self.player.health = current_health
                                # Create new enemies
                                self.enemies = self.create_enemies()
                                # Reset power-ups for new level
                                self.power_ups = []
                                # Adjust power-up spawn intervals based on level
                                if self.current_level == 2:
                                    self.potion_spawn_interval = self.base_potion_interval * 0.8
                                    self.staff_spawn_interval = self.base_staff_interval * 0.8
                                elif self.current_level == 3:
                                    self.potion_spawn_interval = self.base_potion_interval * 0.6
                                    self.staff_spawn_interval = self.base_staff_interval * 0.6
                    break
    
    def create_pixelated_text(self, text, size, color):
        # Create a surface for the text
        font = pygame.font.Font(None, size)
        text_surface = font.render(text, True, color)
        
        # Scale down and back up to create pixelation effect
        scale_factor = 4
        small_surface = pygame.transform.scale(text_surface, 
            (text_surface.get_width()//scale_factor, 
             text_surface.get_height()//scale_factor))
        return pygame.transform.scale(small_surface, 
            (small_surface.get_width()*scale_factor, 
             small_surface.get_height()*scale_factor))
    
    def draw_retro_button(self, rect, color):
        # Draw main button
        pygame.draw.rect(self.screen, color, rect)
        
        # Draw lighter top/left edges
        light_color = (min(color[0] + 50, 255), 
                      min(color[1] + 50, 255), 
                      min(color[2] + 50, 255))
        pygame.draw.line(self.screen, light_color, rect.topleft, rect.topright)
        pygame.draw.line(self.screen, light_color, rect.topleft, rect.bottomleft)
        
        # Draw darker bottom/right edges
        dark_color = (max(color[0] - 50, 0), 
                     max(color[1] - 50, 0), 
                     max(color[2] - 50, 0))
        pygame.draw.line(self.screen, dark_color, rect.bottomleft, rect.bottomright)
        pygame.draw.line(self.screen, dark_color, rect.topright, rect.bottomright)
    
    def draw_game_over(self):
        # Create CRT-style scanline effect
        for y in range(0, WINDOW_HEIGHT, 2):
            pygame.draw.line(self.screen, (0, 0, 0), (0, y), (WINDOW_WIDTH, y))
        
        # Create semi-transparent overlay with retro color
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.fill((20, 0, 40))  # Dark purple for retro feel
        overlay.set_alpha(200)
        self.screen.blit(overlay, (0, 0))
        
        # Create pixelated Game Over text with glow effect
        glow_colors = [(180, 0, 0), (220, 0, 0), (255, 0, 0)]
        for i, color in enumerate(glow_colors):
            text = self.create_pixelated_text('GAME OVER', 74 + i*2, color)
            text_rect = text.get_rect(center=(WINDOW_WIDTH/2, WINDOW_HEIGHT/2 - 50))
            offset = i * 2
            self.screen.blit(text, (text_rect.x - offset, text_rect.y - offset))
        
        # Create pixelated button text
        restart_text = self.create_pixelated_text('RESTART', 36, (255, 255, 255))
        exit_text = self.create_pixelated_text('EXIT', 36, (255, 255, 255))
        
        # Button backgrounds with retro style
        button_padding = 20
        restart_rect = pygame.Rect(0, 0, restart_text.get_width() + button_padding*2, 
                                 restart_text.get_height() + button_padding)
        restart_rect.centerx = WINDOW_WIDTH/2 - 100
        restart_rect.centery = WINDOW_HEIGHT/2 + 50
        
        exit_rect = pygame.Rect(0, 0, exit_text.get_width() + button_padding*2,
                               exit_text.get_height() + button_padding)
        exit_rect.centerx = WINDOW_WIDTH/2 + 100
        exit_rect.centery = WINDOW_HEIGHT/2 + 50
        
        # Draw retro-styled buttons
        self.draw_retro_button(restart_rect, (80, 0, 160))  # Purple
        self.draw_retro_button(exit_rect, (160, 0, 80))    # Red-Purple
        
        # Draw button text
        restart_text_rect = restart_text.get_rect(center=restart_rect.center)
        exit_text_rect = exit_text.get_rect(center=exit_rect.center)
        self.screen.blit(restart_text, restart_text_rect)
        self.screen.blit(exit_text, exit_text_rect)
        
        # Add some retro decoration
        for i in range(4):
            pygame.draw.rect(self.screen, (60, 0, 120), 
                           (20 + i*4, 20 + i*4, WINDOW_WIDTH - 40 - i*8, WINDOW_HEIGHT - 40 - i*8), 
                           2)
        
        pygame.display.flip()
        
        # Store button rects for click detection
        self.restart_button = restart_rect
        self.exit_button = exit_rect
    
    def draw(self):
        self.screen.fill(COLORS['black'])
        
        # Draw level
        self.level.draw(self.screen)
        
        # Draw power-ups
        for power_up in self.power_ups:
            power_up.draw(self.screen)
        
        # Draw enemies
        for enemy in self.enemies:
            enemy.draw(self.screen)
        
        # Draw player
        self.player.draw(self.screen)
        
        if self.state == GameState.GAME_OVER:
            self.draw_game_over()
        else:
            pygame.display.flip()
    
    def run(self):
        while self.running:
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_a:
                        self.player.facing = Direction.LEFT
                        self.player.move(-1, 0, self.level.walls)
                    elif event.key == pygame.K_d:
                        self.player.facing = Direction.RIGHT
                        self.player.move(1, 0, self.level.walls)
                    elif event.key == pygame.K_w:
                        self.player.facing = Direction.UP
                        self.player.move(0, -1, self.level.walls)
                    elif event.key == pygame.K_s:
                        self.player.facing = Direction.DOWN
                        self.player.move(0, 1, self.level.walls)
                    elif event.key == pygame.K_SPACE:
                        self.player.shoot(self.player.facing.value)
            
            self.handle_input()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()

if __name__ == '__main__':
    try:
        print("Starting game...")
        game = Game()
        print("Game initialized, starting game loop...")
        game.run()
    except Exception as e:
        print(f"Error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        pygame.quit()