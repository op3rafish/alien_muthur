"""
Test environment for ALIEN: CHRONOS
"""

import pygame
from scenes.maze import run_maze_game

def main():
    pygame.init()
    
    player_name = "Test Player"
    
    # Run just the maze game
    run_maze_game(player_name)
    
    pygame.quit()

if __name__ == "__main__":
    main()