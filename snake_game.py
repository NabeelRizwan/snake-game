import pygame
import random
import math
from collections import deque

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 900, 700
GRID_SIZE = 20
GRID_WIDTH = WIDTH // GRID_SIZE
GRID_HEIGHT = HEIGHT // GRID_SIZE
FPS = 60

# Futuristic color palette
BG_COLOR = (5, 5, 20)
GRID_COLOR = (20, 20, 40)
SNAKE_COLOR = (0, 255, 200)
SNAKE_GLOW = (0, 200, 150)
FOOD_COLOR = (255, 50, 150)
FOOD_GLOW = (200, 30, 120)
OBSTACLE_COLOR = (255, 100, 0)
TEXT_COLOR = (0, 255, 255)

# Power-up types
POWERUP_SPEED = (100, 200, 255)
POWERUP_INVINCIBLE = (255, 215, 0)
POWERUP_MULTIPLIER = (255, 100, 255)
POWERUP_SHRINK = (150, 255, 150)


class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-3, 3)
        self.life = 30
        self.color = color
        self.size = random.randint(2, 5)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        self.size = max(1, self.size * 0.95)

    def draw(self, screen):
        alpha = int(255 * (self.life / 30))
        color = (*self.color[:3], alpha)
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), int(self.size))


class PowerUp:
    def __init__(self):
        self.x = random.randint(0, GRID_WIDTH - 1)
        self.y = random.randint(0, GRID_HEIGHT - 1)
        self.type = random.choice(['speed', 'invincible', 'multiplier', 'shrink'])
        self.lifetime = 300
        self.angle = 0

    def get_color(self):
        colors = {
            'speed': POWERUP_SPEED,
            'invincible': POWERUP_INVINCIBLE,
            'multiplier': POWERUP_MULTIPLIER,
            'shrink': POWERUP_SHRINK
        }
        return colors[self.type]

    def update(self):
        self.lifetime -= 1
        self.angle += 0.1
        return self.lifetime > 0


class Obstacle:
    def __init__(self):
        self.x = random.randint(2, GRID_WIDTH - 3)
        self.y = random.randint(2, GRID_HEIGHT - 3)
        self.vx = random.choice([-1, 0, 1])
        self.vy = random.choice([-1, 0, 1])
        self.move_timer = 0
        self.size = random.randint(1, 2)

    def update(self):
        self.move_timer += 1
        if self.move_timer > 30:
            self.move_timer = 0
            self.x = max(0, min(GRID_WIDTH - 1, self.x + self.vx))
            self.y = max(0, min(GRID_HEIGHT - 1, self.y + self.vy))
            if random.random() < 0.3:
                self.vx = random.choice([-1, 0, 1])
                self.vy = random.choice([-1, 0, 1])


