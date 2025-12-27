"""
Airlock puzzle for ALIEN: CHRONOS
Herd the xenomorph to the cargo hold and blow it into space
"""

import pygame
import sys
import math
import random
from config import (WIDTH, HEIGHT, TERMINAL_GREEN, BRIGHT_GREEN, 
                   DIM_GREEN, TERMINAL_BLACK, load_fonts)
from engine import apply_crt_effects, green_flash

class Room:
    """Represents a ship room"""
    def __init__(self, name, shape, x, y, w, h):
        self.name = name
        self.shape = shape  # 'angular', 'hex', 'circular', 'octagon', 'rect'
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.center_x = x + w // 2
        self.center_y = y + h // 2
        
    def draw(self, surface, font):
        """Draw the room based on its shape"""
        if self.shape == 'angular':
            self._draw_angular(surface)
        elif self.shape == 'hex':
            self._draw_hex(surface)
        elif self.shape == 'circular':
            self._draw_circular(surface)
        elif self.shape == 'octagon':
            self._draw_octagon(surface)
        else:
            self._draw_rect(surface)
        
        # Draw label
        text = font.render(self.name, True, TERMINAL_GREEN)
        text_rect = text.get_rect(center=(self.center_x, self.y + 20))
        surface.blit(text, text_rect)
    
    def _draw_angular(self, surface):
        offset = 10
        points = [
            (self.x + offset, self.y),
            (self.x + self.w - offset, self.y),
            (self.x + self.w, self.y + offset),
            (self.x + self.w, self.y + self.h - offset),
            (self.x + self.w - offset, self.y + self.h),
            (self.x + offset, self.y + self.h),
            (self.x, self.y + self.h - offset),
            (self.x, self.y + offset)
        ]
        pygame.draw.polygon(surface, TERMINAL_GREEN, points, 2)
    
    def _draw_hex(self, surface):
        points = [
            (self.x + self.w * 0.25, self.y),
            (self.x + self.w * 0.75, self.y),
            (self.x + self.w, self.y + self.h * 0.5),
            (self.x + self.w * 0.75, self.y + self.h),
            (self.x + self.w * 0.25, self.y + self.h),
            (self.x, self.y + self.h * 0.5)
        ]
        pygame.draw.polygon(surface, TERMINAL_GREEN, points, 2)
    
    def _draw_circular(self, surface):
        pygame.draw.ellipse(surface, TERMINAL_GREEN, 
                          (self.x, self.y, self.w, self.h), 2)
    
    def _draw_octagon(self, surface):
        cx = self.center_x
        cy = self.center_y
        radius = min(self.w, self.h) // 2
        points = []
        for i in range(8):
            angle = (i / 8) * math.pi * 2 - math.pi / 8
            px = cx + math.cos(angle) * radius
            py = cy + math.sin(angle) * radius
            points.append((px, py))
        pygame.draw.polygon(surface, TERMINAL_GREEN, points, 2)
    
    def _draw_rect(self, surface):
        pygame.draw.rect(surface, TERMINAL_GREEN, 
                        (self.x, self.y, self.w, self.h), 3)
    
    def contains_point(self, x, y):
        """Check if point is inside room bounds"""
        return (self.x <= x <= self.x + self.w and 
                self.y <= y <= self.y + self.h)

class Corridor:
    """Represents a corridor connection"""
    def __init__(self, x1, y1, x2, y2, width=30):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.width = width
    
    def draw(self, surface):
        """Draw parallel lines for corridor"""
        # Calculate perpendicular offset
        dx = self.x2 - self.x1
        dy = self.y2 - self.y1
        length = math.sqrt(dx*dx + dy*dy)
        if length == 0:
            return
        
        # Perpendicular vector
        px = -dy / length * (self.width / 2)
        py = dx / length * (self.width / 2)
        
        # Draw two parallel lines
        pygame.draw.line(surface, TERMINAL_GREEN,
                        (self.x1 + px, self.y1 + py),
                        (self.x2 + px, self.y2 + py), 2)
        pygame.draw.line(surface, TERMINAL_GREEN,
                        (self.x1 - px, self.y1 - py),
                        (self.x2 - px, self.y2 - py), 2)

