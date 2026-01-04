"""
Game Over sequence for ALIEN: MUTHUR
"""

import pygame
import sys
import time
import random
from config import WIDTH, HEIGHT, TERMINAL_GREEN, BRIGHT_GREEN, DIM_GREEN, TERMINAL_BLACK, load_fonts

def heavy_static_effect(surface, intensity=200):
    """Create heavy static interference"""
    for _ in range(intensity):
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)
        brightness = random.randint(50, 255)
        color = (0, brightness, 0)
        size = random.randint(1, 3)
        pygame.draw.circle(surface, color, (x, y), size)

def scanline_effect(surface):
    """Draw horizontal scanlines across screen"""
    scanline_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for y in range(0, HEIGHT, 3):
        alpha = random.randint(5, 20)
        pygame.draw.line(scanline_surface, (0, 0, 0, alpha), (0, y), (WIDTH, y), 1)
    surface.blit(scanline_surface, (0, 0))

def flicker_effect(surface, intensity):
    """Apply screen flicker"""
    if intensity > 0:
        flicker_overlay = pygame.Surface((WIDTH, HEIGHT))
        flicker_overlay.fill((0, 0, 0))
        flicker_overlay.set_alpha(intensity)
        surface.blit(flicker_overlay, (0, 0))

def draw_glitch_text(surface, text, x, y, font, base_color):
    """Draw text with glitch offset effect"""
    # Draw offset "ghost" copies
    offsets = [(-2, -2), (2, 2), (-3, 1)]
    for offset_x, offset_y in offsets:
        if random.random() < 0.7:
            ghost_color = (0, random.randint(100, 200), 0)
            ghost_surface = font.render(text, True, ghost_color)
            surface.blit(ghost_surface, (x + offset_x, y + offset_y))
    
    # Draw main text
    text_surface = font.render(text, True, base_color)
    surface.blit(text_surface, (x, y))

def run_game_over_sequence(screen):
    """Display game over sequence"""
    font_large, font_medium, font_small = load_fonts()
    
    # Create even larger font for main text
    try:
        title_font = pygame.font.Font("assets/VT323-Regular.ttf", 72)
    except:
        title_font = pygame.font.Font(None, 72)
    
    clock = pygame.time.Clock()
    
    # Phase 1: Heavy static and disruption (2 seconds)
    start_time = time.time()
    phase_duration = 2.0
    
    while time.time() - start_time < phase_duration:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        
        screen.fill(TERMINAL_BLACK)
        heavy_static_effect(screen, 400)
        
        # Random error-like text flashing
        if random.random() < 0.3:
            error_texts = ["CRITICAL", "FAILURE", "ERROR", "TERMINATED", ">>>"]
            error_text = random.choice(error_texts)
            x = random.randint(50, WIDTH - 200)
            y = random.randint(50, HEIGHT - 100)
            color = (0, random.randint(150, 255), 0)
            error_surface = font_medium.render(error_text, True, color)
            screen.blit(error_surface, (x, y))
        
        scanline_effect(screen)
        pygame.display.flip()
        clock.tick(60)
    
    # Phase 2: "GAME OVER" glitches in (3 seconds)
    start_time = time.time()
    phase_duration = 3.0
    
    while time.time() - start_time < phase_duration:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        
        progress = (time.time() - start_time) / phase_duration
        
        screen.fill(TERMINAL_BLACK)
        
        # Decreasing static
        if random.random() < 0.4:
            heavy_static_effect(screen, int(200 * (1 - progress)))
        
        # Draw "GAME OVER" with heavy glitching
        game_over_text = "GAME OVER"
        text_surface = title_font.render(game_over_text, True, TERMINAL_GREEN)
        text_rect = text_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        
        # Heavy glitch early, stabilizing later
        if random.random() < (1 - progress):
            draw_glitch_text(screen, game_over_text, text_rect.x, text_rect.y, 
                           title_font, TERMINAL_GREEN)
        else:
            screen.blit(text_surface, text_rect)
        
        # Aggressive flicker
        if random.random() < 0.2:
            flicker_effect(screen, random.randint(20, 80))
        
        scanline_effect(screen)
        pygame.display.flip()
        clock.tick(60)
    
    # Phase 3: Stable "GAME OVER" (2 seconds)
    start_time = time.time()
    phase_duration = 2.0
    
    while time.time() - start_time < phase_duration:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        
        screen.fill(TERMINAL_BLACK)
        
        # Minimal static
        if random.random() < 0.1:
            heavy_static_effect(screen, 30)
        
        # Main text centered
        game_over_text = "GAME OVER"
        text_surface = title_font.render(game_over_text, True, TERMINAL_GREEN)
        text_rect = text_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(text_surface, text_rect)
        
        # Occasional flicker
        if random.random() < 0.08:
            flicker_effect(screen, random.randint(10, 30))
        
        scanline_effect(screen)
        pygame.display.flip()
        clock.tick(60)
    
    # Phase 4: Slow fade to black (2 seconds)
    fade_duration = 2.0
    fade_start = time.time()
    
    # Capture the final frame
    final_frame = screen.copy()
    
    while time.time() - fade_start < fade_duration:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        
        fade_progress = (time.time() - fade_start) / fade_duration
        
        screen.blit(final_frame, (0, 0))
        
        # Occasional static flashes
        if random.random() < 0.05:
            heavy_static_effect(screen, int(20 * (1 - fade_progress)))
        
        # Darken overlay
        dark_overlay = pygame.Surface((WIDTH, HEIGHT))
        dark_overlay.fill((0, 0, 0))
        dark_overlay.set_alpha(int(255 * fade_progress))
        screen.blit(dark_overlay, (0, 0))
        
        pygame.display.flip()
        clock.tick(60)
    
    # Hold on black
    screen.fill(TERMINAL_BLACK)
    pygame.display.flip()
    time.sleep(1)