
"""
Airlock puzzle for ALIEN: CHRONOS 
"""

# Remove junction from bottom so cargo bay is bigger and map is simpler overall
# Alien gets stuck in Corridor when trying to enter bridge?

import pygame
import sys
import math
import random
from config import (WIDTH, HEIGHT, TERMINAL_GREEN, BRIGHT_GREEN, 
                   DIM_GREEN, TERMINAL_BLACK, load_fonts)
from engine import apply_crt_effects

class Room:
    def __init__(self, name, shape, x, y, w, h):
        self.name = name
        self.shape = shape
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.center_x = x + w // 2
        self.center_y = y + h // 2
        
    def draw(self, surface, font):
        if self.shape == 'angular':
            offset = 12
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
        elif self.shape == 'hex':
            points = [
                (self.x + self.w * 0.25, self.y),
                (self.x + self.w * 0.75, self.y),
                (self.x + self.w, self.y + self.h * 0.5),
                (self.x + self.w * 0.75, self.y + self.h),
                (self.x + self.w * 0.25, self.y + self.h),
                (self.x, self.y + self.h * 0.5)
            ]
            pygame.draw.polygon(surface, TERMINAL_GREEN, points, 2)
        elif self.shape == 'circular':
            pygame.draw.ellipse(surface, TERMINAL_GREEN, (self.x, self.y, self.w, self.h), 2)
        elif self.shape == 'octagon':
            cx, cy = self.center_x, self.center_y
            radius = min(self.w, self.h) // 2
            points = [(cx + math.cos((i/8)*math.pi*2 - math.pi/8)*radius,
                       cy + math.sin((i/8)*math.pi*2 - math.pi/8)*radius) for i in range(8)]
            pygame.draw.polygon(surface, TERMINAL_GREEN, points, 2)
        else:
            pygame.draw.rect(surface, TERMINAL_GREEN, (self.x, self.y, self.w, self.h), 3)
        
        # Label slightly higher to avoid corridor overlap
        text = font.render(self.name, True, TERMINAL_GREEN)
        text_rect = text.get_rect(center=(self.center_x, self.y + 15))
        surface.blit(text, text_rect)

class PathNode:
    def __init__(self, x, y, name):
        self.x = x
        self.y = y
        self.name = name
        self.connections = []
    
    def add_connection(self, node, bulkhead=None):
        self.connections.append((node, bulkhead))
        node.connections.append((self, bulkhead))

class Bulkhead:
    def __init__(self, name, x, y, orientation='v'):
        self.name = name
        self.x = x
        self.y = y
        self.orientation = orientation
        self.sealed = False
    
    def draw(self, surface, font_small):
        color = BRIGHT_GREEN if self.sealed else TERMINAL_GREEN
        width = 5 if self.sealed else 2
        
        if self.orientation == 'v':
            pygame.draw.line(surface, color, (self.x, self.y - 18), (self.x, self.y + 18), width)
            pygame.draw.line(surface, color, (self.x + 5, self.y - 18), (self.x + 5, self.y + 18), width)
            label = font_small.render(self.name, True, color)
            surface.blit(label, (self.x + 12, self.y - 6))
            if self.sealed:
                surface.blit(font_small.render('[SEAL]', True, color), (self.x + 12, self.y + 8))
        else:
            pygame.draw.line(surface, color, (self.x - 18, self.y), (self.x + 18, self.y), width)
            pygame.draw.line(surface, color, (self.x - 18, self.y + 5), (self.x + 18, self.y + 5), width)
            label = font_small.render(self.name, True, color)
            surface.blit(label, (self.x + 25, self.y - 2))
            if self.sealed:
                surface.blit(font_small.render('[SEAL]', True, color), (self.x + 25, self.y + 13))