class Bulkhead:
    """Represents a sealable bulkhead"""
    def __init__(self, name, x, y, orientation='v'):
        self.name = name
        self.x = x
        self.y = y
        self.orientation = orientation  # 'v' or 'h'
        self.sealed = False
    
    def draw(self, surface, font_small):
        color = BRIGHT_GREEN if self.sealed else TERMINAL_GREEN
        width = 5 if self.sealed else 2
        
        if self.orientation == 'v':
            # Vertical bulkhead (blocks horizontal movement)
            pygame.draw.line(surface, color, (self.x, self.y - 15), (self.x, self.y + 15), width)
            pygame.draw.line(surface, color, (self.x + 5, self.y - 15), (self.x + 5, self.y + 15), width)
            
            label = font_small.render(self.name, True, color)
            surface.blit(label, (self.x + 10, self.y - 5))
            if self.sealed:
                sealed_text = font_small.render('[SEALED]', True, color)
                surface.blit(sealed_text, (self.x + 10, self.y + 8))
        else:
            # Horizontal bulkhead (blocks vertical movement)
            pygame.draw.line(surface, color, (self.x - 15, self.y), (self.x + 15, self.y), width)
            pygame.draw.line(surface, color, (self.x - 15, self.y + 5), (self.x + 15, self.y + 5), width)
            
            label = font_small.render(self.name, True, color)
            surface.blit(label, (self.x + 20, self.y))
            if self.sealed:
                sealed_text = font_small.render('[SEALED]', True, color)
                surface.blit(sealed_text, (self.x + 20, self.y + 12))
    
    def blocks_movement(self, x1, y1, x2, y2):
        """Check if bulkhead blocks movement from (x1,y1) to (x2,y2)"""
        if not self.sealed:
            return False
        
        # Check if movement crosses bulkhead
        if self.orientation == 'v':
            # Vertical bulkhead blocks horizontal movement
            if (x1 < self.x < x2 or x2 < self.x < x1):
                if abs(y1 - self.y) < 20 and abs(y2 - self.y) < 20:
                    return True
        else:
            # Horizontal bulkhead blocks vertical movement
            if (y1 < self.y < y2 or y2 < self.y < y1):
                if abs(x1 - self.x) < 20 and abs(x2 - self.x) < 20:
                    return True
        return False

