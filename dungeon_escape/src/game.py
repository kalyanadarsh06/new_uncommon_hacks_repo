import os
import random
import math
import time
import sys
from enum import Enum

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

WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
TILE_SIZE = 40
PLAYER_SIZE = 40
FPS = 60

COLORS = {
    'black': (0, 0, 0),
    'white': (255, 255, 255),
    'red': (255, 0, 0),
    'green': (0, 255, 0),
    'blue': (0, 0, 255),
    'brown': (139, 69, 19),
    'dark_brown': (101, 67, 33),
    'light_brown': (181, 101, 29),
    'very_light_brown': (205, 133, 63),
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
    PAUSED = 4
    GAME_WON = 5

class PowerUpType(Enum):
    HEALTH_POTION = 1
    MAGIC_STAFF = 2

class Arrow:
    def __init__(self, x, y, direction):
        self.rect = pygame.Rect(x, y, 8, 8)
        self.direction = direction
        self.speed = 15
        self.damage = 20
        self.active = True
    
    def update(self, walls):
        new_rect = self.rect.copy()
        new_rect.x += self.direction[0] * self.speed
        new_rect.y += self.direction[1] * self.speed
        
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
        
        if power_up_type == PowerUpType.HEALTH_POTION:
            self.sprite = Sprite(os.path.join('..', 'assets', 'images', 'sprites', 'potion.png'), TILE_SIZE)
        else:
            self.sprite = Sprite(os.path.join('..', 'assets', 'images', 'sprites', 'staff.png'), TILE_SIZE)
            
        self.effect_radius = 0
        self.max_radius = TILE_SIZE * 5
        self.effect_active = False
        
    def draw(self, screen):
        self.sprite.rect.x = self.rect.x
        self.sprite.rect.y = self.rect.y
        screen.blit(self.sprite.image, self.sprite.rect)
        
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
        self.grid_move_size = TILE_SIZE
        self.health = 150
        self.max_health = 150
        self.arrows = []
        self.last_shot_time = 0
        self.shoot_delay = 500
        self.facing = Direction.RIGHT
        self.invulnerable = False
        self.invulnerable_time = 0
        self.invulnerable_duration = 500
        self.is_moving = False
        self.damage_multiplier = 1.0
        
    def move(self, dx, dy, walls):
        if self.is_moving:
            return False
            
        self.is_moving = True
        
        new_x = self.rect.x + dx * self.grid_move_size
        new_y = self.rect.y + dy * self.grid_move_size
        
        new_rect = pygame.Rect(new_x, new_y, self.rect.width, self.rect.height)
        
        new_x = max(0, min(new_x, WINDOW_WIDTH - self.rect.width))
        new_y = max(0, min(new_y, WINDOW_HEIGHT - self.rect.height))
        new_rect = pygame.Rect(new_x, new_y, self.rect.width, self.rect.height)
        
        can_move = True
        for wall in walls:
            if new_rect.colliderect(wall):
                can_move = False
                break
        
        if can_move:
            self.rect.x = new_x
            self.rect.y = new_y
        else:
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
            arrow = Arrow(self.rect.centerx, self.rect.centery, direction)
            self.arrows.append(arrow)
            self.last_shot_time = current_time
    
    def draw(self, screen):
        screen.blit(self.sprite.image, self.rect)
        
        indicator_color = COLORS['yellow']
        if self.facing == Direction.UP:
            pygame.draw.rect(screen, indicator_color, (self.rect.centerx - 2, self.rect.top - 5, 4, 4))
        elif self.facing == Direction.DOWN:
            pygame.draw.rect(screen, indicator_color, (self.rect.centerx - 2, self.rect.bottom + 1, 4, 4))
        elif self.facing == Direction.LEFT:
            pygame.draw.rect(screen, indicator_color, (self.rect.left - 5, self.rect.centery - 2, 4, 4))
        elif self.facing == Direction.RIGHT:
            pygame.draw.rect(screen, indicator_color, (self.rect.right + 1, self.rect.centery - 2, 4, 4))
        
        for arrow in self.arrows:
            arrow.draw(screen)
        
        pygame.draw.rect(screen, COLORS['red'], (10, 10, 200, 20))
        pygame.draw.rect(screen, COLORS['green'], 
                        (10, 10, 200 * (self.health / self.max_health), 20))

class Enemy:
    def __init__(self, x, y, level=1):
        self.sprite = Sprite('../assets/images/sprites/enemy.png', PLAYER_SIZE)
        self.rect = pygame.Rect(x, y, PLAYER_SIZE, PLAYER_SIZE)
        self.speed = 0.8
        
        health_multiplier = 1.2 if level == 2 else 1.0
        self.health = int(60 * health_multiplier)
        self.max_health = int(60 * health_multiplier)
        self.last_damage_time = 0
        self.damage_cooldown = 1000
        self.last_move_time = pygame.time.get_ticks()
        self.move_delay = 16
        self.damage = 15
    
    def draw(self, screen):
        screen.blit(self.sprite.image, self.rect)
        
        health_width = int((self.health / self.max_health) * self.rect.width)
        health_height = 5
        health_y = self.rect.y - 10
        
        pygame.draw.rect(screen, COLORS['red'],
                        (self.rect.x, health_y, self.rect.width, health_height))
        pygame.draw.rect(screen, COLORS['green'],
                        (self.rect.x, health_y, health_width, health_height))
    
    def move_towards(self, target, walls, other_enemies, lava_tiles, fire_pillars):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_move_time < self.move_delay:
            return
        
        dx = target.rect.centerx - self.rect.centerx
        dy = target.rect.centery - self.rect.centery
        
        distance = math.sqrt(dx * dx + dy * dy)
        if distance == 0:
            return
        
        dx = (dx / distance) * self.speed
        dy = (dy / distance) * self.speed
        
        new_rect = self.rect.copy()
        new_rect.x += dx
        new_rect.y += dy
        
        is_level_3 = hasattr(target, 'current_level') and target.current_level == 3
        if is_level_3:
            can_move = True
            for pillar in fire_pillars:
                if hasattr(pillar, 'colors') and pillar.colors[0] == COLORS['poison']:
                    poison_center_x = pillar.rect.centerx
                    poison_center_y = pillar.rect.centery
                    new_center_x = new_rect.centerx
                    new_center_y = new_rect.centery
                    
                    distance = ((poison_center_x - new_center_x) ** 2 + 
                               (poison_center_y - new_center_y) ** 2) ** 0.5
                    
                    if distance < TILE_SIZE * 1.5:
                        can_move = False
                        break
            
            if can_move:
                self.rect = new_rect
                self.last_move_time = current_time
            return
        
        can_move = True
        
        for wall in walls:
            if new_rect.colliderect(wall):
                can_move = False
                break
        
        for pillar in fire_pillars:
            if new_rect.colliderect(pillar.rect):
                can_move = False
                break
        
        for lava in lava_tiles:
            if new_rect.colliderect(lava):
                can_move = False
                break
        
        for other in other_enemies:
            if other != self and new_rect.colliderect(other.rect):
                can_move = False
                break
        
        if can_move:
            self.rect = new_rect
        
        self.last_move_time = current_time

class Boss(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, level=3)
        self.sprite = Sprite('../assets/images/sprites/enemy.png', PLAYER_SIZE)
        original_surface = self.sprite.image
        self.sprite.image = pygame.Surface(original_surface.get_size(), pygame.SRCALPHA)
        self.sprite.image.fill((0, 0, 0, 255))
        eye_color = (255, 0, 0)
        eye_width = PLAYER_SIZE // 8
        eye_height = PLAYER_SIZE // 8
        eye_y = PLAYER_SIZE // 3
        pygame.draw.rect(self.sprite.image, eye_color, 
                        (PLAYER_SIZE//4 - eye_width//2, eye_y, eye_width, eye_height))
        pygame.draw.rect(self.sprite.image, eye_color,
                        (3*PLAYER_SIZE//4 - eye_width//2, eye_y, eye_width, eye_height))
        self.rect = pygame.Rect(x, y, PLAYER_SIZE, PLAYER_SIZE)
        self.speed = 1
        self.health = 150
        self.max_health = 120
        self.damage = 50  
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
            
        dx = dx / dist
        dy = dy / dist
        
        near_wall = False
        wall_check_rect = self.rect.inflate(20, 20)
        for wall in walls:
            if wall_check_rect.colliderect(wall):
                near_wall = True
                break
        
        directions = [
            (dx, dy),     
            (dx, dy),
            (dx * 0.866, dy * 0.5),
            (dx * 0.5, dy * 0.866),
            (-dx * 0.5, dy * 0.866),
            (dx * 0.866, -dy * 0.5),
            (1, 0), (-1, 0), (0, 1), (0, -1),
            (0.707, 0.707), (-0.707, 0.707),
            (0.707, -0.707), (-0.707, -0.707)
        ]
        
        if near_wall:
            directions.extend([
                (-dx, -dy),
                (-dx * 0.866, -dy * 0.5),
                (-dx * 0.5, -dy * 0.866),
                (dy, -dx), (-dy, dx)
            ])
        
        for direction in directions:
            base_speed = self.speed * random.uniform(0.8, 1.0)
            
            step_sizes = [0.5, 0.25, 0.125] if near_wall else [1.0, 0.75, 0.5, 0.25]
            for step_size in step_sizes:
                move_dx = direction[0] * base_speed * step_size
                move_dy = direction[1] * base_speed * step_size
                
                test_rect = self.rect.copy()
                test_rect.x += move_dx
                test_rect.y += move_dy
                
                padding = TILE_SIZE // 2
                if (test_rect.left < padding or 
                    test_rect.right > WINDOW_WIDTH - padding or
                    test_rect.top < padding or 
                    test_rect.bottom > WINDOW_HEIGHT - padding):
                    continue
                
                test_rect.inflate_ip(4, 4)
                
                collision = False
                
                for wall in walls:
                    if test_rect.colliderect(wall):
                        collision = True
                        break
                if collision:
                    continue
                
                for hazard in lava_tiles + [p.rect for p in fire_pillars]:
                    if test_rect.colliderect(hazard):
                        collision = True
                        break
                if collision:
                    continue
                
                test_rect.inflate_ip(-2, -2)
                for enemy in other_enemies:
                    if enemy != self and test_rect.colliderect(enemy.rect):
                        collision = True
                        break
                if collision:
                    continue
                
                self.rect.x += move_dx
                self.rect.y += move_dy
                return True
        
        return False



    def draw(self, screen):
        screen.blit(self.sprite.image, self.rect)
        
        if self.health < self.max_health:
            bar_width = 30
            bar_height = 4
            health_ratio = self.health / self.max_health
            health_width = int(bar_width * health_ratio)
            
            pygame.draw.rect(screen, (255, 0, 0),
                           (self.rect.centerx - bar_width//2,
                            self.rect.top - 8,
                            bar_width, bar_height))
            
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
        self.update_delay = 400
        if is_poison:
            self.colors = [COLORS['poison'], COLORS['poison_light'], COLORS['poison_dark'], COLORS['obsidian']]
            self.fixed_pattern = [(i, j) for i in range(4) for j in range(4)]
        else:
            self.colors = [COLORS['dark_red'], COLORS['red'], COLORS['orange']]
            self.fixed_pattern = [(i, j) for i in range(4) for j in range(4) 
                                 if random.random() > 0.2]
        self.generate_pixels()
    
    def generate_pixels(self):
        self.pixels = []
        pixel_size = TILE_SIZE // 4
        
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
        pygame.draw.rect(screen, COLORS['dark_red'], self.rect)
        
        for pixel in self.pixels:
            pygame.draw.rect(screen, pixel['color'],
                           (pixel['x'], pixel['y'], 
                            pixel['size'], pixel['size']))

class Level:
    def __init__(self, level_number):
        self.level_number = level_number
        self.walls = []
        self.fire_pillars = []
        self.lava_tiles = []
        self.tiles = {
            'floor': [Sprite(f'../assets/images/tiles/floor_{i}.png', TILE_SIZE) for i in range(3)],
            'wall': [Sprite(f'../assets/images/tiles/wall_{i}.png', TILE_SIZE) for i in range(3)]
        }
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
        
        flood_fill(start_x, start_y)
        
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
        
        for y in range(height):
            row = []
            for x in range(width):
                variant = random.randint(0, 2)
                row.append(('floor', variant))
            tilemap.append(row)
        
        if self.level_number == 3:
            num_pools = random.randint(6, 8)
            for _ in range(num_pools):
                x = random.randint(2, width-3)
                y = random.randint(2, height-3)
                size = random.randint(3, 4)
                
                temp_tilemap = [row[:] for row in tilemap]
                
                for i in range(size):
                    for j in range(size):
                        if random.random() < 0.7:
                            if 0 <= y+i < height-1 and 0 <= x+j < width-1:
                                temp_tilemap[y+i][x+j] = ('poison', 0)
                
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
                    for i in range(size):
                        for j in range(size):
                            if 0 <= y+i < height-1 and 0 <= x+j < width-1:
                                if temp_tilemap[y+i][x+j][0] == 'poison':
                                    px = (x+j) * TILE_SIZE
                                    py = (y+i) * TILE_SIZE
                                    self.fire_pillars.append(FirePillar(px, py, is_poison=True))
                                    self.lava_tiles.append(pygame.Rect(px, py, TILE_SIZE, TILE_SIZE))
        else:
            for x in range(width):
                variant = random.randint(0, 2)
                tilemap[0][x] = ('wall', variant)
                tilemap[height-1][x] = ('wall', variant)
                self.walls.append(pygame.Rect(x * TILE_SIZE, 0, TILE_SIZE, TILE_SIZE))
                self.walls.append(pygame.Rect(x * TILE_SIZE, (height-1) * TILE_SIZE, TILE_SIZE, TILE_SIZE))
                
                if x > 0 and x < width-1:
                    self.fire_pillars.append(FirePillar(x * TILE_SIZE, TILE_SIZE))
                    self.fire_pillars.append(FirePillar(x * TILE_SIZE, (height-2) * TILE_SIZE))
            
            for y in range(height):
                variant = random.randint(0, 2)
                tilemap[y][0] = ('wall', variant)
                tilemap[y][width-1] = ('wall', variant)
                self.walls.append(pygame.Rect(0, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))
                self.walls.append(pygame.Rect((width-1) * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))
                
                if y > 0 and y < height-1:
                    self.fire_pillars.append(FirePillar(TILE_SIZE, y * TILE_SIZE))
                    self.fire_pillars.append(FirePillar((width-2) * TILE_SIZE, y * TILE_SIZE))
            
            num_obstacles = random.randint(5, 8)
            for _ in range(num_obstacles):
                x = random.randint(2, width-3)
                y = random.randint(2, height-3)
                size = random.randint(2, 3)
                
                temp_tilemap = [row[:] for row in tilemap]
                
                for i in range(size):
                    for j in range(size):
                        if 0 <= y+i < height and 0 <= x+j < width:
                            temp_tilemap[y+i][x+j] = ('wall', random.randint(0, 2))
                
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
                    for i in range(size):
                        for j in range(size):
                            if 0 <= y+i < height and 0 <= x+j < width:
                                tilemap[y+i][x+j] = temp_tilemap[y+i][x+j]
                                self.walls.append(pygame.Rect((x+j) * TILE_SIZE, (y+i) * TILE_SIZE, TILE_SIZE, TILE_SIZE))
        
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
        
        return [[('floor', random.randint(0, 2)) for _ in range(width)] for _ in range(height)]
    
    def update(self):
        for pillar in self.fire_pillars:
            pillar.update()
    
    def draw(self, screen):
        for y, row in enumerate(self.tilemap):
            for x, (tile_type, variant) in enumerate(row):
                screen_x = x * TILE_SIZE
                screen_y = y * TILE_SIZE
                
                if self.level_number == 3:
                    if tile_type == 'floor':
                        pygame.draw.rect(screen, COLORS['obsidian'], (screen_x, screen_y, TILE_SIZE, TILE_SIZE))
                        for _ in range(2):
                            px = screen_x + random.randint(2, TILE_SIZE-4)
                            py = screen_y + random.randint(2, TILE_SIZE-4)
                            pygame.draw.circle(screen, COLORS['very_dark_gray'], (px, py), 2)
                else:
                    pygame.draw.rect(screen, COLORS['light_brown'], (screen_x, screen_y, TILE_SIZE, TILE_SIZE))
                    pygame.draw.rect(screen, COLORS['very_light_brown'], 
                                   (screen_x + 2, screen_y + 2, TILE_SIZE - 4, TILE_SIZE - 4))
                
                if tile_type == 'wall':
                    pygame.draw.rect(screen, COLORS['dark_brown'], (screen_x, screen_y, TILE_SIZE, TILE_SIZE))
                    
                    crack_seed = hash(f"{screen_x},{screen_y}")
                    random.seed(crack_seed)
                    
                    for _ in range(3):
                        start_x = screen_x + random.randint(5, TILE_SIZE-5)
                        start_y = screen_y + random.randint(5, TILE_SIZE-5)
                        
                        for _ in range(random.randint(2, 3)):
                            end_x = start_x + random.randint(-8, 8)
                            end_y = start_y + random.randint(-8, 8)
                            
                            end_x = max(screen_x + 2, min(screen_x + TILE_SIZE - 2, end_x))
                            end_y = max(screen_y + 2, min(screen_y + TILE_SIZE - 2, end_y))
                            
                            pygame.draw.line(screen, COLORS['black'],
                                           (start_x, start_y), (end_x, end_y), 2)
                            
                            start_x, start_y = end_x, end_y
                    
                    random.seed()
        
        for pillar in self.fire_pillars:
            pillar.draw(screen)
            self.lava_tiles.append(pillar.rect)

class Game:
    def __init__(self):
        try:
            self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.HWSURFACE | pygame.DOUBLEBUF)
            pygame.display.set_caption("Dungeon Escape")
        except pygame.error as e:
            print(f"Could not initialize display with hardware surface, trying software: {e}")
            try:
                self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SWSURFACE)
                pygame.display.set_caption("Dungeon Escape")
            except pygame.error as e:
                print(f"Could not initialize display at all: {e}")
                pygame.quit()
                exit(1)
        
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = GameState.COMBAT
        self.current_level = 1
        self.level = Level(self.current_level)
        self.selected_button = 0
        
        spawn_x, spawn_y = self.find_safe_spawn()
        self.player = Player(spawn_x, spawn_y)
        
        self.enemies = self.create_enemies()
        
        self.power_ups = []
        self.last_potion_spawn = time.time()
        self.last_staff_spawn = time.time()
        self.base_potion_interval = 30  
        self.base_staff_interval = 45  
        self.potion_spawn_interval = self.base_potion_interval
        self.staff_spawn_interval = self.base_staff_interval
    
    def find_safe_spawn(self):
        valid_positions = []
        
        for y in range(TILE_SIZE * 2, WINDOW_HEIGHT - TILE_SIZE * 2, TILE_SIZE):
            for x in range(TILE_SIZE * 2, WINDOW_WIDTH - TILE_SIZE * 2, TILE_SIZE):
                tile_x = x // TILE_SIZE
                tile_y = y // TILE_SIZE
                
                if (tile_y < len(self.level.tilemap) and 
                    tile_x < len(self.level.tilemap[tile_y]) and 
                    self.level.tilemap[tile_y][tile_x][0] != 'wall'):
                    
                    test_rect = pygame.Rect(x - PLAYER_SIZE//2, y - PLAYER_SIZE//2, 
                                           PLAYER_SIZE, PLAYER_SIZE)
                    collision = False
                    
                    for wall in self.level.walls:
                        if test_rect.colliderect(wall):
                            collision = True
                            break
                    
                    for pillar in self.level.fire_pillars:
                        if test_rect.colliderect(pillar.rect):
                            collision = True
                            break
                    
                    if not collision:
                        valid_positions.append((x, y))
        
        if valid_positions:
            center_x = WINDOW_WIDTH // 2
            center_y = WINDOW_HEIGHT // 2
            
            valid_positions.sort(key=lambda pos: -((pos[0] - center_x)**2 + (pos[1] - center_y)**2))
            
            return random.choice(valid_positions[:3])
        
        return WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2
    
    def is_valid_spawn_position(self, x, y, check_enemies=True):
        test_rect = pygame.Rect(x - TILE_SIZE//2, y - TILE_SIZE//2, 
                                TILE_SIZE, TILE_SIZE)
        
        # Check wall collisions and adjacency
        for wall in self.level.walls:
            if test_rect.colliderect(wall):
                return False
            # Check adjacent tiles
            wall_x, wall_y = wall.x // TILE_SIZE, wall.y // TILE_SIZE
            spawn_x, spawn_y = x // TILE_SIZE, y // TILE_SIZE
            if abs(wall_x - spawn_x) <= 1 and abs(wall_y - spawn_y) <= 1:
                return False

        # Check boundaries
        buffer = TILE_SIZE * 2
        if (x < buffer or x > WINDOW_WIDTH - buffer or 
            y < buffer or y > WINDOW_HEIGHT - buffer):
            return False

        # Check if on floor tile
        tile_x = x // TILE_SIZE
        tile_y = y // TILE_SIZE
        if (tile_y >= len(self.level.tilemap) or
            tile_x >= len(self.level.tilemap[tile_y]) or
            self.level.tilemap[tile_y][tile_x][0] != 'floor'):
            return False

        # Check existing enemies and boss
        if check_enemies and hasattr(self, 'enemies'):
            for enemy in self.enemies:
                enemy_rect = enemy.rect
                if test_rect.colliderect(enemy_rect):
                    return False
                # Add extra buffer around boss
                if isinstance(enemy, Boss):
                    boss_buffer = TILE_SIZE * 3
                    boss_area = pygame.Rect(
                        enemy_rect.x - boss_buffer,
                        enemy_rect.y - boss_buffer,
                        enemy_rect.width + boss_buffer * 2,
                        enemy_rect.height + boss_buffer * 2
                    )
                    if test_rect.colliderect(boss_area):
                        return False

        # Level 3 specific checks
        if self.current_level == 3:
            for pillar in self.level.fire_pillars:
                if pillar.rect.collidepoint(x, y):
                    return False
                    
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    check_x = x + dx * TILE_SIZE
                    check_y = y + dy * TILE_SIZE
                    for pillar in self.level.fire_pillars:
                        if pillar.rect.collidepoint(check_x, check_y):
                            return False
        
        tile_x = x // TILE_SIZE
        tile_y = y // TILE_SIZE
        
        if (tile_y >= len(self.level.tilemap) or
            tile_x >= len(self.level.tilemap[tile_y]) or
            self.level.tilemap[tile_y][tile_x][0] == 'wall'):
            return False
        
        return True
        
    def is_valid_position(self, x, y):
        test_rect = pygame.Rect(x, y, PLAYER_SIZE, PLAYER_SIZE)
        
        if self.current_level == 3:
            player_dist = math.sqrt((x - self.player.rect.x)**2 + (y - self.player.rect.y)**2)
            return player_dist >= 200
        
        for wall in self.level.walls:
            if test_rect.colliderect(wall):
                return False
        
        player_dist = math.sqrt((x - self.player.rect.x)**2 + (y - self.player.rect.y)**2)
        if player_dist < 200:
            return False
            
        return True
    
    def create_enemies(self):
        enemies = []
        
        if self.current_level == 3:
            center_x = ((WINDOW_WIDTH // TILE_SIZE) // 2) * TILE_SIZE
            center_y = ((WINDOW_HEIGHT // TILE_SIZE) // 2) * TILE_SIZE
            
            boss_spawned = False
            if self.is_valid_spawn_position(center_x, center_y, check_enemies=False):
                enemies.append(Boss(center_x, center_y))
                boss_spawned = True
            else:
                for _ in range(10):
                    x = random.randint(4, (WINDOW_WIDTH // TILE_SIZE) - 4) * TILE_SIZE
                    y = random.randint(4, (WINDOW_HEIGHT // TILE_SIZE) - 4) * TILE_SIZE
                    if self.is_valid_spawn_position(x, y, check_enemies=False):
                        enemies.append(Boss(x, y))
                        boss_spawned = True
                        break
            
            if not boss_spawned:
                return enemies
            
            enemies_spawned = 0
            max_attempts = 50
            
            while enemies_spawned < 6:
                x = random.randint(3, (WINDOW_WIDTH // TILE_SIZE) - 3) * TILE_SIZE
                y = random.randint(3, (WINDOW_HEIGHT // TILE_SIZE) - 3) * TILE_SIZE
                
                if self.is_valid_spawn_position(x, y, check_enemies=True):
                    player_dist = math.sqrt((x - self.player.rect.centerx)**2 + 
                                           (y - self.player.rect.centery)**2)
                    
                    if player_dist >= TILE_SIZE * 4:
                        enemies.append(Enemy(x, y, self.current_level))
                        enemies_spawned += 1                
                max_attempts -= 1
                if max_attempts <= 0:
                    break
        else:
            num_enemies = 6 if self.current_level == 2 else 3
            for _ in range(num_enemies):
                attempts = 0
                while attempts < 100:
                    x = random.randint(TILE_SIZE * 3, WINDOW_WIDTH - TILE_SIZE * 3)
                    y = random.randint(TILE_SIZE * 3, WINDOW_HEIGHT - TILE_SIZE * 3)
                    
                    if self.is_valid_spawn_position(x, y):
                        player_dist = math.sqrt((x - self.player.rect.centerx)**2 + 
                                              (y - self.player.rect.centery)**2)
                        
                        too_close = False
                        for enemy in enemies:
                            enemy_dist = math.sqrt((x - enemy.rect.centerx)**2 + 
                                                  (y - enemy.rect.centery)**2)
                            if enemy_dist < TILE_SIZE * 4:
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
            elif event.type == pygame.MOUSEBUTTONDOWN and (self.state == GameState.GAME_OVER or self.state == GameState.GAME_WON):
                mouse_pos = pygame.mouse.get_pos()
                if self.restart_button.collidepoint(mouse_pos):
                    self.__init__()
                    self.state = GameState.COMBAT
                elif self.exit_button.collidepoint(mouse_pos):
                    self.running = False
            elif event.type == pygame.KEYDOWN:
                if self.state == GameState.COMBAT:
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
                    elif event.key == pygame.K_ESCAPE:
                        self.state = GameState.PAUSED
                        self.selected_button = 0
                elif self.state == GameState.PAUSED:
                    if event.key == pygame.K_a:
                        self.selected_button = 0
                    elif event.key == pygame.K_d:
                        self.selected_button = 1
                    elif event.key == pygame.K_SPACE:
                        if self.selected_button == 0:
                            self.state = GameState.COMBAT
                        else:
                            self.running = False
                    elif event.key == pygame.K_ESCAPE:
                        self.state = GameState.COMBAT
                elif self.state in [GameState.GAME_OVER, GameState.GAME_WON]:
                    if event.key == pygame.K_a:
                        self.selected_button = 0
                    elif event.key == pygame.K_d:
                        self.selected_button = 1
                    elif event.key == pygame.K_SPACE:
                        if self.selected_button == 0:
                            self.__init__()
                        else:
                            self.running = False
    
    def find_power_up_position(self):
        while True:
            x = random.randint(TILE_SIZE, WINDOW_WIDTH - TILE_SIZE)
            y = random.randint(TILE_SIZE, WINDOW_HEIGHT - TILE_SIZE)
            tile_x = x // TILE_SIZE
            tile_y = y // TILE_SIZE
            
            if (tile_y < len(self.level.tilemap) and
                tile_x < len(self.level.tilemap[tile_y]) and
                self.level.tilemap[tile_y][tile_x][0] == 'floor'):
                
                x = tile_x * TILE_SIZE
                y = tile_y * TILE_SIZE
                
                test_rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
                collision = False
                
                for wall in self.level.walls:
                    if test_rect.colliderect(wall):
                        collision = True
                        break
                
                for pillar in self.level.fire_pillars:
                    if test_rect.colliderect(pillar.rect):
                        collision = True
                        break
                
                for power_up in self.power_ups:
                    if test_rect.colliderect(power_up.rect):
                        collision = True
                        break
                
                player_dist = math.sqrt((x - self.player.rect.centerx)**2 + 
                                      (y - self.player.rect.centery)**2)
                if player_dist < TILE_SIZE * 3:
                    collision = True
                
                if not collision:
                    return x, y
    
    def update(self):
        current_time = time.time()
        
        if current_time - self.last_potion_spawn >= self.potion_spawn_interval:
            x, y = self.find_power_up_position()
            self.power_ups.append(PowerUp(x, y, PowerUpType.HEALTH_POTION))
            self.last_potion_spawn = current_time
        
        staff_interval = self.staff_spawn_interval
        if self.player.health < self.player.max_health * 0.2:
            staff_interval = 10
            
        if current_time - self.last_staff_spawn >= staff_interval:
            x, y = self.find_power_up_position()
            self.power_ups.append(PowerUp(x, y, PowerUpType.MAGIC_STAFF))
            self.last_staff_spawn = current_time
        
        self.level.lava_tiles = []
        self.level.update()
        
        current_time = pygame.time.get_ticks()
        
        # Check for level completion
        if all(enemy.health <= 0 for enemy in self.enemies):
            if self.current_level == 3:
                # Victory on level 3
                self.state = GameState.GAME_WON
                self.selected_button = 0
                return
            else:
                # Advance to next level
                self.current_level += 1
                self.level = Level(self.current_level)
                current_health = self.player.health
                spawn_x, spawn_y = self.find_safe_spawn()
                self.player = Player(spawn_x, spawn_y)
                self.player.health = current_health
                self.enemies = self.create_enemies()
                return

        # Check for pillar collision
        for pillar in self.level.fire_pillars:
            if self.player.rect.colliderect(pillar.rect):
                self.player.health = 0
                self.state = GameState.GAME_OVER
                self.selected_button = 0
                return
        
        if self.player.invulnerable and current_time - self.player.invulnerable_time >= self.player.invulnerable_duration:
            self.player.invulnerable = False
        
        touching_enemies = []
        
        for enemy in self.enemies:
            enemy.move_towards(self.player, self.level.walls, self.enemies, 
                             self.level.lava_tiles, self.level.fire_pillars)
            if self.player.rect.colliderect(enemy.rect):
                touching_enemies.append(enemy)
        
        if touching_enemies and not self.player.invulnerable:
            if current_time - touching_enemies[0].last_damage_time >= touching_enemies[0].damage_cooldown:
                damage = 15 * len(touching_enemies)
                self.player.health -= damage
                self.player.invulnerable = True
                self.player.invulnerable_time = current_time
                for enemy in touching_enemies:
                    enemy.last_damage_time = current_time
                if self.player.health <= 0:
                    self.player.health = 0
                    self.state = GameState.GAME_OVER
                    self.selected_button = 0
        
        for pillar in self.level.fire_pillars:
            if self.player.rect.colliderect(pillar.rect):
                self.player.health = 0
                self.state = GameState.GAME_OVER
                self.selected_button = 0
                break
        
        for lava in self.level.lava_tiles:
            if self.player.rect.colliderect(lava):
                self.player.health = 0
                self.state = GameState.GAME_OVER
                self.selected_button = 0
                break
                
        for power_up in self.power_ups[:]:
            if self.player.rect.colliderect(power_up.rect):
                if power_up.type == PowerUpType.HEALTH_POTION:
                    self.player.health = min(self.player.max_health, 
                                           self.player.health + 15)
                else:
                    self.player.damage_multiplier = 1.5
                    power_up.effect_active = True
                    for enemy in self.enemies[:]:
                        enemy.health -= 20
                        if enemy.health <= 0:
                            self.enemies.remove(enemy)
                            if not self.enemies:
                                if self.current_level < 3:
                                    self.current_level += 1
                                    self.level = Level(self.current_level)
                                    current_health = self.player.health
                                    spawn_x, spawn_y = self.find_safe_spawn()
                                    self.player = Player(spawn_x, spawn_y)
                                    self.player.health = current_health
                                    self.enemies = self.create_enemies()
                                    self.power_ups = []
                                    if self.current_level == 2:
                                        self.potion_spawn_interval = self.base_potion_interval * 0.8
                                        self.staff_spawn_interval = self.base_staff_interval * 0.8
                                    elif self.current_level == 3:
                                        self.potion_spawn_interval = self.base_potion_interval * 0.6
                                        self.staff_spawn_interval = self.base_staff_interval * 0.6
                self.power_ups.remove(power_up)

        for arrow in self.player.arrows[:]:
            arrow.update(self.level.walls)
            if not arrow.active:
                self.player.arrows.remove(arrow)
                continue
            
            for enemy in self.enemies[:]:
                if arrow.rect.colliderect(enemy.rect):
                    enemy.health -= arrow.damage * self.player.damage_multiplier
                    arrow.active = False
                    self.player.arrows.remove(arrow)
                    
                    if enemy.health <= 0:
                        self.enemies.remove(enemy)
                        if not self.enemies:
                            if self.current_level < 3:
                                self.current_level += 1
                                self.level = Level(self.current_level)
                                current_health = self.player.health
                                spawn_x, spawn_y = self.find_safe_spawn()
                                self.player = Player(spawn_x, spawn_y)
                                self.player.health = current_health
                                self.enemies = self.create_enemies()
                                self.power_ups = []
                                if self.current_level == 2:
                                    self.potion_spawn_interval = self.base_potion_interval * 0.8
                                    self.staff_spawn_interval = self.base_staff_interval * 0.8
                                elif self.current_level == 3:
                                    self.potion_spawn_interval = self.base_potion_interval * 0.6
                                    self.staff_spawn_interval = self.base_staff_interval * 0.6
                    break
    
    def create_pixelated_text(self, text, size, color):
        font = pygame.font.Font(None, size)
        text_surface = font.render(text, True, color)
        
        scale_factor = 4
        small_surface = pygame.transform.scale(text_surface, 
            (text_surface.get_width()//scale_factor, 
             text_surface.get_height()//scale_factor))
        return pygame.transform.scale(small_surface, 
            (small_surface.get_width()*scale_factor, 
             small_surface.get_height()*scale_factor))
    
    def draw_retro_button(self, rect, color):
        pygame.draw.rect(self.screen, color, rect)
        
        light_color = (min(color[0] + 50, 255), 
                      min(color[1] + 50, 255), 
                      min(color[2] + 50, 255))
        pygame.draw.line(self.screen, light_color, rect.topleft, rect.topright)
        pygame.draw.line(self.screen, light_color, rect.topleft, rect.bottomleft)
        
        dark_color = (max(color[0] - 50, 0), 
                     max(color[1] - 50, 0), 
                     max(color[2] - 50, 0))
        pygame.draw.line(self.screen, dark_color, rect.bottomleft, rect.bottomright)
        pygame.draw.line(self.screen, dark_color, rect.topright, rect.bottomright)
    
    def create_menu_text(self, text, size, color):
        try:
            font = pygame.font.Font(None, size)
            return font.render(text, True, color)
        except:
            return self.create_pixelated_text(text, size, color)



    def draw_pause_menu(self):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(200)
        self.screen.blit(overlay, (0, 0))

        border_padding = 20
        pygame.draw.rect(self.screen, COLORS['white'], 
                       (border_padding, border_padding, 
                        WINDOW_WIDTH - 2*border_padding, 
                        WINDOW_HEIGHT - 2*border_padding), 2)

        title = self.create_menu_text("GAME PAUSED", 60, COLORS['white'])
        self.screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, 40))

        sections = [
            ("CONTROLS", [
                "A/D - Select button",
                "Space - Confirm selection",
                "R - Pause/Resume"
            ]),
            ("POWER-UPS", [
                "Health Potion - Restores health",
                "Magic Staff - Doubles damage"
            ]),
            ("TIPS", [
                "Avoid  poison and lava",
                "Defeat all enemies to advance",
                "Boss appears in level 3!"
            ])
        ]

        y = 120
        for section_title, items in sections:
            header = self.create_menu_text(section_title, 36, COLORS['yellow'])
            self.screen.blit(header, (WINDOW_WIDTH//2 - header.get_width()//2, y))
            y += 35

            for item in items:
                text = self.create_menu_text(item, 28, COLORS['white'])
                self.screen.blit(text, (WINDOW_WIDTH//2 - text.get_width()//2, y))
                y += 30
            
            y += 15

        button_y = WINDOW_HEIGHT - 80
        resume_rect = pygame.Rect(WINDOW_WIDTH//4 - 100, button_y, 200, 50)
        quit_rect = pygame.Rect(WINDOW_WIDTH*3//4 - 100, button_y, 200, 50)
        self.draw_retro_button(resume_rect, COLORS['green'] if self.selected_button == 0 else COLORS['dark_red'])
        self.draw_retro_button(quit_rect, COLORS['red'] if self.selected_button == 1 else COLORS['dark_red'])
        resume_text = self.create_menu_text("RESUME", 32, COLORS['white'])
        quit_text = self.create_menu_text("QUIT", 32, COLORS['white'])

        self.screen.blit(resume_text, (resume_rect.centerx - resume_text.get_width()//2, 
                                      resume_rect.centery - resume_text.get_height()//2))
        self.screen.blit(quit_text, (quit_rect.centerx - quit_text.get_width()//2, 
                                    quit_rect.centery - quit_text.get_height()//2))

        # Store button rects for interaction
        self.restart_button = resume_rect
        self.exit_button = quit_rect

        pygame.display.flip()

    def draw_victory_screen(self):
        # Create semi-transparent overlay
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(200)
        self.screen.blit(overlay, (0, 0))

        border_padding = 20
        pygame.draw.rect(self.screen, COLORS['white'], 
                       (border_padding, border_padding, 
                        WINDOW_WIDTH - 2*border_padding, 
                        WINDOW_HEIGHT - 2*border_padding), 2)

        title = self.create_menu_text("VICTORY!", 60, COLORS['green'])
        self.screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, 40))

        sections = [
            ("CONGRATULATIONS!", [
                "You've escaped the dungeon!",
            ]),
            ("FINAL STATS", [
                f"Level Reached: {self.current_level}",
                f"Health Remaining: {self.player.health}",
            ])
        ]

        y = 120
        for section_title, items in sections:
            header = self.create_menu_text(section_title, 36, COLORS['yellow'])
            self.screen.blit(header, (WINDOW_WIDTH//2 - header.get_width()//2, y))
            y += 35

            for item in items:
                text = self.create_menu_text(item, 28, COLORS['white'])
                self.screen.blit(text, (WINDOW_WIDTH//2 - text.get_width()//2, y))
                y += 30
            
            y += 15

        # Create buttons
        button_y = WINDOW_HEIGHT - 80
        restart_rect = pygame.Rect(WINDOW_WIDTH//4 - 100, button_y, 200, 50)
        exit_rect = pygame.Rect(WINDOW_WIDTH*3//4 - 100, button_y, 200, 50)

        # Draw buttons with selection highlight
        self.draw_retro_button(restart_rect, COLORS['green'] if self.selected_button == 0 else COLORS['dark_red'])
        self.draw_retro_button(exit_rect, COLORS['red'] if self.selected_button == 1 else COLORS['dark_red'])

        # Button text
        restart_text = self.create_menu_text("PLAY AGAIN", 32, COLORS['white'])
        exit_text = self.create_menu_text("QUIT", 32, COLORS['white'])

        self.screen.blit(restart_text, (restart_rect.centerx - restart_text.get_width()//2, 
                                      restart_rect.centery - restart_text.get_height()//2))
        self.screen.blit(exit_text, (exit_rect.centerx - exit_text.get_width()//2, 
                                    exit_rect.centery - exit_text.get_height()//2))

        # Store button rects for interaction
        self.restart_button = restart_rect
        self.exit_button = exit_rect

        pygame.display.flip()

    def draw_game_over_screen(self):
        # Create semi-transparent overlay
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(200)
        self.screen.blit(overlay, (0, 0))

        border_padding = 20
        pygame.draw.rect(self.screen, COLORS['white'], 
                       (border_padding, border_padding, 
                        WINDOW_WIDTH - 2*border_padding, 
                        WINDOW_HEIGHT - 2*border_padding), 2)

        title = self.create_menu_text("GAME OVER", 60, COLORS['red'])
        self.screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, 40))

        message = self.create_menu_text("Better luck next time!", 36, COLORS['yellow'])
        self.screen.blit(message, (WINDOW_WIDTH//2 - message.get_width()//2, WINDOW_HEIGHT//2 - 50))

        # Create buttons
        button_y = WINDOW_HEIGHT - 80
        restart_rect = pygame.Rect(WINDOW_WIDTH//4 - 100, button_y, 200, 50)
        exit_rect = pygame.Rect(WINDOW_WIDTH*3//4 - 100, button_y, 200, 50)

        # Draw buttons with selection highlight
        self.draw_retro_button(restart_rect, COLORS['green'] if self.selected_button == 0 else COLORS['dark_red'])
        self.draw_retro_button(exit_rect, COLORS['red'] if self.selected_button == 1 else COLORS['dark_red'])

        # Button text
        restart_text = self.create_menu_text("TRY AGAIN", 32, COLORS['white'])
        exit_text = self.create_menu_text("QUIT", 32, COLORS['white'])

        self.screen.blit(restart_text, (restart_rect.centerx - restart_text.get_width()//2, 
                                      restart_rect.centery - restart_text.get_height()//2))
        self.screen.blit(exit_text, (exit_rect.centerx - exit_text.get_width()//2, 
                                    exit_rect.centery - exit_text.get_height()//2))

        # Store button rects for interaction
        self.restart_button = restart_rect
        self.exit_button = exit_rect

        pygame.display.flip()
    
    def draw(self):
        self.screen.fill(COLORS['black'])
        
        self.level.draw(self.screen)
        
        for power_up in self.power_ups:
            power_up.draw(self.screen)
        
        for enemy in self.enemies:
            enemy.draw(self.screen)
        
        self.player.draw(self.screen)
        
        # Draw base game state first
        pygame.display.flip()
        
        # Then overlay menus if needed
        if self.state == GameState.GAME_OVER:
            self.draw_game_over_screen()
        elif self.state == GameState.GAME_WON:
            self.draw_victory_screen()
        elif self.state == GameState.PAUSED:
            self.draw_pause_menu()
    
    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r and self.state in [GameState.COMBAT, GameState.PAUSED]:
                        if self.state == GameState.PAUSED:
                            self.state = GameState.COMBAT
                        else:
                            self.state = GameState.PAUSED
                            self.selected_button = 0
                    elif self.state == GameState.COMBAT:
                        if event.key == pygame.K_ESCAPE:
                            self.state = GameState.PAUSED
                            self.selected_button = 0
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
                    elif self.state in [GameState.PAUSED, GameState.GAME_OVER, GameState.GAME_WON]:
                        if event.key == pygame.K_ESCAPE and self.state == GameState.PAUSED:
                            self.state = GameState.COMBAT
                        elif event.key == pygame.K_a:
                            self.selected_button = 0
                        elif event.key == pygame.K_d:
                            self.selected_button = 1
                        elif event.key == pygame.K_SPACE:
                            if self.selected_button == 0:
                                if self.state in [GameState.GAME_OVER, GameState.GAME_WON]:
                                    self.__init__()
                                    self.state = GameState.COMBAT
                                else:
                                    self.state = GameState.COMBAT
                            else:
                                return
            
            if self.state == GameState.COMBAT:
                self.handle_input()
                self.update()
                self.draw()
            elif self.state == GameState.PAUSED:
                self.draw_pause_menu()
            elif self.state == GameState.GAME_OVER:
                self.draw_game_over_screen()
            elif self.state == GameState.GAME_WON:
                self.draw_victory_screen()
            
            self.clock.tick(FPS)
        
        return

if __name__ == '__main__':
    game = Game()
    game.run()
    print("here")