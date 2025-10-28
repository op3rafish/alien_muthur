"""
Shared utilities and effects for ALIEN: CHRONOS
"""

import pygame
import random
import time
import sys
from config import WIDTH, HEIGHT, TERMINAL_GREEN, TERMINAL_BLACK

# CRT Effects globals
flicker_intensity = 0
static_active = False
static_timer = 0

def display_typing_sequence(texts, screen, start_y=50, line_spacing=35, line_pauses=None):
    """Display a sequence of typing texts
    
    Args:
        texts: List of (text, font) tuples
        screen: Pygame screen
        start_y: Starting y position
        line_spacing: Space between lines
        line_pauses: Optional dict of {line_index: pause_time} for pauses after specific lines
                     Example: {0: 1.0, 2: 0.5} pauses 1 sec after line 0, 0.5 sec after line 2
    """
    clock = pygame.time.Clock()
    text_objects = []
    current_text_index = 0
    y_position = start_y
    pause_until = None
    
    # Default: no pauses between lines
    if line_pauses is None:
        line_pauses = {}
    
    for text_info in texts:
        text, font = text_info
        text_obj = TypingText(text, 50, y_position, font, TERMINAL_GREEN)
        text_objects.append(text_obj)
        y_position += line_spacing
    
    # Animate all texts
    all_finished = False
    while not all_finished:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        
        current_time = time.time()
        
        # Check if we're in a pause
        if pause_until and current_time < pause_until:
            pass  # Wait during pause
        else:
            pause_until = None
            # Update current text
            if current_text_index < len(text_objects):
                if text_objects[current_text_index].update(current_time):
                    # Line finished typing, check if it needs a pause
                    if current_text_index in line_pauses:
                        pause_until = current_time + line_pauses[current_text_index]
                    current_text_index += 1
        
        # Check if all finished
        all_finished = all(text.finished for text in text_objects) and pause_until is None
        
        # Draw
        screen.fill(TERMINAL_BLACK)
        for text_obj in text_objects:
            text_obj.draw(screen)
        apply_crt_effects(screen)
        
        pygame.display.flip()
        clock.tick(60)
    
    return text_objects


def apply_crt_effects(surface):
    """Apply CRT screen effects like flicker and static"""
    global flicker_intensity, static_active, static_timer
    
    # Random flicker effect
    if random.random() < 0.05:
        flicker_intensity = random.randint(5, 25)
    
    if flicker_intensity > 0:
        flicker_overlay = pygame.Surface((WIDTH, HEIGHT))
        flicker_overlay.fill((0, 0, 0))
        flicker_overlay.set_alpha(flicker_intensity)
        surface.blit(flicker_overlay, (0, 0))
        flicker_intensity = max(0, flicker_intensity - 2)
    
    # Random static effect
    static_timer -= 1
    if static_timer <= 0 and random.random() < 0.02:
        static_active = True
        static_timer = random.randint(2, 6)
    
    if static_active:
        for _ in range(50):
            x = random.randint(0, WIDTH)
            y = random.randint(0, HEIGHT)
            intensity = random.randint(100, 255)
            color = (0, intensity, 0)
            pygame.draw.circle(surface, color, (x, y), 1)
        
        static_timer -= 1
        if static_timer <= 0:
            static_active = False
    
    # Scanline effect
    if random.random() < 0.3:
        scanline_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for y in range(0, HEIGHT, 4):
            pygame.draw.line(scanline_surface, (0, 0, 0, 10), (0, y), (WIDTH, y), 1)
        surface.blit(scanline_surface, (0, 0))

def green_flash(screen, duration=0.1):
    """Flash the screen green"""
    flash_surface = pygame.Surface((WIDTH, HEIGHT))
    flash_surface.fill(TERMINAL_GREEN)
    flash_surface.set_alpha(200)
    screen.blit(flash_surface, (0, 0))
    pygame.display.flip()
    time.sleep(duration)

def wait_for_time(duration, screen, texts_to_draw):
    """Wait for a duration while keeping the display updated"""
    start_time = time.time()
    clock = pygame.time.Clock()
    
    while time.time() - start_time < duration:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        
        screen.fill(TERMINAL_BLACK)
        for text_obj in texts_to_draw:
            text_obj.draw(screen)
        apply_crt_effects(screen)
        pygame.display.flip()
        clock.tick(60)

class TypingText:
    """Handles typing animation for text"""
    def __init__(self, text, x, y, font, color, delay=0.06):
        self.text = text
        self.x = x
        self.y = y
        self.font = font
        self.color = color
        self.delay = delay
        self.current_char = 0
        self.last_update = 0
        self.finished = False
        
    def update(self, current_time):
        if not self.finished and current_time - self.last_update > self.delay:
            self.current_char += 1
            self.last_update = current_time
            if self.current_char >= len(self.text):
                self.finished = True
        return self.finished
    
    def draw(self, surface):
        if self.current_char > 0:
            displayed_text = self.text[:self.current_char]
            text_surface = self.font.render(displayed_text, True, self.color)
            surface.blit(text_surface, (self.x, self.y))