"""
Title sequence for ALIEN: CHRONOS
"""

import pygame
import sys
import time
import random
from config import WIDTH, HEIGHT, TERMINAL_GREEN, BRIGHT_GREEN, DIM_GREEN, TERMINAL_BLACK, load_fonts
from engine import green_flash

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

def boot_sequence(screen):
    """MOTHER computer boot sequence with random characters and lines"""
    font_large, font_medium, font_small = load_fonts()
    clock = pygame.time.Clock()
    
    # Character sets weighted toward MOTHER-style characters
    system_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    special_chars = "________----====||||"
    boot_lines = []
    max_lines = 35
    
    start_time = time.time()
    boot_duration = 3.0  # 3 seconds of boot sequence
    
    while time.time() - start_time < boot_duration:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        
        screen.fill(TERMINAL_BLACK)
        
        # Add new random lines
        if random.random() < 0.5 and len(boot_lines) < max_lines:
            # Mix of system text and special characters
            line_parts = []
            line_length = random.randint(8, 50)
            
            # Build line with chunks of different character types
            i = 0
            while i < line_length:
                chunk_type = random.choice(['system', 'special', 'space'])
                if chunk_type == 'system':
                    chunk_len = random.randint(2, 8)
                    line_parts.append("".join(random.choice(system_chars) for _ in range(chunk_len)))
                    i += chunk_len
                elif chunk_type == 'special':
                    chunk_len = random.randint(3, 15)
                    line_parts.append(random.choice(['_', '-', '=']) * chunk_len)
                    i += chunk_len
                else:
                    line_parts.append(" " * random.randint(1, 3))
                    i += random.randint(1, 3)
            
            line_text = "".join(line_parts)[:line_length]
            x_pos = random.randint(0, WIDTH - 600)
            y_pos = random.randint(20, HEIGHT - 40)
            boot_lines.append({
                'text': line_text,
                'x': x_pos,
                'y': y_pos,
                'alpha': 255,
                'color': random.choice([TERMINAL_GREEN, BRIGHT_GREEN, DIM_GREEN])
            })
        
        # Draw all boot lines
        for line in boot_lines:
            line_surface = font_small.render(line['text'], True, line['color'])
            jitter_x = line['x'] + random.randint(-3, 3)
            jitter_y = line['y'] + random.randint(-1, 1)
            screen.blit(line_surface, (jitter_x, jitter_y))
            
            # Fade out old lines
            line['alpha'] = max(0, line['alpha'] - 3)
        
        # Remove fully faded lines
        boot_lines = [line for line in boot_lines if line['alpha'] > 0]
        
        # Draw random horizontal lines (more frequent and varied)
        for _ in range(random.randint(3, 8)):
            y = random.randint(0, HEIGHT)
            width = random.randint(100, WIDTH - 100)
            x = random.randint(0, WIDTH - width)
            color = random.choice([TERMINAL_GREEN, DIM_GREEN])
            thickness = random.choice([1, 1, 1, 2])  # Mostly thin, occasionally thicker
            pygame.draw.line(screen, color, (x, y), (x + width, y), thickness)
        
        # Add some static
        if random.random() < 0.3:
            heavy_static_effect(screen, 20)
        
        scanline_effect(screen)
        pygame.display.flip()
        clock.tick(60)
    
    # Flash to indicate boot complete
    green_flash(screen)

