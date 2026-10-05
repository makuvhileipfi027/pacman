import pygame
import sys
import random
import math
from enum import Enum

# ---------- Constants ----------

TILE = 24
ROWS, COLS = 21, 19
WIDTH, HEIGHT = COLS * TILE, ROWS * TILE + 40
FPS = 60

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 235, 59)
BLUE = (25, 25, 112)
RED = (255, 82, 82)
PINK = (255, 143, 171)
CYAN = (0, 229, 255)
ORANGE = (255, 160, 0)
FRIGHT = (33, 33, 222)

MAZE = [
    "###################",
    "#........#........#",
    "#o##.###.#.###.##o#",
    "#.................#",
    "#.##.#.#####.#.##.#",
    "#....#...#...#....#",
    "####.###.#.###.####",
    "####.#.......#.####",
    "####.#.##-##.#.####",
    "#......#---#......#",
    "####.#.#####.#.####",
    "####.#.......#.####",
    "####.#.#####.#.####",
    "#........#........#",
    "#.##.###.#.###.##.#",
    "#o..#..........#..#",
    "###.#.#.#####.#.###",
    "###.#.#.....#.#.###",
    "#.....#.###.#.....#",
    "###################",
]


class Dir(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)


# ---------- Pygame ----------

pygame.init()
pygame.mixer.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("PAC-MAN")

clock = pygame.time.Clock()

font = pygame.font.Font(None, 28)
small_font = pygame.font.Font(None, 22)
big_font = pygame.font.Font(None, 64)
ready_font = pygame.font.Font(None, 52)


# ---------- Sounds ----------

eat_sound_0 = pygame.mixer.Sound("sounds/eat_dot_0.wav")
eat_sound_1 = pygame.mixer.Sound("sounds/eat_dot_1.wav")
power_sound = pygame.mixer.Sound("sounds/fright.wav")
ghost_sound = pygame.mixer.Sound("sounds/eat_ghost.wav")
death_sound = pygame.mixer.Sound("sounds/death_0.wav")
start_sound = pygame.mixer.Sound("sounds/start.wav")

eat_sound_0.set_volume(0.35)
eat_sound_1.set_volume(0.35)
power_sound.set_volume(0.45)
ghost_sound.set_volume(0.55)
death_sound.set_volume(0.60)
start_sound.set_volume(0.55)


# ---------- Board ----------

class Board:

    def __init__(self, layout):

        self.grid = [list(row) for row in layout]
        self.dots = 0

        for row in self.grid:
            for ch in row:
                if ch in ('.', 'o'):
                    self.dots += 1

    def is_wall(self, x, y):

        if 0 <= x < COLS and 0 <= y < ROWS:
            return self.grid[y][x] == '#'

        return True

    def at(self, x, y):

        if 0 <= x < COLS and 0 <= y < ROWS:
            return self.grid[y][x]

        return '#'

    def eat(self, x, y):

        if not (0 <= x < COLS and 0 <= y < ROWS):
            return None

        if self.grid[y][x] == '.':

            self.grid[y][x] = ' '
            self.dots -= 1

            return 'dot'

        if self.grid[y][x] == 'o':

            self.grid[y][x] = ' '
            self.dots -= 1

            return 'power'

        return None


# ---------- Actor ----------

class Actor:

    def __init__(self, x, y, color, speed):

        self.tile_x = x
        self.tile_y = y

        self.px = x * TILE
        self.py = y * TILE

        self.color = color
        self.speed = speed

        self.dir = None
        self.next_dir = None

        self.mouth = 0

    def tile_centered(self):

        return self.px % TILE == 0 and self.py % TILE == 0

    def can_move(self, d, board):

        if d is None:
            return False

        nx = self.tile_x + d.value[0]
        ny = self.tile_y + d.value[1]

        return not board.is_wall(nx, ny)

    def update_tile(self):

        self.tile_x = round(self.px / TILE)
        self.tile_y = round(self.py / TILE)


# ---------- Pacman ----------