class Alien:
    def __init__(self, start_node):
        self.current_node = start_node
        self.x = start_node.x
        self.y = start_node.y
        self.trail = []
        self.speed = 2.5
        self.wander_timer = 0
        self.wander_interval = random.randint(60, 120)
        self.path = []
        self.pace_offset = 0
        self.pace_direction = 1
        self.hunting = False
        self.bridge_node = None
    
    def find_path(self, target_node, bulkheads):
        if self.current_node == target_node:
            return []
        queue = [(self.current_node, [self.current_node])]
        visited = {self.current_node}
        while queue:
            node, path = queue.pop(0)
            for next_node, bulkhead_name in node.connections:
                if bulkhead_name and bulkhead_name in bulkheads and bulkheads[bulkhead_name].sealed:
                    continue
                if next_node == target_node:
                    return path + [next_node]
                if next_node not in visited:
                    visited.add(next_node)
                    queue.append((next_node, path + [next_node]))
        return []
    
    def update(self, all_nodes, bulkheads, player_pos):
        dist_to_player = math.hypot(self.x - player_pos[0], self.y - player_pos[1])
        
        if dist_to_player < 150:
            if not self.hunting:
                self.hunting = True
                self.path = []
            if self.bridge_node and self.current_node != self.bridge_node:
                new_path = self.find_path(self.bridge_node, bulkheads)
                if new_path and new_path != self.path:
                    self.path = new_path
        else:
            self.hunting = False
            self.wander_timer += 1
            if self.wander_timer >= self.wander_interval and not self.path:
                self.path = self.find_path(random.choice(all_nodes), bulkheads)
                self.wander_timer = 0
                self.wander_interval = random.randint(60, 120)
        
        if self.path:
            next_node = self.path[0]
            dx = next_node.x - self.x
            dy = next_node.y - self.y
            dist = math.hypot(dx, dy)
            if dist < 5:
                self.current_node = next_node
                self.x = next_node.x
                self.y = next_node.y
                self.path.pop(0)
            else:
                speed = self.speed * 1.5 if self.hunting else self.speed
                self.x += (dx / dist) * speed
                self.y += (dy / dist) * speed
        else:
            self.pace_offset += self.pace_direction * 0.5
            if abs(self.pace_offset) > 20:
                self.pace_direction *= -1
            self.x = self.current_node.x + self.pace_offset
        
        self.trail.append((self.x, self.y))
        if len(self.trail) > 20:
            self.trail.pop(0)
    
    def draw(self, surface):
        if len(self.trail) > 1:
            for i in range(len(self.trail) - 1):
                alpha = int((i / len(self.trail)) * 150)
                pygame.draw.line(surface, (0, alpha, 0), self.trail[i], self.trail[i+1], 3)
        
        pulse = math.sin(pygame.time.get_ticks() / 200) * 2 + 9
        if self.hunting:
            pulse += 3
        
        points = [(self.x, self.y - pulse), (self.x + pulse, self.y),
                  (self.x, self.y + pulse), (self.x - pulse, self.y)]
        color = BRIGHT_GREEN if self.hunting else TERMINAL_GREEN
        pygame.draw.polygon(surface, color, points)
        pygame.draw.polygon(surface, BRIGHT_GREEN, points, 2)
        
        if (pygame.time.get_ticks() // 300) % 2 == 0:
            pygame.draw.circle(surface, BRIGHT_GREEN, (int(self.x), int(self.y)), int(pulse + 6), 1)

def draw_corridor(surface, x1, y1, x2, y2, width=35):
    dx = x2 - x1
    dy = y2 - y1
    length = math.hypot(dx, dy)
    if length == 0:
        return
    px = -dy / length * (width / 2)
    py = dx / length * (width / 2)
    pygame.draw.line(surface, TERMINAL_GREEN, (x1 + px, y1 + py), (x2 + px, y2 + py), 2)
    pygame.draw.line(surface, TERMINAL_GREEN, (x1 - px, y1 - py), (x2 - px, y2 - py), 2)

def run_airlock_puzzle(player_name):
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("MUTHER - AIRLOCK PROTOCOL")
    
    font_large, font_medium, font_small = load_fonts()
    clock = pygame.time.Clock()
    
    rooms = {
        'bridge': Room('BRIDGE', 'angular', 30, 30, 120, 90),
        'airlock_entry': Room('CORRIDOR', 'rect', 200, 45, 100, 60),
        'kitchen': Room('GALLEY', 'hex', 350, 30, 120, 90),
        'mother': Room('MOTHER', 'circular', 520, 30, 100, 90),
        'hypersleep': Room('HYPERSLEEP', 'circular', 670, 30, 110, 90),
        'crew': Room('CREW', 'angular', 30, 180, 120, 90),
        'storage': Room('STORAGE', 'rect', 200, 180, 100, 90),
        'medbay': Room('MEDBAY', 'hex', 470, 180, 130, 90),
        'autodoc': Room('AUTODOC', 'angular', 650, 180, 130, 90),
        'junction_low': Room('JUNCTION', 'rect', 350, 330, 120, 60),
        'engineering': Room('ENGINE', 'circular', 200, 450, 140, 110),
        'reactor': Room('REACTOR', 'octagon', 500, 460, 100, 100),
        'cargo': Room('CARGO BAY', 'rect', 150, 580, 350, 40)
    }
    
    nodes = {
        'bridge': PathNode(90, 75, 'bridge'),
        'airlock_entry': PathNode(250, 75, 'airlock_entry'),
        'kitchen': PathNode(410, 75, 'kitchen'),
        'mother': PathNode(570, 75, 'mother'),
        'hypersleep': PathNode(725, 75, 'hypersleep'),
        'crew': PathNode(90, 225, 'crew'),
        'storage': PathNode(250, 225, 'storage'),
        'medbay': PathNode(535, 225, 'medbay'),
        'autodoc': PathNode(715, 225, 'autodoc'),
        'junction_low': PathNode(410, 360, 'junction_low'),
        'engineering': PathNode(270, 505, 'engineering'),
        'reactor': PathNode(550, 510, 'reactor'),
        'cargo': PathNode(325, 600, 'cargo'),
    }
    
    bulkheads = {
        'B0': Bulkhead('B0', 165, 75, 'v'),
        'B1': Bulkhead('B1', 315, 75, 'v'),
        'B2': Bulkhead('B2', 465, 75, 'v'),
        'B3': Bulkhead('B3', 635, 75, 'v'),
        'B4': Bulkhead('B4', 250, 155, 'h'),
        'B5': Bulkhead('B5', 535, 155, 'h'),
        'B6': Bulkhead('B6', 615, 225, 'v'),
        'B7': Bulkhead('B7', 410, 290, 'h'),
        'B8': Bulkhead('B8', 410, 395, 'h'),
        'B9': Bulkhead('B9', 270, 565, 'h'),
    }
    
    # Graph
    nodes['bridge'].add_connection(nodes['airlock_entry'], 'B0')
    nodes['airlock_entry'].add_connection(nodes['kitchen'], 'B1')
    nodes['kitchen'].add_connection(nodes['mother'], 'B2')
    nodes['mother'].add_connection(nodes['hypersleep'], 'B3')
    nodes['airlock_entry'].add_connection(nodes['storage'], 'B4')
    nodes['mother'].add_connection(nodes['medbay'], 'B5')
    nodes['medbay'].add_connection(nodes['autodoc'], 'B6')
    nodes['crew'].add_connection(nodes['storage'])
    nodes['storage'].add_connection(nodes['medbay'])
    nodes['kitchen'].add_connection(nodes['junction_low'], 'B7')
    nodes['medbay'].add_connection(nodes['junction_low'])
    nodes['junction_low'].add_connection(nodes['engineering'], 'B8')
    nodes['junction_low'].add_connection(nodes['reactor'])
    nodes['engineering'].add_connection(nodes['cargo'], 'B9')
    
    alien = Alien(nodes['crew'])
    alien.bridge_node = nodes['bridge']
    
    # Game state
    game_won = game_over = cargo_sealed = False
    command_input = ""
    command_history = []
    error_message = ""
    message_timer = 0
    win_timer = 0
    player_pos = (90, 75)
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN and not game_won and not game_over:
                if event.key == pygame.K_RETURN:
                    cmd = command_input.strip().upper()
                    command_history.append(f"> {cmd}")
                    
                    if cmd.startswith('SEAL '):
                        bh = cmd[5:]
                        if bh in bulkheads:
                            bulkheads[bh].sealed = True
                            command_history.append(f"BULKHEAD {bh} SEALED")
                            if bh == 'B9':
                                cargo_sealed = True
                                command_history.append("CARGO BAY ISOLATED")
                        else:
                            error_message = "DOES NOT COMPUTE"
                            message_timer = pygame.time.get_ticks() + 2000
                    elif cmd.startswith('OPEN '):
                        target = cmd[5:]
                        if target == 'AIRLOCK':
                            if not cargo_sealed:
                                error_message = "CARGO BAY NOT SEALED"
                            elif alien.current_node.name != 'cargo':
                                error_message = "TARGET NOT IN CARGO BAY"
                            else:
                                game_won = True
                                win_timer = pygame.time.get_ticks() + 3000
                                command_history.append("AIRLOCK OPENING...")
                                command_history.append("DECOMPRESSION INITIATED")
                            message_timer = pygame.time.get_ticks() + 2000
                        elif target in bulkheads:
                            bulkheads[target].sealed = False
                            command_history.append(f"BULKHEAD {target} OPENED")
                            if target == 'B9':
                                cargo_sealed = False
                        else:
                            error_message = "DOES NOT COMPUTE"
                            message_timer = pygame.time.get_ticks() + 2000
                    else:
                        error_message = "DOES NOT COMPUTE"
                        message_timer = pygame.time.get_ticks() + 2000
                    
                    command_input = ""
                    command_history = command_history[-8:]
                elif event.key == pygame.K_BACKSPACE:
                    command_input = command_input[:-1]
                elif event.unicode.isprintable() and len(command_input) < 30:
                    command_input += event.unicode
        
        if not game_won and not game_over:
            alien.update(list(nodes.values()), bulkheads, player_pos)
            if alien.current_node.name == 'bridge':
                game_over = True
        
        if game_won and pygame.time.get_ticks() > win_timer:
            running = False
        
        if message_timer and pygame.time.get_ticks() > message_timer:
            error_message = ""
            message_timer = 0
        
        screen.fill(TERMINAL_BLACK)
        
        # FIXED CORRIDORS – clean connections, no floating segments
        draw_corridor(screen, nodes['bridge'].x, nodes['bridge'].y, nodes['airlock_entry'].x, nodes['airlock_entry'].y)
        draw_corridor(screen, nodes['airlock_entry'].x, nodes['airlock_entry'].y, nodes['kitchen'].x, nodes['kitchen'].y)
        draw_corridor(screen, nodes['kitchen'].x, nodes['kitchen'].y, nodes['mother'].x, nodes['mother'].y)
        draw_corridor(screen, nodes['mother'].x, nodes['mother'].y, nodes['hypersleep'].x, nodes['hypersleep'].y)
        
        draw_corridor(screen, nodes['airlock_entry'].x, nodes['airlock_entry'].y + 30, nodes['storage'].x, nodes['storage'].y)
        draw_corridor(screen, nodes['mother'].x, nodes['mother'].y + 30, nodes['medbay'].x, nodes['medbay'].y - 30)
        
        draw_corridor(screen, nodes['crew'].x, nodes['crew'].y, nodes['storage'].x, nodes['storage'].y)
        draw_corridor(screen, nodes['storage'].x, nodes['storage'].y, nodes['medbay'].x, nodes['medbay'].y)
        draw_corridor(screen, nodes['medbay'].x, nodes['medbay'].y, nodes['autodoc'].x, nodes['autodoc'].y)
        
        draw_corridor(screen, nodes['kitchen'].x, nodes['kitchen'].y + 45, nodes['junction_low'].x, nodes['junction_low'].y - 30)
        draw_corridor(screen, nodes['medbay'].x, nodes['medbay'].y + 30, nodes['junction_low'].x + 50, nodes['junction_low'].y)
        
        draw_corridor(screen, nodes['junction_low'].x, nodes['junction_low'].y + 30, nodes['engineering'].x, nodes['engineering'].y - 30)
        draw_corridor(screen, nodes['junction_low'].x + 50, nodes['junction_low'].y + 20, nodes['reactor'].x, nodes['reactor'].y)
        
        draw_corridor(screen, nodes['engineering'].x, nodes['engineering'].y + 40, nodes['cargo'].x, nodes['cargo'].y)
        
        # Draw rooms
        for room in rooms.values():
            room.draw(screen, font_small)
        
        # Player
        pygame.draw.circle(screen, BRIGHT_GREEN, player_pos, 7)
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            pygame.draw.circle(screen, BRIGHT_GREEN, player_pos, 12, 2)
        
        # Details
        screen.blit(font_medium.render('⚕', True, TERMINAL_GREEN), (525, 220))
        screen.blit(font_medium.render('⚠ ⚠ ⚠', True, BRIGHT_GREEN), (230, 500))
        for i in range(3):
            color = BRIGHT_GREEN if (pygame.time.get_ticks() // 400) % 2 else TERMINAL_GREEN
            pygame.draw.circle(screen, color, (535 + i * 20, 510), 7)
        for i in range(12):
            pygame.draw.rect(screen, DIM_GREEN, (170 + i * 28, 595, 15, 15))
        
        airlock_color = BRIGHT_GREEN if cargo_sealed else DIM_GREEN
        airlock_points = [(505, 590), (545, 590), (552, 600), (545, 610), (505, 610)]
        pygame.draw.polygon(screen, airlock_color, airlock_points, 3)
        screen.blit(font_small.render('AIRLOCK', True, airlock_color), (508, 597))
        
        # Bulkheads & alien
        for bh in bulkheads.values():
            bh.draw(screen, font_small)
        if not game_won:
            alien.draw(screen)
        
        # Terminal UI
        ui_x, ui_y = 820, 60
        screen.blit(font_medium.render('MUTHER TERMINAL', True, BRIGHT_GREEN), (ui_x, ui_y))
        ui_y += 45
        for i, line in enumerate(command_history):
            color = TERMINAL_GREEN if line.startswith('>') else DIM_GREEN
            screen.blit(font_small.render(line, True, color), (ui_x, ui_y + i * 20))
        ui_y += len(command_history) * 20 + 35
        screen.blit(font_small.render('> ' + command_input + '_', True, BRIGHT_GREEN), (ui_x, ui_y))
        if error_message:
            ui_y += 35
            screen.blit(font_small.render(error_message, True, (255, 100, 100)), (ui_x, ui_y))
        
        # Help
        help_lines = ['COMMANDS:', 'SEAL B0-B9', 'OPEN B0-B9', 'OPEN AIRLOCK', '',
                      'Seal B0 to protect bridge', 'Herd alien to cargo bay', 'Seal B9, open airlock']
        for i, line in enumerate(help_lines):
            screen.blit(font_small.render(line, True, DIM_GREEN), (ui_x, HEIGHT - 180 + i * 20))
        
        # Win/lose overlay
        if game_won:
            text = font_large.render('AIRLOCK OPENED', True, BRIGHT_GREEN)
            screen.blit(text, text.get_rect(center=(WIDTH//2, HEIGHT//2)))
        if game_over:
            text = font_large.render('LIFE SIGNS NEGATIVE', True, (255, 68, 68))
            screen.blit(text, text.get_rect(center=(WIDTH//2, HEIGHT//2)))
        
        apply_crt_effects(screen)
        pygame.display.flip()
        clock.tick(60)




"""
Claude V5 -- also has corridor problem and lower half is a mess
"""
# import pygame
# import sys
# import math
# import random
# from config import (WIDTH, HEIGHT, TERMINAL_GREEN, BRIGHT_GREEN, 
#                    DIM_GREEN, TERMINAL_BLACK, load_fonts)
# from engine import apply_crt_effects, green_flash

# class Room:
#     """Represents a ship room"""
#     def __init__(self, name, shape, x, y, w, h):
#         self.name = name
#         self.shape = shape
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
#         offset = 12
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

# class PathNode:
#     """Navigation node for alien pathfinding"""
#     def __init__(self, x, y, name):
#         self.x = x
#         self.y = y
#         self.name = name
#         self.connections = []
    
#     def add_connection(self, node, bulkhead=None):
#         """Add bidirectional connection with bulkhead"""
#         self.connections.append((node, bulkhead))
#         node.connections.append((self, bulkhead))

# class Bulkhead:
#     """Represents a sealable bulkhead"""
#     def __init__(self, name, x, y, orientation='v'):
#         self.name = name
#         self.x = x
#         self.y = y
#         self.orientation = orientation
#         self.sealed = False
    
#     def draw(self, surface, font_small):
#         color = BRIGHT_GREEN if self.sealed else TERMINAL_GREEN
#         width = 5 if self.sealed else 2
        
#         if self.orientation == 'v':
#             pygame.draw.line(surface, color, (self.x, self.y - 18), (self.x, self.y + 18), width)
#             pygame.draw.line(surface, color, (self.x + 5, self.y - 18), (self.x + 5, self.y + 18), width)
            
#             label = font_small.render(self.name, True, color)
#             surface.blit(label, (self.x + 12, self.y - 6))
#             if self.sealed:
#                 sealed_text = font_small.render('[SEAL]', True, color)
#                 surface.blit(sealed_text, (self.x + 12, self.y + 8))
#         else:
#             pygame.draw.line(surface, color, (self.x - 18, self.y), (self.x + 18, self.y), width)
#             pygame.draw.line(surface, color, (self.x - 18, self.y + 5), (self.x + 18, self.y + 5), width)
            
#             label = font_small.render(self.name, True, color)
#             surface.blit(label, (self.x + 25, self.y - 2))
#             if self.sealed:
#                 sealed_text = font_small.render('[SEAL]', True, color)
#                 surface.blit(sealed_text, (self.x + 25, self.y + 13))

# class Alien:
#     """The xenomorph with pathfinding"""
#     def __init__(self, start_node):
#         self.current_node = start_node
#         self.target_node = start_node
#         self.x = start_node.x
#         self.y = start_node.y
#         self.trail = []
#         self.speed = 2.5
#         self.wander_timer = 0
#         self.wander_interval = random.randint(60, 120)
#         self.path = []
#         self.pace_offset = 0
#         self.pace_direction = 1
#         self.hunting = False
#         self.bridge_node = None
    
#     def find_path(self, target_node, bulkheads):
#         """BFS pathfinding that STRICTLY respects sealed bulkheads"""
#         if self.current_node == target_node:
#             return []
        
#         queue = [(self.current_node, [self.current_node])]
#         visited = {self.current_node}
        
#         while queue:
#             node, path = queue.pop(0)
            
#             for next_node, bulkhead_name in node.connections:
#                 # CRITICAL: If there's a bulkhead and it's sealed, CANNOT pass
#                 if bulkhead_name is not None:
#                     if bulkhead_name in bulkheads and bulkheads[bulkhead_name].sealed:
#                         continue  # This path is blocked
                
#                 if next_node == target_node:
#                     return path + [next_node]
                
#                 if next_node not in visited:
#                     visited.add(next_node)
#                     queue.append((next_node, path + [next_node]))
        
#         return []  # No path found - alien is trapped
    
#     def update(self, all_nodes, bulkheads, player_pos):
#         """Update alien movement with hunting behavior"""
#         # Check if alien can sense player (within 150 units)
#         dist_to_player = math.sqrt((self.x - player_pos[0])**2 + (self.y - player_pos[1])**2)
        
#         if dist_to_player < 150:
#             # HUNTING MODE - make beeline for player (bridge)
#             if not self.hunting:
#                 self.hunting = True
#                 self.path = []  # Clear current path
            
#             # Try to path to bridge
#             if self.bridge_node and self.current_node != self.bridge_node:
#                 new_path = self.find_path(self.bridge_node, bulkheads)
#                 if new_path and new_path != self.path:
#                     self.path = new_path
#                     self.target_node = self.bridge_node
#         else:
#             self.hunting = False
            
#             # EXPLORATION MODE
#             self.wander_timer += 1
#             if self.wander_timer >= self.wander_interval and not self.path:
#                 self.target_node = random.choice(all_nodes)
#                 self.path = self.find_path(self.target_node, bulkheads)
#                 self.wander_timer = 0
#                 self.wander_interval = random.randint(60, 120)
        
#         # Move along path
#         if self.path:
#             next_node = self.path[0]
#             dx = next_node.x - self.x
#             dy = next_node.y - self.y
#             dist = math.sqrt(dx*dx + dy*dy)
            
#             if dist < 5:
#                 self.current_node = next_node
#                 self.x = next_node.x
#                 self.y = next_node.y
#                 self.path.pop(0)
#             else:
#                 move_speed = self.speed * 1.5 if self.hunting else self.speed
#                 self.x += (dx / dist) * move_speed
#                 self.y += (dy / dist) * move_speed
#         else:
#             # Pace when stuck
#             self.pace_offset += self.pace_direction * 0.5
#             if abs(self.pace_offset) > 20:
#                 self.pace_direction *= -1
#             self.x = self.current_node.x + self.pace_offset
        
#         # Update trail
#         self.trail.append((self.x, self.y))
#         if len(self.trail) > 20:
#             self.trail.pop(0)
    
#     def draw(self, surface):
#         """Draw alien with pulsing effect"""
#         if len(self.trail) > 1:
#             for i in range(len(self.trail) - 1):
#                 alpha = int((i / len(self.trail)) * 150)
#                 color = (0, alpha, 0)
#                 pygame.draw.line(surface, color, self.trail[i], self.trail[i + 1], 3)
        
#         pulse = math.sin(pygame.time.get_ticks() / 200) * 2 + 9
        
#         # Hunting indicator - larger and brighter
#         if self.hunting:
#             pulse += 3
        
#         points = [
#             (self.x, self.y - pulse),
#             (self.x + pulse, self.y),
#             (self.x, self.y + pulse),
#             (self.x - pulse, self.y)
#         ]
        
#         color = BRIGHT_GREEN if self.hunting else TERMINAL_GREEN
#         pygame.draw.polygon(surface, color, points)
#         pygame.draw.polygon(surface, BRIGHT_GREEN, points, 2)
        
#         if (pygame.time.get_ticks() // 300) % 2 == 0:
#             pygame.draw.circle(surface, BRIGHT_GREEN, (int(self.x), int(self.y)), 
#                              int(pulse + 6), 1)

# def draw_corridor(surface, x1, y1, x2, y2, width=35):
#     """Draw a corridor with parallel lines"""
#     dx = x2 - x1
#     dy = y2 - y1
#     length = math.sqrt(dx*dx + dy*dy)
#     if length == 0:
#         return
    
#     px = -dy / length * (width / 2)
#     py = dx / length * (width / 2)
    
#     pygame.draw.line(surface, TERMINAL_GREEN, (x1 + px, y1 + py), (x2 + px, y2 + py), 2)
#     pygame.draw.line(surface, TERMINAL_GREEN, (x1 - px, y1 - py), (x2 - px, y2 - py), 2)

# def run_airlock_puzzle(player_name):
#     """Main function to run the airlock puzzle"""
#     pygame.init()
#     screen = pygame.display.set_mode((WIDTH, HEIGHT))
#     pygame.display.set_caption("MUTHER - AIRLOCK PROTOCOL")
    
#     font_large, font_medium, font_small = load_fonts()
#     clock = pygame.time.Clock()
    
#     # Much wider, bigger ship layout
#     rooms = {
#         'bridge': Room('BRIDGE', 'angular', 30, 30, 120, 90),
#         'airlock_entry': Room('CORRIDOR', 'rect', 200, 45, 100, 60),
#         'kitchen': Room('GALLEY', 'hex', 350, 30, 120, 90),
#         'mother': Room('MOTHER', 'circular', 520, 30, 100, 90),
#         'hypersleep': Room('HYPERSLEEP', 'circular', 670, 30, 110, 90),
        
#         'crew': Room('CREW', 'angular', 30, 180, 120, 90),
#         'storage': Room('STORAGE', 'rect', 200, 180, 100, 90),
#         'medbay': Room('MEDBAY', 'hex', 470, 180, 130, 90),
#         'autodoc': Room('AUTODOC', 'angular', 650, 180, 130, 90),
        
#         'junction_low': Room('JUNCTION', 'rect', 350, 330, 120, 60),
        
#         'engineering': Room('ENGINE', 'circular', 200, 450, 140, 110),
#         'reactor': Room('REACTOR', 'octagon', 500, 460, 100, 100),
        
#         'cargo': Room('CARGO BAY', 'rect', 150, 580, 350, 40)
#     }
    
#     # Navigation nodes with more detailed pathfinding
#     nodes = {
#         'bridge': PathNode(90, 75, 'bridge'),
#         'airlock_entry': PathNode(250, 75, 'airlock_entry'),
#         'kitchen': PathNode(410, 75, 'kitchen'),
#         'mother': PathNode(570, 75, 'mother'),
#         'hypersleep': PathNode(725, 75, 'hypersleep'),
        
#         'crew': PathNode(90, 225, 'crew'),
#         'storage': PathNode(250, 225, 'storage'),
#         'medbay': PathNode(535, 225, 'medbay'),
#         'autodoc': PathNode(715, 225, 'autodoc'),
        
#         'junction_low': PathNode(410, 360, 'junction_low'),
        
#         'engineering': PathNode(270, 505, 'engineering'),
#         'reactor': PathNode(550, 510, 'reactor'),
        
#         'cargo': PathNode(325, 600, 'cargo'),
#     }
    
#     # Bulkheads - more of them for better control
#     bulkheads = {
#         'B0': Bulkhead('B0', 165, 75, 'v'),     # Bridge entrance - NEW!
#         'B1': Bulkhead('B1', 315, 75, 'v'),     # After airlock entry
#         'B2': Bulkhead('B2', 465, 75, 'v'),     # Kitchen to mother
#         'B3': Bulkhead('B3', 635, 75, 'v'),     # Mother to hypersleep
#         'B4': Bulkhead('B4', 250, 155, 'h'),    # Airlock entry down to storage
#         'B5': Bulkhead('B5', 535, 155, 'h'),    # Mother down to medbay
#         'B6': Bulkhead('B6', 615, 225, 'v'),    # Medbay to autodoc
#         'B7': Bulkhead('B7', 410, 290, 'h'),    # Kitchen down to junction
#         'B8': Bulkhead('B8', 410, 395, 'h'),    # Junction down
#         'B9': Bulkhead('B9', 270, 565, 'h'),    # Engineering to cargo
#     }
    
#     # Build navigation graph - CRITICAL: Pass bulkhead names correctly
#     nodes['bridge'].add_connection(nodes['airlock_entry'], 'B0')
#     nodes['airlock_entry'].add_connection(nodes['kitchen'], 'B1')
#     nodes['kitchen'].add_connection(nodes['mother'], 'B2')
#     nodes['mother'].add_connection(nodes['hypersleep'], 'B3')
    
#     nodes['airlock_entry'].add_connection(nodes['storage'], 'B4')
#     nodes['mother'].add_connection(nodes['medbay'], 'B5')
#     nodes['medbay'].add_connection(nodes['autodoc'], 'B6')
    
#     nodes['crew'].add_connection(nodes['storage'])
#     nodes['storage'].add_connection(nodes['medbay'])
    
#     nodes['kitchen'].add_connection(nodes['junction_low'], 'B7')
#     nodes['medbay'].add_connection(nodes['junction_low'])
    
#     nodes['junction_low'].add_connection(nodes['engineering'], 'B8')
#     nodes['junction_low'].add_connection(nodes['reactor'])
    
#     nodes['engineering'].add_connection(nodes['cargo'], 'B9')
    
#     # Create alien starting in crew quarters
#     alien = Alien(nodes['crew'])
#     alien.bridge_node = nodes['bridge']  # Set bridge as hunting target
    
#     # Game state
#     game_won = False
#     game_over = False
#     cargo_sealed = False
#     command_input = ""
#     command_history = []
#     error_message = ""
#     message_timer = 0
#     win_timer = 0
    
#     player_pos = (90, 75)  # Bridge position
    
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
#                     cmd = command_input.strip().upper()
#                     command_history.append(f"> {cmd}")
                    
#                     if cmd.startswith('SEAL '):
#                         parts = cmd.split(' ')
#                         if len(parts) == 2:
#                             bulkhead_name = parts[1]
#                             if bulkhead_name in bulkheads:
#                                 bulkheads[bulkhead_name].sealed = True
#                                 command_history.append(f"BULKHEAD {bulkhead_name} SEALED")
                                
#                                 if bulkhead_name == 'B9':
#                                     cargo_sealed = True
#                                     command_history.append("CARGO BAY ISOLATED")
                                
#                                 error_message = ""
#                             else:
#                                 error_message = "DOES NOT COMPUTE"
#                                 message_timer = pygame.time.get_ticks() + 2000
#                         else:
#                             error_message = "DOES NOT COMPUTE"
#                             message_timer = pygame.time.get_ticks() + 2000
                    
#                     elif cmd.startswith('OPEN '):
#                         parts = cmd.split(' ')
#                         if len(parts) == 2:
#                             target = parts[1]
                            
#                             if target == 'AIRLOCK':
#                                 if not cargo_sealed:
#                                     error_message = "CARGO BAY NOT SEALED"
#                                     message_timer = pygame.time.get_ticks() + 2000
#                                 elif alien.current_node.name != 'cargo':
#                                     error_message = "TARGET NOT IN CARGO BAY"
#                                     message_timer = pygame.time.get_ticks() + 2000
#                                 else:
#                                     game_won = True
#                                     win_timer = pygame.time.get_ticks() + 3000
#                                     command_history.append("AIRLOCK OPENING...")
#                                     command_history.append("DECOMPRESSION INITIATED")
#                             elif target in bulkheads:
#                                 bulkheads[target].sealed = False
#                                 command_history.append(f"BULKHEAD {target} OPENED")
                                
#                                 if target == 'B9':
#                                     cargo_sealed = False
                                
#                                 error_message = ""
#                             else:
#                                 error_message = "DOES NOT COMPUTE"
#                                 message_timer = pygame.time.get_ticks() + 2000
#                         else:
#                             error_message = "DOES NOT COMPUTE"
#                             message_timer = pygame.time.get_ticks() + 2000
#                     else:
#                         error_message = "DOES NOT COMPUTE"
#                         message_timer = pygame.time.get_ticks() + 2000
                    
#                     command_input = ""
                    
#                     if len(command_history) > 8:
#                         command_history = command_history[-8:]
                
#                 elif event.key == pygame.K_BACKSPACE:
#                     command_input = command_input[:-1]
#                     error_message = ""
                
#                 elif event.unicode.isprintable():
#                     if len(command_input) < 30:
#                         command_input += event.unicode
#                         error_message = ""
        
#         # Update alien
#         if not game_won and not game_over:
#             alien.update(list(nodes.values()), bulkheads, player_pos)
            
#             if alien.current_node.name == 'bridge':
#                 game_over = True
        
#         if game_won and pygame.time.get_ticks() > win_timer:
#             running = False
        
#         if message_timer > 0 and pygame.time.get_ticks() > message_timer:
#             error_message = ""
#             message_timer = 0
        
#         # DRAW
#         screen.fill(TERMINAL_BLACK)
        
#         # Draw all corridors
#         draw_corridor(screen, 150, 75, 200, 75)
#         draw_corridor(screen, 300, 75, 350, 75)
#         draw_corridor(screen, 470, 75, 520, 75)
#         draw_corridor(screen, 620, 75, 670, 75)
        
#         draw_corridor(screen, 250, 105, 250, 180)
#         draw_corridor(screen, 570, 120, 570, 180)
        
#         draw_corridor(screen, 150, 225, 200, 225)
#         draw_corridor(screen, 300, 225, 470, 225)
#         draw_corridor(screen, 600, 225, 650, 225)
        
#         draw_corridor(screen, 410, 120, 410, 330)
#         draw_corridor(screen, 535, 270, 535, 330)
#         draw_corridor(screen, 410, 330, 500, 330)
        
#         draw_corridor(screen, 410, 390, 410, 450)
#         draw_corridor(screen, 470, 360, 500, 460)
        
#         draw_corridor(screen, 270, 560, 270, 580)
        
#         # Draw rooms
#         for room in rooms.values():
#             room.draw(screen, font_small)
        
#         # Player in bridge
#         pygame.draw.circle(screen, BRIGHT_GREEN, player_pos, 7)
#         if (pygame.time.get_ticks() // 500) % 2 == 0:
#             pygame.draw.circle(screen, BRIGHT_GREEN, player_pos, 12, 2)
        
#         # Med symbol
#         med_symbol = font_medium.render('⚕', True, TERMINAL_GREEN)
#         screen.blit(med_symbol, (525, 220))
        
#         # Engineering hazards
#         hazard = font_medium.render('⚠ ⚠ ⚠', True, BRIGHT_GREEN)
#         screen.blit(hazard, (230, 500))
        
#         # Reactor cores
#         for i in range(3):
#             glow = (pygame.time.get_ticks() // 400) % 2 == 0
#             color = BRIGHT_GREEN if glow else TERMINAL_GREEN
#             pygame.draw.circle(screen, color, (535 + i * 20, 510), 7)
        
#         # Cargo crates
#         for i in range(12):
#             pygame.draw.rect(screen, DIM_GREEN, (170 + i * 28, 595, 15, 15))
        
#         # Airlock
#         airlock_color = BRIGHT_GREEN if cargo_sealed else DIM_GREEN
#         airlock_points = [(505, 590), (545, 590), (552, 600), (545, 610), (505, 610)]
#         pygame.draw.polygon(screen, airlock_color, airlock_points, 3)
#         airlock_label = font_small.render('AIRLOCK', True, airlock_color)
#         screen.blit(airlock_label, (508, 597))
        
#         # Draw bulkheads
#         for bulkhead in bulkheads.values():
#             bulkhead.draw(screen, font_small)
        
#         # Draw alien
#         if not game_won:
#             alien.draw(screen)
        
#         # UI
#         ui_x = 820
#         ui_y = 60
        
#         title = font_medium.render('MUTHER TERMINAL', True, BRIGHT_GREEN)
#         screen.blit(title, (ui_x, ui_y))
#         ui_y += 45
        
#         for i, line in enumerate(command_history):
#             hist_color = TERMINAL_GREEN if line.startswith('>') else DIM_GREEN
#             hist_text = font_small.render(line, True, hist_color)
#             screen.blit(hist_text, (ui_x, ui_y + i * 20))
        
#         ui_y += len(command_history) * 20 + 35
        
#         prompt = font_small.render('> ' + command_input + '_', True, BRIGHT_GREEN)
#         screen.blit(prompt, (ui_x, ui_y))
#         ui_y += 35
        
#         if error_message:
#             err_text = font_small.render(error_message, True, (255, 100, 100))
#             screen.blit(err_text, (ui_x, ui_y))
        
#         help_y = HEIGHT - 180
#         help_lines = [
#             'COMMANDS:',
#             'SEAL B0-B9',
#             'OPEN B0-B9',
#             'OPEN AIRLOCK',
#             '',
#             'Seal B0 to protect bridge',
#             'Herd alien to cargo bay',
#             'Seal B9, open airlock'
#         ]
        
#         for i, line in enumerate(help_lines):
#             help_text = font_small.render(line, True, DIM_GREEN)
#             screen.blit(help_text, (ui_x, help_y + i * 20))
        
#         # Win/lose
#         if game_won:
#             win_text = font_large.render('AIRLOCK OPENED', True, BRIGHT_GREEN)
#             win_rect = win_text.get_rect(center=(400, 300))
#             screen.blit(win_text, win_rect)
        
#         if game_over:
#             lose_text = font_large.render('LIFE SIGNS NEGATIVE', True, (255, 68, 68))
#             lose_rect = lose_text.get_rect(center=(400, 300))
#             screen.blit(lose_text, lose_rect)
        
#         apply_crt_effects(screen)
#         pygame.display.flip()
#         clock.tick(60)



"""
Grok attempted improvements, still getting stuck in corridor and graphically meh
"""

# import pygame
# import sys
# import math
# import random
# from config import (WIDTH, HEIGHT, TERMINAL_GREEN, BRIGHT_GREEN, 
#                    DIM_GREEN, TERMINAL_BLACK, load_fonts)
# from engine import apply_crt_effects

# class Room:
#     def __init__(self, name, shape, x, y, w, h):
#         self.name = name
#         self.shape = shape
#         self.x = x
#         self.y = y
#         self.w = w
#         self.h = h
#         self.center_x = x + w // 2
#         self.center_y = y + h // 2
        
#     def draw(self, surface, font):
#         if self.shape == 'angular':
#             offset = 12
#             points = [
#                 (self.x + offset, self.y),
#                 (self.x + self.w - offset, self.y),
#                 (self.x + self.w, self.y + offset),
#                 (self.x + self.w, self.y + self.h - offset),
#                 (self.x + self.w - offset, self.y + self.h),
#                 (self.x + offset, self.y + self.h),
#                 (self.x, self.y + self.h - offset),
#                 (self.x, self.y + offset)
#             ]
#             pygame.draw.polygon(surface, TERMINAL_GREEN, points, 2)
#         elif self.shape == 'hex':
#             points = [
#                 (self.x + self.w * 0.25, self.y),
#                 (self.x + self.w * 0.75, self.y),
#                 (self.x + self.w, self.y + self.h * 0.5),
#                 (self.x + self.w * 0.75, self.y + self.h),
#                 (self.x + self.w * 0.25, self.y + self.h),
#                 (self.x, self.y + self.h * 0.5)
#             ]
#             pygame.draw.polygon(surface, TERMINAL_GREEN, points, 2)
#         elif self.shape == 'circular':
#             pygame.draw.ellipse(surface, TERMINAL_GREEN, (self.x, self.y, self.w, self.h), 2)
#         elif self.shape == 'octagon':
#             cx, cy = self.center_x, self.center_y
#             radius = min(self.w, self.h) // 2
#             points = [(cx + math.cos((i/8)*math.pi*2 - math.pi/8)*radius,
#                        cy + math.sin((i/8)*math.pi*2 - math.pi/8)*radius) for i in range(8)]
#             pygame.draw.polygon(surface, TERMINAL_GREEN, points, 2)
#         else:
#             pygame.draw.rect(surface, TERMINAL_GREEN, (self.x, self.y, self.w, self.h), 3)
        
#         # Label slightly higher to avoid corridor overlap
#         text = font.render(self.name, True, TERMINAL_GREEN)
#         text_rect = text.get_rect(center=(self.center_x, self.y + 15))
#         surface.blit(text, text_rect)

# class PathNode:
#     def __init__(self, x, y, name):
#         self.x = x
#         self.y = y
#         self.name = name
#         self.connections = []
    
#     def add_connection(self, node, bulkhead=None):
#         self.connections.append((node, bulkhead))
#         node.connections.append((self, bulkhead))

# class Bulkhead:
#     def __init__(self, name, x, y, orientation='v'):
#         self.name = name
#         self.x = x
#         self.y = y
#         self.orientation = orientation
#         self.sealed = False
    
#     def draw(self, surface, font_small):
#         color = BRIGHT_GREEN if self.sealed else TERMINAL_GREEN
#         width = 5 if self.sealed else 2
        
#         if self.orientation == 'v':
#             pygame.draw.line(surface, color, (self.x, self.y - 18), (self.x, self.y + 18), width)
#             pygame.draw.line(surface, color, (self.x + 5, self.y - 18), (self.x + 5, self.y + 18), width)
#             label = font_small.render(self.name, True, color)
#             surface.blit(label, (self.x + 12, self.y - 6))
#             if self.sealed:
#                 surface.blit(font_small.render('[SEAL]', True, color), (self.x + 12, self.y + 8))
#         else:
#             pygame.draw.line(surface, color, (self.x - 18, self.y), (self.x + 18, self.y), width)
#             pygame.draw.line(surface, color, (self.x - 18, self.y + 5), (self.x + 18, self.y + 5), width)
#             label = font_small.render(self.name, True, color)
#             surface.blit(label, (self.x + 25, self.y - 2))
#             if self.sealed:
#                 surface.blit(font_small.render('[SEAL]', True, color), (self.x + 25, self.y + 13))

# class Alien:
#     def __init__(self, start_node):
#         self.current_node = start_node
#         self.x = start_node.x
#         self.y = start_node.y
#         self.trail = []
#         self.speed = 2.5
#         self.wander_timer = 0
#         self.wander_interval = random.randint(60, 120)
#         self.path = []
#         self.pace_offset = 0
#         self.pace_direction = 1
#         self.hunting = False
#         self.bridge_node = None
    
#     def find_path(self, target_node, bulkheads):
#         if self.current_node == target_node:
#             return []
#         queue = [(self.current_node, [self.current_node])]
#         visited = {self.current_node}
#         while queue:
#             node, path = queue.pop(0)
#             for next_node, bulkhead_name in node.connections:
#                 if bulkhead_name and bulkhead_name in bulkheads and bulkheads[bulkhead_name].sealed:
#                     continue
#                 if next_node == target_node:
#                     return path + [next_node]
#                 if next_node not in visited:
#                     visited.add(next_node)
#                     queue.append((next_node, path + [next_node]))
#         return []
    
#     def update(self, all_nodes, bulkheads, player_pos):
#         dist_to_player = math.hypot(self.x - player_pos[0], self.y - player_pos[1])
        
#         if dist_to_player < 150:
#             if not self.hunting:
#                 self.hunting = True
#                 self.path = []
#             if self.bridge_node and self.current_node != self.bridge_node:
#                 new_path = self.find_path(self.bridge_node, bulkheads)
#                 if new_path and new_path != self.path:
#                     self.path = new_path
#         else:
#             self.hunting = False
#             self.wander_timer += 1
#             if self.wander_timer >= self.wander_interval and not self.path:
#                 self.path = self.find_path(random.choice(all_nodes), bulkheads)
#                 self.wander_timer = 0
#                 self.wander_interval = random.randint(60, 120)
        
#         if self.path:
#             next_node = self.path[0]
#             dx = next_node.x - self.x
#             dy = next_node.y - self.y
#             dist = math.hypot(dx, dy)
#             if dist < 5:
#                 self.current_node = next_node
#                 self.x = next_node.x
#                 self.y = next_node.y
#                 self.path.pop(0)
#             else:
#                 speed = self.speed * 1.5 if self.hunting else self.speed
#                 self.x += (dx / dist) * speed
#                 self.y += (dy / dist) * speed
#         else:
#             # Reduced pacing in narrow rooms to prevent jitter/stuck appearance
#             max_pace = 8 if self.current_node.name in ('airlock_entry', 'junction_low') else 20
#             self.pace_offset += self.pace_direction * 0.5
#             if abs(self.pace_offset) > max_pace:
#                 self.pace_direction *= -1
#             self.x = self.current_node.x + self.pace_offset
        
#         self.trail.append((self.x, self.y))
#         if len(self.trail) > 20:
#             self.trail.pop(0)
    
#     def draw(self, surface):
#         if len(self.trail) > 1:
#             for i in range(len(self.trail) - 1):
#                 alpha = int((i / len(self.trail)) * 150)
#                 pygame.draw.line(surface, (0, alpha, 0), self.trail[i], self.trail[i+1], 3)
        
#         pulse = math.sin(pygame.time.get_ticks() / 200) * 2 + 9
#         if self.hunting:
#             pulse += 3
        
#         points = [(self.x, self.y - pulse), (self.x + pulse, self.y),
#                   (self.x, self.y + pulse), (self.x - pulse, self.y)]
#         color = BRIGHT_GREEN if self.hunting else TERMINAL_GREEN
#         pygame.draw.polygon(surface, color, points)
#         pygame.draw.polygon(surface, BRIGHT_GREEN, points, 2)
        
#         if (pygame.time.get_ticks() // 300) % 2 == 0:
#             pygame.draw.circle(surface, BRIGHT_GREEN, (int(self.x), int(self.y)), int(pulse + 6), 1)

# def draw_corridor(surface, x1, y1, x2, y2, width=35):
#     dx = x2 - x1
#     dy = y2 - y1
#     length = math.hypot(dx, dy)
#     if length == 0:
#         return
#     px = -dy / length * (width / 2)
#     py = dx / length * (width / 2)
#     pygame.draw.line(surface, TERMINAL_GREEN, (x1 + px, y1 + py), (x2 + px, y2 + py), 2)
#     pygame.draw.line(surface, TERMINAL_GREEN, (x1 - px, y1 - py), (x2 - px, y2 - py), 2)

# def run_airlock_puzzle(player_name):
#     pygame.init()
#     screen = pygame.display.set_mode((WIDTH, HEIGHT))
#     pygame.display.set_caption("MUTHER - AIRLOCK PROTOCOL")
    
#     font_large, font_medium, font_small = load_fonts()
#     clock = pygame.time.Clock()
    
#     rooms = {
#         'bridge': Room('BRIDGE', 'angular', 30, 30, 120, 90),
#         'airlock_entry': Room('CORRIDOR', 'rect', 200, 45, 100, 60),
#         'kitchen': Room('GALLEY', 'hex', 350, 30, 120, 90),
#         'mother': Room('MOTHER', 'circular', 520, 30, 100, 90),
#         'hypersleep': Room('HYPERSLEEP', 'circular', 670, 30, 110, 90),
#         'crew': Room('CREW', 'angular', 30, 180, 120, 90),
#         'storage': Room('STORAGE', 'rect', 200, 180, 100, 90),
#         'medbay': Room('MEDBAY', 'hex', 470, 180, 130, 90),
#         'autodoc': Room('AUTODOC', 'angular', 650, 180, 130, 90),
#         'junction_low': Room('JUNCTION', 'rect', 350, 330, 120, 60),
#         'engineering': Room('ENGINE', 'circular', 200, 450, 140, 110),
#         'reactor': Room('REACTOR', 'octagon', 500, 460, 100, 100),
#         'cargo': Room('CARGO BAY', 'rect', 150, 580, 350, 40)
#     }
    
#     nodes = {
#         'bridge': PathNode(90, 75, 'bridge'),
#         'airlock_entry': PathNode(250, 75, 'airlock_entry'),
#         'kitchen': PathNode(410, 75, 'kitchen'),
#         'mother': PathNode(570, 75, 'mother'),
#         'hypersleep': PathNode(725, 75, 'hypersleep'),
#         'crew': PathNode(90, 225, 'crew'),
#         'storage': PathNode(250, 225, 'storage'),
#         'medbay': PathNode(535, 225, 'medbay'),
#         'autodoc': PathNode(715, 225, 'autodoc'),
#         'junction_low': PathNode(410, 360, 'junction_low'),
#         'engineering': PathNode(270, 505, 'engineering'),
#         'reactor': PathNode(550, 510, 'reactor'),
#         'cargo': PathNode(325, 600, 'cargo'),
#     }
    
#     bulkheads = {
#         'B0': Bulkhead('B0', 165, 75, 'v'),
#         'B1': Bulkhead('B1', 315, 75, 'v'),
#         'B2': Bulkhead('B2', 465, 75, 'v'),
#         'B3': Bulkhead('B3', 635, 75, 'v'),
#         'B4': Bulkhead('B4', 250, 155, 'h'),
#         'B5': Bulkhead('B5', 535, 155, 'h'),
#         'B6': Bulkhead('B6', 615, 225, 'v'),
#         'B7': Bulkhead('B7', 410, 290, 'h'),
#         'B8': Bulkhead('B8', 410, 395, 'h'),
#         'B9': Bulkhead('B9', 270, 565, 'h'),
#     }
    
#     # Graph
#     nodes['bridge'].add_connection(nodes['airlock_entry'], 'B0')
#     nodes['airlock_entry'].add_connection(nodes['kitchen'], 'B1')
#     nodes['kitchen'].add_connection(nodes['mother'], 'B2')
#     nodes['mother'].add_connection(nodes['hypersleep'], 'B3')
#     nodes['airlock_entry'].add_connection(nodes['storage'], 'B4')
#     nodes['mother'].add_connection(nodes['medbay'], 'B5')
#     nodes['medbay'].add_connection(nodes['autodoc'], 'B6')
#     nodes['crew'].add_connection(nodes['storage'])
#     nodes['storage'].add_connection(nodes['medbay'])
#     nodes['kitchen'].add_connection(nodes['junction_low'], 'B7')
#     nodes['medbay'].add_connection(nodes['junction_low'])
#     nodes['junction_low'].add_connection(nodes['engineering'], 'B8')
#     nodes['junction_low'].add_connection(nodes['reactor'])
#     nodes['engineering'].add_connection(nodes['cargo'], 'B9')
    
#     alien = Alien(nodes['crew'])
#     alien.bridge_node = nodes['bridge']
    
#     # Game state
#     game_won = game_over = cargo_sealed = False
#     command_input = ""
#     command_history = []
#     error_message = ""
#     message_timer = 0
#     win_timer = 0
#     player_pos = (90, 75)
    
#     running = True
#     while running:
#         for event in pygame.event.get():
#             if event.type == pygame.QUIT:
#                 pygame.quit()
#                 sys.exit()
#             elif event.type == pygame.KEYDOWN and not game_won and not game_over:
#                 if event.key == pygame.K_RETURN:
#                     cmd = command_input.strip().upper()
#                     command_history.append(f"> {cmd}")
                    
#                     if cmd.startswith('SEAL '):
#                         bh = cmd[5:]
#                         if bh in bulkheads:
#                             bulkheads[bh].sealed = True
#                             command_history.append(f"BULKHEAD {bh} SEALED")
#                             if bh == 'B9':
#                                 cargo_sealed = True
#                                 command_history.append("CARGO BAY ISOLATED")
#                         else:
#                             error_message = "DOES NOT COMPUTE"
#                             message_timer = pygame.time.get_ticks() + 2000
#                     elif cmd.startswith('OPEN '):
#                         target = cmd[5:]
#                         if target == 'AIRLOCK':
#                             if not cargo_sealed:
#                                 error_message = "CARGO BAY NOT SEALED"
#                             elif alien.current_node.name != 'cargo':
#                                 error_message = "TARGET NOT IN CARGO BAY"
#                             else:
#                                 game_won = True
#                                 win_timer = pygame.time.get_ticks() + 3000
#                                 command_history.append("AIRLOCK OPENING...")
#                                 command_history.append("DECOMPRESSION INITIATED")
#                             message_timer = pygame.time.get_ticks() + 2000
#                         elif target in bulkheads:
#                             bulkheads[target].sealed = False
#                             command_history.append(f"BULKHEAD {target} OPENED")
#                             if target == 'B9':
#                                 cargo_sealed = False
#                         else:
#                             error_message = "DOES NOT COMPUTE"
#                             message_timer = pygame.time.get_ticks() + 2000
#                     else:
#                         error_message = "DOES NOT COMPUTE"
#                         message_timer = pygame.time.get_ticks() + 2000
                    
#                     command_input = ""
#                     command_history = command_history[-8:]
#                 elif event.key == pygame.K_BACKSPACE:
#                     command_input = command_input[:-1]
#                 elif event.unicode.isprintable() and len(command_input) < 30:
#                     command_input += event.unicode
        
#         if not game_won and not game_over:
#             alien.update(list(nodes.values()), bulkheads, player_pos)
#             if alien.current_node.name == 'bridge':
#                 game_over = True
        
#         if game_won and pygame.time.get_ticks() > win_timer:
#             running = False
        
#         if message_timer and pygame.time.get_ticks() > message_timer:
#             error_message = ""
#             message_timer = 0
        
#         screen.fill(TERMINAL_BLACK)
        
#         # CLEAN CORRIDOR LINES – offset to avoid crossing into rooms
#         draw_corridor(screen, nodes['bridge'].x + 50, nodes['bridge'].y, nodes['airlock_entry'].x - 40, nodes['airlock_entry'].y)
#         draw_corridor(screen, nodes['airlock_entry'].x + 40, nodes['airlock_entry'].y, nodes['kitchen'].x - 50, nodes['kitchen'].y)
#         draw_corridor(screen, nodes['kitchen'].x + 50, nodes['kitchen'].y, nodes['mother'].x - 40, nodes['mother'].y)
#         draw_corridor(screen, nodes['mother'].x + 40, nodes['mother'].y, nodes['hypersleep'].x - 50, nodes['hypersleep'].y)
        
#         draw_corridor(screen, nodes['airlock_entry'].x, nodes['airlock_entry'].y + 25, nodes['storage'].x, nodes['storage'].y - 35)
#         draw_corridor(screen, nodes['mother'].x, nodes['mother'].y + 35, nodes['medbay'].x, nodes['medbay'].y - 35)
        
#         draw_corridor(screen, nodes['crew'].x + 50, nodes['crew'].y, nodes['storage'].x - 40, nodes['storage'].y)
#         draw_corridor(screen, nodes['storage'].x + 40, nodes['storage'].y, nodes['medbay'].x - 50, nodes['medbay'].y)
#         draw_corridor(screen, nodes['medbay'].x + 55, nodes['medbay'].y, nodes['autodoc'].x - 55, nodes['autodoc'].y)
        
#         draw_corridor(screen, nodes['kitchen'].x, nodes['kitchen'].y + 40, nodes['junction_low'].x, nodes['junction_low'].y - 25)
#         draw_corridor(screen, nodes['medbay'].x, nodes['medbay'].y + 35, nodes['junction_low'].x + 40, nodes['junction_low'].y - 10)
        
#         draw_corridor(screen, nodes['junction_low'].x, nodes['junction_low'].y + 25, nodes['engineering'].x, nodes['engineering'].y - 45)
#         draw_corridor(screen, nodes['junction_low'].x + 50, nodes['junction_low'].y + 15, nodes['reactor'].x - 40, nodes['reactor'].y)
        
#         draw_corridor(screen, nodes['engineering'].x, nodes['engineering'].y + 45, nodes['cargo'].x, nodes['cargo'].y - 15)
        
#         # Draw rooms
#         for room in rooms.values():
#             room.draw(screen, font_small)
        
#         # Player
#         pygame.draw.circle(screen, BRIGHT_GREEN, player_pos, 7)
#         if (pygame.time.get_ticks() // 500) % 2 == 0:
#             pygame.draw.circle(screen, BRIGHT_GREEN, player_pos, 12, 2)
        
#         # Details
#         screen.blit(font_medium.render('⚕', True, TERMINAL_GREEN), (525, 220))
#         screen.blit(font_medium.render('⚠ ⚠ ⚠', True, BRIGHT_GREEN), (230, 500))
#         for i in range(3):
#             color = BRIGHT_GREEN if (pygame.time.get_ticks() // 400) % 2 else TERMINAL_GREEN
#             pygame.draw.circle(screen, color, (535 + i * 20, 510), 7)
#         for i in range(12):
#             pygame.draw.rect(screen, DIM_GREEN, (170 + i * 28, 595, 15, 15))
        
#         airlock_color = BRIGHT_GREEN if cargo_sealed else DIM_GREEN
#         airlock_points = [(505, 590), (545, 590), (552, 600), (545, 610), (505, 610)]
#         pygame.draw.polygon(screen, airlock_color, airlock_points, 3)
#         screen.blit(font_small.render('AIRLOCK', True, airlock_color), (508, 597))
        
#         # Bulkheads & alien
#         for bh in bulkheads.values():
#             bh.draw(screen, font_small)
#         if not game_won:
#             alien.draw(screen)
        
#         # Terminal UI
#         ui_x, ui_y = 820, 60
#         screen.blit(font_medium.render('MUTHER TERMINAL', True, BRIGHT_GREEN), (ui_x, ui_y))
#         ui_y += 45
#         for i, line in enumerate(command_history):
#             color = TERMINAL_GREEN if line.startswith('>') else DIM_GREEN
#             screen.blit(font_small.render(line, True, color), (ui_x, ui_y + i * 20))
#         ui_y += len(command_history) * 20 + 35
#         screen.blit(font_small.render('> ' + command_input + '_', True, BRIGHT_GREEN), (ui_x, ui_y))
#         if error_message:
#             ui_y += 35
#             screen.blit(font_small.render(error_message, True, (255, 100, 100)), (ui_x, ui_y))
        
#         # Help
#         help_lines = ['COMMANDS:', 'SEAL B0-B9', 'OPEN B0-B9', 'OPEN AIRLOCK', '',
#                       'Seal B0 to protect bridge', 'Herd alien to cargo bay', 'Seal B9, open airlock']
#         for i, line in enumerate(help_lines):
#             screen.blit(font_small.render(line, True, DIM_GREEN), (ui_x, HEIGHT - 180 + i * 20))
        
#         # Win/lose overlay
#         if game_won:
#             text = font_large.render('AIRLOCK OPENED', True, BRIGHT_GREEN)
#             screen.blit(text, text.get_rect(center=(WIDTH//2, HEIGHT//2)))
#         if game_over:
#             text = font_large.render('LIFE SIGNS NEGATIVE', True, (255, 68, 68))
#             screen.blit(text, text.get_rect(center=(WIDTH//2, HEIGHT//2)))
        
#         apply_crt_effects(screen)
#         pygame.display.flip()
#         clock.tick(60)


"""
Good standard gameplay version but needs graphical improvement and alien gets stuck in Corridor -- keep
"""
# import pygame
# import sys
# import math
# import random
# from config import (WIDTH, HEIGHT, TERMINAL_GREEN, BRIGHT_GREEN, 
#                    DIM_GREEN, TERMINAL_BLACK, load_fonts)
# from engine import apply_crt_effects

# class Room:
#     def __init__(self, name, shape, x, y, w, h):
#         self.name = name
#         self.shape = shape
#         self.x = x
#         self.y = y
#         self.w = w
#         self.h = h
#         self.center_x = x + w // 2
#         self.center_y = y + h // 2
        
#     def draw(self, surface, font):
#         if self.shape == 'angular':
#             offset = 12
#             points = [
#                 (self.x + offset, self.y),
#                 (self.x + self.w - offset, self.y),
#                 (self.x + self.w, self.y + offset),
#                 (self.x + self.w, self.y + self.h - offset),
#                 (self.x + self.w - offset, self.y + self.h),
#                 (self.x + offset, self.y + self.h),
#                 (self.x, self.y + self.h - offset),
#                 (self.x, self.y + offset)
#             ]
#             pygame.draw.polygon(surface, TERMINAL_GREEN, points, 2)
#         elif self.shape == 'hex':
#             points = [
#                 (self.x + self.w * 0.25, self.y),
#                 (self.x + self.w * 0.75, self.y),
#                 (self.x + self.w, self.y + self.h * 0.5),
#                 (self.x + self.w * 0.75, self.y + self.h),
#                 (self.x + self.w * 0.25, self.y + self.h),
#                 (self.x, self.y + self.h * 0.5)
#             ]
#             pygame.draw.polygon(surface, TERMINAL_GREEN, points, 2)
#         elif self.shape == 'circular':
#             pygame.draw.ellipse(surface, TERMINAL_GREEN, (self.x, self.y, self.w, self.h), 2)
#         elif self.shape == 'octagon':
#             cx, cy = self.center_x, self.center_y
#             radius = min(self.w, self.h) // 2
#             points = [(cx + math.cos((i/8)*math.pi*2 - math.pi/8)*radius,
#                        cy + math.sin((i/8)*math.pi*2 - math.pi/8)*radius) for i in range(8)]
#             pygame.draw.polygon(surface, TERMINAL_GREEN, points, 2)
#         else:
#             pygame.draw.rect(surface, TERMINAL_GREEN, (self.x, self.y, self.w, self.h), 3)
        
#         # Label slightly higher to avoid corridor overlap
#         text = font.render(self.name, True, TERMINAL_GREEN)
#         text_rect = text.get_rect(center=(self.center_x, self.y + 15))
#         surface.blit(text, text_rect)

# class PathNode:
#     def __init__(self, x, y, name):
#         self.x = x
#         self.y = y
#         self.name = name
#         self.connections = []
    
#     def add_connection(self, node, bulkhead=None):
#         self.connections.append((node, bulkhead))
#         node.connections.append((self, bulkhead))

# class Bulkhead:
#     def __init__(self, name, x, y, orientation='v'):
#         self.name = name
#         self.x = x
#         self.y = y
#         self.orientation = orientation
#         self.sealed = False
    
#     def draw(self, surface, font_small):
#         color = BRIGHT_GREEN if self.sealed else TERMINAL_GREEN
#         width = 5 if self.sealed else 2
        
#         if self.orientation == 'v':
#             pygame.draw.line(surface, color, (self.x, self.y - 18), (self.x, self.y + 18), width)
#             pygame.draw.line(surface, color, (self.x + 5, self.y - 18), (self.x + 5, self.y + 18), width)
#             label = font_small.render(self.name, True, color)
#             surface.blit(label, (self.x + 12, self.y - 6))
#             if self.sealed:
#                 surface.blit(font_small.render('[SEAL]', True, color), (self.x + 12, self.y + 8))
#         else:
#             pygame.draw.line(surface, color, (self.x - 18, self.y), (self.x + 18, self.y), width)
#             pygame.draw.line(surface, color, (self.x - 18, self.y + 5), (self.x + 18, self.y + 5), width)
#             label = font_small.render(self.name, True, color)
#             surface.blit(label, (self.x + 25, self.y - 2))
#             if self.sealed:
#                 surface.blit(font_small.render('[SEAL]', True, color), (self.x + 25, self.y + 13))

# class Alien:
#     def __init__(self, start_node):
#         self.current_node = start_node
#         self.x = start_node.x
#         self.y = start_node.y
#         self.trail = []
#         self.speed = 2.5
#         self.wander_timer = 0
#         self.wander_interval = random.randint(60, 120)
#         self.path = []
#         self.pace_offset = 0
#         self.pace_direction = 1
#         self.hunting = False
#         self.bridge_node = None
    
#     def find_path(self, target_node, bulkheads):
#         if self.current_node == target_node:
#             return []
#         queue = [(self.current_node, [self.current_node])]
#         visited = {self.current_node}
#         while queue:
#             node, path = queue.pop(0)
#             for next_node, bulkhead_name in node.connections:
#                 if bulkhead_name and bulkhead_name in bulkheads and bulkheads[bulkhead_name].sealed:
#                     continue
#                 if next_node == target_node:
#                     return path + [next_node]
#                 if next_node not in visited:
#                     visited.add(next_node)
#                     queue.append((next_node, path + [next_node]))
#         return []
    
#     def update(self, all_nodes, bulkheads, player_pos):
#         dist_to_player = math.hypot(self.x - player_pos[0], self.y - player_pos[1])
        
#         if dist_to_player < 150:
#             if not self.hunting:
#                 self.hunting = True
#                 self.path = []
#             if self.bridge_node and self.current_node != self.bridge_node:
#                 new_path = self.find_path(self.bridge_node, bulkheads)
#                 if new_path and new_path != self.path:
#                     self.path = new_path
#         else:
#             self.hunting = False
#             self.wander_timer += 1
#             if self.wander_timer >= self.wander_interval and not self.path:
#                 self.path = self.find_path(random.choice(all_nodes), bulkheads)
#                 self.wander_timer = 0
#                 self.wander_interval = random.randint(60, 120)
        
#         if self.path:
#             next_node = self.path[0]
#             dx = next_node.x - self.x
#             dy = next_node.y - self.y
#             dist = math.hypot(dx, dy)
#             if dist < 5:
#                 self.current_node = next_node
#                 self.x = next_node.x
#                 self.y = next_node.y
#                 self.path.pop(0)
#             else:
#                 speed = self.speed * 1.5 if self.hunting else self.speed
#                 self.x += (dx / dist) * speed
#                 self.y += (dy / dist) * speed
#         else:
#             self.pace_offset += self.pace_direction * 0.5
#             if abs(self.pace_offset) > 20:
#                 self.pace_direction *= -1
#             self.x = self.current_node.x + self.pace_offset
        
#         self.trail.append((self.x, self.y))
#         if len(self.trail) > 20:
#             self.trail.pop(0)
    
#     def draw(self, surface):
#         if len(self.trail) > 1:
#             for i in range(len(self.trail) - 1):
#                 alpha = int((i / len(self.trail)) * 150)
#                 pygame.draw.line(surface, (0, alpha, 0), self.trail[i], self.trail[i+1], 3)
        
#         pulse = math.sin(pygame.time.get_ticks() / 200) * 2 + 9
#         if self.hunting:
#             pulse += 3
        
#         points = [(self.x, self.y - pulse), (self.x + pulse, self.y),
#                   (self.x, self.y + pulse), (self.x - pulse, self.y)]
#         color = BRIGHT_GREEN if self.hunting else TERMINAL_GREEN
#         pygame.draw.polygon(surface, color, points)
#         pygame.draw.polygon(surface, BRIGHT_GREEN, points, 2)
        
#         if (pygame.time.get_ticks() // 300) % 2 == 0:
#             pygame.draw.circle(surface, BRIGHT_GREEN, (int(self.x), int(self.y)), int(pulse + 6), 1)

# def draw_corridor(surface, x1, y1, x2, y2, width=35):
#     dx = x2 - x1
#     dy = y2 - y1
#     length = math.hypot(dx, dy)
#     if length == 0:
#         return
#     px = -dy / length * (width / 2)
#     py = dx / length * (width / 2)
#     pygame.draw.line(surface, TERMINAL_GREEN, (x1 + px, y1 + py), (x2 + px, y2 + py), 2)
#     pygame.draw.line(surface, TERMINAL_GREEN, (x1 - px, y1 - py), (x2 - px, y2 - py), 2)

# def run_airlock_puzzle(player_name):
#     pygame.init()
#     screen = pygame.display.set_mode((WIDTH, HEIGHT))
#     pygame.display.set_caption("MUTHER - AIRLOCK PROTOCOL")
    
#     font_large, font_medium, font_small = load_fonts()
#     clock = pygame.time.Clock()
    
#     rooms = {
#         'bridge': Room('BRIDGE', 'angular', 30, 30, 120, 90),
#         'airlock_entry': Room('CORRIDOR', 'rect', 200, 45, 100, 60),
#         'kitchen': Room('GALLEY', 'hex', 350, 30, 120, 90),
#         'mother': Room('MOTHER', 'circular', 520, 30, 100, 90),
#         'hypersleep': Room('HYPERSLEEP', 'circular', 670, 30, 110, 90),
#         'crew': Room('CREW', 'angular', 30, 180, 120, 90),
#         'storage': Room('STORAGE', 'rect', 200, 180, 100, 90),
#         'medbay': Room('MEDBAY', 'hex', 470, 180, 130, 90),
#         'autodoc': Room('AUTODOC', 'angular', 650, 180, 130, 90),
#         'junction_low': Room('JUNCTION', 'rect', 350, 330, 120, 60),
#         'engineering': Room('ENGINE', 'circular', 200, 450, 140, 110),
#         'reactor': Room('REACTOR', 'octagon', 500, 460, 100, 100),
#         'cargo': Room('CARGO BAY', 'rect', 150, 580, 350, 40)
#     }
    
#     nodes = {
#         'bridge': PathNode(90, 75, 'bridge'),
#         'airlock_entry': PathNode(250, 75, 'airlock_entry'),
#         'kitchen': PathNode(410, 75, 'kitchen'),
#         'mother': PathNode(570, 75, 'mother'),
#         'hypersleep': PathNode(725, 75, 'hypersleep'),
#         'crew': PathNode(90, 225, 'crew'),
#         'storage': PathNode(250, 225, 'storage'),
#         'medbay': PathNode(535, 225, 'medbay'),
#         'autodoc': PathNode(715, 225, 'autodoc'),
#         'junction_low': PathNode(410, 360, 'junction_low'),
#         'engineering': PathNode(270, 505, 'engineering'),
#         'reactor': PathNode(550, 510, 'reactor'),
#         'cargo': PathNode(325, 600, 'cargo'),
#     }
    
#     bulkheads = {
#         'B0': Bulkhead('B0', 165, 75, 'v'),
#         'B1': Bulkhead('B1', 315, 75, 'v'),
#         'B2': Bulkhead('B2', 465, 75, 'v'),
#         'B3': Bulkhead('B3', 635, 75, 'v'),
#         'B4': Bulkhead('B4', 250, 155, 'h'),
#         'B5': Bulkhead('B5', 535, 155, 'h'),
#         'B6': Bulkhead('B6', 615, 225, 'v'),
#         'B7': Bulkhead('B7', 410, 290, 'h'),
#         'B8': Bulkhead('B8', 410, 395, 'h'),
#         'B9': Bulkhead('B9', 270, 565, 'h'),
#     }
    
#     # Graph
#     nodes['bridge'].add_connection(nodes['airlock_entry'], 'B0')
#     nodes['airlock_entry'].add_connection(nodes['kitchen'], 'B1')
#     nodes['kitchen'].add_connection(nodes['mother'], 'B2')
#     nodes['mother'].add_connection(nodes['hypersleep'], 'B3')
#     nodes['airlock_entry'].add_connection(nodes['storage'], 'B4')
#     nodes['mother'].add_connection(nodes['medbay'], 'B5')
#     nodes['medbay'].add_connection(nodes['autodoc'], 'B6')
#     nodes['crew'].add_connection(nodes['storage'])
#     nodes['storage'].add_connection(nodes['medbay'])
#     nodes['kitchen'].add_connection(nodes['junction_low'], 'B7')
#     nodes['medbay'].add_connection(nodes['junction_low'])
#     nodes['junction_low'].add_connection(nodes['engineering'], 'B8')
#     nodes['junction_low'].add_connection(nodes['reactor'])
#     nodes['engineering'].add_connection(nodes['cargo'], 'B9')
    
#     alien = Alien(nodes['crew'])
#     alien.bridge_node = nodes['bridge']
    
#     # Game state
#     game_won = game_over = cargo_sealed = False
#     command_input = ""
#     command_history = []
#     error_message = ""
#     message_timer = 0
#     win_timer = 0
#     player_pos = (90, 75)
    
#     running = True
#     while running:
#         for event in pygame.event.get():
#             if event.type == pygame.QUIT:
#                 pygame.quit()
#                 sys.exit()
#             elif event.type == pygame.KEYDOWN and not game_won and not game_over:
#                 if event.key == pygame.K_RETURN:
#                     cmd = command_input.strip().upper()
#                     command_history.append(f"> {cmd}")
                    
#                     if cmd.startswith('SEAL '):
#                         bh = cmd[5:]
#                         if bh in bulkheads:
#                             bulkheads[bh].sealed = True
#                             command_history.append(f"BULKHEAD {bh} SEALED")
#                             if bh == 'B9':
#                                 cargo_sealed = True
#                                 command_history.append("CARGO BAY ISOLATED")
#                         else:
#                             error_message = "DOES NOT COMPUTE"
#                             message_timer = pygame.time.get_ticks() + 2000
#                     elif cmd.startswith('OPEN '):
#                         target = cmd[5:]
#                         if target == 'AIRLOCK':
#                             if not cargo_sealed:
#                                 error_message = "CARGO BAY NOT SEALED"
#                             elif alien.current_node.name != 'cargo':
#                                 error_message = "TARGET NOT IN CARGO BAY"
#                             else:
#                                 game_won = True
#                                 win_timer = pygame.time.get_ticks() + 3000
#                                 command_history.append("AIRLOCK OPENING...")
#                                 command_history.append("DECOMPRESSION INITIATED")
#                             message_timer = pygame.time.get_ticks() + 2000
#                         elif target in bulkheads:
#                             bulkheads[target].sealed = False
#                             command_history.append(f"BULKHEAD {target} OPENED")
#                             if target == 'B9':
#                                 cargo_sealed = False
#                         else:
#                             error_message = "DOES NOT COMPUTE"
#                             message_timer = pygame.time.get_ticks() + 2000
#                     else:
#                         error_message = "DOES NOT COMPUTE"
#                         message_timer = pygame.time.get_ticks() + 2000
                    
#                     command_input = ""
#                     command_history = command_history[-8:]
#                 elif event.key == pygame.K_BACKSPACE:
#                     command_input = command_input[:-1]
#                 elif event.unicode.isprintable() and len(command_input) < 30:
#                     command_input += event.unicode
        
#         if not game_won and not game_over:
#             alien.update(list(nodes.values()), bulkheads, player_pos)
#             if alien.current_node.name == 'bridge':
#                 game_over = True
        
#         if game_won and pygame.time.get_ticks() > win_timer:
#             running = False
        
#         if message_timer and pygame.time.get_ticks() > message_timer:
#             error_message = ""
#             message_timer = 0
        
#         screen.fill(TERMINAL_BLACK)
        
#         # FIXED CORRIDORS – clean connections, no floating segments
#         draw_corridor(screen, nodes['bridge'].x, nodes['bridge'].y, nodes['airlock_entry'].x, nodes['airlock_entry'].y)
#         draw_corridor(screen, nodes['airlock_entry'].x, nodes['airlock_entry'].y, nodes['kitchen'].x, nodes['kitchen'].y)
#         draw_corridor(screen, nodes['kitchen'].x, nodes['kitchen'].y, nodes['mother'].x, nodes['mother'].y)
#         draw_corridor(screen, nodes['mother'].x, nodes['mother'].y, nodes['hypersleep'].x, nodes['hypersleep'].y)
        
#         draw_corridor(screen, nodes['airlock_entry'].x, nodes['airlock_entry'].y + 30, nodes['storage'].x, nodes['storage'].y)
#         draw_corridor(screen, nodes['mother'].x, nodes['mother'].y + 30, nodes['medbay'].x, nodes['medbay'].y - 30)
        
#         draw_corridor(screen, nodes['crew'].x, nodes['crew'].y, nodes['storage'].x, nodes['storage'].y)
#         draw_corridor(screen, nodes['storage'].x, nodes['storage'].y, nodes['medbay'].x, nodes['medbay'].y)
#         draw_corridor(screen, nodes['medbay'].x, nodes['medbay'].y, nodes['autodoc'].x, nodes['autodoc'].y)
        
#         draw_corridor(screen, nodes['kitchen'].x, nodes['kitchen'].y + 45, nodes['junction_low'].x, nodes['junction_low'].y - 30)
#         draw_corridor(screen, nodes['medbay'].x, nodes['medbay'].y + 30, nodes['junction_low'].x + 50, nodes['junction_low'].y)
        
#         draw_corridor(screen, nodes['junction_low'].x, nodes['junction_low'].y + 30, nodes['engineering'].x, nodes['engineering'].y - 30)
#         draw_corridor(screen, nodes['junction_low'].x + 50, nodes['junction_low'].y + 20, nodes['reactor'].x, nodes['reactor'].y)
        
#         draw_corridor(screen, nodes['engineering'].x, nodes['engineering'].y + 40, nodes['cargo'].x, nodes['cargo'].y)
        
#         # Draw rooms
#         for room in rooms.values():
#             room.draw(screen, font_small)
        
#         # Player
#         pygame.draw.circle(screen, BRIGHT_GREEN, player_pos, 7)
#         if (pygame.time.get_ticks() // 500) % 2 == 0:
#             pygame.draw.circle(screen, BRIGHT_GREEN, player_pos, 12, 2)
        
#         # Details
#         screen.blit(font_medium.render('⚕', True, TERMINAL_GREEN), (525, 220))
#         screen.blit(font_medium.render('⚠ ⚠ ⚠', True, BRIGHT_GREEN), (230, 500))
#         for i in range(3):
#             color = BRIGHT_GREEN if (pygame.time.get_ticks() // 400) % 2 else TERMINAL_GREEN
#             pygame.draw.circle(screen, color, (535 + i * 20, 510), 7)
#         for i in range(12):
#             pygame.draw.rect(screen, DIM_GREEN, (170 + i * 28, 595, 15, 15))
        
#         airlock_color = BRIGHT_GREEN if cargo_sealed else DIM_GREEN
#         airlock_points = [(505, 590), (545, 590), (552, 600), (545, 610), (505, 610)]
#         pygame.draw.polygon(screen, airlock_color, airlock_points, 3)
#         screen.blit(font_small.render('AIRLOCK', True, airlock_color), (508, 597))
        
#         # Bulkheads & alien
#         for bh in bulkheads.values():
#             bh.draw(screen, font_small)
#         if not game_won:
#             alien.draw(screen)
        
#         # Terminal UI
#         ui_x, ui_y = 820, 60
#         screen.blit(font_medium.render('MUTHER TERMINAL', True, BRIGHT_GREEN), (ui_x, ui_y))
#         ui_y += 45
#         for i, line in enumerate(command_history):
#             color = TERMINAL_GREEN if line.startswith('>') else DIM_GREEN
#             screen.blit(font_small.render(line, True, color), (ui_x, ui_y + i * 20))
#         ui_y += len(command_history) * 20 + 35
#         screen.blit(font_small.render('> ' + command_input + '_', True, BRIGHT_GREEN), (ui_x, ui_y))
#         if error_message:
#             ui_y += 35
#             screen.blit(font_small.render(error_message, True, (255, 100, 100)), (ui_x, ui_y))
        
#         # Help
#         help_lines = ['COMMANDS:', 'SEAL B0-B9', 'OPEN B0-B9', 'OPEN AIRLOCK', '',
#                       'Seal B0 to protect bridge', 'Herd alien to cargo bay', 'Seal B9, open airlock']
#         for i, line in enumerate(help_lines):
#             screen.blit(font_small.render(line, True, DIM_GREEN), (ui_x, HEIGHT - 180 + i * 20))
        
#         # Win/lose overlay
#         if game_won:
#             text = font_large.render('AIRLOCK OPENED', True, BRIGHT_GREEN)
#             screen.blit(text, text.get_rect(center=(WIDTH//2, HEIGHT//2)))
#         if game_over:
#             text = font_large.render('LIFE SIGNS NEGATIVE', True, (255, 68, 68))
#             screen.blit(text, text.get_rect(center=(WIDTH//2, HEIGHT//2)))
        
#         apply_crt_effects(screen)
#         pygame.display.flip()
#         clock.tick(60)








# """
# Airlock puzzle for ALIEN: CHRONOS
# Herd the xenomorph to the cargo hold and blow it into space
# """

# import pygame
# import sys
# import math
# import random
# from config import (WIDTH, HEIGHT, TERMINAL_GREEN, BRIGHT_GREEN, 
#                    DIM_GREEN, TERMINAL_BLACK, load_fonts)
# from engine import apply_crt_effects, green_flash

# class Room:
#     """Represents a ship room"""
#     def __init__(self, name, shape, x, y, w, h):
#         self.name = name
#         self.shape = shape
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
#         offset = 12
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

# class PathNode:
#     """Navigation node for alien pathfinding"""
#     def __init__(self, x, y, name):
#         self.x = x
#         self.y = y
#         self.name = name
#         self.connections = []
    
#     def add_connection(self, node, bulkhead=None):
#         """Add bidirectional connection with bulkhead"""
#         self.connections.append((node, bulkhead))
#         node.connections.append((self, bulkhead))

# class Bulkhead:
#     """Represents a sealable bulkhead"""
#     def __init__(self, name, x, y, orientation='v'):
#         self.name = name
#         self.x = x
#         self.y = y
#         self.orientation = orientation
#         self.sealed = False
    
#     def draw(self, surface, font_small):
#         color = BRIGHT_GREEN if self.sealed else TERMINAL_GREEN
#         width = 5 if self.sealed else 2
        
#         if self.orientation == 'v':
#             pygame.draw.line(surface, color, (self.x, self.y - 18), (self.x, self.y + 18), width)
#             pygame.draw.line(surface, color, (self.x + 5, self.y - 18), (self.x + 5, self.y + 18), width)
            
#             label = font_small.render(self.name, True, color)
#             surface.blit(label, (self.x + 12, self.y - 6))
#             if self.sealed:
#                 sealed_text = font_small.render('[SEAL]', True, color)
#                 surface.blit(sealed_text, (self.x + 12, self.y + 8))
#         else:
#             pygame.draw.line(surface, color, (self.x - 18, self.y), (self.x + 18, self.y), width)
#             pygame.draw.line(surface, color, (self.x - 18, self.y + 5), (self.x + 18, self.y + 5), width)
            
#             label = font_small.render(self.name, True, color)
#             surface.blit(label, (self.x + 25, self.y - 2))
#             if self.sealed:
#                 sealed_text = font_small.render('[SEAL]', True, color)
#                 surface.blit(sealed_text, (self.x + 25, self.y + 13))

# class Alien:
#     """The xenomorph with pathfinding"""
#     def __init__(self, start_node):
#         self.current_node = start_node
#         self.target_node = start_node
#         self.x = start_node.x
#         self.y = start_node.y
#         self.trail = []
#         self.speed = 2.5
#         self.wander_timer = 0
#         self.wander_interval = random.randint(60, 120)
#         self.path = []
#         self.pace_offset = 0
#         self.pace_direction = 1
#         self.hunting = False
#         self.bridge_node = None
    
#     def find_path(self, target_node, bulkheads):
#         """BFS pathfinding that STRICTLY respects sealed bulkheads"""
#         if self.current_node == target_node:
#             return []
        
#         queue = [(self.current_node, [self.current_node])]
#         visited = {self.current_node}
        
#         while queue:
#             node, path = queue.pop(0)
            
#             for next_node, bulkhead_name in node.connections:
#                 # CRITICAL: If there's a bulkhead and it's sealed, CANNOT pass
#                 if bulkhead_name is not None:
#                     if bulkhead_name in bulkheads and bulkheads[bulkhead_name].sealed:
#                         continue  # This path is blocked
                
#                 if next_node == target_node:
#                     return path + [next_node]
                
#                 if next_node not in visited:
#                     visited.add(next_node)
#                     queue.append((next_node, path + [next_node]))
        
#         return []  # No path found - alien is trapped
    
#     def update(self, all_nodes, bulkheads, player_pos):
#         """Update alien movement with hunting behavior"""
#         # Check if alien can sense player (within 150 units)
#         dist_to_player = math.sqrt((self.x - player_pos[0])**2 + (self.y - player_pos[1])**2)
        
#         if dist_to_player < 150:
#             # HUNTING MODE - make beeline for player (bridge)
#             if not self.hunting:
#                 self.hunting = True
#                 self.path = []  # Clear current path
            
#             # Try to path to bridge
#             if self.bridge_node and self.current_node != self.bridge_node:
#                 new_path = self.find_path(self.bridge_node, bulkheads)
#                 if new_path and new_path != self.path:
#                     self.path = new_path
#                     self.target_node = self.bridge_node
#         else:
#             self.hunting = False
            
#             # EXPLORATION MODE
#             self.wander_timer += 1
#             if self.wander_timer >= self.wander_interval and not self.path:
#                 self.target_node = random.choice(all_nodes)
#                 self.path = self.find_path(self.target_node, bulkheads)
#                 self.wander_timer = 0
#                 self.wander_interval = random.randint(60, 120)
        
#         # Move along path
#         if self.path:
#             next_node = self.path[0]
#             dx = next_node.x - self.x
#             dy = next_node.y - self.y
#             dist = math.sqrt(dx*dx + dy*dy)
            
#             if dist < 5:
#                 self.current_node = next_node
#                 self.x = next_node.x
#                 self.y = next_node.y
#                 self.path.pop(0)
#             else:
#                 move_speed = self.speed * 1.5 if self.hunting else self.speed
#                 self.x += (dx / dist) * move_speed
#                 self.y += (dy / dist) * move_speed
#         else:
#             # Pace when stuck
#             self.pace_offset += self.pace_direction * 0.5
#             if abs(self.pace_offset) > 20:
#                 self.pace_direction *= -1
#             self.x = self.current_node.x + self.pace_offset
        
#         # Update trail
#         self.trail.append((self.x, self.y))
#         if len(self.trail) > 20:
#             self.trail.pop(0)
    
#     def draw(self, surface):
#         """Draw alien with pulsing effect"""
#         if len(self.trail) > 1:
#             for i in range(len(self.trail) - 1):
#                 alpha = int((i / len(self.trail)) * 150)
#                 color = (0, alpha, 0)
#                 pygame.draw.line(surface, color, self.trail[i], self.trail[i + 1], 3)
        
#         pulse = math.sin(pygame.time.get_ticks() / 200) * 2 + 9
        
#         # Hunting indicator - larger and brighter
#         if self.hunting:
#             pulse += 3
        
#         points = [
#             (self.x, self.y - pulse),
#             (self.x + pulse, self.y),
#             (self.x, self.y + pulse),
#             (self.x - pulse, self.y)
#         ]
        
#         color = BRIGHT_GREEN if self.hunting else TERMINAL_GREEN
#         pygame.draw.polygon(surface, color, points)
#         pygame.draw.polygon(surface, BRIGHT_GREEN, points, 2)
        
#         if (pygame.time.get_ticks() // 300) % 2 == 0:
#             pygame.draw.circle(surface, BRIGHT_GREEN, (int(self.x), int(self.y)), 
#                              int(pulse + 6), 1)

# def draw_corridor(surface, x1, y1, x2, y2, width=35):
#     """Draw a corridor with parallel lines"""
#     dx = x2 - x1
#     dy = y2 - y1
#     length = math.sqrt(dx*dx + dy*dy)
#     if length == 0:
#         return
    
#     px = -dy / length * (width / 2)
#     py = dx / length * (width / 2)
    
#     pygame.draw.line(surface, TERMINAL_GREEN, (x1 + px, y1 + py), (x2 + px, y2 + py), 2)
#     pygame.draw.line(surface, TERMINAL_GREEN, (x1 - px, y1 - py), (x2 - px, y2 - py), 2)

# def run_airlock_puzzle(player_name):
#     """Main function to run the airlock puzzle"""
#     pygame.init()
#     screen = pygame.display.set_mode((WIDTH, HEIGHT))
#     pygame.display.set_caption("MUTHER - AIRLOCK PROTOCOL")
    
#     font_large, font_medium, font_small = load_fonts()
#     clock = pygame.time.Clock()
    
#     # Much wider, bigger ship layout
#     rooms = {
#         'bridge': Room('BRIDGE', 'angular', 30, 30, 120, 90),
#         'airlock_entry': Room('CORRIDOR', 'rect', 200, 45, 100, 60),
#         'kitchen': Room('GALLEY', 'hex', 350, 30, 120, 90),
#         'mother': Room('MOTHER', 'circular', 520, 30, 100, 90),
#         'hypersleep': Room('HYPERSLEEP', 'circular', 670, 30, 110, 90),
        
#         'crew': Room('CREW', 'angular', 30, 180, 120, 90),
#         'storage': Room('STORAGE', 'rect', 200, 180, 100, 90),
#         'medbay': Room('MEDBAY', 'hex', 470, 180, 130, 90),
#         'autodoc': Room('AUTODOC', 'angular', 650, 180, 130, 90),
        
#         'junction_low': Room('JUNCTION', 'rect', 350, 330, 120, 60),
        
#         'engineering': Room('ENGINE', 'circular', 200, 450, 140, 110),
#         'reactor': Room('REACTOR', 'octagon', 500, 460, 100, 100),
        
#         'cargo': Room('CARGO BAY', 'rect', 150, 580, 350, 40)
#     }
    
#     # Navigation nodes with more detailed pathfinding
#     nodes = {
#         'bridge': PathNode(90, 75, 'bridge'),
#         'airlock_entry': PathNode(250, 75, 'airlock_entry'),
#         'kitchen': PathNode(410, 75, 'kitchen'),
#         'mother': PathNode(570, 75, 'mother'),
#         'hypersleep': PathNode(725, 75, 'hypersleep'),
        
#         'crew': PathNode(90, 225, 'crew'),
#         'storage': PathNode(250, 225, 'storage'),
#         'medbay': PathNode(535, 225, 'medbay'),
#         'autodoc': PathNode(715, 225, 'autodoc'),
        
#         'junction_low': PathNode(410, 360, 'junction_low'),
        
#         'engineering': PathNode(270, 505, 'engineering'),
#         'reactor': PathNode(550, 510, 'reactor'),
        
#         'cargo': PathNode(325, 600, 'cargo'),
#     }
    
#     # Bulkheads - more of them for better control
#     bulkheads = {
#         'B0': Bulkhead('B0', 165, 75, 'v'),     # Bridge entrance - NEW!
#         'B1': Bulkhead('B1', 315, 75, 'v'),     # After airlock entry
#         'B2': Bulkhead('B2', 465, 75, 'v'),     # Kitchen to mother
#         'B3': Bulkhead('B3', 635, 75, 'v'),     # Mother to hypersleep
#         'B4': Bulkhead('B4', 250, 155, 'h'),    # Airlock entry down to storage
#         'B5': Bulkhead('B5', 535, 155, 'h'),    # Mother down to medbay
#         'B6': Bulkhead('B6', 615, 225, 'v'),    # Medbay to autodoc
#         'B7': Bulkhead('B7', 410, 290, 'h'),    # Kitchen down to junction
#         'B8': Bulkhead('B8', 410, 395, 'h'),    # Junction down
#         'B9': Bulkhead('B9', 270, 565, 'h'),    # Engineering to cargo
#     }
    
#     # Build navigation graph - CRITICAL: Pass bulkhead names correctly
#     nodes['bridge'].add_connection(nodes['airlock_entry'], 'B0')
#     nodes['airlock_entry'].add_connection(nodes['kitchen'], 'B1')
#     nodes['kitchen'].add_connection(nodes['mother'], 'B2')
#     nodes['mother'].add_connection(nodes['hypersleep'], 'B3')
    
#     nodes['airlock_entry'].add_connection(nodes['storage'], 'B4')
#     nodes['mother'].add_connection(nodes['medbay'], 'B5')
#     nodes['medbay'].add_connection(nodes['autodoc'], 'B6')
    
#     nodes['crew'].add_connection(nodes['storage'])
#     nodes['storage'].add_connection(nodes['medbay'])
    
#     nodes['kitchen'].add_connection(nodes['junction_low'], 'B7')
#     nodes['medbay'].add_connection(nodes['junction_low'])
    
#     nodes['junction_low'].add_connection(nodes['engineering'], 'B8')
#     nodes['junction_low'].add_connection(nodes['reactor'])
    
#     nodes['engineering'].add_connection(nodes['cargo'], 'B9')
    
#     # Create alien starting in crew quarters
#     alien = Alien(nodes['crew'])
#     alien.bridge_node = nodes['bridge']  # Set bridge as hunting target
    
#     # Game state
#     game_won = False
#     game_over = False
#     cargo_sealed = False
#     command_input = ""
#     command_history = []
#     error_message = ""
#     message_timer = 0
#     win_timer = 0
    
#     player_pos = (90, 75)  # Bridge position
    
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
#                     cmd = command_input.strip().upper()
#                     command_history.append(f"> {cmd}")
                    
#                     if cmd.startswith('SEAL '):
#                         parts = cmd.split(' ')
#                         if len(parts) == 2:
#                             bulkhead_name = parts[1]
#                             if bulkhead_name in bulkheads:
#                                 bulkheads[bulkhead_name].sealed = True
#                                 command_history.append(f"BULKHEAD {bulkhead_name} SEALED")
                                
#                                 if bulkhead_name == 'B9':
#                                     cargo_sealed = True
#                                     command_history.append("CARGO BAY ISOLATED")
                                
#                                 error_message = ""
#                             else:
#                                 error_message = "DOES NOT COMPUTE"
#                                 message_timer = pygame.time.get_ticks() + 2000
#                         else:
#                             error_message = "DOES NOT COMPUTE"
#                             message_timer = pygame.time.get_ticks() + 2000
                    
#                     elif cmd.startswith('OPEN '):
#                         parts = cmd.split(' ')
#                         if len(parts) == 2:
#                             target = parts[1]
                            
#                             if target == 'AIRLOCK':
#                                 if not cargo_sealed:
#                                     error_message = "CARGO BAY NOT SEALED"
#                                     message_timer = pygame.time.get_ticks() + 2000
#                                 elif alien.current_node.name != 'cargo':
#                                     error_message = "TARGET NOT IN CARGO BAY"
#                                     message_timer = pygame.time.get_ticks() + 2000
#                                 else:
#                                     game_won = True
#                                     win_timer = pygame.time.get_ticks() + 3000
#                                     command_history.append("AIRLOCK OPENING...")
#                                     command_history.append("DECOMPRESSION INITIATED")
#                             elif target in bulkheads:
#                                 bulkheads[target].sealed = False
#                                 command_history.append(f"BULKHEAD {target} OPENED")
                                
#                                 if target == 'B9':
#                                     cargo_sealed = False
                                
#                                 error_message = ""
#                             else:
#                                 error_message = "DOES NOT COMPUTE"
#                                 message_timer = pygame.time.get_ticks() + 2000
#                         else:
#                             error_message = "DOES NOT COMPUTE"
#                             message_timer = pygame.time.get_ticks() + 2000
#                     else:
#                         error_message = "DOES NOT COMPUTE"
#                         message_timer = pygame.time.get_ticks() + 2000
                    
#                     command_input = ""
                    
#                     if len(command_history) > 8:
#                         command_history = command_history[-8:]
                
#                 elif event.key == pygame.K_BACKSPACE:
#                     command_input = command_input[:-1]
#                     error_message = ""
                
#                 elif event.unicode.isprintable():
#                     if len(command_input) < 30:
#                         command_input += event.unicode
#                         error_message = ""
        
#         # Update alien
#         if not game_won and not game_over:
#             alien.update(list(nodes.values()), bulkheads, player_pos)
            
#             if alien.current_node.name == 'bridge':
#                 game_over = True
        
#         if game_won and pygame.time.get_ticks() > win_timer:
#             running = False
        
#         if message_timer > 0 and pygame.time.get_ticks() > message_timer:
#             error_message = ""
#             message_timer = 0
        
#         # DRAW
#         screen.fill(TERMINAL_BLACK)
        
#         # Draw all corridors
#         draw_corridor(screen, 150, 75, 200, 75)
#         draw_corridor(screen, 300, 75, 350, 75)
#         draw_corridor(screen, 470, 75, 520, 75)
#         draw_corridor(screen, 620, 75, 670, 75)
        
#         draw_corridor(screen, 250, 105, 250, 180)
#         draw_corridor(screen, 570, 120, 570, 180)
        
#         draw_corridor(screen, 150, 225, 200, 225)
#         draw_corridor(screen, 300, 225, 470, 225)
#         draw_corridor(screen, 600, 225, 650, 225)
        
#         draw_corridor(screen, 410, 120, 410, 330)
#         draw_corridor(screen, 535, 270, 535, 330)
#         draw_corridor(screen, 410, 330, 500, 330)
        
#         draw_corridor(screen, 410, 390, 410, 450)
#         draw_corridor(screen, 470, 360, 500, 460)
        
#         draw_corridor(screen, 270, 560, 270, 580)
        
#         # Draw rooms
#         for room in rooms.values():
#             room.draw(screen, font_small)
        
#         # Player in bridge
#         pygame.draw.circle(screen, BRIGHT_GREEN, player_pos, 7)
#         if (pygame.time.get_ticks() // 500) % 2 == 0:
#             pygame.draw.circle(screen, BRIGHT_GREEN, player_pos, 12, 2)
        
#         # Med symbol
#         med_symbol = font_medium.render('⚕', True, TERMINAL_GREEN)
#         screen.blit(med_symbol, (525, 220))
        
#         # Engineering hazards
#         hazard = font_medium.render('⚠ ⚠ ⚠', True, BRIGHT_GREEN)
#         screen.blit(hazard, (230, 500))
        
#         # Reactor cores
#         for i in range(3):
#             glow = (pygame.time.get_ticks() // 400) % 2 == 0
#             color = BRIGHT_GREEN if glow else TERMINAL_GREEN
#             pygame.draw.circle(screen, color, (535 + i * 20, 510), 7)
        
#         # Cargo crates
#         for i in range(12):
#             pygame.draw.rect(screen, DIM_GREEN, (170 + i * 28, 595, 15, 15))
        
#         # Airlock
#         airlock_color = BRIGHT_GREEN if cargo_sealed else DIM_GREEN
#         airlock_points = [(505, 590), (545, 590), (552, 600), (545, 610), (505, 610)]
#         pygame.draw.polygon(screen, airlock_color, airlock_points, 3)
#         airlock_label = font_small.render('AIRLOCK', True, airlock_color)
#         screen.blit(airlock_label, (508, 597))
        
#         # Draw bulkheads
#         for bulkhead in bulkheads.values():
#             bulkhead.draw(screen, font_small)
        
#         # Draw alien
#         if not game_won:
#             alien.draw(screen)
        
#         # UI
#         ui_x = 820
#         ui_y = 60
        
#         title = font_medium.render('MUTHER TERMINAL', True, BRIGHT_GREEN)
#         screen.blit(title, (ui_x, ui_y))
#         ui_y += 45
        
#         for i, line in enumerate(command_history):
#             hist_color = TERMINAL_GREEN if line.startswith('>') else DIM_GREEN
#             hist_text = font_small.render(line, True, hist_color)
#             screen.blit(hist_text, (ui_x, ui_y + i * 20))
        
#         ui_y += len(command_history) * 20 + 35
        
#         prompt = font_small.render('> ' + command_input + '_', True, BRIGHT_GREEN)
#         screen.blit(prompt, (ui_x, ui_y))
#         ui_y += 35
        
#         if error_message:
#             err_text = font_small.render(error_message, True, (255, 100, 100))
#             screen.blit(err_text, (ui_x, ui_y))
        
#         help_y = HEIGHT - 180
#         help_lines = [
#             'COMMANDS:',
#             'SEAL B0-B9',
#             'OPEN B0-B9',
#             'OPEN AIRLOCK',
#             '',
#             'Seal B0 to protect bridge',
#             'Herd alien to cargo bay',
#             'Seal B9, open airlock'
#         ]
        
#         for i, line in enumerate(help_lines):
#             help_text = font_small.render(line, True, DIM_GREEN)
#             screen.blit(help_text, (ui_x, help_y + i * 20))
        
#         # Win/lose
#         if game_won:
#             win_text = font_large.render('AIRLOCK OPENED', True, BRIGHT_GREEN)
#             win_rect = win_text.get_rect(center=(400, 300))
#             screen.blit(win_text, win_rect)
        
#         if game_over:
#             lose_text = font_large.render('LIFE SIGNS NEGATIVE', True, (255, 68, 68))
#             lose_rect = lose_text.get_rect(center=(400, 300))
#             screen.blit(lose_text, lose_rect)
        
#         apply_crt_effects(screen)
#         pygame.display.flip()
#         clock.tick(60)
