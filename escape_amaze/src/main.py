import pyxel
from maze_generator import MazeGenerator
from game_state import Game, GameState, Player

class MazeGame:
    def __init__(self):
        # Initialize game window
        self.CELL_SIZE = 60  # Increased cell size for 600x600 window
        self.GRID_SIZE = 10
        window_size = self.CELL_SIZE * self.GRID_SIZE
        pyxel.init(window_size, window_size, title="AI Maze Escape")
        
        # Colors
        self.COLORS = {
            'wall': 5,      # Dark blue
            'player': 11,   # Yellow
            'coin': 10,     # Yellow
            'exit': 3,      # Green
            'path': 1,      # Dark blue
            'bg': 0,       # Black
            'text': 7,      # White
            'placed_block': 13,  # Purple for player-placed blocks
            'cursor': 14,   # Pink for cursor highlight
            'highlight': 6  # Light blue for highlighting
        }
        
        # Initialize game components
        self.maze_generator = MazeGenerator()
        self.game = Game()
        
        # Menu states and text
        self.menu_state = None  # Can be 'pause' or 'victory'
        self.menu_cursor_pos = 0  # 0 for left button, 1 for right button
        self.game_instructions = [
            "Your goal is to beat as many levels as possible.",
            "Arrows move your ball, WASD moves your cursor,",
            "[f] places a block, [e] deletes a block.",
            "You can collect coins to buy blocks and deletions.",
            "After 10 levels, you win!"
        ]
        
        # Start first level
        self.init_level()
        self.game.state = GameState.PLAYING
        
        # Start the game loop
        pyxel.run(self.update, self.draw)
    
    def init_level(self):
        """Initialize a new level."""
        maze_data = self.maze_generator.generate_maze(self.game.current_level)
        self.game.init_level(maze_data)
    
    def update(self):
        """Update game state."""
        if self.menu_state:
            # Handle menu navigation
            if pyxel.btnp(pyxel.KEY_A) or pyxel.btnp(pyxel.KEY_D) or \
               pyxel.btnp(pyxel.KEY_W) or pyxel.btnp(pyxel.KEY_S):  
                self.menu_cursor_pos = 1 - self.menu_cursor_pos  # Toggle between 0 and 1
            
            if pyxel.btnp(pyxel.KEY_RETURN):
                if self.menu_cursor_pos == 1:  
                    pyxel.quit()
                else:  
                    self.menu_state = None  # Just clear the menu state, nothing else
            

        elif self.game.state == GameState.PLAYING:
            # Only show victory menu the first time reaching 10 levels
            if self.game.levels_beaten == 10 and not self.menu_state:
                self.menu_state = 'victory'
                self.menu_cursor_pos = 0
                return
            
            # Handle input
            if not self.game.player.moving:
                if pyxel.btnp(pyxel.KEY_UP):
                    self.game.start_movement(0, -1)
                elif pyxel.btnp(pyxel.KEY_DOWN):
                    self.game.start_movement(0, 1)
                elif pyxel.btnp(pyxel.KEY_LEFT):
                    self.game.start_movement(-1, 0)
                elif pyxel.btnp(pyxel.KEY_RIGHT):
                    self.game.start_movement(1, 0)
                elif pyxel.btnp(pyxel.KEY_C):  
                    self.game.commit_blockcide()
                elif pyxel.btnp(pyxel.KEY_R):  
                    self.menu_state = 'pause'
                    self.menu_cursor_pos = 0
            
            # Update cursor position with WASD
            if pyxel.btnp(pyxel.KEY_W):
                self.game.cursor.move(0, -1, self.GRID_SIZE)
            elif pyxel.btnp(pyxel.KEY_S):
                self.game.cursor.move(0, 1, self.GRID_SIZE)
            elif pyxel.btnp(pyxel.KEY_A):
                self.game.cursor.move(-1, 0, self.GRID_SIZE)
            elif pyxel.btnp(pyxel.KEY_D):
                self.game.cursor.move(1, 0, self.GRID_SIZE)
            
            # Place block with F key at cursor position
            if pyxel.btnp(pyxel.KEY_F):
                self.game.try_place_block()
                
            # Destroy block with E key at cursor position
            if pyxel.btnp(pyxel.KEY_E):
                self.game.try_destroy_block()
            
            # Update player movement
            self.game.update_player_movement()
            
            # Check win/lose conditions
            self.game.check_game_over()
            self.game.check_level_complete()
            
        elif self.game.state == GameState.LEVEL_COMPLETE:
            if pyxel.btnp(pyxel.KEY_RETURN):
                self.game.levels_beaten += 1
                self.game.current_level += 1  
                self.init_level()
                self.game.state = GameState.PLAYING
                
        elif self.game.state == GameState.GAME_OVER:
            if pyxel.btnp(pyxel.KEY_C):
                self.game.reset_game()
                self.init_level()
                
        elif self.game.state == GameState.BLOCKCIDE:
            if pyxel.btnp(pyxel.KEY_C):
                self.game.reset_game()
                self.init_level()
    
    def draw(self):
        """Draw the game."""
        pyxel.cls(self.COLORS['bg'])
        
        # Draw grid and visited cells
        for y in range(self.GRID_SIZE):
            for x in range(self.GRID_SIZE):
                if self.game.grid[y][x]:
                    self.draw_cell(x, y, self.COLORS['path'])
        
        # Draw walls
        for wall in self.game.walls:
            self.draw_cell(wall[0], wall[1], self.COLORS['wall'])
        
        # Draw player-placed blocks
        for block in self.game.player_placed_blocks:
            self.draw_cell(block[0], block[1], self.COLORS['placed_block'])
        
        # Draw coins
        for coin in self.game.coin_positions:
            self.draw_coin(coin[0], coin[1])
        
        # Draw goal (top-right corner)
        self.draw_cell(self.GRID_SIZE - 1, 0, self.COLORS['exit'])
        
        # Draw player
        self.draw_player(self.game.player.x, self.game.player.y)
        
        # Draw cursor with highlight effect
        cursor_x = self.game.cursor.x
        cursor_y = self.game.cursor.y
        pos = [cursor_x, cursor_y]
        
        # Draw lighter version of whatever is under the cursor
        if pos in self.game.walls or pos in self.game.player_placed_blocks:
            color = self.COLORS['highlight']  
        elif pos == [self.GRID_SIZE - 1, 0]:  
            color = self.COLORS['highlight']  
        else:
            color = self.COLORS['cursor']  
            
        self.draw_cell(cursor_x, cursor_y, color)
        
        # Draw UI
        self.draw_ui()
        
        # Draw coins and costs
        pyxel.text(4, 4, f"Coins: {self.game.coins}", self.COLORS['text'])
        next_place_cost = self.game.get_next_block_cost()
        next_destroy_cost = self.game.get_next_destroy_cost()
        pyxel.text(4, 12, f"Place Cost: {next_place_cost}", self.COLORS['text'])
        pyxel.text(4, 20, f"Destroy Cost: {next_destroy_cost}", self.COLORS['text'])
        pyxel.text(4, 28, f"Level: {self.game.current_level}", self.COLORS['text'])
        pyxel.text(4, 36, f"Levels Beaten: {self.game.levels_beaten}", self.COLORS['text'])
        
        # Draw instructions
        pyxel.text(4, pyxel.height - 40, "Arrow keys to move", self.COLORS['text'])
        pyxel.text(4, pyxel.height - 32, "WASD to move cursor", self.COLORS['text'])
        pyxel.text(4, pyxel.height - 24, "F to place block", self.COLORS['text'])
        pyxel.text(4, pyxel.height - 16, "E to remove wall/block", self.COLORS['text'])
        pyxel.text(4, pyxel.height - 8, "C to forfeit game", self.COLORS['text'])
        
        # Draw game over screen
        if self.game.state == GameState.GAME_OVER:
            self.draw_centered_text("Game Over!", pyxel.height // 2)
            self.draw_centered_text("Press C to restart", pyxel.height // 2 + 10)
            self.draw_centered_text(f"Levels Beaten: {self.game.levels_beaten}", pyxel.height // 2 + 20)
        
        # Draw level complete screen
        elif self.game.state == GameState.LEVEL_COMPLETE:
            self.draw_centered_text("Level Complete!", pyxel.height // 2)
            self.draw_centered_text("Press ENTER for next level", pyxel.height // 2 + 10)
        
        # Draw blockcide screen
        elif self.game.state == GameState.BLOCKCIDE:
            self.draw_centered_text("You commit blockcide and die.", pyxel.height // 2)
            self.draw_centered_text(f"Levels Beaten: {self.game.levels_beaten}", pyxel.height // 2 + 10)
            self.draw_centered_text("Press C to restart", pyxel.height // 2 + 20)
        
        # Draw menu overlays if active
        if self.menu_state == 'pause':
            # Draw semi-transparent overlay
            for y in range(pyxel.height):
                for x in range(pyxel.width):
                    if (x + y) % 2 == 0:  
                        pyxel.pset(x, y, self.COLORS['bg'])
            
            # Draw instructions
            y_pos = 50
            for line in self.game_instructions:
                self.draw_centered_text(line, y_pos)
                y_pos += 10
            
            # Draw menu buttons
            self.draw_menu_button("Resume", pyxel.width // 4, pyxel.height - 50, self.menu_cursor_pos == 0)
            self.draw_menu_button("Main Menu", 3 * pyxel.width // 4, pyxel.height - 50, self.menu_cursor_pos == 1)
            
        elif self.menu_state == 'victory':
            # Draw semi-transparent overlay
            for y in range(pyxel.height):
                for x in range(pyxel.width):
                    if (x + y) % 2 == 0:
                        pyxel.pset(x, y, self.COLORS['bg'])
            
            # Draw victory message
            self.draw_centered_text("You win!", pyxel.height // 3)
            
            # Draw menu buttons
            self.draw_menu_button("Continue to Unlimited", pyxel.width // 4, pyxel.height - 50, self.menu_cursor_pos == 0)
            self.draw_menu_button("Main Menu", 3 * pyxel.width // 4, pyxel.height - 50, self.menu_cursor_pos == 1)
    
    def draw_cell(self, x, y, color):
        """Draw a single cell."""
        pyxel.rect(
            x * self.CELL_SIZE,
            y * self.CELL_SIZE,
            self.CELL_SIZE - 1,
            self.CELL_SIZE - 1,
            color
        )
    
    def draw_coin(self, x, y):
        """Draw a coin."""
        center_x = x * self.CELL_SIZE + self.CELL_SIZE // 2
        center_y = y * self.CELL_SIZE + self.CELL_SIZE // 2
        radius = self.CELL_SIZE // 4
        pyxel.circ(center_x, center_y, radius, self.COLORS['coin'])
    
    def draw_player(self, x, y):
        """Draw the player."""
        center_x = x * self.CELL_SIZE + self.CELL_SIZE // 2
        center_y = y * self.CELL_SIZE + self.CELL_SIZE // 2
        radius = self.CELL_SIZE // 3
        pyxel.circ(center_x, center_y, radius, self.COLORS['player'])
    
    def draw_ui(self):
        """Draw game UI."""
        # Score and level
        pyxel.text(4, 20, f"Level: {self.game.current_level}", 7)
    
    def draw_centered_text(self, text, y):
        """Draw text centered on screen."""
        x = (pyxel.width - len(text) * 4) // 2
        pyxel.text(x, y, text, self.COLORS['text'])
        
    def draw_menu_button(self, text, x, y, selected):
        """Draw a menu button with selection highlight."""
        color = self.COLORS['highlight'] if selected else self.COLORS['text']
        text_width = len(text) * 4  
        pyxel.text(x - text_width // 2, y, text, color)
    
    def reset_game(self):
        """Reset the game state without reinitializing Pyxel."""
        self.game = Game()
        self.init_level()
        self.game.state = GameState.PLAYING
    
    def check_game_over(self):
        """Check win/lose conditions."""
        if self.game.levels_beaten >= 10 and self.menu_state == 'victory':
            self.menu_state = None
            self.menu_cursor_pos = 0

if __name__ == '__main__':
    MazeGame()