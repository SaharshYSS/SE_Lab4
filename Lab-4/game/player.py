import math
import pygame


class Puller:
    """Represents a puller character anchor on either side of the rope.

    `facing` is -1 for the left puller (leans back to the left) and +1 for the
    right puller (leans back to the right).
    """

    def __init__(self, x, y, color, label, facing):
        self.x = x
        self.y = y
        self.color = color
        self.label = label
        self.facing = facing
        self.lean = 0.15          # current lean angle in radians (smoothed)
        self.font = pygame.font.SysFont(None, 24)

    def update_lean(self, target):
        # Ease towards the target so the posture changes smoothly
        self.lean += (target - self.lean) * 0.2

    def _rot(self, px, py):
        """Rotate a point (relative to the feet) by the lean angle, away from the rope centre."""
        theta = self.facing * self.lean
        c, s = math.cos(theta), math.sin(theta)
        fx, fy = self.x, self.y + 35          # pivot at the feet
        return (fx + px * c - py * s, fy + px * s + py * c)

    def render(self, surface, rope_y=None, glow=None):
        """Draw a leaning avatar holding the rope, plus its label."""
        if rope_y is None:
            rope_y = self.y

        # Legs (planted, splay slightly opposite the lean)
        feet_y = self.y + 35
        hip = self._rot(0, -30)
        pygame.draw.line(surface, (60, 60, 70), (self.x - 12, feet_y), hip, 7)
        pygame.draw.line(surface, (60, 60, 70), (self.x + 12, feet_y), hip, 7)

        # Torso as a rotated rectangle
        corners = [self._rot(-18, -30), self._rot(18, -30), self._rot(18, -85), self._rot(-18, -85)]
        if glow:
            pygame.draw.polygon(surface, glow, corners, 6)
        pygame.draw.polygon(surface, self.color, corners)

        # Head
        head = self._rot(0, -102)
        pygame.draw.circle(surface, (240, 210, 180), (int(head[0]), int(head[1])), 16)

        # Arms reach towards the centre and grip the rope
        shoulder = self._rot(0, -75)
        hands = (self.x - self.facing * 45, rope_y)
        pygame.draw.line(surface, (240, 210, 180), shoulder, hands, 6)
        pygame.draw.circle(surface, (240, 210, 180), (int(hands[0]), int(hands[1])), 6)

        label_surf = self.font.render(self.label, True, (240, 240, 240))
        surface.blit(label_surf, (self.x - label_surf.get_width() // 2, self.y + 50))
