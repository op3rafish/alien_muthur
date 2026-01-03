"""
Test environment for ALIEN: CHRONOS
"""

import pygame
import sys
import time
from config import WIDTH, HEIGHT, TERMINAL_GREEN, BRIGHT_GREEN, TERMINAL_BLACK, load_fonts
from engine import TypingText, apply_crt_effects, green_flash, wait_for_time, display_typing_sequence
from scenes.dialogue import OPENING_DIALOGUE, MAZE_DIALOGUE

from scenes.maze import run_maze_game
from scenes.narrative import run_maze_completion, run_navigation_dialogue, run_airlock_intro, run_airlock_ending, run_victory_narrative
from scenes.airlock import run_airlock_puzzle

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Test - Airlock Puzzle + Endings")

    player_name = "Jackson"

    # run_navigation_dialogue(screen, player_name)

    # run_airlock_intro(screen)

    # Run the airlock puzzle
    outcome = run_airlock_puzzle(player_name)
    
    # Display the appropriate ending
    run_airlock_ending(screen, player_name, outcome)

    # "Victory sequence"
    if outcome == "victory":
        run_victory_narrative(screen, player_name)
    
    pygame.quit()

if __name__ == "__main__":
    main()