class Alien:
    """The xenomorph"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.target_x = x
        self.target_y = y
        self.trail = []
        self.speed = 1.5
        self.wander_timer = 0
        self.wander_interval = random.randint(120, 240)  # Frames between new targets
        self.exploring = True
        
        # Waypoints the alien knows about
        self.waypoints = [
            (90, 245),   # Crew quarters
            (255, 85),   # Kitchen
            (415, 85),   # Mother
            (605, 85),   # Hypersleep
            (400, 245),  # Med bay
            (610, 245),  # Autodoc
            (340, 470),  # Engineering
            (490, 470),  # Reactor
            (350, 588),  # Cargo
        ]
    
    def update(self, bulkheads, rooms):
        """Move toward target and pick new exploration targets"""
        # Wander behavior - pick random waypoints
        self.wander_timer += 1
        if self.wander_timer >= self.wander_interval:
            # Pick a random waypoint to explore
            new_target = random.choice(self.waypoints)
            self.target_x, self.target_y = new_target
            self.wander_timer = 0
            self.wander_interval = random.randint(120, 240)
        
        # Move toward target
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        dist = math.sqrt(dx*dx + dy*dy)
        
        if dist > 5:
            # Calculate next position
            next_x = self.x + (dx / dist) * self.speed
            next_y = self.y + (dy / dist) * self.speed
            
            # Check if movement is blocked by sealed bulkheads
            blocked = False
            for bulkhead in bulkheads.values():
                if bulkhead.blocks_movement(self.x, self.y, next_x, next_y):
                    blocked = True
                    # Pick new random target when blocked
                    self.wander_timer = self.wander_interval
                    break
            
            if not blocked:
                self.x = next_x
                self.y = next_y
                
                # Update trail
                self.trail.append((self.x, self.y))
                if len(self.trail) > 15:
                    self.trail.pop(0)
    
    def set_target(self, x, y):
        self.target_x = x
        self.target_y = y
        self.wander_timer = 0
    
    def draw(self, surface):
        """Draw alien with pulsing effect"""
        # Motion trail
        if len(self.trail) > 1:
            for i in range(len(self.trail) - 1):
                alpha = int((i / len(self.trail)) * 150)
                color = (0, alpha, 0)
                pygame.draw.line(surface, color, self.trail[i], self.trail[i + 1], 3)
        
        # Pulsing diamond
        pulse = math.sin(pygame.time.get_ticks() / 200) * 2 + 8
        
        points = [
            (self.x, self.y - pulse),
            (self.x + pulse, self.y),
            (self.x, self.y + pulse),
            (self.x - pulse, self.y)
        ]
        pygame.draw.polygon(surface, TERMINAL_GREEN, points)
        pygame.draw.polygon(surface, BRIGHT_GREEN, points, 2)
        
        # Blink effect
        if (pygame.time.get_ticks() // 300) % 2 == 0:
            pygame.draw.circle(surface, BRIGHT_GREEN, (int(self.x), int(self.y)), 
                             int(pulse + 6), 1)

def run_airlock_puzzle(player_name):
    """Main function to run the airlock puzzle"""
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("MUTHER - AIRLOCK PROTOCOL")
    
    font_large, font_medium, font_small = load_fonts()
    clock = pygame.time.Clock()
    
    # Create ship layout
    rooms = {
        'bridge': Room('BRIDGE', 'angular', 40, 40, 100, 90),
        'kitchen': Room('KITCHEN', 'hex', 200, 40, 110, 90),
        'mother': Room('MOTHER', 'circular', 380, 40, 70, 90),
        'hypersleep': Room('HYPERSLEEP', 'circular', 560, 40, 90, 90),
        'crew': Room('CREW', 'angular', 40, 200, 100, 90),
        'medbay': Room('MED BAY', 'hex', 340, 200, 120, 90),
        'autodoc': Room('AUTODOC', 'angular', 560, 200, 100, 90),
        'engineering': Room('ENGINE', 'circular', 290, 420, 100, 100),
        'reactor': Room('REACTOR', 'octagon', 450, 430, 80, 80),
        'cargo': Room('CARGO', 'rect', 200, 560, 300, 55)
    }
    
    # Create corridors - ensuring proper connections
    corridors = [
        # Top row - bridge to kitchen
        Corridor(140, 70, 200, 70),
        Corridor(140, 100, 200, 100),
        # Kitchen to mother
        Corridor(310, 70, 380, 70),
        Corridor(310, 100, 380, 100),
        # Mother to hypersleep
        Corridor(450, 70, 560, 70),
        Corridor(450, 100, 560, 100),
        
        # Vertical from kitchen down
        Corridor(240, 130, 240, 200),
        Corridor(270, 130, 270, 200),
        # Vertical from mother down
        Corridor(400, 130, 400, 200),
        Corridor(430, 130, 430, 200),
        
        # Crew quarters to medbay junction
        Corridor(140, 230, 240, 230),
        Corridor(140, 260, 240, 260),
        # Continue to medbay
        Corridor(270, 230, 340, 230),
        Corridor(270, 260, 340, 260),
        
        # Medbay to autodoc
        Corridor(460, 230, 560, 230),
        Corridor(460, 260, 560, 260),
        
        # Mother corridor continues down
        Corridor(400, 290, 400, 360),
        Corridor(430, 290, 430, 360),
        
        # From kitchen/medbay down
        Corridor(240, 290, 240, 360),
        Corridor(270, 290, 270, 360),
        
        # Horizontal junction merge
        Corridor(240, 360, 340, 360),
        Corridor(240, 390, 340, 390),
        Corridor(380, 360, 430, 360),
        Corridor(380, 390, 430, 390),
        
        # Down to engineering
        Corridor(325, 390, 325, 420),
        Corridor(355, 390, 355, 420),
        
        # Engineering to reactor
        Corridor(390, 455, 450, 455),
        Corridor(390, 485, 450, 485),
        
        # Engineering down to cargo
        Corridor(325, 520, 325, 560),
        Corridor(355, 520, 355, 560)
    ]
    
    # Create bulkheads
    bulkheads = {
        'B1': Bulkhead('B1', 505, 85, 'v'),
        'B2': Bulkhead('B2', 255, 165, 'h'),
        'B3': Bulkhead('B3', 415, 165, 'h'),
        'B4': Bulkhead('B4', 510, 245, 'v'),
        'B5': Bulkhead('B5', 350, 375, 'v'),
        'B6': Bulkhead('B6', 340, 540, 'h')
    }
    
    # Create alien (starts in crew quarters)
    alien = Alien(90, 245)
    
    # Game state
    game_won = False
    game_over = False
    cargo_sealed = False
    airlock_ready = False
    command_input = ""
    command_history = []
    error_message = ""
    message_timer = 0
    
    # Main game loop
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()
            
            elif event.type == pygame.KEYDOWN and not game_won and not game_over:
                if event.key == pygame.K_RETURN:
                    # Process command
                    cmd = command_input.strip().upper()
                    command_history.append(f"> {cmd}")
                    
                    # Check if it's a valid bulkhead command
                    if cmd.startswith('SEAL ') or cmd.startswith('OPEN '):
                        action, bulkhead_name = cmd.split(' ', 1)
                        
                        if bulkhead_name in bulkheads:
                            if action == 'SEAL':
                                bulkheads[bulkhead_name].sealed = True
                                command_history.append(f"BULKHEAD {bulkhead_name} SEALED")
                            else:
                                bulkheads[bulkhead_name].sealed = False
                                command_history.append(f"BULKHEAD {bulkhead_name} OPENED")
                            
                            error_message = ""
                            
                            # Check if cargo is sealed
                            if bulkhead_name == 'B6' and bulkheads['B6'].sealed:
                                cargo_sealed = True
                                command_history.append("CARGO HOLD ISOLATED")
                                airlock_ready = True
                            elif bulkhead_name == 'B6' and not bulkheads['B6'].sealed:
                                cargo_sealed = False
                                airlock_ready = False
                        else:
                            error_message = "ERROR: INVALID BULKHEAD DESIGNATION"
                            message_timer = pygame.time.get_ticks() + 2000
                    
                    elif cmd == 'OPEN AIRLOCK':
                        if cargo_sealed and 200 < alien.x < 500 and alien.y > 560:
                            # Win condition!
                            game_won = True
                            command_history.append("AIRLOCK OPENING...")
                            command_history.append("DECOMPRESSION SEQUENCE INITIATED")
                        elif not cargo_sealed:
                            error_message = "ERROR: CARGO HOLD NOT SEALED"
                            message_timer = pygame.time.get_ticks() + 2000
                        else:
                            error_message = "ERROR: TARGET NOT IN CARGO HOLD"
                            message_timer = pygame.time.get_ticks() + 2000
                    
                    else:
                        error_message = "ERROR: INVALID COMMAND"
                        message_timer = pygame.time.get_ticks() + 2000
                    
                    command_input = ""
                    
                    # Keep only last 8 history lines
                    if len(command_history) > 8:
                        command_history = command_history[-8:]
                
                elif event.key == pygame.K_BACKSPACE:
                    command_input = command_input[:-1]
                    error_message = ""
                
                elif event.unicode.isprintable():
                    if len(command_input) < 30:
                        command_input += event.unicode
                        error_message = ""
        
        # Update alien exploration
        if not game_won and not game_over:
            alien.update(bulkheads, rooms)
            
            # Check if alien reached bridge
            if math.sqrt((alien.x - 90)**2 + (alien.y - 85)**2) < 30:
                game_over = True
        
        # Clear error message after timer
        if message_timer > 0 and pygame.time.get_ticks() > message_timer:
            error_message = ""
            message_timer = 0
        
        # Draw everything
        screen.fill(TERMINAL_BLACK)
        
        # Draw corridors
        for corridor in corridors:
            corridor.draw(screen)
        
        # Draw rooms
        for room in rooms.values():
            room.draw(screen, font_small)
        
        # Draw special room features
        # Player in bridge
        pygame.draw.circle(screen, BRIGHT_GREEN, (90, 85), 6)
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            pygame.draw.circle(screen, BRIGHT_GREEN, (90, 85), 10, 2)
        
        # Dead crew in crew quarters
        dead_text = font_small.render('[X] KANE', True, (255, 68, 68))
        screen.blit(dead_text, (50, 240))
        dead_text = font_small.render('[X] LAMBERT', True, (255, 68, 68))
        screen.blit(dead_text, (50, 255))
        
        # Medical symbol
        med_symbol = font_medium.render('⚕', True, TERMINAL_GREEN)
        screen.blit(med_symbol, (390, 240))
        
        # Engineering hazards
        hazard = font_medium.render('⚠ ⚠ ⚠', True, BRIGHT_GREEN)
        screen.blit(hazard, (310, 460))
        
        # Reactor cores
        for i in range(3):
            glow = (pygame.time.get_ticks() // 400) % 2 == 0
            color = BRIGHT_GREEN if glow else TERMINAL_GREEN
            pygame.draw.circle(screen, color, (480 + (i - 1) * 20, 470), 6)
        
        # Cargo crates
        crate_positions = [(220, 595), (250, 595), (280, 595), (320, 595), 
                          (360, 595), (400, 595), (450, 595)]
        for cx, cy in crate_positions:
            pygame.draw.rect(screen, DIM_GREEN, (cx, cy, 15, 15))
        
        # Airlock
        airlock_color = BRIGHT_GREEN if airlock_ready else DIM_GREEN
        airlock_points = [(500, 575), (540, 575), (550, 587), (540, 600), (500, 600)]
        pygame.draw.polygon(screen, airlock_color, airlock_points, 3)
        airlock_label = font_small.render('AIRLOCK', True, airlock_color)
        screen.blit(airlock_label, (505, 585))
        
        # Draw bulkheads
        for bulkhead in bulkheads.values():
            bulkhead.draw(screen, font_small)
        
        # Draw alien
        if not game_won:
            alien.draw(screen)
        
        # Draw UI overlay (right side)
        ui_x = 700
        ui_y = 50
        
        # Title
        title = font_medium.render('MUTHER TERMINAL', True, BRIGHT_GREEN)
        screen.blit(title, (ui_x, ui_y))
        
        ui_y += 40
        
        # Command history
        for i, line in enumerate(command_history):
            hist_color = TERMINAL_GREEN if line.startswith('>') else DIM_GREEN
            hist_text = font_small.render(line, True, hist_color)
            screen.blit(hist_text, (ui_x, ui_y + i * 20))
        
        ui_y += len(command_history) * 20 + 30
        
        # Command prompt
        prompt = font_small.render('> ' + command_input + '_', True, BRIGHT_GREEN)
        screen.blit(prompt, (ui_x, ui_y))
        
        ui_y += 30
        
        # Error message
        if error_message:
            err_text = font_small.render(error_message, True, (255, 100, 100))
            screen.blit(err_text, (ui_x, ui_y))
        
        ui_y += 40
        
        # Available commands
        help_y = HEIGHT - 150
        help_lines = [
            'COMMANDS:',
            'SEAL B1-B6',
            'OPEN B1-B6',
            'OPEN AIRLOCK',
            '',
            'OBJECTIVE:',
            'Herd xenomorph to cargo',
            'Seal cargo (B6)',
            'Open airlock'
        ]
        
        for i, line in enumerate(help_lines):
            help_text = font_small.render(line, True, DIM_GREEN)
            screen.blit(help_text, (ui_x, help_y + i * 18))
        
        # Win/lose messages
        if game_won:
            win_text = font_large.render('AIRLOCK OPENED', True, BRIGHT_GREEN)
            win_rect = win_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            screen.blit(win_text, win_rect)
            
            # Auto-exit after 3 seconds
            if not hasattr(run_airlock_puzzle, 'win_timer'):
                run_airlock_puzzle.win_timer = pygame.time.get_ticks() + 3000
            
            if pygame.time.get_ticks() > run_airlock_puzzle.win_timer:
                running = False
        
        if game_over:
            lose_text = font_large.render('LIFE SIGNS NEGATIVE', True, (255, 68, 68))
            lose_rect = lose_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            screen.blit(lose_text, lose_rect)
        
        # Apply CRT effects
        apply_crt_effects(screen)
        
        pygame.display.flip()
        clock.tick(60)
    
    # Clear win timer for next game
    if hasattr(run_airlock_puzzle, 'win_timer'):
        delattr(run_airlock_puzzle, 'win_timer')





# """
# Airlock puzzle for ALIEN: CHRONOS
# Herd the xenomorph to the cargo hold and blow it into space
# """

