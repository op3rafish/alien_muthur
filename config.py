"""
Configuration file for ALIEN: MUTHUR
Contains all constants, colors, and font initialization
"""

import pygame

# Screen setup
WIDTH = 1250
HEIGHT = 625

# Terminal colors
TERMINAL_GREEN = (0, 255, 0)
BRIGHT_GREEN = (150, 255, 150)
DIM_GREEN = (0, 150, 0)
TERMINAL_BLACK = (0, 0, 0)

# Maze constants
CELL_SIZE = 25
GRID_WIDTH = 50
GRID_HEIGHT = 25

# System colors
POWER_COLOR = TERMINAL_GREEN
DATA_COLOR = TERMINAL_GREEN
COOLANT_COLOR = TERMINAL_GREEN

def load_fonts():
    """Load and return game fonts"""
    try:
        font_large = pygame.font.Font("assets/VT323-Regular.ttf", 50)
        font_medium = pygame.font.Font("assets/VT323-Regular.ttf", 28)
        font_small = pygame.font.Font("assets/VT323-Regular.ttf", 24)
    except:
        print("VT323 font not found. Using default font.")
        font_large = pygame.font.Font(None, 36)
        font_medium = pygame.font.Font(None, 28)
        font_small = pygame.font.Font(None, 24)
    
    return font_large, font_medium, font_small