class Snake:
    def __init__(self):
        self.reset()

    def reset(self):
        start_x = GRID_WIDTH // 2
        start_y = GRID_HEIGHT // 2
        self.body = deque([(start_x, start_y), (start_x - 1, start_y), (start_x - 2, start_y)])
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.growing = False
        self.score = 0
        self.speed_boost = False
        self.invincible = False
        self.multiplier = 1
        self.boost_timer = 0
        self.invincible_timer = 0
        self.multiplier_timer = 0
        self.trail = deque(maxlen=10)

    def change_direction(self, direction):
        # Prevent 180-degree turns
        if (direction[0] * -1, direction[1] * -1) != self.direction:
            self.next_direction = direction

    def move(self):
        self.direction = self.next_direction
        head = self.body[0]
        new_head = ((head[0] + self.direction[0]) % GRID_WIDTH,
                    (head[1] + self.direction[1]) % GRID_HEIGHT)

        self.trail.append(head)
        self.body.appendleft(new_head)

        if not self.growing:
            self.body.pop()
        else:
            self.growing = False

        # Update power-up timers
        if self.boost_timer > 0:
            self.boost_timer -= 1
            if self.boost_timer == 0:
                self.speed_boost = False

        if self.invincible_timer > 0:
            self.invincible_timer -= 1
            if self.invincible_timer == 0:
                self.invincible = False

        if self.multiplier_timer > 0:
            self.multiplier_timer -= 1
            if self.multiplier_timer == 0:
                self.multiplier = 1

    def grow(self):
        self.growing = True

    def shrink(self):
        if len(self.body) > 3:
            for _ in range(min(3, len(self.body) - 3)):
                self.body.pop()

    def check_collision(self):
        head = self.body[0]
        return head in list(self.body)[1:]

    def apply_powerup(self, powerup_type):
        if powerup_type == 'speed':
            self.speed_boost = True
            self.boost_timer = 180
        elif powerup_type == 'invincible':
            self.invincible = True
            self.invincible_timer = 240
        elif powerup_type == 'multiplier':
            self.multiplier = 2
            self.multiplier_timer = 300
        elif powerup_type == 'shrink':
            self.shrink()


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Neon Snake - Futuristic Edition")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.snake = Snake()
        self.food = self.spawn_food()
        self.particles = []
        self.obstacles = []
        self.powerups = []
        self.level = 1
        self.high_score = 0
        self.game_speed = 8
        self.move_counter = 0
        self.powerup_spawn_timer = 0

    def spawn_food(self):
        while True:
            pos = (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
            if pos not in self.snake.body and not any(pos == (o.x, o.y) for o in self.obstacles):
                return pos

    def spawn_powerup(self):
        while True:
            powerup = PowerUp()
            if (powerup.x, powerup.y) not in self.snake.body and \
                    (powerup.x, powerup.y) != self.food and \
                    not any((powerup.x, powerup.y) == (o.x, o.y) for o in self.obstacles):
                return powerup

    def spawn_obstacle(self):
        while True:
            obstacle = Obstacle()
            if (obstacle.x, obstacle.y) not in self.snake.body and \
                    (obstacle.x, obstacle.y) != self.food:
                return obstacle

    def create_particles(self, x, y, color, count=15):
        for _ in range(count):
            self.particles.append(Particle(x * GRID_SIZE + GRID_SIZE // 2,
                                           y * GRID_SIZE + GRID_SIZE // 2, color))

    def draw_glow(self, surface, color, pos, size):
        glow_surf = pygame.Surface((size * 3, size * 3), pygame.SRCALPHA)
        for i in range(3, 0, -1):
            alpha = 30 * i
            pygame.draw.circle(glow_surf, (*color, alpha),
                               (size * 3 // 2, size * 3 // 2), size * i // 2)
        surface.blit(glow_surf, (pos[0] - size, pos[1] - size))

    def draw(self):
        self.screen.fill(BG_COLOR)

        # Draw grid
        for x in range(0, WIDTH, GRID_SIZE):
            pygame.draw.line(self.screen, GRID_COLOR, (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, GRID_SIZE):
            pygame.draw.line(self.screen, GRID_COLOR, (0, y), (WIDTH, y))

        # Draw trail
        for i, pos in enumerate(self.snake.trail):
            alpha = int(50 * (i / len(self.snake.trail)))
            trail_surf = pygame.Surface((GRID_SIZE, GRID_SIZE), pygame.SRCALPHA)
            pygame.draw.circle(trail_surf, (*SNAKE_COLOR, alpha),
                               (GRID_SIZE // 2, GRID_SIZE // 2), GRID_SIZE // 3)
            self.screen.blit(trail_surf, (pos[0] * GRID_SIZE, pos[1] * GRID_SIZE))

        # Draw snake with glow
        for i, segment in enumerate(self.snake.body):
            color = SNAKE_COLOR if not self.snake.invincible else POWERUP_INVINCIBLE
            pos = (segment[0] * GRID_SIZE + GRID_SIZE // 2,
                   segment[1] * GRID_SIZE + GRID_SIZE // 2)

            # Glow effect
            if i == 0:
                self.draw_glow(self.screen, color, pos, GRID_SIZE)

            # Body
            size = GRID_SIZE // 2 if i == 0 else GRID_SIZE // 2 - 2
            pygame.draw.circle(self.screen, color, pos, size)

            # Inner highlight
            highlight_color = tuple(min(c + 50, 255) for c in color[:3])
            pygame.draw.circle(self.screen, highlight_color, pos, size // 2)

        # Draw food with glow
        food_pos = (self.food[0] * GRID_SIZE + GRID_SIZE // 2,
                    self.food[1] * GRID_SIZE + GRID_SIZE // 2)
        self.draw_glow(self.screen, FOOD_COLOR, food_pos, GRID_SIZE)
        pygame.draw.circle(self.screen, FOOD_COLOR, food_pos, GRID_SIZE // 2)
        pulse = int(5 * math.sin(pygame.time.get_ticks() * 0.01))
        pygame.draw.circle(self.screen, (255, 255, 255), food_pos, GRID_SIZE // 4 + pulse)

        # Draw obstacles
        for obs in self.obstacles:
            obs_pos = (obs.x * GRID_SIZE + GRID_SIZE // 2,
                       obs.y * GRID_SIZE + GRID_SIZE // 2)
            self.draw_glow(self.screen, OBSTACLE_COLOR, obs_pos, GRID_SIZE)
            pygame.draw.rect(self.screen, OBSTACLE_COLOR,
                             (obs.x * GRID_SIZE + 2, obs.y * GRID_SIZE + 2,
                              GRID_SIZE - 4, GRID_SIZE - 4))

        # Draw power-ups
        for powerup in self.powerups:
            color = powerup.get_color()
            pos = (powerup.x * GRID_SIZE + GRID_SIZE // 2,
                   powerup.y * GRID_SIZE + GRID_SIZE // 2)
            offset = int(5 * math.sin(powerup.angle))
            pygame.draw.circle(self.screen, color,
                               (pos[0], pos[1] + offset), GRID_SIZE // 3)
            pygame.draw.circle(self.screen, (255, 255, 255),
                               (pos[0], pos[1] + offset), GRID_SIZE // 6)

        # Draw particles
        for particle in self.particles:
            particle.draw(self.screen)

        # Draw UI
        score_text = self.font.render(f"Score: {self.snake.score}", True, TEXT_COLOR)
        level_text = self.font.render(f"Level: {self.level}", True, TEXT_COLOR)
        high_score_text = self.small_font.render(f"High: {self.high_score}", True, TEXT_COLOR)

        self.screen.blit(score_text, (10, 10))
        self.screen.blit(level_text, (10, 50))
        self.screen.blit(high_score_text, (10, 90))

        # Draw active power-ups
        y_offset = 120
        if self.snake.speed_boost:
            boost_text = self.small_font.render("SPEED BOOST", True, POWERUP_SPEED)
            self.screen.blit(boost_text, (10, y_offset))
            y_offset += 25
        if self.snake.invincible:
            inv_text = self.small_font.render("INVINCIBLE", True, POWERUP_INVINCIBLE)
            self.screen.blit(inv_text, (10, y_offset))
            y_offset += 25
        if self.snake.multiplier > 1:
            mult_text = self.small_font.render("x2 MULTIPLIER", True, POWERUP_MULTIPLIER)
            self.screen.blit(mult_text, (10, y_offset))

        pygame.display.flip()

    def update(self):
        # Move snake based on speed
        speed = self.game_speed * (1.5 if self.snake.speed_boost else 1)
        self.move_counter += speed

        if self.move_counter >= FPS:
            self.move_counter = 0
            self.snake.move()

            # Check food collision
            if self.snake.body[0] == self.food:
                self.snake.grow()
                points = 10 * self.snake.multiplier
                self.snake.score += points
                self.create_particles(self.food[0], self.food[1], FOOD_COLOR)
                self.food = self.spawn_food()

                # Level up
                if self.snake.score // 100 + 1 > self.level:
                    self.level += 1
                    self.game_speed = min(15, 8 + self.level)
                    if self.level % 2 == 0 and len(self.obstacles) < 8:
                        self.obstacles.append(self.spawn_obstacle())

            # Check powerup collision
            for powerup in self.powerups[:]:
                if self.snake.body[0] == (powerup.x, powerup.y):
                    self.snake.apply_powerup(powerup.type)
                    self.create_particles(powerup.x, powerup.y, powerup.get_color())
                    self.powerups.remove(powerup)

            # Check obstacle collision
            if not self.snake.invincible:
                for obs in self.obstacles:
                    if self.snake.body[0] == (obs.x, obs.y):
                        return False

            # Check self collision
            if not self.snake.invincible and self.snake.check_collision():
                return False

        # Update obstacles
        for obs in self.obstacles:
            obs.update()

        # Update powerups
        self.powerups = [p for p in self.powerups if p.update()]

        # Spawn powerups
        self.powerup_spawn_timer += 1
        if self.powerup_spawn_timer > 300 and random.random() < 0.02 and len(self.powerups) < 2:
            self.powerups.append(self.spawn_powerup())
            self.powerup_spawn_timer = 0

        # Update particles
        self.particles = [p for p in self.particles if p.life > 0]
        for particle in self.particles:
            particle.update()

        return True

    def game_over(self):
        if self.snake.score > self.high_score:
            self.high_score = self.snake.score

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        game_over_text = self.font.render("GAME OVER", True, (255, 50, 50))
        score_text = self.font.render(f"Final Score: {self.snake.score}", True, TEXT_COLOR)
        restart_text = self.small_font.render("Press SPACE to restart or ESC to quit", True, TEXT_COLOR)

        self.screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 3))
        self.screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 2))
        self.screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 60))

        pygame.display.flip()

        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.snake.reset()
                        self.food = self.spawn_food()
                        self.obstacles = []
                        self.powerups = []
                        self.particles = []
                        self.level = 1
                        self.game_speed = 8
                        return True
                    if event.key == pygame.K_ESCAPE:
                        return False
        return False

    def run(self):
        running = True
        game_active = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN and game_active:
                    if event.key == pygame.K_UP or event.key == pygame.K_w:
                        self.snake.change_direction((0, -1))
                    elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        self.snake.change_direction((0, 1))
                    elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        self.snake.change_direction((-1, 0))
                    elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        self.snake.change_direction((1, 0))

            if game_active:
                game_active = self.update()
                self.draw()
            else:
                running = self.game_over()
                game_active = True

            self.clock.tick(FPS)

        pygame.quit()


if __name__ == "__main__":
    game = Game()
    game.run()