# import pygame
# import sys
# import math
# from config import (WIDTH, HEIGHT, TERMINAL_GREEN, BRIGHT_GREEN, 
#                    DIM_GREEN, TERMINAL_BLACK, load_fonts)
# from engine import apply_crt_effects, green_flash

# class Room:
#     """Represents a ship room"""
#     def __init__(self, name, shape, x, y, w, h):
#         self.name = name
#         self.shape = shape  # 'angular', 'hex', 'circular', 'octagon', 'rect'
#         self.x = x
#         self.y = y
#         self.w = w
#         self.h = h
#         self.center_x = x + w // 2
#         self.center_y = y + h // 2
        
#     def draw(self, surface, font):
#         """Draw the room based on its shape"""
#         if self.shape == 'angular':
#             self._draw_angular(surface)
#         elif self.shape == 'hex':
#             self._draw_hex(surface)
#         elif self.shape == 'circular':
#             self._draw_circular(surface)
#         elif self.shape == 'octagon':
#             self._draw_octagon(surface)
#         else:
#             self._draw_rect(surface)
        
#         # Draw label
#         text = font.render(self.name, True, TERMINAL_GREEN)
#         text_rect = text.get_rect(center=(self.center_x, self.y + 20))
#         surface.blit(text, text_rect)
    
