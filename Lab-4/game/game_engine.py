import random
import pygame
from game.rope import Rope
from game.player import Puller

MATCH_TIME_LIMIT = 45.0          # seconds before Sudden Death kicks in
SUDDEN_DEATH_MULTIPLIER = 2.0

BASE_COMPUTER_COOLDOWN = 180     # ms between computer pulls normally
PANIC_START = 0.5                # fraction of the way to the player's goal where panic begins
PANIC_MIN_COOLDOWN = 115         # ms between pulls at maximum panic
PANIC_MAX_STRENGTH_BONUS = 0.35  # +35% pull strength at maximum panic


class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.rope = Rope(width, height)
        self.player = Puller(90, height // 2, (50, 120, 220), "PLAYER (A/D)", facing=-1)
        self.computer = Puller(width - 90, height // 2, (220, 80, 50), "COMPUTER", facing=+1)

        self.font_big = pygame.font.SysFont(None, 48)
        self.font_mid = pygame.font.SysFont(None, 34)
        self.font_small = pygame.font.SysFont(None, 26)

        self.reset()

    # ------------------------------------------------------------------ state
    def reset(self):
        self.rope.reset()
        self.last_key = None
        self.winner = None
        self.game_state = "PLAYING"

        now = pygame.time.get_ticks()
        self.match_start = now
        self.elapsed = 0.0
        self.sudden_death = False

        self.computer_pull_cooldown = BASE_COMPUTER_COOLDOWN
        self.last_computer_pull = now
        self.panic_level = 0.0

        # Momentum = recent pulling effort, decays every frame (drives animation)
        self.player_momentum = 0.0
        self.computer_momentum = 0.0
        self.player.lean = self.computer.lean = 0.15

    @property
    def power(self):
        return SUDDEN_DEATH_MULTIPLIER if self.sudden_death else 1.0

    # ------------------------------------------------------------------ input
    def handle_event(self, event):
        if self.game_state != "PLAYING":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self.reset()
            return

        # FIX (Task 1): the old code locked input on KEYDOWN and only unlocked on the
        # KEYUP of that same key. When mashing, the next key goes down before the
        # previous one comes up, so presses were silently dropped (and a missed KEYUP,
        # e.g. after the window loses focus, locked the player out for good).
        # Now every KEYDOWN that alternates from the previous pull counts — no lock,
        # no dependence on KEYUP ordering. Holding a key still can't spam pulls
        # because the same key twice in a row is ignored.
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_a, pygame.K_d):
            if event.key != self.last_key:
                strength = 1.0 * self.power
                self.rope.pull_left(strength)
                self.player_momentum += strength
                self.last_key = event.key
        elif event.type == pygame.WINDOWFOCUSLOST:
            self.last_key = None

    # ------------------------------------------------------------------ update
    def _update_panic(self):
        """Task 2: computer panics as the flag nears the player's goal line."""
        center = self.width / 2
        progress = (center - self.rope.marker_x) / (center - self.rope.left_win_x)  # 0 centre → 1 player win
        if progress > PANIC_START:
            self.panic_level = min(1.0, (progress - PANIC_START) / (1.0 - PANIC_START))
        else:
            self.panic_level = 0.0
        self.computer_pull_cooldown = (
            BASE_COMPUTER_COOLDOWN - (BASE_COMPUTER_COOLDOWN - PANIC_MIN_COOLDOWN) * self.panic_level
        )

    def update(self):
        if self.game_state != "PLAYING":
            return

        now = pygame.time.get_ticks()

        # Task 4: match timer + sudden death
        self.elapsed = (now - self.match_start) / 1000.0
        if not self.sudden_death and self.elapsed >= MATCH_TIME_LIMIT:
            self.sudden_death = True

        self._update_panic()

        if now - self.last_computer_pull >= self.computer_pull_cooldown:
            variance = random.uniform(0.7, 1.2)
            strength = variance * (1.0 + PANIC_MAX_STRENGTH_BONUS * self.panic_level) * self.power
            self.rope.pull_right(strength)
            self.computer_momentum += strength
            self.last_computer_pull = now

        # Task 3: momentum decays → drives leaning and rope tension
        self.player_momentum *= 0.90
        self.computer_momentum *= 0.90
        net = self.player_momentum - self.computer_momentum
        self.player.update_lean(max(0.05, min(0.6, 0.18 + 0.05 * self.player_momentum + 0.04 * net)))
        self.computer.update_lean(max(0.05, min(0.6, 0.18 + 0.05 * self.computer_momentum - 0.04 * net)))

        result = self.rope.check_winner()
        if result:
            self.winner = result
            self.game_state = "GAME_OVER"

    @property
    def tension(self):
        """0 = slack rope, 1 = both sides hauling hard."""
        struggle = min(self.player_momentum, self.computer_momentum)
        return max(0.0, min(1.0, struggle / 4.0 + (0.3 if self.sudden_death else 0.0)))

    # ------------------------------------------------------------------ render
    def render(self, screen):
        time_s = pygame.time.get_ticks() / 1000.0
        bg = (48, 26, 28) if self.sudden_death and int(time_s * 2) % 2 == 0 else (30, 32, 36)
        screen.fill(bg)

        mud_rect = pygame.Rect(self.width // 2 - 120, self.height // 2 - 80, 240, 160)
        pygame.draw.rect(screen, (45, 38, 30), mud_rect, border_radius=12)

        tension = self.tension
        self.rope.render(screen, tension, time_s, self.sudden_death)
        p_rope_y = self.rope.y_at(self.player.x + 45, tension, time_s)
        c_rope_y = self.rope.y_at(self.computer.x - 45, tension, time_s)
        self.player.render(screen, p_rope_y)
        panic_glow = (255, 220, 60) if self.panic_level > 0 and int(time_s * 8) % 2 == 0 else None
        self.computer.render(screen, c_rope_y, glow=panic_glow)

        # Timer
        if self.sudden_death:
            timer_text = f"SUDDEN DEATH  {self.elapsed:4.1f}s  (2x POWER)"
            timer_color = (255, 200, 40)
        else:
            remaining = max(0.0, MATCH_TIME_LIMIT - self.elapsed)
            timer_text = f"TIME  {self.elapsed:4.1f}s   Sudden death in {remaining:4.1f}s"
            timer_color = (230, 230, 230) if remaining > 10 else (255, 140, 60)
        timer_surf = self.font_mid.render(timer_text, True, timer_color)
        screen.blit(timer_surf, (self.width // 2 - timer_surf.get_width() // 2, 18))

        inst_surf = self.font_small.render(
            "Alternate [A] and [D] keys rapidly to pull!", True, (210, 210, 210)
        )
        screen.blit(inst_surf, (self.width // 2 - inst_surf.get_width() // 2, self.height - 45))

        if self.panic_level > 0 and self.game_state == "PLAYING":
            panic_surf = self.font_small.render(
                f"COMPUTER PANIC SURGE! x{1 + PANIC_MAX_STRENGTH_BONUS * self.panic_level:.2f}",
                True, (255, 220, 60)
            )
            screen.blit(panic_surf, (self.width - panic_surf.get_width() - 20, 60))

        if self.game_state == "GAME_OVER":
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))

            win_text = f"{self.winner} WINS!"
            color = (80, 220, 80) if self.winner == "PLAYER" else (240, 80, 80)
            text_surf = self.font_big.render(win_text, True, color)
            screen.blit(text_surf, (self.width // 2 - text_surf.get_width() // 2, self.height // 2 - 50))

            time_surf = self.font_small.render(f"Match time: {self.elapsed:.1f}s", True, (200, 200, 200))
            screen.blit(time_surf, (self.width // 2 - time_surf.get_width() // 2, self.height // 2 + 5))

            restart_surf = self.font_small.render("Press [R] to Play Again", True, (240, 240, 240))
            screen.blit(restart_surf, (self.width // 2 - restart_surf.get_width() // 2, self.height // 2 + 35))