def run_title_sequence(screen):
    """Run the title sequence animation"""
    font_large, font_medium, font_small = load_fonts()
    
    # Create even larger font for title
    try:
        title_font = pygame.font.Font("assets/VT323-Regular.ttf", 72)
    except:
        title_font = pygame.font.Font(None, 72)
    
    clock = pygame.time.Clock()
    
    # Phase 1: Heavy static (2 seconds)
    start_time = time.time()
    phase_duration = 2.0
    
    while time.time() - start_time < phase_duration:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                    return  # Skip to next part
        
        screen.fill(TERMINAL_BLACK)
        heavy_static_effect(screen, 300)
        scanline_effect(screen)
        
        pygame.display.flip()
        clock.tick(60)
    
    green_flash(screen)
    
    # Phase 2: "ALIEN:" appears with glitching (2 seconds)
    start_time = time.time()
    phase_duration = 2.0
    alien_alpha = 0
    
    while time.time() - start_time < phase_duration:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                    return
        
        progress = (time.time() - start_time) / phase_duration
        alien_alpha = min(255, int(progress * 255))
        
        screen.fill(TERMINAL_BLACK)
        
        # Background static (decreasing)
        if random.random() < 0.3:
            heavy_static_effect(screen, int(100 * (1 - progress)))
        
        # Draw "ALIEN:" with glitch effect
        alien_text = "/\LIEN:"
        alien_surface = title_font.render(alien_text, True, TERMINAL_GREEN)
        alien_rect = alien_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
        
        if random.random() < 0.8:
            draw_glitch_text(screen, alien_text, alien_rect.x, alien_rect.y, 
                           title_font, TERMINAL_GREEN)
        
        # Flicker effect
        if random.random() < 0.1:
            flicker_effect(screen, random.randint(10, 40))
        
        scanline_effect(screen)
        pygame.display.flip()
        clock.tick(60)
    
    green_flash(screen)
    
    # Phase 3: "CHRONOS" materializes (2.5 seconds)
    start_time = time.time()
    phase_duration = 2.5
    chronos_chars = list("CHRONOS")
    revealed_chars = 0
    last_reveal = start_time
    
    while time.time() - start_time < phase_duration:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                    return
        
        current_time = time.time()
        
        # Reveal characters progressively
        if current_time - last_reveal > 0.3 and revealed_chars < len(chronos_chars):
            revealed_chars += 1
            last_reveal = current_time
        
        screen.fill(TERMINAL_BLACK)
        
        # Light background static
        if random.random() < 0.2:
            heavy_static_effect(screen, 30)
        
        # Draw "ALIEN:"
        alien_text = "/\LIEN:"
        alien_surface = title_font.render(alien_text, True, TERMINAL_GREEN)
        alien_rect = alien_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
        screen.blit(alien_surface, alien_rect)
        
        # Draw partially revealed "CHRONOS"
        chronos_text = "".join(chronos_chars[:revealed_chars])
        if chronos_text:
            chronos_surface = title_font.render(chronos_text, True, TERMINAL_GREEN)
            chronos_rect = chronos_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30))
            
            # Add glitch to newly appearing letters
            if revealed_chars < len(chronos_chars) and random.random() < 0.5:
                draw_glitch_text(screen, chronos_text, chronos_rect.x, chronos_rect.y,
                               title_font, TERMINAL_GREEN)
            else:
                screen.blit(chronos_surface, chronos_rect)
        
        # Random flicker
        if random.random() < 0.08:
            flicker_effect(screen, random.randint(5, 25))
        
        scanline_effect(screen)
        pygame.display.flip()
        clock.tick(60)
    
    green_flash(screen)
    
    # Phase 4: Stable title with prompt (2 seconds hold, then wait for key)
    start_time = time.time()
    phase_duration = 2.0
    show_prompt = False
    
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                waiting = False
        
        # Show prompt after initial hold period
        if time.time() - start_time > phase_duration:
            show_prompt = True
        
        screen.fill(TERMINAL_BLACK)
        
        # Minimal static
        if random.random() < 0.05:
            heavy_static_effect(screen, 10)
        
        # Draw title
        alien_surface = title_font.render("ALIEN:", True, TERMINAL_GREEN)
        alien_rect = alien_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
        screen.blit(alien_surface, alien_rect)
        
        chronos_surface = title_font.render("CHRONOS", True, TERMINAL_GREEN)
        chronos_rect = chronos_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30))
        screen.blit(chronos_surface, chronos_rect)
        
        # Blinking prompt (only after hold period)
        if show_prompt and int(time.time() * 2) % 2 == 0:
            prompt_surface = font_small.render("PRESS ANY KEY TO INITIALIZE", True, DIM_GREEN)
            prompt_rect = prompt_surface.get_rect(center=(WIDTH // 2, HEIGHT - 80))
            screen.blit(prompt_surface, prompt_rect)
        
        scanline_effect(screen)
        pygame.display.flip()
        clock.tick(60)
    
    # Phase 5: Boot sequence
    boot_sequence(screen)