#     def _draw_angular(self, surface):
#         offset = 10
#         points = [
#             (self.x + offset, self.y),
#             (self.x + self.w - offset, self.y),
#             (self.x + self.w, self.y + offset),
#             (self.x + self.w, self.y + self.h - offset),
#             (self.x + self.w - offset, self.y + self.h),
#             (self.x + offset, self.y + self.h),
#             (self.x, self.y + self.h - offset),
#             (self.x, self.y + offset)
#         ]
#         pygame.draw.polygon(surface, TERMINAL_GREEN, points, 2)
    
#     def _draw_hex(self, surface):
#         points = [
#             (self.x + self.w * 0.25, self.y),
#             (self.x + self.w * 0.75, self.y),
#             (self.x + self.w, self.y + self.h * 0.5),
#             (self.x + self.w * 0.75, self.y + self.h),
#             (self.x + self.w * 0.25, self.y + self.h),
#             (self.x, self.y + self.h * 0.5)
#         ]
#         pygame.draw.polygon(surface, TERMINAL_GREEN, points, 2)
    
#     def _draw_circular(self, surface):
#         pygame.draw.ellipse(surface, TERMINAL_GREEN, 
#                           (self.x, self.y, self.w, self.h), 2)
    
#     def _draw_octagon(self, surface):
#         cx = self.center_x
#         cy = self.center_y
#         radius = min(self.w, self.h) // 2
#         points = []
#         for i in range(8):
#             angle = (i / 8) * math.pi * 2 - math.pi / 8
#             px = cx + math.cos(angle) * radius
#             py = cy + math.sin(angle) * radius
#             points.append((px, py))
#         pygame.draw.polygon(surface, TERMINAL_GREEN, points, 2)
    
#     def _draw_rect(self, surface):
#         pygame.draw.rect(surface, TERMINAL_GREEN, 
#                         (self.x, self.y, self.w, self.h), 3)

# class Corridor:
#     """Represents a corridor connection"""
#     def __init__(self, x1, y1, x2, y2, width=30):
#         self.x1 = x1
#         self.y1 = y1
#         self.x2 = x2
#         self.y2 = y2
#         self.width = width
    
#     def draw(self, surface):
#         """Draw parallel lines for corridor"""
#         # Calculate perpendicular offset
#         dx = self.x2 - self.x1
#         dy = self.y2 - self.y1
#         length = math.sqrt(dx*dx + dy*dy)
#         if length == 0:
#             return
        
#         # Perpendicular vector
#         px = -dy / length * (self.width / 2)
#         py = dx / length * (self.width / 2)
        
#         # Draw two parallel lines
#         pygame.draw.line(surface, TERMINAL_GREEN,
#                         (self.x1 + px, self.y1 + py),
#                         (self.x2 + px, self.y2 + py), 2)
#         pygame.draw.line(surface, TERMINAL_GREEN,
#                         (self.x1 - px, self.y1 - py),
#                         (self.x2 - px, self.y2 - py), 2)