class Pacman(Actor):

    def __init__(self, x, y):

        super().__init__(x, y, YELLOW, 3)

    def move(self, board):

        if self.tile_centered():

            self.update_tile()

            if self.next_dir and self.can_move(self.next_dir, board):
                self.dir = self.next_dir

            if not self.can_move(self.dir, board):
                self.dir = None

        if self.dir:

            self.px += self.dir.value[0] * self.speed
            self.py += self.dir.value[1] * self.speed

            self.mouth = (self.mouth + 1) % 30

    def draw(self, surf):

        cx = self.px + TILE // 2
        cy = self.py + TILE // 2 + 40

        if self.dir == Dir.LEFT:
            base = 180

        elif self.dir == Dir.UP:
            base = 90

        elif self.dir == Dir.DOWN:
            base = 270

        else:
            base = 0

        mouth_angle = 30 + 15 * abs(15 - self.mouth) // 15

        v1 = pygame.math.Vector2(1, 0).rotate(base - mouth_angle)
        v2 = pygame.math.Vector2(1, 0).rotate(base + mouth_angle)

        pygame.draw.circle(
            surf,
            YELLOW,
            (cx, cy),
            TILE // 2 - 2
        )

        pygame.draw.polygon(
            surf,
            BLACK,
            [
                (cx, cy),

                (
                    cx + (TILE // 2) * v1.x,
                    cy + (TILE // 2) * v1.y
                ),

                (
                    cx + (TILE // 2) * v2.x,
                    cy + (TILE // 2) * v2.y
                )
            ]
        )


# ---------- Ghost ----------

class Ghost(Actor):

    COLORS = [
        RED,
        PINK,
        CYAN,
        ORANGE
    ]

    def __init__(self, x, y, idx):

        super().__init__(
            x,
            y,
            self.COLORS[idx],
            2
        )

        self.home = (x, y)

        self.frightened = 0
        self.in_house = idx != 0

    def choose_dir(self, board, pac):

        options = [
            d for d in Dir
            if self.can_move(d, board)
        ]

        if self.dir and len(options) > 1:

            rev = Dir(
                (
                    -self.dir.value[0],
                    -self.dir.value[1]
                )
            )

            options = [
                d for d in options
                if d != rev
            ]

        if not options:
            return None

        if self.frightened > 0:
            return random.choice(options)

        best = None
        best_d = 10 ** 9

        for d in options:

            nx = self.tile_x + d.value[0]
            ny = self.tile_y + d.value[1]

            dist = (
                (nx - pac.tile_x) ** 2
                +
                (ny - pac.tile_y) ** 2
            )

            if dist < best_d:

                best = d
                best_d = dist

        return best

    def move(self, board, pac):

        if self.frightened > 0:
            self.frightened -= 1

        if self.tile_centered():

            self.update_tile()

            self.dir = self.choose_dir(
                board,
                pac
            )

        if self.dir:

            self.px += self.dir.value[0] * self.speed
            self.py += self.dir.value[1] * self.speed

    def respawn(self):

        self.px = self.home[0] * TILE
        self.py = self.home[1] * TILE

        self.tile_x = self.home[0]
        self.tile_y = self.home[1]

        self.frightened = 0
        self.dir = None

    def draw(self, surf):

        cx = self.px + TILE // 2
        cy = self.py + TILE // 2 + 40

        if self.frightened > 0:

            if self.frightened < 120:

                if (self.frightened // 15) % 2 == 0:
                    color = WHITE
                else:
                    color = FRIGHT

            else:
                color = FRIGHT

        else:
            color = self.color

        pygame.draw.circle(
            surf,
            color,
            (cx, cy - 2),
            TILE // 2 - 2
        )

        pygame.draw.rect(
            surf,
            color,
            (
                cx - TILE // 2 + 2,
                cy - 2,
                TILE - 4,
                TILE // 2
            )
        )

        pygame.draw.circle(
            surf,
            WHITE,
            (cx - 5, cy - 4),
            3
        )

        pygame.draw.circle(
            surf,
            WHITE,
            (cx + 5, cy - 4),
            3
        )

        pygame.draw.circle(
            surf,
            BLUE,
            (cx - 5, cy - 4),
            1
        )

        pygame.draw.circle(
            surf,
            BLUE,
            (cx + 5, cy - 4),
            1
        )


# ---------- Floating Score ----------

class FloatingText:

    def __init__(self, text, x, y):

        self.text = text
        self.x = x
        self.y = y

        self.timer = 60

    def update(self):

        self.y -= 0.5
        self.timer -= 1

    def draw(self, surf):

        txt = font.render(
            self.text,
            True,
            CYAN
        )

        surf.blit(
            txt,
            (self.x, self.y)
        )


# ---------- Ready Screen ----------

def ready_screen():

    start_sound.play()

    messages = [
        ("READY!", 900),
        ("3", 600),
        ("2", 600),
        ("1", 600),
        ("GO!", 700)
    ]

    for message, delay in messages:

        screen.fill(BLACK)

        txt = ready_font.render(
            message,
            True,
            YELLOW
        )

        screen.blit(
            txt,
            (
                WIDTH // 2 - txt.get_width() // 2,
                HEIGHT // 2 - txt.get_height() // 2
            )
        )

        pygame.display.flip()

        start_time = pygame.time.get_ticks()

        while pygame.time.get_ticks() - start_time < delay:

            for event in pygame.event.get():

                if event.type == pygame.QUIT:

                    pygame.quit()
                    sys.exit()

            clock.tick(FPS)


# ---------- Main Game ----------

def main():

    board = Board(MAZE)

    pac = Pacman(9, 15)

    ghosts = [
        Ghost(8, 9, 0),
        Ghost(9, 9, 1),
        Ghost(10, 9, 2),
        Ghost(9, 8, 3)
    ]

    score = 0
    high_score = 0
    lives = 3

    eat_toggle = 0

    state = "play"

    floating_texts = []

    power_flash = 0

    KEYMAP = {

        pygame.K_UP: Dir.UP,
        pygame.K_DOWN: Dir.DOWN,
        pygame.K_LEFT: Dir.LEFT,
        pygame.K_RIGHT: Dir.RIGHT,

        pygame.K_w: Dir.UP,
        pygame.K_s: Dir.DOWN,
        pygame.K_a: Dir.LEFT,
        pygame.K_d: Dir.RIGHT
    }

    ready_screen()

    while True:

        clock.tick(FPS)

        power_flash += 1

        # ---------- Events ----------

        for e in pygame.event.get():

            if e.type == pygame.QUIT:

                pygame.quit()
                sys.exit()

            if e.type == pygame.KEYDOWN:

                if e.key in KEYMAP:
                    pac.next_dir = KEYMAP[e.key]

                if e.key == pygame.K_r and state != "play":

                    main()
                    return

        # ---------- Update ----------

        if state == "play":

            pac.move(board)

            for g in ghosts:
                g.move(board, pac)

            # ---------- Eat Dots ----------

            item = board.eat(
                pac.tile_x,
                pac.tile_y
            )

            if item == 'dot':

                score += 10

                if eat_toggle == 0:

                    eat_sound_0.play()
                    eat_toggle = 1

                else:

                    eat_sound_1.play()
                    eat_toggle = 0

            # ---------- Power Pellet ----------

            elif item == 'power':

                score += 50

                power_sound.play()

                for g in ghosts:
                    g.frightened = 400

            # ---------- High Score ----------

            if score > high_score:
                high_score = score

            # ---------- Ghost Collision ----------

            for g in ghosts:

                if (
                    g.tile_x == pac.tile_x
                    and
                    g.tile_y == pac.tile_y
                ):

                    if g.frightened > 0:

                        score += 200

                        ghost_sound.play()

                        floating_texts.append(
                            FloatingText(
                                "+200",
                                g.px,
                                g.py + 40
                            )
                        )

                        g.respawn()

                    else:

                        lives -= 1

                        death_sound.play()

                        pygame.time.delay(600)

                        pac = Pacman(9, 15)

                        for gh in ghosts:
                            gh.respawn()

                        if lives <= 0:

                            state = "gameover"

                        else:

                            pygame.time.delay(400)

            # ---------- Win ----------

            if board.dots == 0:

                state = "win"

        # ---------- Floating Scores ----------

        for text_object in floating_texts[:]:

            text_object.update()

            if text_object.timer <= 0:
                floating_texts.remove(text_object)

        # ---------- Draw ----------

        screen.fill(BLACK)

        # Maze

        for y, row in enumerate(board.grid):

            for x, ch in enumerate(row):

                rect = pygame.Rect(
                    x * TILE,
                    y * TILE + 40,
                    TILE,
                    TILE
                )

                if ch == '#':

                    pygame.draw.rect(
                        screen,
                        BLUE,
                        rect
                    )

                    pygame.draw.rect(
                        screen,
                        (50, 50, 200),
                        rect,
                        2
                    )

                elif ch == '.':

                    pygame.draw.circle(
                        screen,
                        WHITE,
                        rect.center,
                        3
                    )

                elif ch == 'o':

                    # Blinking power pellet

                    if (power_flash // 20) % 2 == 0:

                        pygame.draw.circle(
                            screen,
                            WHITE,
                            rect.center,
                            7
                        )

        # ---------- HUD ----------

        score_text = font.render(
            f"SCORE {score}",
            True,
            WHITE
        )

        screen.blit(
            score_text,
            (10, 8)
        )

        high_text = small_font.render(
            f"HIGH {high_score}",
            True,
            WHITE
        )

        screen.blit(
            high_text,
            (
                WIDTH // 2 - high_text.get_width() // 2,
                10
            )
        )

        lives_text = font.render(
            f"LIVES {'o' * lives}",
            True,
            YELLOW
        )

        screen.blit(
            lives_text,
            (
                WIDTH - 130,
                8
            )
        )

        # ---------- Characters ----------

        pac.draw(screen)

        for g in ghosts:
            g.draw(screen)

        # Floating +200

        for text_object in floating_texts:
            text_object.draw(screen)

        # ---------- Game Over / Win ----------

        if state in ("win", "gameover"):

            if state == "win":

                msg = "YOU WIN!"

                color = YELLOW

            else:

                msg = "GAME OVER"

                color = RED

            txt = big_font.render(
                msg,
                True,
                color
            )

            screen.blit(
                txt,
                (
                    WIDTH // 2 - txt.get_width() // 2,
                    HEIGHT // 2 - 50
                )
            )

            restart = font.render(
                "Press R to play again",
                True,
                WHITE
            )

            screen.blit(
                restart,
                (
                    WIDTH // 2 - restart.get_width() // 2,
                    HEIGHT // 2 + 20
                )
            )

        pygame.display.flip()


if __name__ == "__main__":
    main()