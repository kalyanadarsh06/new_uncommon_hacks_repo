import pygame
import random
import time
import serial

# Game Constants
WIDTH, HEIGHT = 600, 600
CAR_WIDTH, CAR_HEIGHT = 30, 60
TRACK_Y = HEIGHT // 4
FPS = 60
BAR_SPEED = 2
MAX_HITS = 3
WRONG_HITS_LIMIT = 3
move_increment = 40
command_cooldown = 100

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
FINISH_LINE_COLOR = (255, 255, 0)
GRAY = (128, 128, 128)

# Initialize Pygame and Arduino
pygame.init()
font = pygame.font.Font(None, 36)

try:
    arduino = serial.Serial('/dev/tty.usbmodem141101', 9600, timeout=0.1)
    print("Connected to Arduino on /dev/tty.usbmodem141101")
except:
    arduino = None
    print("No Arduino found. Game will use keyboard controls only.")

last_command_time = pygame.time.get_ticks()
command_cooldown = 100

# Screen setup
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Retro Racing Arcade")

# Player class
class PlayerCar:
    def __init__(self, x, y, controls, car_image, speed=0):
        self.x = x
        self.y = y
        self.speed = speed  # Player speed when allowed to move forward
        self.controls = controls  # Control keys for the player
        self.progress = 0  # Track player progress
        self.car_image = car_image  # Car image for the player

    def move(self):
        self.x += self.speed

    def draw(self, screen):
        screen.blit(self.car_image, (self.x, self.y))  # Draw the car image

