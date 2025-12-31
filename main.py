"""
ALIEN: CHRONOS - Main launcher
"""

import pygame
from config import WIDTH, HEIGHT
from scenes.title import run_title_sequence
from scenes.narrative import run_opening, run_maze_completion, run_airlock_intro, run_airlock_ending
from scenes.maze import run_maze_game
from scenes.airlock import run_airlock_puzzle

def main():
    """Initialize game and run sequences"""
    # Initialize Pygame
    pygame.init()
    
    # Create screen
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Alien: Chronos")
    
    # Run title sequence
    run_title_sequence(screen)
    
    # Run opening sequence: player name, scene setting
    player_name = run_opening(screen)

    # Launch puzzle 1: maze game
    run_maze_game(player_name)
    
    # Maze completion narrative
    run_maze_completion(screen, player_name)
    
    # Airlock puzzle introduction
    run_airlock_intro(screen)
    
    # Launch puzzle 2: airlock puzzle
    outcome = run_airlock_puzzle(player_name)
    
    # Display airlock ending based on outcome
    run_airlock_ending(screen, player_name, outcome)
    
    # Close game
    pygame.quit()

if __name__ == "__main__":
    main()