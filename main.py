"""
ALIEN: CHRONOS - Main launcher
"""

import pygame
from config import WIDTH, HEIGHT
from scenes.title import run_title_sequence
from scenes.narrative import run_opening, run_maze_completion
from scenes.maze import run_maze_game

def main():
    """Initialize game and run sequences"""
    # Initialize Pygame
    pygame.init()
    
    # Create screen
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Alien: Chronos")
    
    # Run title sequence first
    run_title_sequence(screen)
    
    # Run opening sequence: player name, scene setting
    player_name = run_opening(screen)

    # Set timer

    # Launch puzzle 1: maze game
    run_maze_game(player_name)

    run_maze_completion(screen, player_name)

    # TESTING SOMETHING ELSE!


    # Launch puzzle 2: logic game

    # Victory

    # Game over

    # Close opening window
    pygame.quit()

if __name__ == "__main__":
    main()