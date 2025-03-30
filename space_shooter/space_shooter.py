import pygame
import random
import sys

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 600, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Shooter")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

# Clock for controlling frame rate
clock = pygame.time.Clock()

# Spaceship class
class Spaceship:
    def __init__(self):
        self.width = 60  # Increased width of the player sprite
        self.height = 60  # Increased height of the player sprite
        self.x = 60
        self.y = 300
        self.speed = 5
        self.projectiles = []
        self.shoot_cooldown = 0  # Cooldown timer for shooting
        self.image = pygame.image.load("assets/ship.png")  # Load the ship image
        self.image = pygame.transform.scale(self.image, (self.width, self.height))  # Scale the image to fit

    def draw(self):
        # Draw the ship image instead of the triangle
        screen.blit(self.image, (self.x, self.y))
        for projectile in self.projectiles:
            projectile.draw()

    def move(self, direction):
        if direction == "UP" and self.y > 0:
            self.y -= 60  # Move in 10x10 grid
        elif direction == "DOWN" and self.y < HEIGHT - self.height:
            self.y += 60  # Move in 10x10 grid
        elif direction == "LEFT" and self.x > 0:
            self.x -= 60  # Move in 10x10 grid
        elif direction == "RIGHT" and self.x < WIDTH - self.width:
            self.x += 60  # Move in 10x10 grid

    def shoot(self):
        if self.shoot_cooldown == 0:  # Only shoot if cooldown is 0
            # Fire two beams with a smaller gap between them
            self.projectiles.append(Projectile(self.x + self.width, self.y + self.height // 2 - 10))  # Top beam
            self.projectiles.append(Projectile(self.x + self.width, self.y + self.height // 2 + 10))  # Bottom beam
            self.shoot_cooldown = 15  # Cooldown remains the same

    def update_cooldown(self):
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

# Projectile class
class Projectile:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 10
        self.height = 5
        self.speed = 3  # Further reduced projectile speed

    def draw(self):
        pygame.draw.rect(screen, WHITE, (self.x, self.y, self.width, self.height))

    def move(self):
        self.x += self.speed

# Enemy class
class Enemy:
    def __init__(self):
        self.width = 70  # Increased width of the enemy sprite
        self.height = 70  # Increased height of the enemy sprite
        self.x = WIDTH
        self.y = 60 * round((random.randint(0, HEIGHT - self.height)) / 60)
        self.speed = random.uniform(2, 4)  # Slightly vary enemy speed
        self.image = pygame.image.load("assets/Alien Spaceship.png")  # Load enemy sprite
        self.image = pygame.transform.scale(self.image, (self.width, self.height))  # Scale the sprite

    def draw(self):
        screen.blit(self.image, (self.x, self.y))

    def move(self):
        self.x -= self.speed

# Asteroid class
class Asteroid:
    def __init__(self):
        self.size = random.randint(100, 200)  # Increased size for the sprite
        self.x = WIDTH
        self.y = 60 * round((random.randint(0, HEIGHT - self.size)) / 60)
        self.speed = random.uniform(0.5, 2)  # Slower speed for asteroids
        self.image = pygame.image.load("assets/Asteroid Brown.png")  # Load asteroid sprite
        self.image = pygame.transform.scale(self.image, (self.size, self.size))  # Scale the sprite
        self.hit_count = 0  # Track the number of hits
        self.flash_timer = 0  # Timer for flashing effect

    def draw(self):
        if self.flash_timer > 0:  # Flash effect
            if int(self.flash_timer * 10) % 2 == 0:  # Alternate visibility
                screen.blit(self.image, (self.x, self.y))
        else:
            screen.blit(self.image, (self.x, self.y))

    def move(self):
        self.x -= self.speed
        if self.flash_timer > 0:
            self.flash_timer -= 1 / 60  # Decrease flash timer (assuming 60 FPS)

# Coin class
class Coin:
    def __init__(self):
        self.size = 30  # Adjusted size for the sprite
        self.x = 60 * round((random.randint(WIDTH // 3, WIDTH - self.size)) / 60)  # Spawn on the right half of the grid
        self.y = 60 * round((random.randint(0, HEIGHT - self.size)) / 60)  # Align to grid
        self.lifetime = 300  # Lifetime in frames (e.g., 5 seconds at 60 FPS)
        self.image = pygame.image.load("assets/coin_spin-Sheet.png")  # Load coin sprite
        self.image = pygame.transform.scale(self.image, (self.size, self.size))  # Scale the sprite

    def draw(self):
        # Flash effect: alternate visibility in the last 60 frames
        if self.lifetime > 60 or self.lifetime % 10 < 5:
            screen.blit(self.image, (self.x, self.y))

    def update(self):
        self.lifetime -= 1  # Decrease lifetime

# Load health bar images
HEALTH_IMAGES = {
    5: pygame.image.load("assets/Health Bar Five.png"),
    4: pygame.image.load("assets/Health Bar Four.png"),
    3: pygame.image.load("assets/Health Bar Three.png"),
    2: pygame.image.load("assets/Health Bar Two.png"),
    1: pygame.image.load("assets/Health Bar One.png"),
}

def game_over_screen(score):
    screen.fill(BLACK)
    font = pygame.font.SysFont(None, 72)
    game_over_text = font.render("GAME OVER", True, RED)
    score_text = pygame.font.SysFont(None, 36).render(f"Score: {score}", True, WHITE)
    restart_text = pygame.font.SysFont(None, 36).render("Press R to Restart", True, WHITE)

    screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 3))
    screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 2))
    screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 50))

    pygame.display.flip()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                main()  # Restart the game

# Main game loop
def main():
    spaceship = Spaceship()
    enemies = []
    asteroids = []  # List to store asteroids
    coins = []  # List to store coins
    score = 0
    health = 5  # Player's health set to 5
    font = pygame.font.SysFont(None, 36)
    enemy_spawn_rate = 120  # Slightly decreased spawn rate for enemies
    asteroid_spawn_rate = 500  # Less frequent asteroid spawn rate
    coin_spawn_rate = 500  # Coin spawn rate
    enemy_speed_increment = 0.05  # Decrease the rate of enemy speed increment
    asteroid_spawn_rate_increment = 50  # Increment to make asteroids spawn less frequently over time
    game_start_time = pygame.time.get_ticks()  # Track the start time of the game
    time_of_last_keydown = -1000  # Timer for keydown events

    while True:
        screen.fill(BLACK)

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            time_since_last_keydown = pygame.time.get_ticks() - time_of_last_keydown  # Calculate time since last keydown
            if event.type == pygame.KEYDOWN and (time_since_last_keydown > 200):
                if event.key == pygame.K_UP:
                    spaceship.move("UP")
                elif event.key == pygame.K_DOWN:
                    spaceship.move("DOWN")
                elif event.key == pygame.K_LEFT:
                    spaceship.move("LEFT")
                elif event.key == pygame.K_RIGHT:
                    spaceship.move("RIGHT")
                elif event.key == pygame.K_SPACE:
                    spaceship.shoot()
                time_of_last_keydown = 0  # Reset the timer after a key press

        spaceship.update_cooldown()  # Update the cooldown timer

        # Update projectiles
        for projectile in spaceship.projectiles[:]:
            projectile.move()
            if projectile.x > WIDTH:
                spaceship.projectiles.remove(projectile)

        # Spawn enemies
        if random.randint(1, enemy_spawn_rate) == 1:
            enemies.append(Enemy())

        # Spawn asteroids only after 6 seconds of gameplay
        if pygame.time.get_ticks() - game_start_time > 6000:  # 6 seconds in milliseconds
            if random.randint(1, asteroid_spawn_rate) == 1:
                asteroids.append(Asteroid())

        # Spawn coins occasionally
        if random.randint(1, coin_spawn_rate) == 1:
            coins.append(Coin())

        # Gradually increase enemy speed and spawn rate
        if score % 20 == 0 and score > 0:  # Every 20 points (slower rate)
            for enemy in enemies:
                enemy.speed += enemy_speed_increment
            if enemy_spawn_rate > 30:  # Limit how fast enemies spawn
                enemy_spawn_rate -= 1
            if asteroid_spawn_rate < 1000:  # Limit how infrequent asteroids spawn
                asteroid_spawn_rate += asteroid_spawn_rate_increment

        # Update enemies
        for enemy in enemies[:]:
            enemy.move()
            if enemy.x < 0:
                enemies.remove(enemy)  # Remove enemy if it reaches the left side
                health -= 1  # Reduce health by 1
                if health <= 0:
                    game_over_screen(score)  # Show game over screen
            elif (
                spaceship.x < enemy.x + enemy.width
                and spaceship.x + spaceship.width > enemy.x
                and spaceship.y < enemy.y + enemy.height
                and spaceship.y + spaceship.height > enemy.y
            ):
                enemies.remove(enemy)  # Remove enemy on collision (no damage to the player)
            for projectile in spaceship.projectiles[:]:
                if (
                    projectile.x < enemy.x + enemy.width
                    and projectile.x + projectile.width > enemy.x
                    and projectile.y < enemy.y + enemy.height
                    and projectile.y + projectile.height > enemy.y
                ):
                    spaceship.projectiles.remove(projectile)
                    enemies.remove(enemy)
                    score += 1
                    break

        # Update asteroids
        for asteroid in asteroids[:]:
            asteroid.move()
            if asteroid.x + asteroid.size < 0:
                asteroids.remove(asteroid)  # Remove asteroid if it moves off-screen
            else:
                for projectile in spaceship.projectiles[:]:
                    if (
                        projectile.x < asteroid.x + asteroid.size
                        and projectile.x + projectile.width > asteroid.x
                        and projectile.y < asteroid.y + asteroid.size
                        and projectile.y + projectile.height > asteroid.y
                    ):
                        spaceship.projectiles.remove(projectile)
                        asteroid.hit_count += 1  # Increment hit count
                        if asteroid.hit_count >= 10:
                            asteroid.flash_timer = 0.2  # Start flashing for 0.2 seconds
                            asteroids.remove(asteroid)  # Remove asteroid after flashing
                            break
                if (
                    spaceship.x < asteroid.x + asteroid.size
                    and spaceship.x + spaceship.width > asteroid.x
                    and spaceship.y < spaceship.y + asteroid.size
                    and spaceship.y + spaceship.height > asteroid.y
                    ):
                    asteroid.flash_timer = 0.2  # Start flashing for 0.2 seconds
                    asteroids.remove(asteroid)  # Remove asteroid after flashing
                    health -= 1  # Reduce health by 1
                    if health <= 0:
                        game_over_screen(score)  # Show game over screen

        # Update coins
        for coin in coins[:]:
            coin.update()
            if coin.lifetime <= 0:  # Remove coin if its lifetime expires
                coins.remove(coin)
            elif (
                spaceship.x < coin.x + coin.size
                and spaceship.x + spaceship.width > coin.x
                and spaceship.y < coin.y + coin.size
                and spaceship.y + spaceship.height > coin.y
            ):
                coins.remove(coin)  # Collect the coin
                score += 5  # Increase score when collecting a coin

        # Draw everything
        spaceship.draw()
        for enemy in enemies:
            enemy.draw()
        for asteroid in asteroids:
            asteroid.draw()
        for coin in coins:
            coin.draw()

        # Display score at the top middle
        score_text = font.render(f"Score: {score}", True, WHITE)
        screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, 10))

        # Draw health bar using heart assets
        if health > 0:
            health_image = pygame.transform.scale(HEALTH_IMAGES[health], (200, 40))  # Increased size to 200x40
            screen.blit(health_image, (WIDTH // 2 - 100, HEIGHT - 50))  # Adjusted position for larger size
        else:
            game_over_screen(score)  # Show game over screen when health is 0

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()