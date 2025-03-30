import pygame
import time
import sys
#sys.path.insert(1, "../../racing/src/main.py")
# Initialize Pygame
#import main as a
from racing.src import main as racer
from space_shooter import space_shooter
#from monkey_game.src import game
from dungeon_escape.src import game as game4
from escape_amaze.src import game_state 
from escape_amaze.src import maze_generator
from escape_amaze.src import main as main2 
pygame.init()

# Set the screen dimensions
WIDTH, HEIGHT = 600, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Arcade")

# Define colors
WHITE = (255, 255, 255)
HOVER_COLOR = (255, 223, 0)  # Yellow highlight color
DARK_BLUE = (40, 44, 52)
current_game = 0  # Track current selected game

# Set up fonts
font = pygame.font.SysFont('Arial', 72)
small_font = pygame.font.SysFont('Arial', 24)

# Load the image for the games (replace with your image path)
image1 = pygame.image.load("combine/game1art.png")  # Path to your image
image1 = pygame.transform.scale(image1, (150, 100))  # Resize image to fit the rectangle size
image2 = pygame.image.load("combine/game2art.png")  # Path to your image
image2 = pygame.transform.scale(image2, (100, 100))  # Resize image to fit the rectangle size
image2 = pygame.transform.rotate(image2, 90)
image3 = pygame.image.load("combine/game3art.png")  # Path to your image
image3 = pygame.transform.scale(image3, (150, 100))  # Resize image to fit the rectangle size
image4 = pygame.image.load("combine/game4art.png")  # Path to your image
image4 = pygame.transform.scale(image4, (150, 100))  # Resize image to fit the rectangle size
image5 = pygame.image.load("combine/game5art.jpg")  # Path to your image
image5 = pygame.transform.scale(image5, (150, 100))  # Resize image to fit the rectangle size
image6 = pygame.image.load("combine/game6art.png")  # Path to your image
image6 = pygame.transform.scale(image6, (150, 100))  # Resize image to fit the rectangle size

image = [image1, image2, image3, image4, image5, image6]

# Function to display text
def display_text(text, font, color, y_offset=0):
    label = font.render(text, True, color)
    text_rect = label.get_rect(center=(WIDTH // 2, HEIGHT // 2 + y_offset))
    screen.blit(label, text_rect)

# Main function to display the arcade screen and transition
def arcade_game():
    global current_game  # Use the global variable to track the current game selection
    clock = pygame.time.Clock()
    start_time = time.time()
    
    # Show "Arcade" on the screen for 5 seconds
    while True:
        screen.fill(DARK_BLUE)

        # Event handling for quitting the program
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
        
        # Check elapsed time
        if time.time() - start_time > 5:
            break

        display_text("Arcade", font, WHITE)
        pygame.display.flip()
        clock.tick(60)
    
    # Transition to the second screen with 6 images
    padding_x = (WIDTH - 3 * 150) // 4  # Space between columns
    padding_y = (HEIGHT - 2 * 100) // 3  # Space between rows
    
    image_positions = [
        (padding_x, padding_y),
        (2 * padding_x + 150, padding_y),
        (3 * padding_x + 2 * 150, padding_y),
        (padding_x, 2 * padding_y + 100),
        (2 * padding_x + 150, 2 * padding_y + 100),
        (3 * padding_x + 2 * 150, 2 * padding_y + 100)
    ]
    
    while True:
        screen.fill(DARK_BLUE)

        mouse_pos = pygame.mouse.get_pos()  # Get mouse position inside the loop
        
        for i, (x, y) in enumerate(image_positions):
            # Create a rectangle around the image to detect hover
            image_rect = pygame.Rect(x, y, 150, 150)
            
            # Check if the mouse is hovering over the image
            if current_game == 0: 
                pygame.draw.rect(screen, HOVER_COLOR, pygame.Rect(padding_x, padding_y, 150, 100), 5)
                # Display image number
            if current_game == 1:
                pygame.draw.rect(screen, HOVER_COLOR, pygame.Rect(2 * padding_x + 150, padding_y, 150, 100), 5)
                # Display image number

            if current_game == 2:
                pygame.draw.rect(screen, HOVER_COLOR, pygame.Rect(3 * padding_x + 2 * 150, padding_y, 150, 100), 5)
                # Display image number

            if current_game == 3:
                pygame.draw.rect(screen, HOVER_COLOR, pygame.Rect(padding_x, 2 * padding_y + 100, 150, 100), 5)
                # Display image number

            if current_game == 4:
                pygame.draw.rect(screen, HOVER_COLOR, pygame.Rect(2 * padding_x + 150, 2 * padding_y + 100, 150, 100), 5)
                # Display image number

            if current_game == 5:
                pygame.draw.rect(screen, HOVER_COLOR, pygame.Rect(3 * padding_x + 2 * 150, 2 * padding_y + 100, 150, 100), 5)
                # Display image number


            
            # Draw the image on the screen
            screen.blit(image[i], (x, y))

        # Event handling for quitting the program
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            
            if event.type == pygame.KEYDOWN:
                # Arrow key movement to select a game
                if event.key == pygame.K_LEFT and current_game % 3 > 0:  # Move left
                    current_game -= 1
                elif event.key == pygame.K_RIGHT and current_game % 3 < 2:  # Move right
                    current_game += 1
                elif event.key == pygame.K_UP and current_game >= 3:  # Move up
                    current_game -= 3
                elif event.key == pygame.K_DOWN and current_game < 3:  # Move down
                    current_game += 3
                elif event.key == pygame.K_SPACE:  # Press space to print selected game number
                    print(f"Current Game: {current_game + 1}")
                    if current_game == 0: 
                        racer.main()
                    if current_game == 1: 
                        space_shooter.main()
                    #if current_game == 2: 
                       # game.main()
                    if current_game == 3: 
                        game4.main()
                    if current_game == 4:
                        main2.MazeGame()

                        


                    

        # Display the current selected game
        current_game_text = f"Current Game: {current_game + 1}"
        display_text(current_game_text, small_font, WHITE, y_offset=-250)

        pygame.display.flip()
        clock.tick(60)

# Run the game
if __name__ == "__main__":
    arcade_game()
    pygame.quit()