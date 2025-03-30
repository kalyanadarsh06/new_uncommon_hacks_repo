from enum import Enum

class GameState(Enum):
    PLAYING = 0
    LEVEL_COMPLETE = 1
    GAME_OVER = 2
    BLOCKCIDE = 3  # New state for voluntary reset

class Player:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.moving = False
        self.move_progress = 0

class Cursor:
    def __init__(self):
        self.x = 0
        self.y = 0

    def move(self, dx, dy, grid_size):
        """Move cursor within grid bounds."""
        new_x = self.x + dx
        new_y = self.y + dy
        if 0 <= new_x < grid_size and 0 <= new_y < grid_size:
            self.x = new_x
            self.y = new_y

class Game:
    def __init__(self):
        self.reset_game()

    def reset_game(self):
        """Reset all game state."""
        self.current_level = 1  # Start at level 1
        self.levels_beaten = 0  # Start at 0 (always level - 1)
        self.state = GameState.PLAYING
        self.coins = 1  # Start with 1 coin
        self.blocks_placed = 0  # Counter for place cost
        self.blocks_destroyed = 0  # Counter for destroy cost
        self.player = Player()
        self.cursor = Cursor()
        self.grid = [[False] * 10 for _ in range(10)]
        self.walls = []
        self.coin_positions = []
        self.player_placed_blocks = []
        self.grid_size = 10

    def init_level(self, maze_data):
        """Initialize level with maze data."""
        self.walls = maze_data['walls']
        self.coin_positions = maze_data['coins']
        self.player.x = maze_data['start'][0]
        self.player.y = maze_data['start'][1]
        self.cursor.x = maze_data['start'][0]
        self.cursor.y = maze_data['start'][1]
        self.grid = [[False] * maze_data['size'] for _ in range(maze_data['size'])]
        self.player_placed_blocks = []  # Reset placed blocks for new level
        self.grid[self.player.y][self.player.x] = True
        self.grid_size = maze_data['size']
        # Don't reset block counters - they persist until game restart

    def get_next_block_cost(self):
        """Get the cost of placing the next block."""
        return self.blocks_placed + 1  # Cost increases by 1 for each block placed

    def get_next_destroy_cost(self):
        """Get the cost of destroying the next block."""
        return self.blocks_destroyed + 1  # Cost increases by 1 for each block destroyed

    def try_place_block(self):
        """Try to place a block at cursor position."""
        block_cost = self.get_next_block_cost()
        pos = [self.cursor.x, self.cursor.y]
        if (pos not in self.walls and
            pos not in self.coin_positions and
            pos != [self.player.x, self.player.y] and
            pos not in self.player_placed_blocks and
            self.coins >= block_cost):  # Only check if we have enough coins
            self.player_placed_blocks.append(pos)
            self.coins -= block_cost
            self.blocks_placed += 1  # Increment counter for next cost
            return True
        return False

    def try_destroy_block(self):
        """Try to destroy a block or wall at cursor position, turning it into free space."""
        destroy_cost = self.get_next_destroy_cost()
        pos = [self.cursor.x, self.cursor.y]
        
        # Can destroy either placed blocks or walls
        can_destroy = (pos in self.player_placed_blocks or pos in self.walls)
        
        if (can_destroy and self.coins >= destroy_cost):
            # Remove block/wall and make space free
            if pos in self.player_placed_blocks:
                self.player_placed_blocks.remove(pos)
            if pos in self.walls:
                self.walls.remove(pos)
            self.coins -= destroy_cost
            self.blocks_destroyed += 1  # Increment counter for next cost
            # Make sure the space is marked as passable
            self.grid[pos[1]][pos[0]] = True
            return True
        return False

    def commit_blockcide(self):
        """Player gives up, show final score."""
        self.state = GameState.BLOCKCIDE

    def start_movement(self, dx, dy):
        """Start player movement in the given direction."""
        current_x = self.player.x
        current_y = self.player.y
        
        # Keep moving until hitting a wall, block, or boundary
        while True:
            new_x = current_x + dx
            new_y = current_y + dy
            
            # Check if movement is valid
            if (0 <= new_x < len(self.grid) and 0 <= new_y < len(self.grid) and
                [new_x, new_y] not in self.walls and
                [new_x, new_y] not in self.player_placed_blocks):
                current_x = new_x
                current_y = new_y
                self.grid[current_y][current_x] = True
                
                # Collect any coins along the path
                if [current_x, current_y] in self.coin_positions:
                    self.coin_positions.remove([current_x, current_y])
                    self.coins += 1
            else:
                break
        
        # Update final position
        if (current_x != self.player.x or current_y != self.player.y):
            self.player.moving = True
            self.player.x = current_x
            self.player.y = current_y
            
            # Check if we reached top-right corner
            if self.player.x == self.grid_size - 1 and self.player.y == 0:
                self.levels_beaten += 1  # Increment only when beating a level
                self.state = GameState.LEVEL_COMPLETE

    def update_player_movement(self):
        """Update player movement animation."""
        if self.player.moving:
            self.player.move_progress += 1
            if self.player.move_progress >= 1:
                self.player.moving = False
                self.player.move_progress = 0

    def check_game_over(self):
        """Check if player has lost."""
        player_pos = [self.player.x, self.player.y]
        if player_pos in self.walls or player_pos in self.player_placed_blocks:
            self.state = GameState.GAME_OVER

    def check_level_complete(self):
        """Check if level is complete (reached top-right corner)."""
        if (self.player.x == self.grid_size - 1 and 
            self.player.y == 0 and 
            self.state == GameState.PLAYING):
            self.levels_beaten = self.current_level - 1  # Update levels beaten
            self.current_level += 1  # Increment level
            self.state = GameState.LEVEL_COMPLETE
            return True
        return False