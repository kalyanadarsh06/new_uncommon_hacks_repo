import pygame
import random
import time
#sprites from https://www.spriters-resource.com/
#ChatGPT used to help with coding framework
# Initialize pygame
pygame.init()

# Game Constants
WIDTH, HEIGHT = 600, 600
CAR_WIDTH, CAR_HEIGHT = 30, 60  # Smaller car
TRACK_Y = HEIGHT // 4  # Track position
FPS = 60
BAR_SPEED = 3  # Bar speed for the green zone
MAX_HITS = 3  # Number of hits to move forward
WRONG_HITS_LIMIT = 3  # Wrong hits limit before game over
move_increment = 20 
 
# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
FINISH_LINE_COLOR = (255, 255, 0)
GRAY = (128, 128, 128)

# Screen setup
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Retro Racing Arcade")
font = pygame.font.Font(None, 36)

# Player class
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

    def draw(self):
        screen.blit(self.car_image, (self.x, self.y))  # Draw the car image

def game_loop():
    running = True
    clock = pygame.time.Clock()


    # Load car images
    background_image = pygame.image.load('racing/background.jpeg')
    background_image = pygame.transform.scale(background_image, (WIDTH, HEIGHT))

    car1_image = pygame.image.load("racing/car1.png")
    car2_image = pygame.image.load("racing/car2.png")
    finish_line = pygame.image.load("racing/finish.png")

    car1_image = pygame.transform.scale(car1_image, (70, 30))  # Adjust car sizes
    car2_image = pygame.transform.scale(car2_image, (70, 30))
    finish_line = pygame.transform.scale(finish_line, (600, 100))
    finish_line = pygame.transform.rotate(finish_line, 90)
    
    finish_line_x = WIDTH - 50

    player1_x = WIDTH // 3 - 100
    player2_x = WIDTH // 3 - 100
    player1_y = TRACK_Y 
    player2_y = TRACK_Y + 100
    bar_position = 0
    bar_direction = 1
    bar_speed = BAR_SPEED  # Speed of the green bar
    bar_x, bar_y = WIDTH // 3, HEIGHT - 100
    success_zone = (40, 160)  # Green zone for success
    hit_count1 = 0
    hit_count2 = 0
    total_score1 = 0
    total_score2 = 0
    fail_streak1 = 0
    fail_streak2 = 0
    max_hits_for_move = MAX_HITS  # Fewer hits needed to progress
    move_speed = 2  # Player car speed when moving forward
    wrong_hits1 = 0  # Track wrong hits for player 1
    wrong_hits2 = 0  # Track wrong hits for player 2
    finish_line_x = WIDTH - 100  # Position of the finish line

    # Initialize player cars with images
    player1 = PlayerCar(player1_x, player1_y, controls="player1", car_image=car1_image)
    player2 = PlayerCar(player2_x, player2_y, controls="player2", car_image=car2_image)
    
    start_time = time.time()  # Start time to calculate game duration

    while running:
        screen.blit(background_image, (0, 0))
        screen.blit(finish_line, (finish_line_x, 0))
        
        # Draw the finish line
        pygame.draw.line(screen, FINISH_LINE_COLOR, (finish_line_x, 0), (finish_line_x, HEIGHT), 5)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False


            # Player 1 controls (arrow keys)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if success_zone[0] <= bar_position <= success_zone[1]:
                        player1.x += move_increment  # Increase x position more significantly after each hit
                        hit_count1 += 1
                        total_score1 += 1
                        fail_streak1 = 0  # Reset fail streak on success
                        player1.speed = move_speed 
                    else:
                        wrong_hits1 += 1
                        if wrong_hits1 >= WRONG_HITS_LIMIT:
                            choice = win_screen("Player 2")
                            if choice == "play_again":
                                game_loop()
                            elif choice == "main_menu":
                                running = False
                                return
                           
                        player1.speed = 0  # Stop movement until corrected


            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_w:
                    if success_zone[0] <= bar_position <= success_zone[1]:
                        player2.x += move_increment  # Increase x position more significantly after each hit
                        hit_count2 += 1
                        total_score2 += 1
                        fail_streak2 = 0  # Reset fail streak on success
                        player2.speed = move_speed 
                    else:
                        wrong_hits2 += 1
                        if wrong_hits2 >= WRONG_HITS_LIMIT:
                            choice = win_screen("Player 1")
                            if choice == "play_again":
                                game_loop()
                            elif choice == "main_menu":
                                running = False
                                return
                        player2.speed = 0  # Stop movement until corrected
                if event.key == pygame.K_r: 
                    a = pause_menu()
                    if a == "stop":
                        return


        # Update bar movement
        bar_position += bar_speed * bar_direction
        if bar_position > 200 or bar_position < 0:
            bar_direction *= -1

        # Draw player cars and the sliding bar
        player1.draw()
        player2.draw()
        draw_sliding_bar(bar_position, success_zone, bar_x, bar_y)

        # Draw score and wrong hits
        score_text1 = font.render(f"Player 1 Score: {total_score1}", True, BLACK)
        screen.blit(score_text1, (10, 10))

        score_text2 = font.render(f"Player 2 Score: {total_score2}", True, BLACK)
        screen.blit(score_text2, (WIDTH - 250, 10))
        
        wrong_hits_text1 = font.render(f"Player 1 Wrong Hits: {wrong_hits1}", True, BLACK)
        screen.blit(wrong_hits_text1, (10, HEIGHT - 40))

        wrong_hits_text2 = font.render(f"Player 2 Wrong Hits: {wrong_hits2}", True, BLACK)
        screen.blit(wrong_hits_text2, (WIDTH - 300, HEIGHT - 40))

        # Move the bar when either player reaches 3 hits
        if hit_count1 >= MAX_HITS or hit_count2 >= MAX_HITS:
            hit_count1 = 0
            hit_count2 = 0
            bar_speed += 0.1  # Slightly increase the speed of the bar
            success_zone = (random.randint(10, 150), random.randint(160, 200))  # Change success zone size and position
            bar_position = random.randint(0, 200)  # Move the bar to a random position after each hit

        # Check if Player 1 reached the finish line
        if player1.x + CAR_WIDTH >= finish_line_x:
            choice = win_screen("Player 1")
            if choice == "play_again":
                game_loop()
            elif choice == "main_menu":
                running = False
                return

        # Check if Player 2 reached the finish line
        if player2.x + CAR_WIDTH >= finish_line_x:
            choice = win_screen("Player 2")
            if choice == "play_again":
                game_loop()
            elif choice == "main_menu":
                running = False
                return

        pygame.display.flip()
        clock.tick(FPS)

