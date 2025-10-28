"""
Test environment for ALIEN: CHRONOS

"""

import pygame
import sys
import time
from config import WIDTH, HEIGHT, TERMINAL_GREEN, BRIGHT_GREEN, TERMINAL_BLACK, load_fonts
from engine import TypingText, apply_crt_effects, green_flash, wait_for_time, display_typing_sequence
from scenes.dialogue import OPENING_DIALOGUE, MAZE_DIALOGUE


if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Testing")

    font_large, _, _ = load_fonts()
    TOP_POSITION = 100
    player_name = "John Doe"
    
    # Test whatever you want
    # Test just the Special Order 937 section
    screen.fill(TERMINAL_BLACK)
    order_937_lines = [
        line.format(player_name=player_name) for line in OPENING_DIALOGUE["order_937"]
    ]
    texts = display_typing_sequence(
        [(line, font_large) for line in order_937_lines],
        screen,
        TOP_POSITION,
        40,
        line_pauses={0: 1}
    )
    wait_for_time(3, screen, texts)
    green_flash(screen)
    
    pygame.quit()