# class Bulkhead:
#     """Represents a sealable bulkhead"""
#     def __init__(self, name, x, y, orientation='v'):
#         self.name = name
#         self.x = x
#         self.y = y
#         self.orientation = orientation  # 'v' or 'h'
#         self.sealed = False
    
#     def draw(self, surface, font_small):
#         color = BRIGHT_GREEN if self.sealed else TERMINAL_GREEN
#         width = 5 if self.sealed else 2
        
#         if self.orientation == 'v':
#             # Vertical bulkhead (blocks horizontal movement)
#             pygame.draw.line(surface, color, (self.x, self.y - 15), (self.x, self.y + 15), width)
#             pygame.draw.line(surface, color, (self.x + 5, self.y - 15), (self.x + 5, self.y + 15), width)
            
#             label = font_small.render(self.name, True, color)
#             surface.blit(label, (self.x + 10, self.y - 5))
#             if self.sealed:
#                 sealed_text = font_small.render('[SEALED]', True, color)
#                 surface.blit(sealed_text, (self.x + 10, self.y + 8))
#         else:
#             # Horizontal bulkhead (blocks vertical movement)
#             pygame.draw.line(surface, color, (self.x - 15, self.y), (self.x + 15, self.y), width)
#             pygame.draw.line(surface, color, (self.x - 15, self.y + 5), (self.x + 15, self.y + 5), width)
            
#             label = font_small.render(self.name, True, color)
#             surface.blit(label, (self.x + 20, self.y))
#             if self.sealed:
#                 sealed_text = font_small.render('[SEALED]', True, color)
#                 surface.blit(sealed_text, (self.x + 20, self.y + 12))

# class Alien:
#     """The xenomorph"""
#     def __init__(self, x, y):
#         self.x = x
#         self.y = y
#         self.target_x = x
#         self.target_y = y
#         self.trail = []
#         self.speed = 2.0
    
#     def update(self):
#         """Move toward target"""
#         dx = self.target_x - self.x
#         dy = self.target_y - self.y
#         dist = math.sqrt(dx*dx + dy*dy)
        
#         if dist > 2:
#             self.x += (dx / dist) * self.speed
#             self.y += (dy / dist) * self.speed
            
#             # Update trail
#             self.trail.append((self.x, self.y))
#             if len(self.trail) > 10:
#                 self.trail.pop(0)
    
#     def set_target(self, x, y):
#         self.target_x = x
#         self.target_y = y
    
#     def draw(self, surface):
#         """Draw alien with pulsing effect"""
#         # Motion trail
#         if len(self.trail) > 1:
#             for i in range(len(self.trail) - 1):
#                 alpha = int((i / len(self.trail)) * 100)
#                 color = (0, alpha, 0)
#                 pygame.draw.line(surface, color, self.trail[i], self.trail[i + 1], 3)
        
#         # Pulsing diamond
#         pulse = math.sin(pygame.time.get_ticks() / 200) * 2 + 8
        
#         points = [
#             (self.x, self.y - pulse),
#             (self.x + pulse, self.y),
#             (self.x, self.y + pulse),
#             (self.x - pulse, self.y)
#         ]
#         pygame.draw.polygon(surface, TERMINAL_GREEN, points)
#         pygame.draw.polygon(surface, BRIGHT_GREEN, points, 2)
        
#         # Blink effect
#         if (pygame.time.get_ticks() // 300) % 2 == 0:
#             pygame.draw.circle(surface, BRIGHT_GREEN, (int(self.x), int(self.y)), 
#                              int(pulse + 6), 1)

# def run_airlock_puzzle(player_name):
#     """Main function to run the airlock puzzle"""
#     pygame.init()
#     screen = pygame.display.set_mode((WIDTH, HEIGHT))
#     pygame.display.set_caption("MUTHER - AIRLOCK PROTOCOL")
    
#     font_large, font_medium, font_small = load_fonts()
#     clock = pygame.time.Clock()
    
#     # Create ship layout
#     rooms = {
#         'bridge': Room('BRIDGE', 'angular', 40, 40, 100, 90),
#         'kitchen': Room('KITCHEN', 'hex', 200, 40, 110, 90),
#         'mother': Room('MOTHER', 'circular', 380, 40, 70, 90),
#         'hypersleep': Room('HYPERSLEEP', 'circular', 560, 40, 90, 90),
#         'crew': Room('CREW', 'angular', 40, 200, 100, 90),
#         'medbay': Room('MED BAY', 'hex', 340, 200, 120, 90),
#         'autodoc': Room('AUTODOC', 'angular', 560, 200, 100, 90),
#         'engineering': Room('ENGINE', 'circular', 290, 420, 100, 100),
#         'reactor': Room('REACTOR', 'octagon', 450, 430, 80, 80),
#         'cargo': Room('CARGO', 'rect', 200, 560, 300, 55)
#     }
    