def win_screen(winner):
    selected_button = 0  # 0 for Play Again, 1 for Main Menu

    while True:
        screen.fill(WHITE)

        # Display win message
        win_text = font.render(f"{winner} Wins!", True, BLACK)
        screen.blit(win_text, (WIDTH // 2 - 100, HEIGHT // 3))

        # Create buttons
        play_again_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2, 200, 50)
        main_menu_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 70, 200, 50)

        pygame.draw.rect(screen, GRAY, play_again_button)
        pygame.draw.rect(screen, GRAY, main_menu_button)

        play_text = font.render("Play Again", True, BLACK)
        menu_text = font.render("Main Menu", True, BLACK)

        screen.blit(play_text, (WIDTH // 2 - 50, HEIGHT // 2 + 10))
        screen.blit(menu_text, (WIDTH // 2 - 50, HEIGHT // 2 + 80))

        # Highlight the selected button with a white border
        if selected_button == 0:
            pygame.draw.rect(screen, BLACK, play_again_button, 3)
        else:
            pygame.draw.rect(screen, BLACK, main_menu_button, 3)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                    selected_button = 1 - selected_button  # Toggle between 0 and 1
                if event.key == pygame.K_RETURN:
                    return "play_again" if selected_button == 0 else "main_menu"

                
def pause_menu():
    paused = True
    selected_button = 0  # 0 for Resume, 1 for Quit

    while paused:
        screen.fill(GRAY)
        text = font.render("Game Paused", True, BLACK)
        vari = "press buttons when cursor in green"
        instructions = font.render(vari, True, BLACK)

        resume_button = pygame.Rect(WIDTH // 2 - 70, HEIGHT // 2 - 20, 140, 40)
        quit_button = pygame.Rect(WIDTH // 2 - 70, HEIGHT // 2 + 40, 140, 40)

        # Draw buttons
        pygame.draw.rect(screen, GREEN, resume_button)
        pygame.draw.rect(screen, RED, quit_button)

        resume_text = font.render("Resume", True, BLACK)
        quit_text = font.render("Quit", True, BLACK)

        screen.blit(text, (WIDTH // 2 - 80, HEIGHT // 3))
        screen.blit(instructions, (WIDTH // 2 - 190, HEIGHT // 3 + 40))
        screen.blit(resume_text, (WIDTH // 2 - 35, HEIGHT // 2 - 10))
        screen.blit(quit_text, (WIDTH // 2 - 25, HEIGHT // 2 + 50))

        # Highlight the selected button with a white border
        if selected_button == 0:
            pygame.draw.rect(screen, WHITE, resume_button, 3)
        else:
            pygame.draw.rect(screen, WHITE, quit_button, 3)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                    selected_button = 1 - selected_button  # Toggle between 0 and 1
                if event.key == pygame.K_RETURN:
                    if selected_button == 0:
                        paused = False  # Resume
                        return "resume"
                    else:
                        return "stop"


def draw_sliding_bar(position, success_zone, bar_x, bar_y):
    pygame.draw.rect(screen, RED, (bar_x, bar_y, 200, 20))  # Red track
    pygame.draw.rect(screen, GREEN, (bar_x + success_zone[0], bar_y, success_zone[1] - success_zone[0], 20))  # Green success zone
    pygame.draw.rect(screen, BLACK, (bar_x + position, bar_y - 5, 10, 30))  # White indicator for the player to hit
if __name__ == "__main__":
    game_loop()
    print("end")