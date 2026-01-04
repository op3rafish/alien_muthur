"""
ALIEN: CHRONOS - Main launcher
"""

import pygame
from config import WIDTH, HEIGHT
from scenes.title import run_title_sequence
from scenes.narrative import (run_opening, run_maze_completion, run_navigation_dialogue,
                              run_airlock_intro, run_airlock_ending, run_victory_narrative)
from scenes.maze import run_maze_game
from scenes.airlock import run_airlock_puzzle
from scenes.credits import run_credits_screen

def run_airlock_section(screen, player_name):
    """Run airlock puzzle and endings - can be replayed"""
    while True:
        # Airlock puzzle introduction
        run_airlock_intro(screen)
        
        # Launch puzzle 2: airlock puzzle
        outcome = run_airlock_puzzle(player_name)
        
        # Display airlock ending based on outcome
        run_airlock_ending(screen, player_name, outcome)
        
        # If player wins airlock, show "victory" dialogue
        if outcome == "victory":
            run_victory_narrative(screen, player_name)
        
        # Show credits screen (regardless of outcome)
        result = run_credits_screen()
        
        if result == "replay":
            continue  # Replay airlock section
        else:
            break  # Exit to close game

def run_game():
    """Run full game sequence"""
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
    
    # Run navigation dialogue
    run_navigation_dialogue(screen, player_name)

    # Run airlock section (which can be replayed)
    run_airlock_section(screen, player_name)

def main():
    """Main game loop"""
    run_game()
    
    # Close game
    pygame.quit()

if __name__ == "__main__":
    main()