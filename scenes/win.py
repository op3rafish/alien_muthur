"""
Shutdown sequence for ALIEN: CHRONOS
"""

import pygame
import sys
import time
import random
from config import WIDTH, HEIGHT, TERMINAL_GREEN, BRIGHT_GREEN, DIM_GREEN, TERMINAL_BLACK, load_fonts

def shutdown_static_effect(surface, intensity=200):
    """Create static interference during shutdown"""
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

def run_shutdown_sequence(screen):
    """MOTHER computer shutdown sequence with degrading text columns"""
    font_large, font_medium, font_small = load_fonts()
    clock = pygame.time.Clock()
    
    # Character sets
    system_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    special_chars = "________----====||||"
    
    # Create text columns that will degrade
    columns = []
    num_columns = 25
    
    for i in range(num_columns):
        column = {
            'x': random.randint(20, WIDTH - 100),
            'lines': [],
            'fade_speed': random.uniform(2, 8),
            'alive': True
        }
        
        # Generate random lines for this column
        num_lines = random.randint(8, 20)
        for _ in range(num_lines):
            line_length = random.randint(5, 30)
            line_parts = []
            
            for j in range(line_length):
                if random.random() < 0.7:
                    line_parts.append(random.choice(system_chars))
                else:
                    line_parts.append(random.choice(special_chars))
            
            column['lines'].append({
                'text': "".join(line_parts),
                'alpha': 255,
                'y': random.randint(20, HEIGHT - 40)
            })
        
        columns.append(column)
    
    # Flashing bars
    bars = []
    for _ in range(15):
        bars.append({
            'y': random.randint(0, HEIGHT),
            'width': random.randint(200, WIDTH - 100),
            'x': random.randint(0, WIDTH - 200),
            'flash_rate': random.uniform(0.05, 0.2),
            'thickness': random.choice([2, 3, 4, 5]),
            'alive': True
        })
    
    start_time = time.time()
    shutdown_duration = 5.0  # 5 seconds of shutdown
    
    while time.time() - start_time < shutdown_duration:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        
        progress = (time.time() - start_time) / shutdown_duration
        
        screen.fill(TERMINAL_BLACK)
        
        # Draw degrading columns
        for column in columns:
            if not column['alive']:
                continue
            
            for line in column['lines']:
                # Fade out lines
                line['alpha'] = max(0, line['alpha'] - column['fade_speed'])
                
                if line['alpha'] > 0:
                    # Add jitter as it fades
                    jitter_amount = int((255 - line['alpha']) / 30)
                    jitter_x = column['x'] + random.randint(-jitter_amount, jitter_amount)
                    jitter_y = line['y'] + random.randint(-jitter_amount // 2, jitter_amount // 2)
                    
                    # Calculate color with alpha
                    alpha_factor = line['alpha'] / 255
                    color_value = int(255 * alpha_factor * random.uniform(0.6, 1.0))
                    color = (0, color_value, 0)
                    
                    text_surface = font_small.render(line['text'], True, color)
                    screen.blit(text_surface, (jitter_x, jitter_y))
            
            # Check if column is dead
            if all(line['alpha'] <= 0 for line in column['lines']):
                column['alive'] = False
        
        # Draw flashing bars
        for bar in bars:
            if not bar['alive']:
                continue
            
            # Random flashing
            if random.random() < bar['flash_rate']:
                # Fade bars over time
                color_intensity = int(255 * (1 - progress * 0.7))
                color = (0, random.randint(color_intensity // 2, color_intensity), 0)
                
                # Add some vertical drift
                drift = int(progress * 50 * random.choice([-1, 1]))
                y_pos = bar['y'] + drift
                
                pygame.draw.line(screen, color, 
                               (bar['x'], y_pos), 
                               (bar['x'] + bar['width'], y_pos), 
                               bar['thickness'])
            
            # Kill bars over time
            if random.random() < progress * 0.1:
                bar['alive'] = False
        
        # Increasing static as shutdown progresses
        if random.random() < 0.3:
            shutdown_static_effect(screen, int(100 * progress))
        
        # More frequent scanlines during shutdown
        if random.random() < 0.5:
            scanline_effect(screen)
        
        # Screen flicker increases near end
        if progress > 0.7 and random.random() < 0.15:
            flicker_overlay = pygame.Surface((WIDTH, HEIGHT))
            flicker_overlay.fill((0, 0, 0))
            flicker_overlay.set_alpha(random.randint(20, 60))
            screen.blit(flicker_overlay, (0, 0))
        
        pygame.display.flip()
        clock.tick(60)
    
    # Final fade to black
    fade_duration = 1.5
    fade_start = time.time()
    
    while time.time() - fade_start < fade_duration:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        
        fade_progress = (time.time() - fade_start) / fade_duration
        
        screen.fill(TERMINAL_BLACK)
        
        # Occasional flicker of static
        if random.random() < 0.1:
            shutdown_static_effect(screen, int(20 * (1 - fade_progress)))
        
        # Darken overlay
        dark_overlay = pygame.Surface((WIDTH, HEIGHT))
        dark_overlay.fill((0, 0, 0))
        dark_overlay.set_alpha(int(255 * fade_progress))
        screen.blit(dark_overlay, (0, 0))
        
        pygame.display.flip()
        clock.tick(60)
    
    # Hold on black for a moment
    screen.fill(TERMINAL_BLACK)
    pygame.display.flip()
    time.sleep(1)