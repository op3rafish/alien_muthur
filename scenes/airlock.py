
"""
Airlock puzzle for ALIEN: CHRONOS 
"""

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
        else:
            pygame.draw.line(surface, color, (self.x - 18, self.y), (self.x + 18, self.y), width)
            pygame.draw.line(surface, color, (self.x - 18, self.y + 5), (self.x + 18, self.y + 5), width)
            label = font_small.render(self.name, True, color)
            surface.blit(label, (self.x + 25, self.y - 2))

class Alien:
    def __init__(self, start_node, bridge_node):
        self.x = float(start_node.x)
        self.y = float(start_node.y)
        self.current_node = start_node
        self.bridge_node = bridge_node
        self.path = []
        self.move_speed = 1.5
        self.state = 'idle'  # idle, moving, blocked
        self.idle_timer = 0
        self.blocked_timer = 0
        self.blocked_position = None
    
    def get_open_connections(self, node, bulkheads):
        """Get all connections from a node that aren't blocked by sealed bulkheads"""
        open_connections = []
        for connected_node, bulkhead_name in node.connections:
            if bulkhead_name is None:
                # No bulkhead, always open
                open_connections.append(connected_node)
            elif bulkhead_name not in bulkheads or not bulkheads[bulkhead_name].sealed:
                # Bulkhead exists but not sealed, or doesn't exist
                open_connections.append(connected_node)
        return open_connections
    
    def find_path_bfs(self, target_node, bulkheads):
        """Find shortest path using BFS, respecting sealed bulkheads"""
        if self.current_node == target_node:
            return []
        
        visited = {self.current_node}
        queue = [(self.current_node, [])]
        
        while queue:
            node, path = queue.pop(0)
            
            for next_node in self.get_open_connections(node, bulkheads):
                if next_node == target_node:
                    return path + [next_node]
                
                if next_node not in visited:
                    visited.add(next_node)
                    queue.append((next_node, path + [next_node]))
        
        return None  # No path found
    
    def choose_destination(self, all_nodes, bulkheads, hunting):
        """Choose where to go next"""
        if hunting:
            # Try to reach the bridge
            return self.bridge_node
        else:
            # Wander to a random accessible room (not waypoints or cargo)
            valid_targets = [n for n in all_nodes 
                           if n.name not in ['waypoint', 'cargo'] 
                           and n != self.current_node]
            
            if valid_targets:
                return random.choice(valid_targets)
            return None
    
    def update(self, all_nodes, bulkheads, player_pos):
        """Update alien position and behavior"""
        
        # Determine if hunting based on distance to player
        dist_to_player = math.hypot(self.x - player_pos[0], self.y - player_pos[1])
        hunting = dist_to_player < 400
        
        # State: BLOCKED - trying to get through sealed bulkhead
        if self.state == 'blocked':
            self.blocked_timer -= 1
            # Prowl near the blocked position
            offset = math.sin(pygame.time.get_ticks() / 400) * 10
            if self.blocked_position:
                self.x = self.blocked_position[0] + offset
                self.y = self.blocked_position[1]
            
            if self.blocked_timer <= 0:
                self.state = 'idle'
                self.blocked_position = None
                self.idle_timer = 60
            return
        
        # State: IDLE - waiting/thinking
        if self.state == 'idle':
            self.idle_timer -= 1
            if self.idle_timer <= 0:
                self.state = 'choosing'
            return
        
        # State: CHOOSING - pick new destination
        if self.state == 'choosing':
            destination = self.choose_destination(all_nodes, bulkheads, hunting)
            if destination:
                new_path = self.find_path_bfs(destination, bulkheads)
                if new_path:
                    self.path = new_path
                    self.state = 'moving'
                else:
                    # Path blocked - investigate the blockage
                    self.state = 'blocked'
                    self.blocked_timer = 120
                    self.blocked_position = (self.x, self.y)
            else:
                # No valid destinations
                self.state = 'idle'
                self.idle_timer = 90
            return
        
        # State: MOVING - follow the path
        if self.state == 'moving':
            if not self.path:
                # Reached destination
                self.state = 'idle'
                self.idle_timer = random.randint(40, 100) if not hunting else 20
                return
            
            # Get next waypoint
            next_node = self.path[0]
            dx = next_node.x - self.x
            dy = next_node.y - self.y
            distance = math.hypot(dx, dy)
            
            # Check if we've reached this waypoint
            if distance < 2.0:
                self.current_node = next_node
                self.x = float(next_node.x)
                self.y = float(next_node.y)
                self.path.pop(0)
                
                # Check if next step in path is blocked
                if self.path:
                    next_next = self.path[0]
                    if next_next not in self.get_open_connections(self.current_node, bulkheads):
                        # Path blocked mid-journey
                        self.path = []
                        self.state = 'blocked'
                        self.blocked_timer = 150
                        self.blocked_position = (self.x, self.y)
                return
            
            # Move toward next waypoint
            speed = self.move_speed * (2.0 if hunting else 1.0)
            self.x += (dx / distance) * speed
            self.y += (dy / distance) * speed
    
    def draw(self, surface):
        """Draw the alien as a pulsing diamond"""
        pulse = math.sin(pygame.time.get_ticks() / 200) * 2 + 10
        
        # Larger pulse when hunting or blocked
        if self.state == 'blocked':
            pulse += 2
            color = BRIGHT_GREEN
        else:
            color = BRIGHT_GREEN if self.state == 'moving' else TERMINAL_GREEN
        
        # Diamond shape
        points = [
            (self.x, self.y - pulse),
            (self.x + pulse, self.y),
            (self.x, self.y + pulse),
            (self.x - pulse, self.y)
        ]
        pygame.draw.polygon(surface, color, points)
        pygame.draw.polygon(surface, BRIGHT_GREEN, points, 2)
        
        # Scanning ring
        if (pygame.time.get_ticks() // 300) % 2 == 0:
            pygame.draw.circle(surface, color, (int(self.x), int(self.y)), int(pulse + 5), 1)

def draw_corridor(surface, x1, y1, x2, y2, width=35):
    """Draw straight corridors (horizontal or vertical only)"""
    if abs(y1 - y2) < 5:
        y = (y1 + y2) // 2
        pygame.draw.line(surface, TERMINAL_GREEN, (x1, y - width//2), (x2, y - width//2), 2)
        pygame.draw.line(surface, TERMINAL_GREEN, (x1, y + width//2), (x2, y + width//2), 2)
    elif abs(x1 - x2) < 5:
        x = (x1 + x2) // 2
        pygame.draw.line(surface, TERMINAL_GREEN, (x - width//2, y1), (x - width//2, y2), 2)
        pygame.draw.line(surface, TERMINAL_GREEN, (x + width//2, y1), (x + width//2, y2), 2)

def run_airlock_puzzle(player_name):
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("MUTHER - AIRLOCK PROTOCOL")
    
    font_large, font_medium, font_small = load_fonts()
    clock = pygame.time.Clock()
    
    # Room layout
    rooms = {
        'bridge': Room('BRIDGE', 'angular', 40, 40, 140, 100),
        'galley': Room('GALLEY', 'rect', 240, 50, 120, 80),
        'medbay': Room('MEDBAY', 'hex', 420, 40, 140, 100),
        'hypersleep': Room('HYPERSLEEP', 'circular', 620, 40, 130, 100),
        'engineering': Room('ENGINE', 'circular', 80, 240, 160, 120),
        'crew': Room('CREW', 'rect', 320, 260, 120, 80),
        'reactor': Room('REACTOR', 'octagon', 520, 250, 120, 100),
        'cargo': Room('CARGO BAY', 'rect', 80, 440, 600, 150),
    }
    
    # Path nodes for alien navigation
    nodes = {
        'bridge': PathNode(110, 90, 'bridge'),
        'galley': PathNode(300, 90, 'galley'),
        'medbay': PathNode(490, 90, 'medbay'),
        'hypersleep': PathNode(685, 90, 'hypersleep'),
        'engineering': PathNode(160, 300, 'engineering'),
        'crew': PathNode(380, 300, 'crew'),
        'reactor': PathNode(580, 300, 'reactor'),
        'cargo_left': PathNode(160, 515, 'cargo'),
        'cargo_center': PathNode(380, 515, 'cargo'),
        'cargo_right': PathNode(580, 515, 'cargo'),
    }
    
    bulkheads = {
        'B0': Bulkhead('B0', 195, 90, 'v'),
        'B1': Bulkhead('B1', 365, 90, 'v'),
        'B2': Bulkhead('B2', 555, 90, 'v'),
        'B3': Bulkhead('B3', 160, 405, 'h'),
        'B4': Bulkhead('B4', 380, 405, 'h'),
        'B5': Bulkhead('B5', 580, 405, 'h'),
        'B6': Bulkhead('B6', 300, 195, 'h'),  # Galley descent
        'B7': Bulkhead('B7', 490, 195, 'h'),  # Medbay descent
    }
    
    # Build the graph with waypoint nodes at corridor junctions
    waypoint_bridge_out = PathNode(180, 90, 'waypoint')
    waypoint_galley_out_right = PathNode(360, 90, 'waypoint')
    waypoint_galley_down = PathNode(300, 130, 'waypoint')
    waypoint_galley_mid = PathNode(300, 195, 'waypoint')
    waypoint_medbay_out = PathNode(560, 90, 'waypoint')
    waypoint_medbay_down = PathNode(490, 140, 'waypoint')
    waypoint_medbay_mid = PathNode(490, 195, 'waypoint')
    waypoint_eng_out = PathNode(240, 300, 'waypoint')
    waypoint_crew_out_right = PathNode(440, 300, 'waypoint')
    waypoint_eng_down = PathNode(160, 360, 'waypoint')
    waypoint_crew_down = PathNode(380, 340, 'waypoint')
    waypoint_reactor_down = PathNode(580, 350, 'waypoint')
    
    # Top horizontal corridor
    nodes['bridge'].add_connection(waypoint_bridge_out)
    waypoint_bridge_out.add_connection(nodes['galley'], 'B0')
    
    nodes['galley'].add_connection(waypoint_galley_out_right)
    waypoint_galley_out_right.add_connection(nodes['medbay'], 'B1')
    
    nodes['medbay'].add_connection(waypoint_medbay_out)
    waypoint_medbay_out.add_connection(nodes['hypersleep'], 'B2')
    
    # Vertical drops with bulkheads
    nodes['galley'].add_connection(waypoint_galley_down)
    waypoint_galley_down.add_connection(waypoint_galley_mid)
    waypoint_galley_mid.add_connection(nodes['crew'], 'B6')
    
    nodes['medbay'].add_connection(waypoint_medbay_down)
    waypoint_medbay_down.add_connection(waypoint_medbay_mid)
    waypoint_medbay_mid.add_connection(nodes['crew'], 'B7')
    
    # Middle horizontal corridor
    nodes['engineering'].add_connection(waypoint_eng_out)
    waypoint_eng_out.add_connection(nodes['crew'])
    
    nodes['crew'].add_connection(waypoint_crew_out_right)
    waypoint_crew_out_right.add_connection(nodes['reactor'])
    
    # Drops to cargo
    nodes['engineering'].add_connection(waypoint_eng_down)
    waypoint_eng_down.add_connection(nodes['cargo_left'], 'B3')
    
    nodes['crew'].add_connection(waypoint_crew_down)
    waypoint_crew_down.add_connection(nodes['cargo_center'], 'B4')
    
    nodes['reactor'].add_connection(waypoint_reactor_down)
    waypoint_reactor_down.add_connection(nodes['cargo_right'], 'B5')
    
    # Cargo internal
    nodes['cargo_left'].add_connection(nodes['cargo_center'])
    nodes['cargo_center'].add_connection(nodes['cargo_right'])
    
    # All nodes for pathfinding
    all_navigation_nodes = list(nodes.values()) + [
        waypoint_bridge_out, waypoint_galley_out_right, waypoint_galley_down, waypoint_galley_mid,
        waypoint_medbay_out, waypoint_medbay_down, waypoint_medbay_mid, waypoint_eng_out,
        waypoint_crew_out_right, waypoint_eng_down, waypoint_crew_down, waypoint_reactor_down
    ]
    
    # Initialize alien - start at hypersleep
    alien = Alien(nodes['hypersleep'], nodes['bridge'])
    
    # Game state
    game_won = game_over = cargo_sealed = False
    command_input = ""
    command_history = []
    error_message = ""
    message_timer = 0
    win_timer = 0
    player_pos = (110, 90)
    
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
                            if bh in ['B3', 'B4', 'B5']:
                                if all(bulkheads[b].sealed for b in ['B3', 'B4', 'B5']):
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
                            if target in ['B3', 'B4', 'B5']:
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
            alien.update(all_navigation_nodes, bulkheads, player_pos)
            if alien.current_node.name == 'bridge':
                game_over = True
        
        if game_won and pygame.time.get_ticks() > win_timer:
            running = False
        
        if message_timer and pygame.time.get_ticks() > message_timer:
            error_message = ""
            message_timer = 0
        
        screen.fill(TERMINAL_BLACK)
        
        # Draw corridors
        draw_corridor(screen, 180, 90, 240, 90)
        draw_corridor(screen, 360, 90, 420, 90)
        draw_corridor(screen, 560, 90, 620, 90)
        draw_corridor(screen, 300, 130, 300, 260)
        draw_corridor(screen, 490, 140, 490, 260)
        draw_corridor(screen, 240, 300, 320, 300)
        draw_corridor(screen, 440, 300, 520, 300)
        draw_corridor(screen, 160, 360, 160, 440)
        draw_corridor(screen, 380, 340, 380, 440)
        draw_corridor(screen, 580, 350, 580, 440)
        
        # Draw rooms
        for room in rooms.values():
            room.draw(screen, font_small)
        
        # Player indicator
        pygame.draw.circle(screen, BRIGHT_GREEN, player_pos, 7)
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            pygame.draw.circle(screen, BRIGHT_GREEN, player_pos, 12, 2)
        
        # Visual details
        screen.blit(font_medium.render('⚕', True, TERMINAL_GREEN), (485, 85))
        screen.blit(font_medium.render('⚠ ⚠', True, BRIGHT_GREEN), (540, 295))
        for i in range(3):
            color = BRIGHT_GREEN if (pygame.time.get_ticks() // 400) % 2 else TERMINAL_GREEN
            pygame.draw.circle(screen, color, (570 + i * 20, 300), 7)
        
        # Cargo crates
        for i in range(20):
            pygame.draw.rect(screen, DIM_GREEN, (100 + i * 28, 480, 15, 15))
            pygame.draw.rect(screen, DIM_GREEN, (100 + i * 28, 550, 15, 15))
        
        # Airlock
        airlock_color = BRIGHT_GREEN if cargo_sealed else DIM_GREEN
        airlock_points = [(600, 510), (650, 510), (660, 525), (650, 540), (600, 540)]
        pygame.draw.polygon(screen, airlock_color, airlock_points, 3)
        screen.blit(font_small.render('AIRLOCK', True, airlock_color), (605, 520))
        
        # Bulkheads and alien
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
        
        # Help text
        help_lines = [
            'COMMANDS:', 
            'SEAL B0-B7', 
            'OPEN B0-B7', 
            'OPEN AIRLOCK', 
            '',
            'Seal B0 to protect bridge',
            'Control descent routes (B6/B7)',
            'Herd alien to cargo bay',
            'Seal B3, B4, B5',
            'Then open airlock'
        ]
        for i, line in enumerate(help_lines):
            screen.blit(font_small.render(line, True, DIM_GREEN), (ui_x, HEIGHT - 220 + i * 20))
        
        # Overlays
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
Still passing through bulkheads and floating diagonally. Asking Claude to delete movement code and start again.

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
#         else:
#             pygame.draw.line(surface, color, (self.x - 18, self.y), (self.x + 18, self.y), width)
#             pygame.draw.line(surface, color, (self.x - 18, self.y + 5), (self.x + 18, self.y + 5), width)
#             label = font_small.render(self.name, True, color)
#             surface.blit(label, (self.x + 25, self.y - 2))

# class Alien:
#     def __init__(self, start_node):
#         self.current_node = start_node
#         self.target_node = None
#         self.x = float(start_node.x)
#         self.y = float(start_node.y)
#         self.trail = []
#         self.speed = 1.0
#         self.path = []
#         self.hunting = False
#         self.bridge_node = None
#         self.wait_timer = 120  # Start with initial wait
#         self.investigating_timer = 0
#         self.blocked_bulkhead = None
#         self.investigation_offset = 0
    
#     def find_path(self, target_node, bulkheads):
#         """BFS pathfinding that respects sealed bulkheads"""
#         if self.current_node == target_node:
#             return []
        
#         queue = [(self.current_node, [])]
#         visited = {self.current_node}
        
#         while queue:
#             current, path = queue.pop(0)
            
#             for next_node, bulkhead_name in current.connections:
#                 # Skip if bulkhead is sealed
#                 if bulkhead_name and bulkhead_name in bulkheads:
#                     if bulkheads[bulkhead_name].sealed:
#                         continue
                
#                 if next_node == target_node:
#                     return path + [next_node]
                
#                 if next_node not in visited:
#                     visited.add(next_node)
#                     queue.append((next_node, path + [next_node]))
        
#         return []
    
#     def find_closest_accessible_node(self, target_node, all_nodes, bulkheads):
#         """Find the closest node we can actually reach"""
#         reachable = set()
#         queue = [self.current_node]
#         visited = {self.current_node}
        
#         while queue:
#             current = queue.pop(0)
#             reachable.add(current)
            
#             for next_node, bulkhead_name in current.connections:
#                 if bulkhead_name and bulkhead_name in bulkheads:
#                     if bulkheads[bulkhead_name].sealed:
#                         # Store the blocked bulkhead for investigation
#                         self.blocked_bulkhead = bulkhead_name
#                         continue
                
#                 if next_node not in visited:
#                     visited.add(next_node)
#                     queue.append(next_node)
        
#         # Find closest reachable node to target (excluding waypoints for destination)
#         best_node = None
#         best_dist = float('inf')
        
#         for node in reachable:
#             if node.name != 'waypoint':
#                 dist = math.hypot(node.x - target_node.x, node.y - target_node.y)
#                 if dist < best_dist:
#                     best_dist = dist
#                     best_node = node
        
#         return best_node
    
#     def update(self, all_nodes, bulkheads, player_pos):
#         dist_to_player = math.hypot(self.x - player_pos[0], self.y - player_pos[1])
        
#         # Wait timer handling
#         if self.wait_timer > 0:
#             self.wait_timer -= 1
#             return
        
#         # Investigating sealed bulkhead animation
#         if self.investigating_timer > 0:
#             self.investigating_timer -= 1
            
#             # Subtle prowling movement
#             self.investigation_offset = math.sin(pygame.time.get_ticks() / 300) * 8
            
#             if self.investigating_timer == 0:
#                 self.blocked_bulkhead = None
#                 self.investigation_offset = 0
#                 self.wait_timer = 90
#                 self.path = []  # Clear path after investigation
#             return
        
#         # Hunt the player when close enough
#         if dist_to_player < 350:
#             self.hunting = True
#             target = self.bridge_node
#         else:
#             self.hunting = False
#             target = None
        
#         # Need new path?
#         if not self.path and self.wait_timer == 0:
#             if target:
#                 # Try to reach target
#                 new_path = self.find_path(target, bulkheads)
#                 if new_path:
#                     self.path = new_path
#                     self.target_node = target
#                 else:
#                     # Blocked - find closest accessible point
#                     closest = self.find_closest_accessible_node(target, all_nodes, bulkheads)
#                     if closest and closest != self.current_node:
#                         new_path = self.find_path(closest, bulkheads)
#                         if new_path:
#                             self.path = new_path
#                             self.target_node = closest
#                         else:
#                             # Already at closest point - investigate
#                             self.investigating_timer = 180
#                     else:
#                         # At closest point - investigate the blockage
#                         self.investigating_timer = 180
#             else:
#                 # Wander - pick random accessible room
#                 valid_nodes = [n for n in all_nodes 
#                               if n.name not in ['cargo', 'waypoint'] 
#                               and n != self.current_node]
                
#                 if valid_nodes:
#                     # Try up to 5 random targets
#                     for _ in range(5):
#                         target = random.choice(valid_nodes)
#                         new_path = self.find_path(target, bulkheads)
#                         if new_path:
#                             self.path = new_path
#                             self.target_node = target
#                             break
                    
#                     if not self.path:
#                         # All paths blocked - wait
#                         self.wait_timer = 120
        
#         # Follow the path smoothly
#         if self.path:
#             next_node = self.path[0]
#             dx = next_node.x - self.x
#             dy = next_node.y - self.y
#             dist = math.hypot(dx, dy)
            
#             # Threshold for reaching node - smaller for precision
#             reach_threshold = 3.0
            
#             if dist < reach_threshold:
#                 # Reached node - update current node
#                 self.current_node = next_node
#                 self.x = float(next_node.x)
#                 self.y = float(next_node.y)
#                 self.path.pop(0)
                
#                 # If finished path and at a room (not waypoint), pause
#                 if not self.path:
#                     if self.current_node.name not in ['waypoint', 'cargo']:
#                         self.wait_timer = random.randint(60, 120)
#                     elif not self.hunting:
#                         self.wait_timer = 30
#             else:
#                 # Move smoothly toward next node
#                 speed = self.speed * 2.2 if self.hunting else self.speed * 1.2
#                 move_x = (dx / dist) * speed
#                 move_y = (dy / dist) * speed
                
#                 # Don't overshoot
#                 if abs(move_x) > abs(dx):
#                     move_x = dx
#                 if abs(move_y) > abs(dy):
#                     move_y = dy
                
#                 self.x += move_x
#                 self.y += move_y
        
#         # Trail effect - only add if moved significantly
#         if not self.trail or math.hypot(self.x - self.trail[-1][0], self.y - self.trail[-1][1]) > 3:
#             self.trail.append((self.x, self.y))
#             if len(self.trail) > 25:
#                 self.trail.pop(0)
    
#     def draw(self, surface):
#         # Draw trail
#         if len(self.trail) > 1:
#             for i in range(len(self.trail) - 1):
#                 alpha = int((i / len(self.trail)) * 120)
#                 start = self.trail[i]
#                 end = self.trail[i + 1]
#                 pygame.draw.line(surface, (0, alpha, 0), start, end, 3)
        
#         # Draw alien with investigation offset
#         display_x = self.x + self.investigation_offset
#         display_y = self.y
        
#         pulse = math.sin(pygame.time.get_ticks() / 200) * 2 + 9
#         if self.hunting:
#             pulse += 3
#         if self.investigating_timer > 0:
#             pulse += math.sin(pygame.time.get_ticks() / 150) * 2
        
#         points = [
#             (display_x, display_y - pulse),
#             (display_x + pulse, display_y),
#             (display_x, display_y + pulse),
#             (display_x - pulse, display_y)
#         ]
#         color = BRIGHT_GREEN if self.hunting else TERMINAL_GREEN
#         pygame.draw.polygon(surface, color, points)
#         pygame.draw.polygon(surface, BRIGHT_GREEN, points, 2)
        
#         if (pygame.time.get_ticks() // 300) % 2 == 0:
#             pygame.draw.circle(surface, BRIGHT_GREEN, (int(display_x), int(display_y)), int(pulse + 6), 1)

# def draw_corridor(surface, x1, y1, x2, y2, width=35):
#     """Draw straight corridors (horizontal or vertical only)"""
#     if abs(y1 - y2) < 5:
#         y = (y1 + y2) // 2
#         pygame.draw.line(surface, TERMINAL_GREEN, (x1, y - width//2), (x2, y - width//2), 2)
#         pygame.draw.line(surface, TERMINAL_GREEN, (x1, y + width//2), (x2, y + width//2), 2)
#     elif abs(x1 - x2) < 5:
#         x = (x1 + x2) // 2
#         pygame.draw.line(surface, TERMINAL_GREEN, (x - width//2, y1), (x - width//2, y2), 2)
#         pygame.draw.line(surface, TERMINAL_GREEN, (x + width//2, y1), (x + width//2, y2), 2)

# def run_airlock_puzzle(player_name):
#     pygame.init()
#     screen = pygame.display.set_mode((WIDTH, HEIGHT))
#     pygame.display.set_caption("MUTHER - AIRLOCK PROTOCOL")
    
#     font_large, font_medium, font_small = load_fonts()
#     clock = pygame.time.Clock()
    
#     # Room layout
#     rooms = {
#         'bridge': Room('BRIDGE', 'angular', 40, 40, 140, 100),
#         'galley': Room('GALLEY', 'rect', 240, 50, 120, 80),
#         'medbay': Room('MEDBAY', 'hex', 420, 40, 140, 100),
#         'hypersleep': Room('HYPERSLEEP', 'circular', 620, 40, 130, 100),
#         'engineering': Room('ENGINE', 'circular', 80, 240, 160, 120),
#         'crew': Room('CREW', 'rect', 320, 260, 120, 80),
#         'reactor': Room('REACTOR', 'octagon', 520, 250, 120, 100),
#         'cargo': Room('CARGO BAY', 'rect', 80, 440, 600, 150),
#     }
    
#     # Path nodes for alien navigation
#     nodes = {
#         'bridge': PathNode(110, 90, 'bridge'),
#         'galley': PathNode(300, 90, 'galley'),
#         'medbay': PathNode(490, 90, 'medbay'),
#         'hypersleep': PathNode(685, 90, 'hypersleep'),
#         'engineering': PathNode(160, 300, 'engineering'),
#         'crew': PathNode(380, 300, 'crew'),
#         'reactor': PathNode(580, 300, 'reactor'),
#         'cargo_left': PathNode(160, 515, 'cargo'),
#         'cargo_center': PathNode(380, 515, 'cargo'),
#         'cargo_right': PathNode(580, 515, 'cargo'),
#     }
    
#     bulkheads = {
#         'B0': Bulkhead('B0', 195, 90, 'v'),
#         'B1': Bulkhead('B1', 365, 90, 'v'),
#         'B2': Bulkhead('B2', 555, 90, 'v'),
#         'B3': Bulkhead('B3', 160, 405, 'h'),
#         'B4': Bulkhead('B4', 380, 405, 'h'),
#         'B5': Bulkhead('B5', 580, 405, 'h'),
#         'B6': Bulkhead('B6', 300, 195, 'h'),  # Galley descent
#         'B7': Bulkhead('B7', 490, 195, 'h'),  # Medbay descent
#     }
    
#     # Build the graph with waypoint nodes at corridor junctions
#     waypoint_bridge_out = PathNode(180, 90, 'waypoint')
#     waypoint_galley_out_right = PathNode(360, 90, 'waypoint')
#     waypoint_galley_down = PathNode(300, 130, 'waypoint')
#     waypoint_galley_mid = PathNode(300, 195, 'waypoint')
#     waypoint_medbay_out = PathNode(560, 90, 'waypoint')
#     waypoint_medbay_down = PathNode(490, 140, 'waypoint')
#     waypoint_medbay_mid = PathNode(490, 195, 'waypoint')
#     waypoint_eng_out = PathNode(240, 300, 'waypoint')
#     waypoint_crew_out_right = PathNode(440, 300, 'waypoint')
#     waypoint_eng_down = PathNode(160, 360, 'waypoint')
#     waypoint_crew_down = PathNode(380, 340, 'waypoint')
#     waypoint_reactor_down = PathNode(580, 350, 'waypoint')
    
#     # Top horizontal corridor
#     nodes['bridge'].add_connection(waypoint_bridge_out)
#     waypoint_bridge_out.add_connection(nodes['galley'], 'B0')
    
#     nodes['galley'].add_connection(waypoint_galley_out_right)
#     waypoint_galley_out_right.add_connection(nodes['medbay'], 'B1')
    
#     nodes['medbay'].add_connection(waypoint_medbay_out)
#     waypoint_medbay_out.add_connection(nodes['hypersleep'], 'B2')
    
#     # Vertical drops with NEW bulkheads
#     nodes['galley'].add_connection(waypoint_galley_down)
#     waypoint_galley_down.add_connection(waypoint_galley_mid)
#     waypoint_galley_mid.add_connection(nodes['crew'], 'B6')  # B6 on galley descent
    
#     nodes['medbay'].add_connection(waypoint_medbay_down)
#     waypoint_medbay_down.add_connection(waypoint_medbay_mid)
#     waypoint_medbay_mid.add_connection(nodes['crew'], 'B7')  # B7 on medbay descent
    
#     # Middle horizontal corridor
#     nodes['engineering'].add_connection(waypoint_eng_out)
#     waypoint_eng_out.add_connection(nodes['crew'])
    
#     nodes['crew'].add_connection(waypoint_crew_out_right)
#     waypoint_crew_out_right.add_connection(nodes['reactor'])
    
#     # Drops to cargo
#     nodes['engineering'].add_connection(waypoint_eng_down)
#     waypoint_eng_down.add_connection(nodes['cargo_left'], 'B3')
    
#     nodes['crew'].add_connection(waypoint_crew_down)
#     waypoint_crew_down.add_connection(nodes['cargo_center'], 'B4')
    
#     nodes['reactor'].add_connection(waypoint_reactor_down)
#     waypoint_reactor_down.add_connection(nodes['cargo_right'], 'B5')
    
#     # Cargo internal
#     nodes['cargo_left'].add_connection(nodes['cargo_center'])
#     nodes['cargo_center'].add_connection(nodes['cargo_right'])
    
#     # All nodes
#     all_navigation_nodes = list(nodes.values()) + [
#         waypoint_bridge_out, waypoint_galley_out_right, waypoint_galley_down, waypoint_galley_mid,
#         waypoint_medbay_out, waypoint_medbay_down, waypoint_medbay_mid, waypoint_eng_out,
#         waypoint_crew_out_right, waypoint_eng_down, waypoint_crew_down, waypoint_reactor_down
#     ]
    
#     # Initialize alien - start at reactor
#     alien = Alien(nodes['reactor'])
#     alien.bridge_node = nodes['bridge']
    
#     # Game state
#     game_won = game_over = cargo_sealed = False
#     command_input = ""
#     command_history = []
#     error_message = ""
#     message_timer = 0
#     win_timer = 0
#     player_pos = (110, 90)
    
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
#                             if bh in ['B3', 'B4', 'B5']:
#                                 if all(bulkheads[b].sealed for b in ['B3', 'B4', 'B5']):
#                                     cargo_sealed = True
#                                     command_history.append("CARGO BAY ISOLATED")
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
#                             if target in ['B3', 'B4', 'B5']:
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
#             alien.update(all_navigation_nodes, bulkheads, player_pos)
#             if alien.current_node.name == 'bridge':
#                 game_over = True
        
#         if game_won and pygame.time.get_ticks() > win_timer:
#             running = False
        
#         if message_timer and pygame.time.get_ticks() > message_timer:
#             error_message = ""
#             message_timer = 0
        
#         screen.fill(TERMINAL_BLACK)
        
#         # Draw corridors
#         draw_corridor(screen, 180, 90, 240, 90)
#         draw_corridor(screen, 360, 90, 420, 90)
#         draw_corridor(screen, 560, 90, 620, 90)
#         draw_corridor(screen, 300, 130, 300, 260)
#         draw_corridor(screen, 490, 140, 490, 260)
#         draw_corridor(screen, 240, 300, 320, 300)
#         draw_corridor(screen, 440, 300, 520, 300)
#         draw_corridor(screen, 160, 360, 160, 440)
#         draw_corridor(screen, 380, 340, 380, 440)
#         draw_corridor(screen, 580, 350, 580, 440)
        
#         # Draw rooms
#         for room in rooms.values():
#             room.draw(screen, font_small)
        
#         # Player indicator
#         pygame.draw.circle(screen, BRIGHT_GREEN, player_pos, 7)
#         if (pygame.time.get_ticks() // 500) % 2 == 0:
#             pygame.draw.circle(screen, BRIGHT_GREEN, player_pos, 12, 2)
        
#         # Visual details
#         screen.blit(font_medium.render('⚕', True, TERMINAL_GREEN), (485, 85))
#         screen.blit(font_medium.render('⚠ ⚠', True, BRIGHT_GREEN), (540, 295))
#         for i in range(3):
#             color = BRIGHT_GREEN if (pygame.time.get_ticks() // 400) % 2 else TERMINAL_GREEN
#             pygame.draw.circle(screen, color, (570 + i * 20, 300), 7)
        
#         # Cargo crates
#         for i in range(20):
#             pygame.draw.rect(screen, DIM_GREEN, (100 + i * 28, 480, 15, 15))
#             pygame.draw.rect(screen, DIM_GREEN, (100 + i * 28, 550, 15, 15))
        
#         # Airlock
#         airlock_color = BRIGHT_GREEN if cargo_sealed else DIM_GREEN
#         airlock_points = [(600, 510), (650, 510), (660, 525), (650, 540), (600, 540)]
#         pygame.draw.polygon(screen, airlock_color, airlock_points, 3)
#         screen.blit(font_small.render('AIRLOCK', True, airlock_color), (605, 520))
        
#         # Bulkheads and alien
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
        
#         # Help text
#         help_lines = [
#             'COMMANDS:', 
#             'SEAL B0-B7', 
#             'OPEN B0-B7', 
#             'OPEN AIRLOCK', 
#             '',
#             'Seal B0 to protect bridge',
#             'Control descent routes (B6/B7)',
#             'Herd alien to cargo bay',
#             'Seal B3, B4, B5',
#             'Then open airlock'
#         ]
#         for i, line in enumerate(help_lines):
#             screen.blit(font_small.render(line, True, DIM_GREEN), (ui_x, HEIGHT - 220 + i * 20))
        
#         # Overlays
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
Teleporting problems and trail weirdness.
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
#         else:
#             pygame.draw.line(surface, color, (self.x - 18, self.y), (self.x + 18, self.y), width)
#             pygame.draw.line(surface, color, (self.x - 18, self.y + 5), (self.x + 18, self.y + 5), width)
#             label = font_small.render(self.name, True, color)
#             surface.blit(label, (self.x + 25, self.y - 2))

# class Alien:
#     def __init__(self, start_node):
#         self.current_node = start_node
#         self.x = start_node.x
#         self.y = start_node.y
#         self.trail = []
#         self.speed = 1.2
#         self.path = []
#         self.hunting = False
#         self.bridge_node = None
#         self.wait_timer = 0
#         self.investigating_timer = 0
#         self.blocked_bulkhead = None
#         self.last_target = None
    
#     def find_path(self, target_node, bulkheads):
#         """BFS pathfinding that respects sealed bulkheads"""
#         if self.current_node == target_node:
#             return []
        
#         queue = [(self.current_node, [])]
#         visited = {self.current_node}
        
#         while queue:
#             current, path = queue.pop(0)
            
#             for next_node, bulkhead_name in current.connections:
#                 # Skip if bulkhead is sealed
#                 if bulkhead_name and bulkhead_name in bulkheads:
#                     if bulkheads[bulkhead_name].sealed:
#                         continue
                
#                 if next_node == target_node:
#                     return path + [next_node]
                
#                 if next_node not in visited:
#                     visited.add(next_node)
#                     queue.append((next_node, path + [next_node]))
        
#         return []
    
#     def find_path_to_blocked_bulkhead(self, target_node, bulkheads):
#         """Find path as close as possible to target, stopping at sealed bulkheads"""
#         if self.current_node == target_node:
#             return []
        
#         queue = [(self.current_node, [], None)]
#         visited = {self.current_node}
#         closest_path = []
#         closest_dist = float('inf')
        
#         while queue:
#             current, path, blocked_by = queue.pop(0)
            
#             # Calculate distance from current to target
#             dist = math.hypot(current.x - target_node.x, current.y - target_node.y)
#             if dist < closest_dist:
#                 closest_dist = dist
#                 closest_path = path
#                 self.blocked_bulkhead = blocked_by
            
#             for next_node, bulkhead_name in current.connections:
#                 if next_node not in visited:
#                     # If bulkhead is sealed, record it but don't traverse
#                     if bulkhead_name and bulkhead_name in bulkheads:
#                         if bulkheads[bulkhead_name].sealed:
#                             # This is as far as we can go on this route
#                             dist = math.hypot(current.x - target_node.x, current.y - target_node.y)
#                             if dist < closest_dist:
#                                 closest_dist = dist
#                                 closest_path = path
#                                 self.blocked_bulkhead = bulkhead_name
#                             continue
                    
#                     visited.add(next_node)
#                     queue.append((next_node, path + [next_node], blocked_by))
        
#         return closest_path
    
#     def update(self, all_nodes, bulkheads, player_pos):
#         dist_to_player = math.hypot(self.x - player_pos[0], self.y - player_pos[1])
        
#         # Wait timer handling
#         if self.wait_timer > 0:
#             self.wait_timer -= 1
#             return
        
#         # Investigating sealed bulkhead animation
#         if self.investigating_timer > 0:
#             self.investigating_timer -= 1
#             # Slight movement near bulkhead to show investigation
#             if self.blocked_bulkhead and self.blocked_bulkhead in bulkheads:
#                 bh = bulkheads[self.blocked_bulkhead]
#                 offset = math.sin(pygame.time.get_ticks() / 200) * 5
#                 if bh.orientation == 'v':
#                     target_x = bh.x - 30
#                     self.x += (target_x - self.x) * 0.1
#                 else:
#                     target_y = bh.y - 30
#                     self.y += (target_y - self.y) * 0.1
            
#             if self.investigating_timer == 0:
#                 self.blocked_bulkhead = None
#                 self.wait_timer = 30
#             return
        
#         # Hunt the player when close enough
#         if dist_to_player < 300:
#             self.hunting = True
            
#             # Try to path to bridge
#             if self.bridge_node and (not self.path or self.last_target != self.bridge_node):
#                 new_path = self.find_path(self.bridge_node, bulkheads)
#                 if new_path:
#                     self.path = new_path
#                     self.last_target = self.bridge_node
#                 else:
#                     # Can't reach bridge - path to closest point
#                     close_path = self.find_path_to_blocked_bulkhead(self.bridge_node, bulkheads)
#                     if close_path:
#                         self.path = close_path
#                         self.last_target = self.bridge_node
#                     else:
#                         # Already at closest point, investigate the blockage
#                         self.investigating_timer = 90
#                         self.wait_timer = 0
#         else:
#             # Wander behavior when not hunting
#             self.hunting = False
            
#             if not self.path:
#                 # Pick random valid room (not cargo or waypoints)
#                 valid_nodes = [n for n in all_nodes 
#                               if n.name not in ['cargo', 'waypoint'] 
#                               and n != self.current_node]
                
#                 if valid_nodes:
#                     target = random.choice(valid_nodes)
#                     new_path = self.find_path(target, bulkheads)
                    
#                     if new_path:
#                         self.path = new_path
#                         self.last_target = target
#                     else:
#                         # Try to get as close as possible
#                         close_path = self.find_path_to_blocked_bulkhead(target, bulkheads)
#                         if close_path:
#                             self.path = close_path
#                             self.last_target = target
#                         else:
#                             self.wait_timer = 60
        
#         # Follow the path
#         if self.path:
#             next_node = self.path[0]
#             dx = next_node.x - self.x
#             dy = next_node.y - self.y
#             dist = math.hypot(dx, dy)
            
#             if dist < 2:
#                 # Reached node - snap to it
#                 self.current_node = next_node
#                 self.x = next_node.x
#                 self.y = next_node.y
#                 self.path.pop(0)
                
#                 # Check if next node in path is blocked
#                 if self.path:
#                     next_in_path = self.path[0]
#                     for connected_node, bulkhead_name in self.current_node.connections:
#                         if connected_node == next_in_path and bulkhead_name:
#                             if bulkhead_name in bulkheads and bulkheads[bulkhead_name].sealed:
#                                 # Hit a sealed bulkhead - investigate it
#                                 self.blocked_bulkhead = bulkhead_name
#                                 self.investigating_timer = 120
#                                 self.path = []
#                                 break
                
#                 # Wait briefly at rooms (not waypoints)
#                 if not self.path and self.current_node.name not in ['waypoint', 'cargo']:
#                     self.wait_timer = random.randint(40, 80)
#             else:
#                 # Move toward node
#                 speed = self.speed * 1.8 if self.hunting else self.speed
#                 self.x += (dx / dist) * speed
#                 self.y += (dy / dist) * speed
        
#         # Trail effect
#         self.trail.append((self.x, self.y))
#         if len(self.trail) > 30:
#             self.trail.pop(0)
    
#     def draw(self, surface):
#         # Draw trail
#         if len(self.trail) > 1:
#             for i in range(len(self.trail) - 1):
#                 alpha = int((i / len(self.trail)) * 150)
#                 pygame.draw.line(surface, (0, alpha, 0), self.trail[i], self.trail[i+1], 3)
        
#         # Draw alien
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
#     """Draw straight corridors (horizontal or vertical only)"""
#     if abs(y1 - y2) < 5:
#         y = (y1 + y2) // 2
#         pygame.draw.line(surface, TERMINAL_GREEN, (x1, y - width//2), (x2, y - width//2), 2)
#         pygame.draw.line(surface, TERMINAL_GREEN, (x1, y + width//2), (x2, y + width//2), 2)
#     elif abs(x1 - x2) < 5:
#         x = (x1 + x2) // 2
#         pygame.draw.line(surface, TERMINAL_GREEN, (x - width//2, y1), (x - width//2, y2), 2)
#         pygame.draw.line(surface, TERMINAL_GREEN, (x + width//2, y1), (x + width//2, y2), 2)

# def run_airlock_puzzle(player_name):
#     pygame.init()
#     screen = pygame.display.set_mode((WIDTH, HEIGHT))
#     pygame.display.set_caption("MUTHER - AIRLOCK PROTOCOL")
    
#     font_large, font_medium, font_small = load_fonts()
#     clock = pygame.time.Clock()
    
#     # Room layout
#     rooms = {
#         'bridge': Room('BRIDGE', 'angular', 40, 40, 140, 100),
#         'galley': Room('GALLEY', 'rect', 240, 50, 120, 80),
#         'medbay': Room('MEDBAY', 'hex', 420, 40, 140, 100),
#         'hypersleep': Room('HYPERSLEEP', 'circular', 620, 40, 130, 100),
#         'engineering': Room('ENGINE', 'circular', 80, 240, 160, 120),
#         'crew': Room('CREW', 'rect', 320, 260, 120, 80),
#         'reactor': Room('REACTOR', 'octagon', 520, 250, 120, 100),
#         'cargo': Room('CARGO BAY', 'rect', 80, 440, 600, 150),
#     }
    
#     # Path nodes for alien navigation
#     nodes = {
#         'bridge': PathNode(110, 90, 'bridge'),
#         'galley': PathNode(300, 90, 'galley'),
#         'medbay': PathNode(490, 90, 'medbay'),
#         'hypersleep': PathNode(685, 90, 'hypersleep'),
#         'engineering': PathNode(160, 300, 'engineering'),
#         'crew': PathNode(380, 300, 'crew'),
#         'reactor': PathNode(580, 300, 'reactor'),
#         'cargo_left': PathNode(160, 515, 'cargo'),
#         'cargo_center': PathNode(380, 515, 'cargo'),
#         'cargo_right': PathNode(580, 515, 'cargo'),
#     }
    
#     bulkheads = {
#         'B0': Bulkhead('B0', 195, 90, 'v'),
#         'B1': Bulkhead('B1', 365, 90, 'v'),
#         'B2': Bulkhead('B2', 555, 90, 'v'),
#         'B3': Bulkhead('B3', 160, 405, 'h'),
#         'B4': Bulkhead('B4', 380, 405, 'h'),
#         'B5': Bulkhead('B5', 580, 405, 'h'),
#     }
    
#     # Build the graph with waypoint nodes
#     waypoint_bridge_out = PathNode(180, 90, 'waypoint')
#     waypoint_galley_out_right = PathNode(360, 90, 'waypoint')
#     waypoint_galley_down = PathNode(300, 130, 'waypoint')
#     waypoint_galley_mid = PathNode(300, 195, 'waypoint')
#     waypoint_medbay_out = PathNode(560, 90, 'waypoint')
#     waypoint_medbay_down = PathNode(490, 140, 'waypoint')
#     waypoint_medbay_mid = PathNode(490, 195, 'waypoint')
#     waypoint_eng_out = PathNode(240, 300, 'waypoint')
#     waypoint_crew_out_right = PathNode(440, 300, 'waypoint')
#     waypoint_eng_down = PathNode(160, 360, 'waypoint')
#     waypoint_crew_down = PathNode(380, 340, 'waypoint')
#     waypoint_reactor_down = PathNode(580, 350, 'waypoint')
    
#     # Top level connections
#     nodes['bridge'].add_connection(waypoint_bridge_out)
#     waypoint_bridge_out.add_connection(nodes['galley'], 'B0')
    
#     nodes['galley'].add_connection(waypoint_galley_out_right)
#     waypoint_galley_out_right.add_connection(nodes['medbay'], 'B1')
    
#     nodes['medbay'].add_connection(waypoint_medbay_out)
#     waypoint_medbay_out.add_connection(nodes['hypersleep'], 'B2')
    
#     # Vertical connections
#     nodes['galley'].add_connection(waypoint_galley_down)
#     waypoint_galley_down.add_connection(waypoint_galley_mid)
#     waypoint_galley_mid.add_connection(nodes['crew'])
    
#     nodes['medbay'].add_connection(waypoint_medbay_down)
#     waypoint_medbay_down.add_connection(waypoint_medbay_mid)
#     waypoint_medbay_mid.add_connection(nodes['crew'])
    
#     # Middle level
#     nodes['engineering'].add_connection(waypoint_eng_out)
#     waypoint_eng_out.add_connection(nodes['crew'])
    
#     nodes['crew'].add_connection(waypoint_crew_out_right)
#     waypoint_crew_out_right.add_connection(nodes['reactor'])
    
#     # Cargo connections
#     nodes['engineering'].add_connection(waypoint_eng_down)
#     waypoint_eng_down.add_connection(nodes['cargo_left'], 'B3')
    
#     nodes['crew'].add_connection(waypoint_crew_down)
#     waypoint_crew_down.add_connection(nodes['cargo_center'], 'B4')
    
#     nodes['reactor'].add_connection(waypoint_reactor_down)
#     waypoint_reactor_down.add_connection(nodes['cargo_right'], 'B5')
    
#     # Cargo internal
#     nodes['cargo_left'].add_connection(nodes['cargo_center'])
#     nodes['cargo_center'].add_connection(nodes['cargo_right'])
    
#     # All nodes
#     all_navigation_nodes = list(nodes.values()) + [
#         waypoint_bridge_out, waypoint_galley_out_right, waypoint_galley_down, waypoint_galley_mid,
#         waypoint_medbay_out, waypoint_medbay_down, waypoint_medbay_mid, waypoint_eng_out,
#         waypoint_crew_out_right, waypoint_eng_down, waypoint_crew_down, waypoint_reactor_down
#     ]
    
#     # Initialize alien - start at cargo
#     alien = Alien(nodes['cargo_center'])
#     alien.bridge_node = nodes['bridge']
    
#     # Game state
#     game_won = game_over = cargo_sealed = False
#     command_input = ""
#     command_history = []
#     error_message = ""
#     message_timer = 0
#     win_timer = 0
#     player_pos = (110, 90)
    
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
#                             if bh in ['B3', 'B4', 'B5']:
#                                 if all(bulkheads[b].sealed for b in ['B3', 'B4', 'B5']):
#                                     cargo_sealed = True
#                                     command_history.append("CARGO BAY ISOLATED")
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
#                             if target in ['B3', 'B4', 'B5']:
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
#             alien.update(all_navigation_nodes, bulkheads, player_pos)
#             if alien.current_node.name == 'bridge':
#                 game_over = True
        
#         if game_won and pygame.time.get_ticks() > win_timer:
#             running = False
        
#         if message_timer and pygame.time.get_ticks() > message_timer:
#             error_message = ""
#             message_timer = 0
        
#         screen.fill(TERMINAL_BLACK)
        
#         # Draw corridors
#         draw_corridor(screen, 180, 90, 240, 90)
#         draw_corridor(screen, 360, 90, 420, 90)
#         draw_corridor(screen, 560, 90, 620, 90)
#         draw_corridor(screen, 300, 130, 300, 260)
#         draw_corridor(screen, 490, 140, 490, 260)
#         draw_corridor(screen, 240, 300, 320, 300)
#         draw_corridor(screen, 440, 300, 520, 300)
#         draw_corridor(screen, 160, 360, 160, 440)
#         draw_corridor(screen, 380, 340, 380, 440)
#         draw_corridor(screen, 580, 350, 580, 440)
        
#         # Draw rooms
#         for room in rooms.values():
#             room.draw(screen, font_small)
        
#         # Player indicator
#         pygame.draw.circle(screen, BRIGHT_GREEN, player_pos, 7)
#         if (pygame.time.get_ticks() // 500) % 2 == 0:
#             pygame.draw.circle(screen, BRIGHT_GREEN, player_pos, 12, 2)
        
#         # Visual details
#         screen.blit(font_medium.render('⚕', True, TERMINAL_GREEN), (485, 85))
#         screen.blit(font_medium.render('⚠ ⚠', True, BRIGHT_GREEN), (540, 295))
#         for i in range(3):
#             color = BRIGHT_GREEN if (pygame.time.get_ticks() // 400) % 2 else TERMINAL_GREEN
#             pygame.draw.circle(screen, color, (570 + i * 20, 300), 7)
        
#         # Cargo crates
#         for i in range(20):
#             pygame.draw.rect(screen, DIM_GREEN, (100 + i * 28, 480, 15, 15))
#             pygame.draw.rect(screen, DIM_GREEN, (100 + i * 28, 550, 15, 15))
        
#         # Airlock
#         airlock_color = BRIGHT_GREEN if cargo_sealed else DIM_GREEN
#         airlock_points = [(600, 510), (650, 510), (660, 525), (650, 540), (600, 540)]
#         pygame.draw.polygon(screen, airlock_color, airlock_points, 3)
#         screen.blit(font_small.render('AIRLOCK', True, airlock_color), (605, 520))
        
#         # Bulkheads and alien
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
        
#         # Help text
#         help_lines = ['COMMANDS:', 'SEAL B0-B5', 'OPEN B0-B5', 'OPEN AIRLOCK', '',
#                       'Seal B0 to protect bridge', 'Herd alien to cargo bay', 'Seal B3, B4, B5', 'Then open airlock']
#         for i, line in enumerate(help_lines):
#             screen.blit(font_small.render(line, True, DIM_GREEN), (ui_x, HEIGHT - 200 + i * 20))
        
#         # Overlays
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
# Alien just sits in the Galley once B0 is sealed; still floating diagonally (but not as basly)
# """
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
#         else:
#             pygame.draw.line(surface, color, (self.x - 18, self.y), (self.x + 18, self.y), width)
#             pygame.draw.line(surface, color, (self.x - 18, self.y + 5), (self.x + 18, self.y + 5), width)
#             label = font_small.render(self.name, True, color)
#             surface.blit(label, (self.x + 25, self.y - 2))

# class Alien:
#     def __init__(self, start_node):
#         self.current_node = start_node
#         self.x = start_node.x
#         self.y = start_node.y
#         self.trail = []
#         self.speed = 1.5
#         self.wander_timer = 0
#         self.wander_interval = random.randint(90, 150)
#         self.path = []
#         self.hunting = False
#         self.bridge_node = None
#         self.wait_timer = 0
#         self.investigating = True
    
#     def find_path(self, target_node, bulkheads):
#         """BFS pathfinding that STRICTLY respects sealed bulkheads"""
#         if self.current_node == target_node:
#             return []
        
#         queue = [(self.current_node, [])]
#         visited = {self.current_node}
        
#         while queue:
#             current, path = queue.pop(0)
            
#             for next_node, bulkhead_name in current.connections:
#                 # CRITICAL: Skip if bulkhead exists AND is sealed
#                 if bulkhead_name:
#                     if bulkhead_name in bulkheads and bulkheads[bulkhead_name].sealed:
#                         continue  # Cannot pass through sealed bulkhead
                
#                 if next_node == target_node:
#                     return path + [next_node]
                
#                 if next_node not in visited:
#                     visited.add(next_node)
#                     queue.append((next_node, path + [next_node]))
        
#         # No path found - all routes blocked
#         return []
    
#     def update(self, all_nodes, bulkheads, player_pos):
#         dist_to_player = math.hypot(self.x - player_pos[0], self.y - player_pos[1])
        
#         # Hunt the player when close enough
#         if dist_to_player < 250:
#             self.hunting = True
#             self.investigating = False
#             self.wait_timer = 0
            
#             # Calculate path to bridge when hunting (respects bulkheads)
#             if self.bridge_node and not self.path:
#                 new_path = self.find_path(self.bridge_node, bulkheads)
#                 if new_path:
#                     self.path = new_path
#                 else:
#                     # Path blocked by sealed bulkheads - stop hunting and wander
#                     self.hunting = False
#                     self.wait_timer = 60
#         else:
#             # Investigating/wandering behavior
#             self.hunting = False
            
#             # Wait at current location briefly before moving
#             if self.wait_timer > 0:
#                 self.wait_timer -= 1
#                 return
            
#             if not self.path:
#                 # Pick a random room to investigate (not cargo or waypoints)
#                 valid_nodes = [n for n in all_nodes if n.name != 'cargo' and n.name != 'waypoint' and n != self.current_node]
#                 if valid_nodes:
#                     target = random.choice(valid_nodes)
#                     new_path = self.find_path(target, bulkheads)
#                     if new_path:
#                         self.path = new_path
#                         self.investigating = True
#                     else:
#                         # Path blocked - wait and try again
#                         self.wait_timer = 60
        
#         # Follow the path node by node - MUST reach each waypoint exactly
#         if self.path:
#             next_node = self.path[0]
#             dx = next_node.x - self.x
#             dy = next_node.y - self.y
#             dist = math.hypot(dx, dy)
            
#             if dist < 1.5:
#                 # Reached the node - snap EXACTLY to it (no floating)
#                 self.current_node = next_node
#                 self.x = next_node.x
#                 self.y = next_node.y
#                 self.path.pop(0)
                
#                 # If we just passed through a bulkhead, verify it's still open
#                 if self.path and len(self.path) > 0:
#                     # Check if next connection has a sealed bulkhead
#                     next_in_path = self.path[0]
#                     for connected_node, bulkhead_name in self.current_node.connections:
#                         if connected_node == next_in_path and bulkhead_name:
#                             if bulkhead_name in bulkheads and bulkheads[bulkhead_name].sealed:
#                                 # Bulkhead sealed while traveling - stop and recalculate
#                                 self.path = []
#                                 break
                
#                 # If path complete and investigating, wait briefly
#                 if not self.path and self.investigating:
#                     self.wait_timer = random.randint(60, 120)
#                     self.investigating = False
#             else:
#                 # Move toward the node in a straight line
#                 speed = self.speed * 2.0 if self.hunting else self.speed
#                 self.x += (dx / dist) * speed
#                 self.y += (dy / dist) * speed
        
#         # Trail effect
#         self.trail.append((self.x, self.y))
#         if len(self.trail) > 30:
#             self.trail.pop(0)
    
#     def draw(self, surface):
#         # Draw trail
#         if len(self.trail) > 1:
#             for i in range(len(self.trail) - 1):
#                 alpha = int((i / len(self.trail)) * 150)
#                 pygame.draw.line(surface, (0, alpha, 0), self.trail[i], self.trail[i+1], 3)
        
#         # Draw alien
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
#     """Draw straight corridors (horizontal or vertical only)"""
#     if abs(y1 - y2) < 5:
#         y = (y1 + y2) // 2
#         pygame.draw.line(surface, TERMINAL_GREEN, (x1, y - width//2), (x2, y - width//2), 2)
#         pygame.draw.line(surface, TERMINAL_GREEN, (x1, y + width//2), (x2, y + width//2), 2)
#     elif abs(x1 - x2) < 5:
#         x = (x1 + x2) // 2
#         pygame.draw.line(surface, TERMINAL_GREEN, (x - width//2, y1), (x - width//2, y2), 2)
#         pygame.draw.line(surface, TERMINAL_GREEN, (x + width//2, y1), (x + width//2, y2), 2)

# def run_airlock_puzzle(player_name):
#     pygame.init()
#     screen = pygame.display.set_mode((WIDTH, HEIGHT))
#     pygame.display.set_caption("MUTHER - AIRLOCK PROTOCOL")
    
#     font_large, font_medium, font_small = load_fonts()
#     clock = pygame.time.Clock()
    
#     # Room layout
#     rooms = {
#         'bridge': Room('BRIDGE', 'angular', 40, 40, 140, 100),
#         'galley': Room('GALLEY', 'rect', 240, 50, 120, 80),
#         'medbay': Room('MEDBAY', 'hex', 420, 40, 140, 100),
#         'hypersleep': Room('HYPERSLEEP', 'circular', 620, 40, 130, 100),
#         'engineering': Room('ENGINE', 'circular', 80, 240, 160, 120),
#         'crew': Room('CREW', 'rect', 320, 260, 120, 80),
#         'reactor': Room('REACTOR', 'octagon', 520, 250, 120, 100),
#         'cargo': Room('CARGO BAY', 'rect', 80, 440, 600, 150),
#     }
    
#     # Path nodes for alien navigation
#     nodes = {
#         'bridge': PathNode(110, 90, 'bridge'),
#         'galley': PathNode(300, 90, 'galley'),
#         'medbay': PathNode(490, 90, 'medbay'),
#         'hypersleep': PathNode(685, 90, 'hypersleep'),
#         'engineering': PathNode(160, 300, 'engineering'),
#         'crew': PathNode(380, 300, 'crew'),
#         'reactor': PathNode(580, 300, 'reactor'),
#         'cargo_left': PathNode(160, 515, 'cargo'),
#         'cargo_center': PathNode(380, 515, 'cargo'),
#         'cargo_right': PathNode(580, 515, 'cargo'),
#     }
    
#     bulkheads = {
#         'B0': Bulkhead('B0', 195, 90, 'v'),
#         'B1': Bulkhead('B1', 365, 90, 'v'),
#         'B2': Bulkhead('B2', 555, 90, 'v'),
#         'B3': Bulkhead('B3', 160, 405, 'h'),
#         'B4': Bulkhead('B4', 380, 405, 'h'),
#         'B5': Bulkhead('B5', 580, 405, 'h'),
#     }
    
#     # Build the graph - add waypoint nodes at EVERY corridor intersection/bend
#     # This forces the alien to follow the exact corridor layout
#     waypoint_bridge_out = PathNode(180, 90, 'waypoint')
#     waypoint_galley_out_right = PathNode(360, 90, 'waypoint')
#     waypoint_galley_down = PathNode(300, 130, 'waypoint')
#     waypoint_galley_mid = PathNode(300, 195, 'waypoint')
#     waypoint_medbay_out = PathNode(560, 90, 'waypoint')
#     waypoint_medbay_down = PathNode(490, 140, 'waypoint')
#     waypoint_medbay_mid = PathNode(490, 195, 'waypoint')
#     waypoint_eng_out = PathNode(240, 300, 'waypoint')
#     waypoint_crew_out_right = PathNode(440, 300, 'waypoint')
#     waypoint_eng_down = PathNode(160, 360, 'waypoint')
#     waypoint_crew_down = PathNode(380, 340, 'waypoint')
#     waypoint_reactor_down = PathNode(580, 350, 'waypoint')
    
#     # Top level with waypoints at each corridor junction
#     nodes['bridge'].add_connection(waypoint_bridge_out)
#     waypoint_bridge_out.add_connection(nodes['galley'], 'B0')
    
#     nodes['galley'].add_connection(waypoint_galley_out_right)
#     waypoint_galley_out_right.add_connection(nodes['medbay'], 'B1')
    
#     nodes['medbay'].add_connection(waypoint_medbay_out)
#     waypoint_medbay_out.add_connection(nodes['hypersleep'], 'B2')
    
#     # Vertical drops with waypoints
#     nodes['galley'].add_connection(waypoint_galley_down)
#     waypoint_galley_down.add_connection(waypoint_galley_mid)
#     waypoint_galley_mid.add_connection(nodes['crew'])
    
#     nodes['medbay'].add_connection(waypoint_medbay_down)
#     waypoint_medbay_down.add_connection(waypoint_medbay_mid)
#     waypoint_medbay_mid.add_connection(nodes['crew'])
    
#     # Middle horizontal level
#     nodes['engineering'].add_connection(waypoint_eng_out)
#     waypoint_eng_out.add_connection(nodes['crew'])
    
#     nodes['crew'].add_connection(waypoint_crew_out_right)
#     waypoint_crew_out_right.add_connection(nodes['reactor'])
    
#     # Drops to cargo with waypoints
#     nodes['engineering'].add_connection(waypoint_eng_down)
#     waypoint_eng_down.add_connection(nodes['cargo_left'], 'B3')
    
#     nodes['crew'].add_connection(waypoint_crew_down)
#     waypoint_crew_down.add_connection(nodes['cargo_center'], 'B4')
    
#     nodes['reactor'].add_connection(waypoint_reactor_down)
#     waypoint_reactor_down.add_connection(nodes['cargo_right'], 'B5')
    
#     # Cargo internal horizontal
#     nodes['cargo_left'].add_connection(nodes['cargo_center'])
#     nodes['cargo_center'].add_connection(nodes['cargo_right'])
    
#     # All navigation nodes including waypoints
#     all_navigation_nodes = list(nodes.values()) + [
#         waypoint_bridge_out, waypoint_galley_out_right, waypoint_galley_down, waypoint_galley_mid,
#         waypoint_medbay_out, waypoint_medbay_down, waypoint_medbay_mid, waypoint_eng_out,
#         waypoint_crew_out_right, waypoint_eng_down, waypoint_crew_down, waypoint_reactor_down
#     ]
    
#     # Initialize alien
#     alien = Alien(nodes['engineering'])
#     alien.bridge_node = nodes['bridge']
    
#     # Game state
#     game_won = game_over = cargo_sealed = False
#     command_input = ""
#     command_history = []
#     error_message = ""
#     message_timer = 0
#     win_timer = 0
#     player_pos = (110, 90)
    
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
#                             if bh in ['B3', 'B4', 'B5']:
#                                 if all(bulkheads[b].sealed for b in ['B3', 'B4', 'B5']):
#                                     cargo_sealed = True
#                                     command_history.append("CARGO BAY ISOLATED")
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
#                             if target in ['B3', 'B4', 'B5']:
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
#             alien.update(all_navigation_nodes, bulkheads, player_pos)
#             if alien.current_node.name == 'bridge':
#                 game_over = True
        
#         if game_won and pygame.time.get_ticks() > win_timer:
#             running = False
        
#         if message_timer and pygame.time.get_ticks() > message_timer:
#             error_message = ""
#             message_timer = 0
        
#         screen.fill(TERMINAL_BLACK)
        
#         # Draw complete corridors between rooms
#         # Top horizontal corridor
#         draw_corridor(screen, 180, 90, 240, 90)  # Bridge to Galley
#         draw_corridor(screen, 360, 90, 420, 90)  # Galley to Medbay
#         draw_corridor(screen, 560, 90, 620, 90)  # Medbay to Hypersleep
        
#         # Vertical drops to middle level
#         draw_corridor(screen, 300, 130, 300, 260)  # Galley down to Crew
#         draw_corridor(screen, 490, 140, 490, 260)  # Medbay down to Crew
        
#         # Middle horizontal corridor
#         draw_corridor(screen, 240, 300, 320, 300)  # Engineering to Crew
#         draw_corridor(screen, 440, 300, 520, 300)  # Crew to Reactor
        
#         # Vertical drops to cargo
#         draw_corridor(screen, 160, 360, 160, 440)  # Engineering to cargo
#         draw_corridor(screen, 380, 340, 380, 440)  # Crew to cargo
#         draw_corridor(screen, 580, 350, 580, 440)  # Reactor to cargo
        
#         # Draw rooms
#         for room in rooms.values():
#             room.draw(screen, font_small)
        
#         # Player indicator
#         pygame.draw.circle(screen, BRIGHT_GREEN, player_pos, 7)
#         if (pygame.time.get_ticks() // 500) % 2 == 0:
#             pygame.draw.circle(screen, BRIGHT_GREEN, player_pos, 12, 2)
        
#         # Visual details
#         screen.blit(font_medium.render('⚕', True, TERMINAL_GREEN), (485, 85))
#         screen.blit(font_medium.render('⚠ ⚠', True, BRIGHT_GREEN), (540, 295))
#         for i in range(3):
#             color = BRIGHT_GREEN if (pygame.time.get_ticks() // 400) % 2 else TERMINAL_GREEN
#             pygame.draw.circle(screen, color, (570 + i * 20, 300), 7)
        
#         # Cargo bay crates
#         for i in range(20):
#             pygame.draw.rect(screen, DIM_GREEN, (100 + i * 28, 480, 15, 15))
#             pygame.draw.rect(screen, DIM_GREEN, (100 + i * 28, 550, 15, 15))
        
#         # Airlock indicator
#         airlock_color = BRIGHT_GREEN if cargo_sealed else DIM_GREEN
#         airlock_points = [(600, 510), (650, 510), (660, 525), (650, 540), (600, 540)]
#         pygame.draw.polygon(screen, airlock_color, airlock_points, 3)
#         screen.blit(font_small.render('AIRLOCK', True, airlock_color), (605, 520))
        
#         # Draw bulkheads and alien
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
        
#         # Help text
#         help_lines = ['COMMANDS:', 'SEAL B0-B5', 'OPEN B0-B5', 'OPEN AIRLOCK', '',
#                       'Seal B0 to protect bridge', 'Herd alien to cargo bay', 'Seal B3, B4, B5', 'Then open airlock']
#         for i, line in enumerate(help_lines):
#             screen.blit(font_small.render(line, True, DIM_GREEN), (ui_x, HEIGHT - 200 + i * 20))
        
#         # Win/lose overlays
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
Getting there: Still some alien movement issues and it is passing through sealed gates
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
#         else:
#             pygame.draw.line(surface, color, (self.x - 18, self.y), (self.x + 18, self.y), width)
#             pygame.draw.line(surface, color, (self.x - 18, self.y + 5), (self.x + 18, self.y + 5), width)
#             label = font_small.render(self.name, True, color)
#             surface.blit(label, (self.x + 25, self.y - 2))

# class Alien:
#     def __init__(self, start_node):
#         self.current_node = start_node
#         self.x = start_node.x
#         self.y = start_node.y
#         self.trail = []
#         self.speed = 1.5
#         self.wander_timer = 0
#         self.wander_interval = random.randint(90, 150)
#         self.path = []
#         self.hunting = False
#         self.bridge_node = None
#         self.wait_timer = 0
#         self.investigating = True
    
#     def find_path(self, target_node, bulkheads):
#         """BFS pathfinding that respects bulkheads"""
#         if self.current_node == target_node:
#             return []
        
#         queue = [(self.current_node, [])]
#         visited = {self.current_node}
        
#         while queue:
#             current, path = queue.pop(0)
            
#             for next_node, bulkhead_name in current.connections:
#                 # Skip sealed bulkheads
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
        
#         # Hunt the player when close enough
#         if dist_to_player < 250:
#             self.hunting = True
#             self.investigating = False
#             self.wait_timer = 0
            
#             # Always try to path to bridge when hunting
#             if self.bridge_node and not self.path:
#                 new_path = self.find_path(self.bridge_node, bulkheads)
#                 if new_path:
#                     self.path = new_path
#         else:
#             # Investigating/wandering behavior
#             self.hunting = False
            
#             # Wait at current location briefly before moving
#             if self.wait_timer > 0:
#                 self.wait_timer -= 1
#                 return
            
#             if not self.path:
#                 # Pick a random room to investigate (not cargo)
#                 valid_nodes = [n for n in all_nodes if n.name != 'cargo' and n != self.current_node]
#                 if valid_nodes:
#                     target = random.choice(valid_nodes)
#                     new_path = self.find_path(target, bulkheads)
#                     if new_path:
#                         self.path = new_path
#                         self.investigating = True
        
#         # Follow the path node by node
#         if self.path:
#             next_node = self.path[0]
#             dx = next_node.x - self.x
#             dy = next_node.y - self.y
#             dist = math.hypot(dx, dy)
            
#             if dist < 2:
#                 # Reached the node - snap to it
#                 self.current_node = next_node
#                 self.x = next_node.x
#                 self.y = next_node.y
#                 self.path.pop(0)
                
#                 # If path complete and investigating, wait briefly
#                 if not self.path and self.investigating:
#                     self.wait_timer = random.randint(60, 120)
#                     self.investigating = False
#             else:
#                 # Move toward the node
#                 speed = self.speed * 2.0 if self.hunting else self.speed
#                 self.x += (dx / dist) * speed
#                 self.y += (dy / dist) * speed
        
#         # Trail effect
#         self.trail.append((self.x, self.y))
#         if len(self.trail) > 30:
#             self.trail.pop(0)
    
#     def draw(self, surface):
#         # Draw trail
#         if len(self.trail) > 1:
#             for i in range(len(self.trail) - 1):
#                 alpha = int((i / len(self.trail)) * 150)
#                 pygame.draw.line(surface, (0, alpha, 0), self.trail[i], self.trail[i+1], 3)
        
#         # Draw alien
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
#     """Draw straight corridors (horizontal or vertical only)"""
#     if abs(y1 - y2) < 5:
#         y = (y1 + y2) // 2
#         pygame.draw.line(surface, TERMINAL_GREEN, (x1, y - width//2), (x2, y - width//2), 2)
#         pygame.draw.line(surface, TERMINAL_GREEN, (x1, y + width//2), (x2, y + width//2), 2)
#     elif abs(x1 - x2) < 5:
#         x = (x1 + x2) // 2
#         pygame.draw.line(surface, TERMINAL_GREEN, (x - width//2, y1), (x - width//2, y2), 2)
#         pygame.draw.line(surface, TERMINAL_GREEN, (x + width//2, y1), (x + width//2, y2), 2)

# def run_airlock_puzzle(player_name):
#     pygame.init()
#     screen = pygame.display.set_mode((WIDTH, HEIGHT))
#     pygame.display.set_caption("MUTHER - AIRLOCK PROTOCOL")
    
#     font_large, font_medium, font_small = load_fonts()
#     clock = pygame.time.Clock()
    
#     # Room layout
#     rooms = {
#         'bridge': Room('BRIDGE', 'angular', 40, 40, 140, 100),
#         'galley': Room('GALLEY', 'rect', 240, 50, 120, 80),
#         'medbay': Room('MEDBAY', 'hex', 420, 40, 140, 100),
#         'hypersleep': Room('HYPERSLEEP', 'circular', 620, 40, 130, 100),
#         'engineering': Room('ENGINE', 'circular', 80, 240, 160, 120),
#         'crew': Room('CREW', 'rect', 320, 260, 120, 80),
#         'reactor': Room('REACTOR', 'octagon', 520, 250, 120, 100),
#         'cargo': Room('CARGO BAY', 'rect', 80, 440, 600, 150),
#     }
    
#     # Path nodes for alien navigation
#     nodes = {
#         'bridge': PathNode(110, 90, 'bridge'),
#         'galley': PathNode(300, 90, 'galley'),
#         'medbay': PathNode(490, 90, 'medbay'),
#         'hypersleep': PathNode(685, 90, 'hypersleep'),
#         'engineering': PathNode(160, 300, 'engineering'),
#         'crew': PathNode(380, 300, 'crew'),
#         'reactor': PathNode(580, 300, 'reactor'),
#         'cargo_left': PathNode(160, 515, 'cargo'),
#         'cargo_center': PathNode(380, 515, 'cargo'),
#         'cargo_right': PathNode(580, 515, 'cargo'),
#     }
    
#     bulkheads = {
#         'B0': Bulkhead('B0', 195, 90, 'v'),
#         'B1': Bulkhead('B1', 365, 90, 'v'),
#         'B2': Bulkhead('B2', 555, 90, 'v'),
#         'B3': Bulkhead('B3', 160, 405, 'h'),
#         'B4': Bulkhead('B4', 380, 405, 'h'),
#         'B5': Bulkhead('B5', 580, 405, 'h'),
#     }
    
#     # Build the graph - connections follow corridor layout exactly
#     # Top level horizontal
#     nodes['bridge'].add_connection(nodes['galley'], 'B0')
#     nodes['galley'].add_connection(nodes['medbay'], 'B1')
#     nodes['medbay'].add_connection(nodes['hypersleep'], 'B2')
    
#     # Vertical connections to middle level
#     nodes['galley'].add_connection(nodes['crew'])
#     nodes['medbay'].add_connection(nodes['crew'])
    
#     # Middle level horizontal
#     nodes['engineering'].add_connection(nodes['crew'])
#     nodes['crew'].add_connection(nodes['reactor'])
    
#     # Vertical connections to cargo
#     nodes['engineering'].add_connection(nodes['cargo_left'], 'B3')
#     nodes['crew'].add_connection(nodes['cargo_center'], 'B4')
#     nodes['reactor'].add_connection(nodes['cargo_right'], 'B5')
    
#     # Cargo internal horizontal
#     nodes['cargo_left'].add_connection(nodes['cargo_center'])
#     nodes['cargo_center'].add_connection(nodes['cargo_right'])
    
#     # Initialize alien
#     alien = Alien(nodes['engineering'])
#     alien.bridge_node = nodes['bridge']
    
#     # Game state
#     game_won = game_over = cargo_sealed = False
#     command_input = ""
#     command_history = []
#     error_message = ""
#     message_timer = 0
#     win_timer = 0
#     player_pos = (110, 90)
    
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
#                             if bh in ['B3', 'B4', 'B5']:
#                                 if all(bulkheads[b].sealed for b in ['B3', 'B4', 'B5']):
#                                     cargo_sealed = True
#                                     command_history.append("CARGO BAY ISOLATED")
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
#                             if target in ['B3', 'B4', 'B5']:
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
        
#         # Draw complete corridors between rooms
#         # Top horizontal corridor
#         draw_corridor(screen, 180, 90, 240, 90)  # Bridge to Galley
#         draw_corridor(screen, 360, 90, 420, 90)  # Galley to Medbay
#         draw_corridor(screen, 560, 90, 620, 90)  # Medbay to Hypersleep
        
#         # Vertical drops to middle level
#         draw_corridor(screen, 300, 130, 300, 260)  # Galley down to Crew
#         draw_corridor(screen, 490, 140, 490, 260)  # Medbay down to Crew
        
#         # Middle horizontal corridor
#         draw_corridor(screen, 240, 300, 320, 300)  # Engineering to Crew
#         draw_corridor(screen, 440, 300, 520, 300)  # Crew to Reactor
        
#         # Vertical drops to cargo
#         draw_corridor(screen, 160, 360, 160, 440)  # Engineering to cargo
#         draw_corridor(screen, 380, 340, 380, 440)  # Crew to cargo
#         draw_corridor(screen, 580, 350, 580, 440)  # Reactor to cargo
        
#         # Draw rooms
#         for room in rooms.values():
#             room.draw(screen, font_small)
        
#         # Player indicator
#         pygame.draw.circle(screen, BRIGHT_GREEN, player_pos, 7)
#         if (pygame.time.get_ticks() // 500) % 2 == 0:
#             pygame.draw.circle(screen, BRIGHT_GREEN, player_pos, 12, 2)
        
#         # Visual details
#         screen.blit(font_medium.render('⚕', True, TERMINAL_GREEN), (485, 85))
#         screen.blit(font_medium.render('⚠ ⚠', True, BRIGHT_GREEN), (540, 295))
#         for i in range(3):
#             color = BRIGHT_GREEN if (pygame.time.get_ticks() // 400) % 2 else TERMINAL_GREEN
#             pygame.draw.circle(screen, color, (570 + i * 20, 300), 7)
        
#         # Cargo bay crates
#         for i in range(20):
#             pygame.draw.rect(screen, DIM_GREEN, (100 + i * 28, 480, 15, 15))
#             pygame.draw.rect(screen, DIM_GREEN, (100 + i * 28, 550, 15, 15))
        
#         # Airlock indicator
#         airlock_color = BRIGHT_GREEN if cargo_sealed else DIM_GREEN
#         airlock_points = [(600, 510), (650, 510), (660, 525), (650, 540), (600, 540)]
#         pygame.draw.polygon(screen, airlock_color, airlock_points, 3)
#         screen.blit(font_small.render('AIRLOCK', True, airlock_color), (605, 520))
        
#         # Draw bulkheads and alien
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
        
#         # Help text
#         help_lines = ['COMMANDS:', 'SEAL B0-B5', 'OPEN B0-B5', 'OPEN AIRLOCK', '',
#                       'Seal B0 to protect bridge', 'Herd alien to cargo bay', 'Seal B3, B4, B5', 'Then open airlock']
#         for i, line in enumerate(help_lines):
#             screen.blit(font_small.render(line, True, DIM_GREEN), (ui_x, HEIGHT - 200 + i * 20))
        
#         # Win/lose overlays
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
Improvement but alien is still getting stuck and not following the room layout.
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
#         self.speed = 2.0
#         self.wander_timer = 0
#         self.wander_interval = random.randint(120, 240)
#         self.path = []
#         self.hunting = False
#         self.bridge_node = None
    
#     def find_path(self, target_node, bulkheads):
#         """BFS pathfinding that respects bulkheads"""
#         if self.current_node == target_node:
#             return []
        
#         queue = [(self.current_node, [])]
#         visited = {self.current_node}
        
#         while queue:
#             current, path = queue.pop(0)
            
#             for next_node, bulkhead_name in current.connections:
#                 # Skip sealed bulkheads
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
        
#         # Hunt the player when close enough
#         if dist_to_player < 250:
#             if not self.hunting:
#                 self.hunting = True
#                 self.path = []
            
#             # Recalculate path to bridge if needed
#             if self.bridge_node and not self.path:
#                 self.path = self.find_path(self.bridge_node, bulkheads)
#         else:
#             # Wander behavior
#             if self.hunting:
#                 self.hunting = False
#                 self.path = []
            
#             self.wander_timer += 1
#             if self.wander_timer >= self.wander_interval and not self.path:
#                 # Pick a random non-cargo node to wander to
#                 valid_nodes = [n for n in all_nodes if n.name != 'cargo']
#                 if valid_nodes:
#                     target = random.choice(valid_nodes)
#                     self.path = self.find_path(target, bulkheads)
#                 self.wander_timer = 0
#                 self.wander_interval = random.randint(120, 240)
        
#         # Follow the path
#         if self.path:
#             next_node = self.path[0]
#             dx = next_node.x - self.x
#             dy = next_node.y - self.y
#             dist = math.hypot(dx, dy)
            
#             if dist < 3:
#                 # Reached the node
#                 self.current_node = next_node
#                 self.x = next_node.x
#                 self.y = next_node.y
#                 self.path.pop(0)
#             else:
#                 # Move toward the node
#                 speed = self.speed * 1.8 if self.hunting else self.speed
#                 self.x += (dx / dist) * speed
#                 self.y += (dy / dist) * speed
        
#         # Trail effect
#         self.trail.append((self.x, self.y))
#         if len(self.trail) > 25:
#             self.trail.pop(0)
    
#     def draw(self, surface):
#         # Draw trail
#         if len(self.trail) > 1:
#             for i in range(len(self.trail) - 1):
#                 alpha = int((i / len(self.trail)) * 150)
#                 pygame.draw.line(surface, (0, alpha, 0), self.trail[i], self.trail[i+1], 3)
        
#         # Draw alien
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
#     """Draw straight corridors (horizontal or vertical only)"""
#     if abs(y1 - y2) < 5:
#         y = (y1 + y2) // 2
#         pygame.draw.line(surface, TERMINAL_GREEN, (x1, y - width//2), (x2, y - width//2), 2)
#         pygame.draw.line(surface, TERMINAL_GREEN, (x1, y + width//2), (x2, y + width//2), 2)
#     elif abs(x1 - x2) < 5:
#         x = (x1 + x2) // 2
#         pygame.draw.line(surface, TERMINAL_GREEN, (x - width//2, y1), (x - width//2, y2), 2)
#         pygame.draw.line(surface, TERMINAL_GREEN, (x + width//2, y1), (x + width//2, y2), 2)

# def run_airlock_puzzle(player_name):
#     pygame.init()
#     screen = pygame.display.set_mode((WIDTH, HEIGHT))
#     pygame.display.set_caption("MUTHER - AIRLOCK PROTOCOL")
    
#     font_large, font_medium, font_small = load_fonts()
#     clock = pygame.time.Clock()
    
#     # Room layout
#     rooms = {
#         'bridge': Room('BRIDGE', 'angular', 40, 40, 140, 100),
#         'galley': Room('GALLEY', 'rect', 240, 50, 120, 80),
#         'medbay': Room('MEDBAY', 'hex', 420, 40, 140, 100),
#         'hypersleep': Room('HYPERSLEEP', 'circular', 620, 40, 130, 100),
#         'engineering': Room('ENGINE', 'circular', 80, 240, 160, 120),
#         'crew': Room('CREW', 'rect', 320, 260, 120, 80),
#         'reactor': Room('REACTOR', 'octagon', 520, 250, 120, 100),
#         'cargo': Room('CARGO BAY', 'rect', 80, 440, 600, 150),
#     }
    
#     # Path nodes for alien navigation
#     nodes = {
#         'bridge': PathNode(110, 90, 'bridge'),
#         'galley': PathNode(300, 90, 'galley'),
#         'medbay': PathNode(490, 90, 'medbay'),
#         'hypersleep': PathNode(685, 90, 'hypersleep'),
#         'engineering': PathNode(160, 300, 'engineering'),
#         'crew': PathNode(380, 300, 'crew'),
#         'reactor': PathNode(580, 300, 'reactor'),
#         'cargo_left': PathNode(160, 515, 'cargo'),
#         'cargo_center': PathNode(380, 515, 'cargo'),
#         'cargo_right': PathNode(580, 515, 'cargo'),
#     }
    
#     bulkheads = {
#         'B0': Bulkhead('B0', 195, 90, 'v'),
#         'B1': Bulkhead('B1', 365, 90, 'v'),
#         'B2': Bulkhead('B2', 555, 90, 'v'),
#         'B3': Bulkhead('B3', 160, 405, 'h'),
#         'B4': Bulkhead('B4', 380, 405, 'h'),
#         'B5': Bulkhead('B5', 580, 405, 'h'),
#     }
    
#     # Build the graph - connections follow corridor layout exactly
#     # Top level horizontal
#     nodes['bridge'].add_connection(nodes['galley'], 'B0')
#     nodes['galley'].add_connection(nodes['medbay'], 'B1')
#     nodes['medbay'].add_connection(nodes['hypersleep'], 'B2')
    
#     # Vertical connections to middle level
#     nodes['galley'].add_connection(nodes['crew'])
#     nodes['medbay'].add_connection(nodes['crew'])
    
#     # Middle level horizontal
#     nodes['engineering'].add_connection(nodes['crew'])
#     nodes['crew'].add_connection(nodes['reactor'])
    
#     # Vertical connections to cargo
#     nodes['engineering'].add_connection(nodes['cargo_left'], 'B3')
#     nodes['crew'].add_connection(nodes['cargo_center'], 'B4')
#     nodes['reactor'].add_connection(nodes['cargo_right'], 'B5')
    
#     # Cargo internal horizontal
#     nodes['cargo_left'].add_connection(nodes['cargo_center'])
#     nodes['cargo_center'].add_connection(nodes['cargo_right'])
    
#     # Initialize alien
#     alien = Alien(nodes['engineering'])
#     alien.bridge_node = nodes['bridge']
    
#     # Game state
#     game_won = game_over = cargo_sealed = False
#     command_input = ""
#     command_history = []
#     error_message = ""
#     message_timer = 0
#     win_timer = 0
#     player_pos = (110, 90)
    
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
#                             if bh in ['B3', 'B4', 'B5']:
#                                 if all(bulkheads[b].sealed for b in ['B3', 'B4', 'B5']):
#                                     cargo_sealed = True
#                                     command_history.append("CARGO BAY ISOLATED")
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
#                             if target in ['B3', 'B4', 'B5']:
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
        
#         # Draw complete corridors between rooms
#         # Top horizontal corridor
#         draw_corridor(screen, 180, 90, 240, 90)  # Bridge to Galley
#         draw_corridor(screen, 360, 90, 420, 90)  # Galley to Medbay
#         draw_corridor(screen, 560, 90, 620, 90)  # Medbay to Hypersleep
        
#         # Vertical drops to middle level
#         draw_corridor(screen, 300, 130, 300, 260)  # Galley down to Crew
#         draw_corridor(screen, 490, 140, 490, 260)  # Medbay down to Crew
        
#         # Middle horizontal corridor
#         draw_corridor(screen, 240, 300, 320, 300)  # Engineering to Crew
#         draw_corridor(screen, 440, 300, 520, 300)  # Crew to Reactor
        
#         # Vertical drops to cargo
#         draw_corridor(screen, 160, 360, 160, 440)  # Engineering to cargo
#         draw_corridor(screen, 380, 340, 380, 440)  # Crew to cargo
#         draw_corridor(screen, 580, 350, 580, 440)  # Reactor to cargo
        
#         # Draw rooms
#         for room in rooms.values():
#             room.draw(screen, font_small)
        
#         # Player indicator
#         pygame.draw.circle(screen, BRIGHT_GREEN, player_pos, 7)
#         if (pygame.time.get_ticks() // 500) % 2 == 0:
#             pygame.draw.circle(screen, BRIGHT_GREEN, player_pos, 12, 2)
        
#         # Visual details
#         screen.blit(font_medium.render('⚕', True, TERMINAL_GREEN), (485, 85))
#         screen.blit(font_medium.render('⚠ ⚠', True, BRIGHT_GREEN), (540, 295))
#         for i in range(3):
#             color = BRIGHT_GREEN if (pygame.time.get_ticks() // 400) % 2 else TERMINAL_GREEN
#             pygame.draw.circle(screen, color, (570 + i * 20, 300), 7)
        
#         # Cargo bay crates
#         for i in range(20):
#             pygame.draw.rect(screen, DIM_GREEN, (100 + i * 28, 480, 15, 15))
#             pygame.draw.rect(screen, DIM_GREEN, (100 + i * 28, 550, 15, 15))
        
#         # Airlock indicator
#         airlock_color = BRIGHT_GREEN if cargo_sealed else DIM_GREEN
#         airlock_points = [(600, 510), (650, 510), (660, 525), (650, 540), (600, 540)]
#         pygame.draw.polygon(screen, airlock_color, airlock_points, 3)
#         screen.blit(font_small.render('AIRLOCK', True, airlock_color), (605, 520))
        
#         # Draw bulkheads and alien
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
        
#         # Help text
#         help_lines = ['COMMANDS:', 'SEAL B0-B5', 'OPEN B0-B5', 'OPEN AIRLOCK', '',
#                       'Seal B0 to protect bridge', 'Herd alien to cargo bay', 'Seal B3, B4, B5', 'Then open airlock']
#         for i, line in enumerate(help_lines):
#             screen.blit(font_small.render(line, True, DIM_GREEN), (ui_x, HEIGHT - 200 + i * 20))
        
#         # Win/lose overlays
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
# Improved again: Alien movement is still sticky though
# """
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
#         self.reached_destination = False
    
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
        
#         # Hunt the player when close
#         if dist_to_player < 200:
#             if not self.hunting:
#                 self.hunting = True
#                 self.reached_destination = False
#                 self.path = []
            
#             # Only recalculate path if we don't have one or if path is blocked
#             if not self.path and self.bridge_node and self.current_node != self.bridge_node:
#                 new_path = self.find_path(self.bridge_node, bulkheads)
#                 if new_path:
#                     self.path = new_path
#                     self.reached_destination = False
#         else:
#             # Wander when not hunting
#             if self.hunting:
#                 self.hunting = False
#                 self.reached_destination = False
#                 self.path = []
            
#             self.wander_timer += 1
#             if self.wander_timer >= self.wander_interval and not self.path:
#                 target = random.choice(all_nodes)
#                 # Don't wander to cargo nodes
#                 while target.name == 'cargo':
#                     target = random.choice(all_nodes)
#                 self.path = self.find_path(target, bulkheads)
#                 self.wander_timer = 0
#                 self.wander_interval = random.randint(60, 120)
#                 self.reached_destination = False
        
#         # Move along path
#         if self.path and not self.reached_destination:
#             next_node = self.path[0]
#             dx = next_node.x - self.x
#             dy = next_node.y - self.y
#             dist = math.hypot(dx, dy)
            
#             if dist < 5:
#                 self.current_node = next_node
#                 self.x = next_node.x
#                 self.y = next_node.y
#                 self.path.pop(0)
                
#                 # Check if we've completed the entire path
#                 if not self.path:
#                     self.reached_destination = True
#                     self.pace_offset = 0
#             else:
#                 speed = self.speed * 1.5 if self.hunting else self.speed
#                 self.x += (dx / dist) * speed
#                 self.y += (dy / dist) * speed
#         else:
#             # Idle pacing at current location
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
#     """Draw straight corridors (horizontal or vertical only)"""
#     # Draw horizontal corridor
#     if abs(y1 - y2) < 5:
#         y = (y1 + y2) // 2
#         pygame.draw.line(surface, TERMINAL_GREEN, (x1, y - width//2), (x2, y - width//2), 2)
#         pygame.draw.line(surface, TERMINAL_GREEN, (x1, y + width//2), (x2, y + width//2), 2)
#     # Draw vertical corridor
#     elif abs(x1 - x2) < 5:
#         x = (x1 + x2) // 2
#         pygame.draw.line(surface, TERMINAL_GREEN, (x - width//2, y1), (x - width//2, y2), 2)
#         pygame.draw.line(surface, TERMINAL_GREEN, (x + width//2, y1), (x + width//2, y2), 2)

# def run_airlock_puzzle(player_name):
#     pygame.init()
#     screen = pygame.display.set_mode((WIDTH, HEIGHT))
#     pygame.display.set_caption("MUTHER - AIRLOCK PROTOCOL")
    
#     font_large, font_medium, font_small = load_fonts()
#     clock = pygame.time.Clock()
    
#     # SIMPLIFIED LAYOUT - horizontal/vertical corridors only
#     rooms = {
#         'bridge': Room('BRIDGE', 'angular', 40, 40, 140, 100),
#         'storage': Room('STORAGE', 'rect', 240, 50, 120, 80),
#         'medbay': Room('MEDBAY', 'hex', 420, 40, 140, 100),
#         'hypersleep': Room('HYPERSLEEP', 'circular', 620, 40, 130, 100),
#         'engineering': Room('ENGINE', 'circular', 80, 240, 160, 120),
#         'junction': Room('JUNCTION', 'rect', 320, 260, 120, 80),
#         'reactor': Room('REACTOR', 'octagon', 520, 250, 120, 100),
#         'cargo': Room('CARGO BAY', 'rect', 80, 440, 600, 150),
#     }
    
#     nodes = {
#         'bridge': PathNode(110, 90, 'bridge'),
#         'storage': PathNode(300, 90, 'storage'),
#         'medbay': PathNode(490, 90, 'medbay'),
#         'hypersleep': PathNode(685, 90, 'hypersleep'),
#         'engineering': PathNode(160, 300, 'engineering'),
#         'junction': PathNode(380, 300, 'junction'),
#         'reactor': PathNode(580, 300, 'reactor'),
#         'cargo_left': PathNode(160, 515, 'cargo'),
#         'cargo_center': PathNode(380, 515, 'cargo'),
#         'cargo_right': PathNode(580, 515, 'cargo'),
#     }
    
#     bulkheads = {
#         'B0': Bulkhead('B0', 195, 90, 'v'),
#         'B1': Bulkhead('B1', 365, 90, 'v'),
#         'B2': Bulkhead('B2', 555, 90, 'v'),
#         'B3': Bulkhead('B3', 160, 405, 'h'),
#         'B4': Bulkhead('B4', 380, 405, 'h'),
#         'B5': Bulkhead('B5', 580, 405, 'h'),
#     }
    
#     # STRAIGHT CONNECTIONS ONLY
#     nodes['bridge'].add_connection(nodes['storage'], 'B0')
#     nodes['storage'].add_connection(nodes['medbay'], 'B1')
#     nodes['medbay'].add_connection(nodes['hypersleep'], 'B2')
    
#     # Vertical drops from top tier to middle tier
#     nodes['storage'].add_connection(nodes['junction'])
#     nodes['engineering'].add_connection(nodes['junction'])
#     nodes['junction'].add_connection(nodes['reactor'])
    
#     # Vertical drops from middle tier to cargo
#     nodes['engineering'].add_connection(nodes['cargo_left'], 'B3')
#     nodes['junction'].add_connection(nodes['cargo_center'], 'B4')
#     nodes['reactor'].add_connection(nodes['cargo_right'], 'B5')
    
#     # Cargo internal connections
#     nodes['cargo_left'].add_connection(nodes['cargo_center'])
#     nodes['cargo_center'].add_connection(nodes['cargo_right'])
    
#     alien = Alien(nodes['engineering'])
#     alien.bridge_node = nodes['bridge']
    
#     # Game state
#     game_won = game_over = cargo_sealed = False
#     command_input = ""
#     command_history = []
#     error_message = ""
#     message_timer = 0
#     win_timer = 0
#     player_pos = (110, 90)
    
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
#                             if bh in ['B3', 'B4', 'B5']:
#                                 if all(bulkheads[b].sealed for b in ['B3', 'B4', 'B5']):
#                                     cargo_sealed = True
#                                     command_history.append("CARGO BAY ISOLATED")
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
#                             if target in ['B3', 'B4', 'B5']:
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
        
#         # STRAIGHT CORRIDORS ONLY - horizontal and vertical (OUTSIDE rooms only)
#         # Top horizontal corridor (between rooms)
#         draw_corridor(screen, 180, 90, 240, 90)  # Bridge to Storage
#         draw_corridor(screen, 360, 90, 420, 90)  # Storage to Medbay
#         draw_corridor(screen, 560, 90, 620, 90)  # Medbay to Hypersleep
        
#         # Vertical drop from Storage to Junction area
#         draw_corridor(screen, 300, 130, 300, 260)  # Storage down
        
#         # Middle horizontal corridor (between rooms)
#         draw_corridor(screen, 240, 300, 320, 300)  # Engineering to Junction
#         draw_corridor(screen, 440, 300, 520, 300)  # Junction to Reactor
        
#         # Vertical drops to cargo (between rooms)
#         draw_corridor(screen, 160, 360, 160, 440)  # Engineering to cargo
#         draw_corridor(screen, 380, 340, 380, 440)  # Junction to cargo
#         draw_corridor(screen, 580, 350, 580, 440)  # Reactor to cargo
        
#         # Draw rooms
#         for room in rooms.values():
#             room.draw(screen, font_small)
        
#         # Player
#         pygame.draw.circle(screen, BRIGHT_GREEN, player_pos, 7)
#         if (pygame.time.get_ticks() // 500) % 2 == 0:
#             pygame.draw.circle(screen, BRIGHT_GREEN, player_pos, 12, 2)
        
#         # Visual details
#         screen.blit(font_medium.render('⚕', True, TERMINAL_GREEN), (485, 85))
#         screen.blit(font_medium.render('⚠ ⚠', True, BRIGHT_GREEN), (540, 295))
#         for i in range(3):
#             color = BRIGHT_GREEN if (pygame.time.get_ticks() // 400) % 2 else TERMINAL_GREEN
#             pygame.draw.circle(screen, color, (570 + i * 20, 300), 7)
        
#         # Cargo bay crates
#         for i in range(20):
#             pygame.draw.rect(screen, DIM_GREEN, (100 + i * 28, 480, 15, 15))
#             pygame.draw.rect(screen, DIM_GREEN, (100 + i * 28, 550, 15, 15))
        
#         # Airlock indicator
#         airlock_color = BRIGHT_GREEN if cargo_sealed else DIM_GREEN
#         airlock_points = [(600, 510), (650, 510), (660, 525), (650, 540), (600, 540)]
#         pygame.draw.polygon(screen, airlock_color, airlock_points, 3)
#         screen.blit(font_small.render('AIRLOCK', True, airlock_color), (605, 520))
        
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
#         help_lines = ['COMMANDS:', 'SEAL B0-B5', 'OPEN B0-B5', 'OPEN AIRLOCK', '',
#                       'Seal B0 to protect bridge', 'Herd alien to cargo bay', 'Seal B3, B4, B5', 'Then open airlock']
#         for i, line in enumerate(help_lines):
#             screen.blit(font_small.render(line, True, DIM_GREEN), (ui_x, HEIGHT - 200 + i * 20))
        
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
Improvement! But still pacing bug and messy graphics, trying to improve.
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
#         self.reached_destination = False
    
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
        
#         # Hunt the player when close
#         if dist_to_player < 200:
#             if not self.hunting:
#                 self.hunting = True
#                 self.reached_destination = False
#             if self.bridge_node and self.current_node != self.bridge_node:
#                 new_path = self.find_path(self.bridge_node, bulkheads)
#                 if new_path and new_path != self.path:
#                     self.path = new_path
#                     self.reached_destination = False
#         else:
#             # Wander when not hunting
#             if self.hunting:
#                 self.hunting = False
#                 self.reached_destination = False
            
#             self.wander_timer += 1
#             if self.wander_timer >= self.wander_interval and not self.path:
#                 self.path = self.find_path(random.choice(all_nodes), bulkheads)
#                 self.wander_timer = 0
#                 self.wander_interval = random.randint(60, 120)
#                 self.reached_destination = False
        
#         # Move along path
#         if self.path and not self.reached_destination:
#             next_node = self.path[0]
#             dx = next_node.x - self.x
#             dy = next_node.y - self.y
#             dist = math.hypot(dx, dy)
            
#             if dist < 5:
#                 self.current_node = next_node
#                 self.x = next_node.x
#                 self.y = next_node.y
#                 self.path.pop(0)
                
#                 # Check if we've completed the entire path
#                 if not self.path:
#                     self.reached_destination = True
#                     self.pace_offset = 0
#             else:
#                 speed = self.speed * 1.5 if self.hunting else self.speed
#                 self.x += (dx / dist) * speed
#                 self.y += (dy / dist) * speed
#         else:
#             # Idle pacing at current location
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
#     """Draw straight corridors (horizontal or vertical only)"""
#     # Draw horizontal corridor
#     if abs(y1 - y2) < 5:
#         y = (y1 + y2) // 2
#         pygame.draw.line(surface, TERMINAL_GREEN, (x1, y - width//2), (x2, y - width//2), 2)
#         pygame.draw.line(surface, TERMINAL_GREEN, (x1, y + width//2), (x2, y + width//2), 2)
#     # Draw vertical corridor
#     elif abs(x1 - x2) < 5:
#         x = (x1 + x2) // 2
#         pygame.draw.line(surface, TERMINAL_GREEN, (x - width//2, y1), (x - width//2, y2), 2)
#         pygame.draw.line(surface, TERMINAL_GREEN, (x + width//2, y1), (x + width//2, y2), 2)

# def run_airlock_puzzle(player_name):
#     pygame.init()
#     screen = pygame.display.set_mode((WIDTH, HEIGHT))
#     pygame.display.set_caption("MUTHER - AIRLOCK PROTOCOL")
    
#     font_large, font_medium, font_small = load_fonts()
#     clock = pygame.time.Clock()
    
#     # SIMPLIFIED LAYOUT - horizontal/vertical corridors only
#     rooms = {
#         'bridge': Room('BRIDGE', 'angular', 40, 40, 140, 100),
#         'storage': Room('STORAGE', 'rect', 240, 50, 120, 80),
#         'medbay': Room('MEDBAY', 'hex', 420, 40, 140, 100),
#         'hypersleep': Room('HYPERSLEEP', 'circular', 620, 40, 130, 100),
#         'engineering': Room('ENGINE', 'circular', 80, 240, 160, 120),
#         'junction': Room('JUNCTION', 'rect', 320, 260, 120, 80),
#         'reactor': Room('REACTOR', 'octagon', 520, 250, 120, 100),
#         'cargo': Room('CARGO BAY', 'rect', 80, 440, 600, 150),
#     }
    
#     nodes = {
#         'bridge': PathNode(110, 90, 'bridge'),
#         'storage': PathNode(300, 90, 'storage'),
#         'medbay': PathNode(490, 90, 'medbay'),
#         'hypersleep': PathNode(685, 90, 'hypersleep'),
#         'engineering': PathNode(160, 300, 'engineering'),
#         'junction': PathNode(380, 300, 'junction'),
#         'reactor': PathNode(580, 300, 'reactor'),
#         'cargo_left': PathNode(160, 515, 'cargo'),
#         'cargo_center': PathNode(380, 515, 'cargo'),
#         'cargo_right': PathNode(580, 515, 'cargo'),
#     }
    
#     bulkheads = {
#         'B0': Bulkhead('B0', 195, 90, 'v'),
#         'B1': Bulkhead('B1', 365, 90, 'v'),
#         'B2': Bulkhead('B2', 555, 90, 'v'),
#         'B3': Bulkhead('B3', 160, 405, 'h'),
#         'B4': Bulkhead('B4', 380, 405, 'h'),
#         'B5': Bulkhead('B5', 580, 405, 'h'),
#     }
    
#     # STRAIGHT CONNECTIONS ONLY
#     nodes['bridge'].add_connection(nodes['storage'], 'B0')
#     nodes['storage'].add_connection(nodes['medbay'], 'B1')
#     nodes['medbay'].add_connection(nodes['hypersleep'], 'B2')
    
#     # Vertical drops from top tier to middle tier
#     nodes['storage'].add_connection(nodes['junction'])
#     nodes['engineering'].add_connection(nodes['junction'])
#     nodes['junction'].add_connection(nodes['reactor'])
    
#     # Vertical drops from middle tier to cargo
#     nodes['engineering'].add_connection(nodes['cargo_left'], 'B3')
#     nodes['junction'].add_connection(nodes['cargo_center'], 'B4')
#     nodes['reactor'].add_connection(nodes['cargo_right'], 'B5')
    
#     # Cargo internal connections
#     nodes['cargo_left'].add_connection(nodes['cargo_center'])
#     nodes['cargo_center'].add_connection(nodes['cargo_right'])
    
#     alien = Alien(nodes['engineering'])
#     alien.bridge_node = nodes['bridge']
    
#     # Game state
#     game_won = game_over = cargo_sealed = False
#     command_input = ""
#     command_history = []
#     error_message = ""
#     message_timer = 0
#     win_timer = 0
#     player_pos = (110, 90)
    
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
#                             if bh in ['B3', 'B4', 'B5']:
#                                 if all(bulkheads[b].sealed for b in ['B3', 'B4', 'B5']):
#                                     cargo_sealed = True
#                                     command_history.append("CARGO BAY ISOLATED")
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
#                             if target in ['B3', 'B4', 'B5']:
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
        
#         # STRAIGHT CORRIDORS ONLY - horizontal and vertical
#         # Top horizontal corridor
#         draw_corridor(screen, nodes['bridge'].x, nodes['bridge'].y, nodes['storage'].x, nodes['storage'].y)
#         draw_corridor(screen, nodes['storage'].x, nodes['storage'].y, nodes['medbay'].x, nodes['medbay'].y)
#         draw_corridor(screen, nodes['medbay'].x, nodes['medbay'].y, nodes['hypersleep'].x, nodes['hypersleep'].y)
        
#         # Vertical drops to middle tier
#         draw_corridor(screen, nodes['storage'].x, nodes['storage'].y, nodes['storage'].x, nodes['junction'].y)
#         draw_corridor(screen, nodes['storage'].x, nodes['junction'].y, nodes['junction'].x, nodes['junction'].y)
        
#         # Middle horizontal corridor
#         draw_corridor(screen, nodes['engineering'].x, nodes['engineering'].y, nodes['junction'].x, nodes['junction'].y)
#         draw_corridor(screen, nodes['junction'].x, nodes['junction'].y, nodes['reactor'].x, nodes['reactor'].y)
        
#         # Vertical drops to cargo
#         draw_corridor(screen, nodes['engineering'].x, nodes['engineering'].y, nodes['engineering'].x, nodes['cargo_left'].y)
#         draw_corridor(screen, nodes['junction'].x, nodes['junction'].y, nodes['junction'].x, nodes['cargo_center'].y)
#         draw_corridor(screen, nodes['reactor'].x, nodes['reactor'].y, nodes['reactor'].x, nodes['cargo_right'].y)
        
#         # Cargo internal corridors
#         draw_corridor(screen, nodes['cargo_left'].x, nodes['cargo_left'].y, nodes['cargo_center'].x, nodes['cargo_center'].y)
#         draw_corridor(screen, nodes['cargo_center'].x, nodes['cargo_center'].y, nodes['cargo_right'].x, nodes['cargo_right'].y)
        
#         # Draw rooms
#         for room in rooms.values():
#             room.draw(screen, font_small)
        
#         # Player
#         pygame.draw.circle(screen, BRIGHT_GREEN, player_pos, 7)
#         if (pygame.time.get_ticks() // 500) % 2 == 0:
#             pygame.draw.circle(screen, BRIGHT_GREEN, player_pos, 12, 2)
        
#         # Visual details
#         screen.blit(font_medium.render('⚕', True, TERMINAL_GREEN), (485, 85))
#         screen.blit(font_medium.render('⚠ ⚠', True, BRIGHT_GREEN), (540, 295))
#         for i in range(3):
#             color = BRIGHT_GREEN if (pygame.time.get_ticks() // 400) % 2 else TERMINAL_GREEN
#             pygame.draw.circle(screen, color, (570 + i * 20, 300), 7)
        
#         # Cargo bay crates
#         for i in range(20):
#             pygame.draw.rect(screen, DIM_GREEN, (100 + i * 28, 480, 15, 15))
#             pygame.draw.rect(screen, DIM_GREEN, (100 + i * 28, 550, 15, 15))
        
#         # Airlock indicator
#         airlock_color = BRIGHT_GREEN if cargo_sealed else DIM_GREEN
#         airlock_points = [(600, 510), (650, 510), (660, 525), (650, 540), (600, 540)]
#         pygame.draw.polygon(screen, airlock_color, airlock_points, 3)
#         screen.blit(font_small.render('AIRLOCK', True, airlock_color), (605, 520))
        
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
#         help_lines = ['COMMANDS:', 'SEAL B0-B5', 'OPEN B0-B5', 'OPEN AIRLOCK', '',
#                       'Seal B0 to protect bridge', 'Herd alien to cargo bay', 'Seal B3, B4, B5', 'Then open airlock']
#         for i, line in enumerate(help_lines):
#             screen.blit(font_small.render(line, True, DIM_GREEN), (ui_x, HEIGHT - 200 + i * 20))
        
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

