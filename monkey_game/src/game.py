import pygame
import random
import serial
import time

pygame.init()

# Screen settings
WIDTH, HEIGHT = 600, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Retro Monkey Run")

# Load Images
background_img = pygame.image.load("background.png").convert()
background_img = pygame.transform.scale(background_img, (WIDTH, HEIGHT))
player_sprite = pygame.image.load("retro_monkey.png").convert_alpha()
player_sprite = pygame.transform.scale(player_sprite, (60, 120))
tree_img = pygame.image.load("tree.png").convert_alpha()
tree_img = pygame.transform.scale(tree_img, (80, 120))
banana_img = pygame.image.load("banana.png").convert_alpha()
banana_img = pygame.transform.scale(banana_img, (70, 70))

# Lanes
lanes = [75, 225, 375, 525]
current_lane = 1

# Player settings
player_width, player_height = 60, 120
player_rect = pygame.Rect(lanes[current_lane] - player_width // 2, HEIGHT - player_height - 15, player_width, player_height)

# Obstacle settings
obstacle_width, obstacle_height = 80, 120
initial_obstacle_speed = 4
obstacle_speed = initial_obstacle_speed
obstacles = []
spawn_timer = 0

# Coin settings
coin_width, coin_height = 70, 70
coin_speed = 4
coins = []
coin_spawn_timer = 0

# Clock and score
clock = pygame.time.Clock()
score = 0
font = pygame.font.SysFont("Courier", 36, True)

# Game states
START, PLAYING, GAME_OVER, RESUME, WIN = 0, 1, 2, 3, 4
game_state = START
resume_selection = 0  # 0 for Resume/Play Again, 1 for Main Menu
should_return_to_menu = False  # New flag for returning to menu

# Connect to Arduino
arduino = serial.Serial('/dev/tty.usbmodem141101', 9600, timeout=0.1)

# Debounce timers
last_command_time = 0
command_cooldown = 200  # milliseconds

# Drawing functions
def draw():
    screen.blit(background_img, (0, 0))
    screen.blit(player_sprite, player_rect)

    for obs in obstacles:
        screen.blit(tree_img, obs)

    for coin in coins:
        screen.blit(banana_img, coin)

    score_text = font.render(f"SCORE: {score}", True, (255, 255, 255))
    screen.blit(score_text, (10, 10))

    pygame.display.flip()

def draw_start_screen():
    screen.blit(background_img, (0, 0))
    text = font.render("PRESS SPACE TO START", True, (255, 255, 255))
    screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2))
    pygame.display.flip()