#     # Create corridors
#     corridors = [
#         # Top row
#         Corridor(140, 85, 200, 85),
#         Corridor(310, 85, 380, 85),
#         Corridor(450, 85, 560, 85),
#         # Vertical from kitchen and mother
#         Corridor(255, 130, 255, 200),
#         Corridor(415, 130, 415, 200),
#         # Crew to center
#         Corridor(140, 245, 340, 245),
#         # Med to autodoc
#         Corridor(460, 245, 560, 245),
#         # Down from kitchen/med to junction
#         Corridor(255, 290, 255, 360),
#         Corridor(415, 290, 415, 360),
#         # Junction merge
#         Corridor(255, 375, 340, 375),
#         Corridor(380, 375, 415, 375),
#         # Down to engineering
#         Corridor(340, 390, 340, 420),
#         # Engineering to reactor
#         Corridor(390, 470, 450, 470),
#         # Engineering to cargo
#         Corridor(340, 520, 340, 560)
#     ]
    
#     # Create bulkheads
#     bulkheads = {
#         'B1': Bulkhead('B1', 505, 85, 'v'),
#         'B2': Bulkhead('B2', 255, 165, 'h'),
#         'B3': Bulkhead('B3', 415, 165, 'h'),
#         'B4': Bulkhead('B4', 510, 245, 'v'),
#         'B5': Bulkhead('B5', 350, 375, 'v'),
#         'B6': Bulkhead('B6', 340, 540, 'h')
#     }
    
#     # Create alien (starts in crew quarters)
#     alien = Alien(90, 245)
    
#     # Game state
#     game_won = False
#     game_over = False
#     cargo_sealed = False
#     airlock_ready = False
#     command_input = ""
#     command_history = []
#     error_message = ""
#     message_timer = 0
    
#     # Main game loop
#     running = True
#     while running:
#         for event in pygame.event.get():
#             if event.type == pygame.QUIT:
#                 running = False
#                 pygame.quit()
#                 sys.exit()
            
#             elif event.type == pygame.KEYDOWN and not game_won and not game_over:
#                 if event.key == pygame.K_RETURN:
#                     # Process command
#                     cmd = command_input.strip().upper()
#                     command_history.append(f"> {cmd}")
                    
#                     # Check if it's a valid bulkhead command
#                     if cmd.startswith('SEAL ') or cmd.startswith('OPEN '):
#                         action, bulkhead_name = cmd.split(' ', 1)
                        
#                         if bulkhead_name in bulkheads:
#                             if action == 'SEAL':
#                                 bulkheads[bulkhead_name].sealed = True
#                                 command_history.append(f"BULKHEAD {bulkhead_name} SEALED")
#                             else:
#                                 bulkheads[bulkhead_name].sealed = False
#                                 command_history.append(f"BULKHEAD {bulkhead_name} OPENED")
                            
#                             error_message = ""
                            
#                             # Check if cargo is sealed
#                             if bulkhead_name == 'B6' and bulkheads['B6'].sealed:
#                                 cargo_sealed = True
#                                 command_history.append("CARGO HOLD ISOLATED")
#                                 airlock_ready = True
#                         else:
#                             error_message = "ERROR: INVALID BULKHEAD DESIGNATION"
#                             message_timer = pygame.time.get_ticks() + 2000
                    
#                     elif cmd == 'OPEN AIRLOCK':
#                         if cargo_sealed and 200 < alien.x < 500 and alien.y > 560:
#                             # Win condition!
#                             game_won = True
#                             command_history.append("AIRLOCK OPENING...")
#                             command_history.append("DECOMPRESSION SEQUENCE INITIATED")
#                         elif not cargo_sealed:
#                             error_message = "ERROR: CARGO HOLD NOT SEALED"
#                             message_timer = pygame.time.get_ticks() + 2000
#                         else:
#                             error_message = "ERROR: TARGET NOT IN CARGO HOLD"
#                             message_timer = pygame.time.get_ticks() + 2000
                    
#                     else:
#                         error_message = "ERROR: INVALID COMMAND"
#                         message_timer = pygame.time.get_ticks() + 2000
                    
#                     command_input = ""
                    
#                     # Keep only last 8 history lines
#                     if len(command_history) > 8:
#                         command_history = command_history[-8:]
                
#                 elif event.key == pygame.K_BACKSPACE:
#                     command_input = command_input[:-1]
#                     error_message = ""
                
#                 elif event.unicode.isprintable():
#                     if len(command_input) < 30:
#                         command_input += event.unicode
#                         error_message = ""
        
#         # Update alien (simple AI: move toward cargo)
#         if not game_won and not game_over:
#             # Simple pathfinding: alien tries to reach cargo
#             alien.set_target(350, 585)
#             alien.update()
            
#             # Check if alien reached bridge
#             if math.sqrt((alien.x - 90)**2 + (alien.y - 85)**2) < 30:
#                 game_over = True
        
#         # Clear error message after timer
#         if message_timer > 0 and pygame.time.get_ticks() > message_timer:
#             error_message = ""
#             message_timer = 0
        
#         # Draw everything
#         screen.fill(TERMINAL_BLACK)
        
#         # Draw corridors
#         for corridor in corridors:
#             corridor.draw(screen)
        