def game_loop():
    global last_command_time
    
    # Initialize game objects and variables
    background_image = pygame.image.load('../background.jpeg')
    background_image = pygame.transform.scale(background_image, (WIDTH, HEIGHT))

    car1_image = pygame.image.load("../car1.png")
    car2_image = pygame.image.load("../car2.png")
    finish_line = pygame.image.load("../finish.png")

    car1_image = pygame.transform.scale(car1_image, (70, 30))
    car2_image = pygame.transform.scale(car2_image, (70, 30))
    finish_line = pygame.transform.scale(finish_line, (600, 100))
    finish_line = pygame.transform.rotate(finish_line, 90)
    
    player1 = PlayerCar(50, HEIGHT//3, {"up": pygame.K_UP, "down": pygame.K_DOWN}, car1_image)
    player2 = PlayerCar(50, 2*HEIGHT//3, {"up": pygame.K_w, "down": pygame.K_s}, car2_image)
    
    # Game state variables
    running = True
    clock = pygame.time.Clock()
    bar_position = 100
    bar_direction = 1
    
    # Dynamic success zone variables
    min_zone_width = 20  # Minimum width of green zone
    max_zone_width = 80  # Maximum width of green zone
    current_zone_width = 40  # Starting width
    zone_shrink_rate = 2  # How much to shrink by each time
    zone_move_timer = pygame.time.get_ticks()
    zone_move_delay = 3000  # Move zone every 3 seconds
    success_zone = [80, 120]  # Initial success zone
    
    hit_count1 = hit_count2 = 0
    wrong_hits1 = wrong_hits2 = 0
    finish_line_x = WIDTH - 100
    
    # Score variables
    total_score1 = total_score2 = 0
    start_time = time.time()
    difficulty_level = 1

    def update_success_zone():
        nonlocal current_zone_width, success_zone, difficulty_level
        # Shrink the zone as game progresses
        current_zone_width = int(max(min_zone_width, max_zone_width - (difficulty_level * zone_shrink_rate)))
        
        # Randomly position the zone, ensuring it stays within bounds
        zone_start = random.randint(0, int(200 - current_zone_width))
        success_zone = [zone_start, zone_start + current_zone_width]
        
        # Increase difficulty
        difficulty_level += 0.5
        
        # Increase bar speed with difficulty
        return min(5, BAR_SPEED + (difficulty_level * 0.2))

    # Draw initial instructions
    def draw_instructions():
        instructions = [
            "Player 1: Press SPACE in green zone",
            "Player 2: Press A in green zone",
            "Press R to pause",
            "Green zone shrinks as you progress!"
        ]
        y = HEIGHT - 150
        for instruction in instructions:
            text = font.render(instruction, True, BLACK)
            screen.blit(text, (WIDTH//2 - text.get_width()//2, y))
            y += 30

    # Game loop
    show_instructions = True
    instruction_timer = pygame.time.get_ticks()
    current_bar_speed = BAR_SPEED

    while running:
        screen.blit(background_image, (0, 0))
        screen.blit(finish_line, (finish_line_x, 0))
        
        # Update success zone periodically
        if pygame.time.get_ticks() - zone_move_timer > zone_move_delay:
            zone_move_timer = pygame.time.get_ticks()
            current_bar_speed = update_success_zone()
            
        # Draw the finish line
        pygame.draw.line(screen, FINISH_LINE_COLOR, (finish_line_x, 0), (finish_line_x, HEIGHT), 5)

        # Show instructions for first 5 seconds
        if show_instructions and pygame.time.get_ticks() - instruction_timer < 5000:
            draw_instructions()
        else:
            show_instructions = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Player controls
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if bar_position >= success_zone[0] and bar_position <= success_zone[1]:
                        hit_count1 += 1
                        if hit_count1 >= MAX_HITS:
                            player1.x += move_increment
                            hit_count1 = 0
                            total_score1 += 10
                    else:
                        wrong_hits1 += 1
                        if wrong_hits1 >= WRONG_HITS_LIMIT:
                            choice = win_screen("Player 2")
                            if choice == "play_again":
                                return game_loop()
                            elif choice == "main_menu":
                                running = False
                                return
                        player1.speed = 0

                elif event.key == pygame.K_a:
                    if bar_position >= success_zone[0] and bar_position <= success_zone[1]:
                        hit_count2 += 1
                        if hit_count2 >= MAX_HITS:
                            player2.x += move_increment
                            hit_count2 = 0
                            total_score2 += 10
                    else:
                        wrong_hits2 += 1
                        if wrong_hits2 >= WRONG_HITS_LIMIT:
                            choice = win_screen("Player 1")
                            if choice == "play_again":
                                return game_loop()
                            elif choice == "main_menu":
                                running = False
                                return
                        player2.speed = 0

                elif event.key == pygame.K_r:
                    a = pause_menu()
                    if a == "stop":
                        return

        # Handle Arduino input
        if arduino and arduino.in_waiting:
            try:
                command = arduino.readline().decode('utf-8').strip()
                now = pygame.time.get_ticks()
                
                if now - last_command_time > command_cooldown:
                    last_command_time = now
                    
                    if command == "SPACE":
                        if bar_position >= success_zone[0] and bar_position <= success_zone[1]:
                            hit_count1 += 1
                            if hit_count1 >= MAX_HITS:
                                player1.x += move_increment
                                hit_count1 = 0
                                total_score1 += 10
                        else:
                            wrong_hits1 += 1
                            if wrong_hits1 >= WRONG_HITS_LIMIT:
                                choice = win_screen("Player 2")
                                if choice == "play_again":
                                    return game_loop()
                                elif choice == "main_menu":
                                    running = False
                                    return
                            player1.speed = 0

                    elif command == "A":
                        if bar_position >= success_zone[0] and bar_position <= success_zone[1]:
                            hit_count2 += 1
                            if hit_count2 >= MAX_HITS:
                                player2.x += move_increment
                                hit_count2 = 0
                                total_score2 += 10
                        else:
                            wrong_hits2 += 1
                            if wrong_hits2 >= WRONG_HITS_LIMIT:
                                choice = win_screen("Player 1")
                                if choice == "play_again":
                                    return game_loop()
                                elif choice == "main_menu":
                                    running = False
                                    return
                            player2.speed = 0

                    elif command == "R":
                        a = pause_menu()
                        if a == "stop":
                            return
            except Exception as e:
                pass

        # Update bar movement with current speed
        bar_position += current_bar_speed * bar_direction
        if bar_position > 200 or bar_position < 0:
            bar_direction *= -1

        # Draw game elements
        player1.draw(screen)
        player2.draw(screen)
        
        # Draw sliding bars
        draw_sliding_bar(bar_position, success_zone, 50, HEIGHT//3 - 50)
        draw_sliding_bar(bar_position, success_zone, 50, 2*HEIGHT//3 - 50)
        
        # Draw scores and hit counts
        score_text1 = font.render(f"P1 Score: {total_score1} Hits: {hit_count1}/{MAX_HITS}", True, BLACK)
        score_text2 = font.render(f"P2 Score: {total_score2} Hits: {hit_count2}/{MAX_HITS}", True, BLACK)
        level_text = font.render(f"Difficulty: {int(difficulty_level)}", True, BLACK)
        screen.blit(score_text1, (10, 10))
        screen.blit(score_text2, (10, 40))
        screen.blit(level_text, (WIDTH - 150, 10))

        # Check win conditions
        if player1.x + CAR_WIDTH >= finish_line_x:
            choice = win_screen("Player 1")
            if choice == "play_again":
                return game_loop()
            elif choice == "main_menu":
                running = False
                return

        if player2.x + CAR_WIDTH >= finish_line_x:
            choice = win_screen("Player 2")
            if choice == "play_again":
                return game_loop()
            elif choice == "main_menu":
                running = False
                return

        pygame.display.flip()
        clock.tick(FPS)

def win_screen(winner):
    win = True
    selection = 0  # 0 for Play Again, 1 for Main Menu
    
    while win:
        screen.fill(WHITE)
        
        # Draw winner announcement
        winner_text = font.render(f"{winner} WINS!", True, BLACK)
        screen.blit(winner_text, (WIDTH//2 - winner_text.get_width()//2, HEIGHT//3))
        
        # Draw menu options with selection indicator
        play_text = font.render("▶ Play Again" if selection == 0 else "  Play Again", True, BLACK)
        menu_text = font.render("▶ Main Menu" if selection == 1 else "  Main Menu", True, BLACK)
        
        # Draw boxes around options
        play_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT//2, 200, 40)
        menu_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 50, 200, 40)
        
        # Highlight selected option
        if selection == 0:
            pygame.draw.rect(screen, GREEN, play_rect, 3)
            pygame.draw.rect(screen, BLACK, menu_rect, 1)
        else:
            pygame.draw.rect(screen, BLACK, play_rect, 1)
            pygame.draw.rect(screen, GREEN, menu_rect, 3)
        
        screen.blit(play_text, (WIDTH//2 - play_text.get_width()//2, HEIGHT//2 + 10))
        screen.blit(menu_text, (WIDTH//2 - menu_text.get_width()//2, HEIGHT//2 + 60))
        
        # Draw controls help
        controls_text = font.render("A: Change Selection    SPACE: Confirm", True, GRAY)
        screen.blit(controls_text, (WIDTH//2 - controls_text.get_width()//2, HEIGHT - 50))
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "main_menu"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP or event.key == pygame.K_DOWN:
                    selection = 1 - selection
                if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    if selection == 0:
                        return "play_again"
                    else:
                        return "main_menu"
                        
        # Handle Arduino input
        if arduino and arduino.in_waiting:
            try:
                command = arduino.readline().decode('utf-8').strip()
                if command == "A":
                    selection = 1 - selection
                elif command == "SPACE":
                    if selection == 0:
                        return "play_again"
                    else:
                        return "main_menu"
            except:
                pass
                
        pygame.display.flip()

def pause_menu():
    pause = True
    selection = 0  # 0 for Resume, 1 for Main Menu
    
    while pause:
        screen.fill(WHITE)
        
        # Draw title
        title_text = font.render("GAME PAUSED", True, BLACK)
        screen.blit(title_text, (WIDTH//2 - title_text.get_width()//2, HEIGHT//3))
        
        # Draw menu options with selection indicator
        resume_text = font.render("▶ Resume" if selection == 0 else "  Resume", True, BLACK)
        menu_text = font.render("▶ Main Menu" if selection == 1 else "  Main Menu", True, BLACK)
        
        # Draw boxes around options
        resume_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 - 50, 200, 40)
        menu_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 50, 200, 40)
        
        # Highlight selected option
        if selection == 0:
            pygame.draw.rect(screen, GREEN, resume_rect, 3)
            pygame.draw.rect(screen, BLACK, menu_rect, 1)
        else:
            pygame.draw.rect(screen, BLACK, resume_rect, 1)
            pygame.draw.rect(screen, GREEN, menu_rect, 3)
        
        screen.blit(resume_text, (WIDTH//2 - resume_text.get_width()//2, HEIGHT//2 - 40))
        screen.blit(menu_text, (WIDTH//2 - menu_text.get_width()//2, HEIGHT//2 + 60))
        
        # Draw controls help
        controls_text = font.render("A: Change Selection    SPACE: Confirm", True, GRAY)
        screen.blit(controls_text, (WIDTH//2 - controls_text.get_width()//2, HEIGHT - 50))
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "stop"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP or event.key == pygame.K_DOWN:
                    selection = 1 - selection
                if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    if selection == 0:
                        return None
                    else:
                        return "stop"
                        
        # Handle Arduino input
        if arduino and arduino.in_waiting:
            try:
                command = arduino.readline().decode('utf-8').strip()
                if command == "A":
                    selection = 1 - selection
                elif command == "SPACE":
                    if selection == 0:
                        return None
                    else:
                        return "stop"
            except:
                pass
                
        pygame.display.flip()
        
def draw_sliding_bar(position, success_zone, bar_x, bar_y):
    # Draw the track (red background)
    pygame.draw.rect(screen, RED, (bar_x, bar_y, 200, 20))
    
    # Draw success zone (green)
    success_width = success_zone[1] - success_zone[0]
    pygame.draw.rect(screen, GREEN, (bar_x + success_zone[0], bar_y, success_width, 20))
    
    # Draw moving indicator (black)
    pygame.draw.rect(screen, BLACK, (bar_x + position, bar_y - 5, 10, 30))
    
    # Draw text above the bar
    text = font.render("Hit in Green Zone!", True, BLACK)
    screen.blit(text, (bar_x + 20, bar_y - 30))


def main():
    if __name__ == "__main__":
        game_loop()
        if arduino:
            arduino.close()
        pygame.quit()
        print("Game ended")

if __name__ == "__main__":
    main()