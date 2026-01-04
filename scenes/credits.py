"""
Credits and thank you screen for ALIEN: MUTHUR
"""

import pygame
import sys
import webbrowser
from config import WIDTH, HEIGHT, TERMINAL_GREEN, BRIGHT_GREEN, TERMINAL_BLACK, load_fonts

def run_credits_screen():
    """Display credits screen with option to replay or quit"""
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("ALIEN: MUTHUR - Credits")
    
    font_large, font_medium, font_small = load_fonts()
    clock = pygame.time.Clock()
    
# Credits content
    credits_lines = [
        ("ALIEN: MU.TH.UR", font_large, TERMINAL_GREEN, 80),
        ("", font_small, TERMINAL_GREEN, 120),
        ("Thank you for playing!", font_medium, TERMINAL_GREEN, 160),
        ("", font_small, TERMINAL_GREEN, 200),
        ("Created by: Mark Bonington", font_small, TERMINAL_GREEN, 240),
        ("", font_small, TERMINAL_GREEN, 260),
        ("Connect with me on LinkedIn:", font_small, TERMINAL_GREEN, 300),
        ("linkedin.com/in/mark-bonington", font_small, BRIGHT_GREEN, 330),
        ("", font_small, TERMINAL_GREEN, 360),
        ("Built with Python & Pygame", font_small, TERMINAL_GREEN, 390),
        ("Font: VT323 by Peter Hull", font_small, TERMINAL_GREEN, 420),
        ("Inspired by the ALIEN franchise,", font_small, TERMINAL_GREEN, 450),
        ("created by Dan O'Bannon & Ronald Shusett", font_small, TERMINAL_GREEN, 480),
        ("", font_small, TERMINAL_GREEN, 510),
        ("", font_small, TERMINAL_GREEN, 540),
    ]

    controls_lines = [
        (" ", font_small, TERMINAL_GREEN, 450),
        (" ", font_small, TERMINAL_GREEN, 450),
        ("Press R to replay final puzzle", font_medium, TERMINAL_GREEN, HEIGHT - 80),
        ("Press ESC to Quit", font_medium, TERMINAL_GREEN, HEIGHT - 50),
    ]
    
    link_rect = None
    link_url = "https://www.linkedin.com/in/mark-bonington"
    
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                elif event.key == pygame.K_r:
                    return "replay"
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if link_rect and link_rect.collidepoint(event.pos):
                    webbrowser.open(link_url)
        
        screen.fill(TERMINAL_BLACK)
        
        # Draw credits
        for text, font, color, y_pos in credits_lines:
            if text:  # Skip empty lines
                text_surface = font.render(text, True, color)
                text_rect = text_surface.get_rect(center=(WIDTH // 2, y_pos))
                screen.blit(text_surface, text_rect)
                if "linkedin.com" in text:
                    link_rect = text_rect
        
        # Draw controls
        for text, font, color, y_pos in controls_lines:
            text_surface = font.render(text, True, color)
            text_rect = text_surface.get_rect(center=(WIDTH // 2, y_pos))
            screen.blit(text_surface, text_rect)
        
        pygame.display.flip()
        clock.tick(60)