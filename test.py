"""
Test environment for ALIEN: CHRONOS

"""

import pygame
import sys
import time
from config import WIDTH, HEIGHT, TERMINAL_GREEN, BRIGHT_GREEN, TERMINAL_BLACK, load_fonts
from engine import TypingText, apply_crt_effects, green_flash, wait_for_time, display_typing_sequence
from scenes.dialogue import OPENING_DIALOGUE, MAZE_DIALOGUE

from scenes.narrative import run_navigation_dialogue

# THIS IS THE REAL DEAL TEST ENVIRONMENT KEEP IT

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Test navigation dialogue")

    player_name = "Lambert"
    run_navigation_dialogue(screen, player_name)

    pygame.quit()

if __name__ == "__main__":
    main()