#         # Draw rooms
#         for room in rooms.values():
#             room.draw(screen, font_small)
        
#         # Draw special room features
#         # Player in bridge
#         pygame.draw.circle(screen, BRIGHT_GREEN, (90, 85), 6)
#         if (pygame.time.get_ticks() // 500) % 2 == 0:
#             pygame.draw.circle(screen, BRIGHT_GREEN, (90, 85), 10, 2)
        
#         # Dead crew in crew quarters
#         dead_text = font_small.render('[X] KANE', True, (255, 68, 68))
#         screen.blit(dead_text, (50, 240))
#         dead_text = font_small.render('[X] LAMBERT', True, (255, 68, 68))
#         screen.blit(dead_text, (50, 255))
        
#         # Medical symbol
#         med_symbol = font_medium.render('⚕', True, TERMINAL_GREEN)
#         screen.blit(med_symbol, (390, 240))
        
#         # Engineering hazards
#         hazard = font_medium.render('⚠ ⚠ ⚠', True, BRIGHT_GREEN)
#         screen.blit(hazard, (310, 460))
        
#         # Reactor cores
#         for i in range(3):
#             glow = (pygame.time.get_ticks() // 400) % 2 == 0
#             color = BRIGHT_GREEN if glow else TERMINAL_GREEN
#             pygame.draw.circle(screen, color, (480 + (i - 1) * 20, 470), 6)
        
#         # Cargo crates
#         crate_positions = [(220, 595), (250, 595), (280, 595), (320, 595), 
#                           (360, 595), (400, 595), (450, 595)]
#         for cx, cy in crate_positions:
#             pygame.draw.rect(screen, DIM_GREEN, (cx, cy, 15, 15))
        
#         # Airlock
#         airlock_color = BRIGHT_GREEN if airlock_ready else DIM_GREEN
#         airlock_points = [(500, 575), (540, 575), (550, 587), (540, 600), (500, 600)]
#         pygame.draw.polygon(screen, airlock_color, airlock_points, 3)
#         airlock_label = font_small.render('AIRLOCK', True, airlock_color)
#         screen.blit(airlock_label, (505, 585))
        
#         # Draw bulkheads
#         for bulkhead in bulkheads.values():
#             bulkhead.draw(screen, font_small)
        
#         # Draw alien
#         if not game_won:
#             alien.draw(screen)
        
#         # Draw UI overlay (right side)
#         ui_x = 700
#         ui_y = 50
        
#         # Title
#         title = font_medium.render('MUTHER TERMINAL', True, BRIGHT_GREEN)
#         screen.blit(title, (ui_x, ui_y))
        
#         ui_y += 40
        
#         # Command history
#         for i, line in enumerate(command_history):
#             hist_color = TERMINAL_GREEN if line.startswith('>') else DIM_GREEN
#             hist_text = font_small.render(line, True, hist_color)
#             screen.blit(hist_text, (ui_x, ui_y + i * 20))
        
#         ui_y += len(command_history) * 20 + 30
        
#         # Command prompt
#         prompt = font_small.render('> ' + command_input + '_', True, BRIGHT_GREEN)
#         screen.blit(prompt, (ui_x, ui_y))
        
#         ui_y += 30
        
#         # Error message
#         if error_message:
#             err_text = font_small.render(error_message, True, (255, 100, 100))
#             screen.blit(err_text, (ui_x, ui_y))
        
#         ui_y += 40
        
#         # Available commands
#         help_y = HEIGHT - 150
#         help_lines = [
#             'COMMANDS:',
#             'SEAL B1-B6',
#             'OPEN B1-B6',
#             'OPEN AIRLOCK',
#             '',
#             'OBJECTIVE:',
#             'Herd xenomorph to cargo',
#             'Seal cargo (B6)',
#             'Open airlock'
#         ]
        
#         for i, line in enumerate(help_lines):
#             help_text = font_small.render(line, True, DIM_GREEN)
#             screen.blit(help_text, (ui_x, help_y + i * 18))
        
#         # Win/lose messages
#         if game_won:
#             win_text = font_large.render('AIRLOCK OPENED', True, BRIGHT_GREEN)
#             win_rect = win_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
#             screen.blit(win_text, win_rect)
            
#             # Auto-exit after 3 seconds
#             if not hasattr(run_airlock_puzzle, 'win_timer'):
#                 run_airlock_puzzle.win_timer = pygame.time.get_ticks() + 3000
            
#             if pygame.time.get_ticks() > run_airlock_puzzle.win_timer:
#                 running = False
        
#         if game_over:
#             lose_text = font_large.render('LIFE SIGNS NEGATIVE', True, (255, 68, 68))
#             lose_rect = lose_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
#             screen.blit(lose_text, lose_rect)
        
#         # Apply CRT effects
#         apply_crt_effects(screen)
        
#         pygame.display.flip()
#         clock.tick(60)
    
#     # Clear win timer for next game
#     if hasattr(run_airlock_puzzle, 'win_timer'):
#         delattr(run_airlock_puzzle, 'win_timer')