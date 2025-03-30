import pygame
import random
import time

pygame.init()

# Screen settings
WIDTH, HEIGHT = 600, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Retro Monkey Run")

# Load Images
background_img = pygame.image.load("monkey_game/src/background.png").convert()
background_img = pygame.transform.scale(background_img, (WIDTH, HEIGHT))
player_sprite = pygame.image.load("monkey_game/src/retro_monkey.png").convert_alpha()
player_sprite = pygame.transform.scale(player_sprite, (60, 120))
tree_img = pygame.image.load("monkey_game/src/tree.png").convert_alpha()
tree_img = pygame.transform.scale(tree_img, (80, 120))
banana_img = pygame.image.load("monkey_game/src/banana.png").convert_alpha()
banana_img = pygame.transform.scale(banana_img, (70, 70))

# Lanes
lanes = [75, 225, 375, 525]
current_lane = 1  # Starts at the second lane

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
START, PLAYING, GAME_OVER = 0, 1, 2
game_state = START

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
    text = font.render(f"GAME OVER! SCORE: {score}", True, (255, 0, 0))
    screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - 20))
    restart_text = font.render("PRESS SPACE TO RETRY", True, (255, 255, 255))
    screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 20))
    pygame.display.flip()

# Main game loop
# Main game loop
if __name__ == "__main__":
    running = True
    while running:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if game_state == START:
                        game_state = PLAYING
                    elif game_state == GAME_OVER:
                        game_state = PLAYING
                        obstacles.clear()
                        coins.clear()
                        score = 0
                        obstacle_speed = initial_obstacle_speed
                        coin_speed = initial_obstacle_speed
                # Handle player movement with WASD or arrow keys
                elif event.key == pygame.K_a and current_lane > 0:  # Move up (to previous lane)
                    current_lane -= 1
                elif event.key == pygame.K_d and current_lane < len(lanes) - 1:  # Move down (to next lane)
                    current_lane += 1

        if game_state == PLAYING:
            spawn_timer += 1
            coin_spawn_timer += 1
            score += 1
            if score % 300 == 0:
                obstacle_speed += 0.2
                coin_speed += 0.2

            # Update player position (centered on the lane)
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
                    score += 10
                    coins.remove(coin)

            draw()

        elif game_state == START:
            draw_start_screen()
        elif game_state == GAME_OVER:
            draw_game_over_screen()

