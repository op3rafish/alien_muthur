"""
Test environment for ALIEN: MUTHUR
"""

import pygame
from config import WIDTH, HEIGHT
from scenes.credits import run_credits_screen

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Test - Credits")

    result = run_credits_screen()
    print(f"Result: {result}")
    
    pygame.quit()

if __name__ == "__main__":
    main()