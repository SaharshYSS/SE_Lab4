import math
import pygame


class Rope:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.center_y = screen_height // 2
        self.marker_x = float(screen_width // 2)

        self.left_win_x = 180
        self.right_win_x = screen_width - 180
        self.pull_step = 12

    def pull_left(self, strength=1.0):
        # Float maths so fractional strengths (variance, panic, sudden death) aren't truncated
        self.marker_x -= self.pull_step * strength

    def pull_right(self, strength=1.0):
        self.marker_x += self.pull_step * strength

    def check_winner(self):
        if self.marker_x <= self.left_win_x:
            return "PLAYER"
        if self.marker_x >= self.right_win_x:
            return "COMPUTER"
        return None

    def reset(self):
        self.marker_x = float(self.screen_width // 2)

    def _rope_points(self, tension, time_s):
        """Rope as a polyline.

        tension 0..1: 0 = slack (rope sags in the middle),
                      1 = both sides hauling hard (rope is taut and vibrates/hums).
        """
        left, right = 60, self.screen_width - 60
        sag = 18 * (1.0 - tension)                # slack rope droops
        hum = 3.5 * tension ** 1.5                # taut rope vibrates
        points = []
        segments = 60
        for i in range(segments + 1):
            u = i / segments
            x = left + (right - left) * u
            envelope = math.sin(math.pi * u)      # ends are held, middle moves most
            y = self.center_y + sag * envelope
            y += hum * envelope * math.sin(u * 9 * math.pi + time_s * 55)
            points.append((x, y))
        return points

    def y_at(self, x, tension, time_s):
        """Approximate rope height at screen x (used to place the flag and the hands)."""
        pts = self._rope_points(tension, time_s)
        left, right = pts[0][0], pts[-1][0]
        idx = int((x - left) / (right - left) * (len(pts) - 1))
        idx = max(0, min(len(pts) - 1, idx))
        return pts[idx][1]

    def render(self, surface, tension=0.0, time_s=0.0, sudden_death=False):
        points = self._rope_points(tension, time_s)
        # Rope colour shifts from slack tan to strained, brighter fibre colour
        r = int(180 + 50 * tension)
        g = int(140 + 30 * tension)
        b = int(90 - 30 * tension)
        pygame.draw.lines(surface, (r, g, b), False, points, 10)

        pygame.draw.line(surface, (50, 200, 50),
                         (self.left_win_x, self.center_y - 40),
                         (self.left_win_x, self.center_y + 40), 4)
        pygame.draw.line(surface, (200, 50, 50),
                         (self.right_win_x, self.center_y - 40),
                         (self.right_win_x, self.center_y + 40), 4)
        pygame.draw.line(surface, (120, 120, 120),
                         (self.screen_width // 2, self.center_y - 20),
                         (self.screen_width // 2, self.center_y + 20), 2)

        flag_y = self.y_at(self.marker_x, tension, time_s)
        flag_rect = pygame.Rect(int(self.marker_x) - 12, int(flag_y) - 24, 24, 48)
        flag_color = (255, 200, 40) if sudden_death else (230, 40, 40)
        pygame.draw.rect(surface, flag_color, flag_rect, border_radius=4)
        pygame.draw.rect(surface, (255, 255, 255), flag_rect, width=2, border_radius=4)