def draw_game_over_screen():
    screen.blit(background_img, (0, 0))
    
    # Draw game over message
    title_font = pygame.font.SysFont("Courier", 48, True)
    info_font = pygame.font.SysFont("Courier", 24, True)
    
    title = title_font.render("GAME OVER", True, (255, 0, 0))
    subtitle = title_font.render(f"Score: {score}", True, (255, 255, 255))
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 50))
    screen.blit(subtitle, (WIDTH//2 - subtitle.get_width()//2, 120))
    
    info_msg = [
        "Watch out for those trees!",
        "",
        "Arduino: D to select, SPACE to confirm"
    ]
    
    for i, text in enumerate(info_msg):
        info_text = info_font.render(text, True, (255, 255, 255))
        screen.blit(info_text, (WIDTH//2 - info_text.get_width()//2, 200 + i*40))
    
    # Draw menu options side by side
    play_color = (255, 255, 0) if resume_selection == 0 else (255, 255, 255)
    menu_color = (255, 255, 0) if resume_selection == 1 else (255, 255, 255)
    
    play_text = font.render("Play Again", True, play_color)
    menu_text = font.render("Main Menu", True, menu_color)
    
    # Calculate positions for side-by-side buttons
    total_width = play_text.get_width() + menu_text.get_width() + 50  # 50px spacing between buttons
    start_x = WIDTH//2 - total_width//2
    
    screen.blit(play_text, (start_x, 400))
    screen.blit(menu_text, (start_x + play_text.get_width() + 50, 400))

    pygame.display.flip()

def draw_resume_screen():
    screen.blit(background_img, (0, 0))
    
    # Draw "How to Play" information
    title_font = pygame.font.SysFont("Courier", 48, True)
    info_font = pygame.font.SysFont("Courier", 24, True)
    
    title = title_font.render("How to Play", True, (255, 255, 255))
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 50))
    
    instructions = [
        "Use WASD to control the monkey",
        "A/D or Left/Right: Move between lanes",
        "Collect bananas for points",
        "Avoid trees",
        "Press R for this menu",
        "Arduino: D to select, SPACE to confirm"
    ]
    
    for i, text in enumerate(instructions):
        info_text = info_font.render(text, True, (255, 255, 255))
        screen.blit(info_text, (WIDTH//2 - info_text.get_width()//2, 150 + i*40))
    
    # Draw menu options side by side
    resume_color = (255, 255, 0) if resume_selection == 0 else (255, 255, 255)
    menu_color = (255, 255, 0) if resume_selection == 1 else (255, 255, 255)
    
    resume_text = font.render("Resume", True, resume_color)
    menu_text = font.render("Main Menu", True, menu_color)
    
    # Calculate positions for side-by-side buttons
    total_width = resume_text.get_width() + menu_text.get_width() + 50  # 50px spacing between buttons
    start_x = WIDTH//2 - total_width//2
    
    screen.blit(resume_text, (start_x, 400))
    screen.blit(menu_text, (start_x + resume_text.get_width() + 50, 400))

    pygame.display.flip()

def draw_win_screen():
    screen.blit(background_img, (0, 0))
    
    # Draw victory message
    title_font = pygame.font.SysFont("Courier", 48, True)
    info_font = pygame.font.SysFont("Courier", 24, True)
    
    title = title_font.render("VICTORY!", True, (255, 255, 0))
    subtitle = title_font.render("Score: 3000", True, (255, 255, 255))
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 50))
    screen.blit(subtitle, (WIDTH//2 - subtitle.get_width()//2, 120))
    
    congrats_msg = [
        "Congratulations!",
        "You've become the ultimate",
        "banana collector!",
        "",
        "Arduino: D to select, SPACE to confirm"
    ]
    
    for i, text in enumerate(congrats_msg):
        info_text = info_font.render(text, True, (255, 255, 255))
        screen.blit(info_text, (WIDTH//2 - info_text.get_width()//2, 200 + i*40))
    
    # Draw menu options side by side
    play_color = (255, 255, 0) if resume_selection == 0 else (255, 255, 255)
    menu_color = (255, 255, 0) if resume_selection == 1 else (255, 255, 255)
    
    play_text = font.render("Play Again", True, play_color)
    menu_text = font.render("Main Menu", True, menu_color)
    
    # Calculate positions for side-by-side buttons
    total_width = play_text.get_width() + menu_text.get_width() + 50  # 50px spacing between buttons
    start_x = WIDTH//2 - total_width//2
    
    screen.blit(play_text, (start_x, 400))
    screen.blit(menu_text, (start_x + play_text.get_width() + 50, 400))

    pygame.display.flip()

# Main game loop
running = True
while running:
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r and game_state == PLAYING:
                game_state = RESUME
            elif game_state == RESUME:
                if event.key == pygame.K_d:
                    resume_selection = 1  # Move to Main Menu
                elif event.key == pygame.K_a:
                    resume_selection = 0  # Move to Resume
                elif event.key == pygame.K_SPACE:
                    if resume_selection == 1:  # Main Menu selected
                        print("main menu")
                        game_state = START
                        obstacles.clear()
                        coins.clear()
                        score = 0
                        obstacle_speed = initial_obstacle_speed
                        coin_speed = initial_obstacle_speed
                    else:  # Resume selected
                        game_state = PLAYING

    # Handle Arduino input
    if arduino.in_waiting:
        command = arduino.readline().decode('utf-8').strip()
        now = pygame.time.get_ticks()

        if now - last_command_time > command_cooldown:
            last_command_time = now

            if game_state == START and command == "SPACE":
                game_state = PLAYING
            elif game_state == GAME_OVER:
                if command == "D":
                    resume_selection = 1  # Move to Main Menu
                elif command == "A":
                    resume_selection = 0  # Move to Play Again
                elif command == "SPACE":
                    if resume_selection == 1:  # Main Menu selected
                        print("main menu")
                        game_state = START
                        obstacles.clear()
                        coins.clear()
                        score = 0
                        obstacle_speed = initial_obstacle_speed
                        coin_speed = initial_obstacle_speed
                    else:  # Play Again selected
                        game_state = PLAYING
                        obstacles.clear()
                        coins.clear()
                        score = 0
                        obstacle_speed = initial_obstacle_speed
                        coin_speed = initial_obstacle_speed
            elif game_state == WIN:
                if command == "D":
                    resume_selection = 1  # Move to Main Menu
                elif command == "A":
                    resume_selection = 0  # Move to Play Again
                elif command == "SPACE":
                    if resume_selection == 1:  # Main Menu selected
                        print("main menu")
                        game_state = START
                        obstacles.clear()
                        coins.clear()
                        score = 0
                        obstacle_speed = initial_obstacle_speed
                        coin_speed = initial_obstacle_speed
                    else:  # Play Again selected
                        game_state = PLAYING
                        obstacles.clear()
                        coins.clear()
                        score = 0
                        obstacle_speed = initial_obstacle_speed
                        coin_speed = initial_obstacle_speed
            elif game_state == RESUME:
                if command == "D":
                    resume_selection = 1  # Move to Main Menu
                elif command == "A":
                    resume_selection = 0  # Move to Resume
                elif command == "SPACE":
                    if resume_selection == 1:  # Main Menu selected
                        print("main menu")
                        game_state = START
                        obstacles.clear()
                        coins.clear()
                        score = 0
                        obstacle_speed = initial_obstacle_speed
                        coin_speed = initial_obstacle_speed
                    else:  # Resume selected
                        game_state = PLAYING
            elif game_state == PLAYING:
                if command == "A" and current_lane > 0:
                    current_lane -= 1
                elif command == "D" and current_lane < 3:
                    current_lane += 1
                elif command == "R":  # Add R command for Arduino to open resume screen
                    game_state = RESUME

    if game_state == PLAYING:
        spawn_timer += 1
        coin_spawn_timer += 1
        score += 1
        if score % 300 == 0:
            obstacle_speed += 0.2
            coin_speed += 0.2

        # Check for win condition
        if score >= 3000:
            game_state = WIN

        player_rect.x = lanes[current_lane] - player_width // 2

        obstacle_lane = None
        if spawn_timer > 110:
            obstacle_lane = random.choice(lanes)
            stack_height = random.randint(1, 3)
            for i in range(stack_height):
                obstacles.append(pygame.Rect(obstacle_lane - obstacle_width // 2, -(i+1)*obstacle_height, obstacle_width, obstacle_height))
            spawn_timer = 0

        if coin_spawn_timer > 90:
            available_lanes = lanes[:]
            if obstacle_lane and obstacle_lane in available_lanes:
                available_lanes.remove(obstacle_lane)
            coin_lane = random.choice(available_lanes)
            coin_rect = pygame.Rect(coin_lane - coin_width // 2, -coin_height, coin_width, coin_height)
            coins.append(coin_rect)
            coin_spawn_timer = 0

        for obs in obstacles[:]:
            obs.y += obstacle_speed
            if obs.top > HEIGHT:
                obstacles.remove(obs)
            if obs.colliderect(player_rect):
                game_state = GAME_OVER

        for coin in coins[:]:
            coin.y += coin_speed
            if coin.top > HEIGHT:
                coins.remove(coin)
            if coin.collidepoint(player_rect.centerx, player_rect.top):
                score += 100
                coins.remove(coin)

        draw()

    elif game_state == START:
        draw_start_screen()
    elif game_state == GAME_OVER:
        draw_game_over_screen()
    elif game_state == RESUME:
        draw_resume_screen()
    elif game_state == WIN:
        draw_win_screen()

pygame.quit()
