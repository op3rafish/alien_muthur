"""
ALIEN CHRONIS: FINAL AIRLOCK PUZZLE
"""

"""
Improved but still seems to be minor bug when it can sometimes still pass through B8 even from a sealed Cargo Bay.

Also re-sizing airlock text to fit. 

Other improvements:
Alien lingers too long in cargo bay
Alien should rage at closed/confined spaces to try and escape
Another corridor direct from bridge to cargo bay
Alien starting point
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
        
        if self.name == 'HYPERSLEEP':
            text_y = self.center_y + 10
        elif self.name == 'REACTOR':
            text_y = self.center_y + 8
        else:
            text_y = self.y + 15
        
        text = font.render(self.name, True, TERMINAL_GREEN)
        text_rect = text.get_rect(center=(self.center_x, text_y))
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
        self.state = 'idle'
        self.idle_timer = 0
        self.blocked_timer = 0
        self.blocked_position = None
    
    def get_open_connections(self, node, bulkheads):
        open_connections = []
        for connected_node, bulkhead_name in node.connections:
            if bulkhead_name is None:
                open_connections.append(connected_node)
            elif bulkhead_name not in bulkheads or not bulkheads[bulkhead_name].sealed:
                open_connections.append(connected_node)
        return open_connections
    
    def find_path_bfs(self, target_node, bulkheads):
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
        
        return None
    
    def choose_destination(self, all_nodes, bulkheads, hunting):
        if hunting:
            return self.bridge_node
        else:
            valid_targets = [n for n in all_nodes 
                             if n.name != 'waypoint' 
                             and n != self.current_node]
            if valid_targets:
                return random.choice(valid_targets)
            return None
    
    def update(self, all_nodes, bulkheads, player_pos):
        dist_to_player = math.hypot(self.x - player_pos[0], self.y - player_pos[1])
        hunting = dist_to_player < 400
        
        if self.state == 'blocked':
            self.blocked_timer -= 1
            offset = math.sin(pygame.time.get_ticks() / 400) * 10
            if self.blocked_position:
                self.x = self.blocked_position[0] + offset
                self.y = self.blocked_position[1]
            if self.blocked_timer <= 0:
                self.state = 'idle'
                self.blocked_position = None
                self.idle_timer = 60
            return
        
        if self.state == 'idle':
            self.idle_timer -= 1
            if self.idle_timer <= 0:
                self.state = 'choosing'
            return
        
        if self.state == 'choosing':
            destination = self.choose_destination(all_nodes, bulkheads, hunting)
            if destination:
                new_path = self.find_path_bfs(destination, bulkheads)
                if new_path:
                    self.path = new_path
                    self.state = 'moving'
                else:
                    if hunting:
                        wander_dest = self.choose_destination(all_nodes, bulkheads, False)
                        if wander_dest:
                            wander_path = self.find_path_bfs(wander_dest, bulkheads)
                            if wander_path:
                                self.path = wander_path
                                self.state = 'moving'
                                return
                    self.state = 'blocked'
                    self.blocked_timer = 120
                    self.blocked_position = (self.x, self.y)
            else:
                self.state = 'idle'
                self.idle_timer = 90
            return
        
        # MOVING - now 100% airtight against sealed bulkheads
        if self.state == 'moving':
            if not self.path:
                self.state = 'idle'
                self.idle_timer = random.randint(40, 100) if not hunting else 20
                return
            
            next_node = self.path[0]
            
            # CRITICAL: Check every single frame if the current segment is still open
            if next_node not in self.get_open_connections(self.current_node, bulkheads):
                self.path = []
                self.state = 'blocked'
                self.blocked_timer = 180  # Longer prowl when blocked
                self.blocked_position = (self.x, self.y)
                return
            
            dx = next_node.x - self.x
            dy = next_node.y - self.y
            distance = math.hypot(dx, dy)
            
            # Only snap to node when extremely close - prevents overshooting sealed gates
            if distance < 1.5:
                self.current_node = next_node
                self.x = float(next_node.x)
                self.y = float(next_node.y)
                self.path.pop(0)
                
                # Immediately re-check the next segment after arriving
                if self.path:
                    next_next = self.path[0]
                    if next_next not in self.get_open_connections(self.current_node, bulkheads):
                        self.path = []
                        self.state = 'blocked'
                        self.blocked_timer = 180
                        self.blocked_position = (self.x, self.y)
                return
            
            # Normal movement
            speed = self.move_speed * (2.0 if hunting else 1.0)
            self.x += (dx / distance) * speed
            self.y += (dy / distance) * speed
    
    def draw(self, surface):
        pulse = math.sin(pygame.time.get_ticks() / 200) * 2 + 10
        if self.state == 'blocked':
            pulse += 2
            color = BRIGHT_GREEN
        else:
            color = BRIGHT_GREEN if self.state == 'moving' else TERMINAL_GREEN
        
        points = [
            (self.x, self.y - pulse),
            (self.x + pulse, self.y),
            (self.x, self.y + pulse),
            (self.x - pulse, self.y)
        ]
        pygame.draw.polygon(surface, color, points)
        pygame.draw.polygon(surface, BRIGHT_GREEN, points, 2)
        
        if (pygame.time.get_ticks() // 300) % 2 == 0:
            pygame.draw.circle(surface, color, (int(self.x), int(self.y)), int(pulse + 5), 1)

def draw_corridor(surface, x1, y1, x2, y2, width=35):
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
        'B1': Bulkhead('B1', 195, 90, 'v'),
        'B2': Bulkhead('B2', 365, 90, 'v'),
        'B3': Bulkhead('B3', 585, 90, 'v'),
        'B4': Bulkhead('B4', 300, 195, 'h'),
        'B5': Bulkhead('B5', 490, 195, 'h'),
        'B6': Bulkhead('B6', 160, 405, 'h'),
        'B7': Bulkhead('B7', 380, 405, 'h'),
        'B8': Bulkhead('B8', 580, 405, 'h'),
    }
    
    waypoint_bridge_out = PathNode(180, 90, 'waypoint')
    waypoint_galley_out_right = PathNode(360, 90, 'waypoint')
    waypoint_galley_down = PathNode(300, 130, 'waypoint')
    waypoint_galley_mid = PathNode(300, 195, 'waypoint')
    waypoint_medbay_down = PathNode(490, 140, 'waypoint')
    waypoint_medbay_mid = PathNode(490, 195, 'waypoint')
    waypoint_medbay_out = PathNode(560, 90, 'waypoint')
    
    waypoint_eng_out = PathNode(240, 300, 'waypoint')
    waypoint_crew_left_entry = PathNode(320, 300, 'waypoint')
    waypoint_crew_right_entry = PathNode(440, 300, 'waypoint')
    waypoint_reactor_entry = PathNode(520, 300, 'waypoint')
    
    waypoint_eng_down = PathNode(160, 360, 'waypoint')
    waypoint_crew_down = PathNode(380, 340, 'waypoint')
    waypoint_reactor_down = PathNode(580, 350, 'waypoint')
    
    nodes['bridge'].add_connection(waypoint_bridge_out)
    waypoint_bridge_out.add_connection(nodes['galley'], 'B1')
    
    nodes['galley'].add_connection(waypoint_galley_out_right)
    waypoint_galley_out_right.add_connection(nodes['medbay'], 'B2')
    
    nodes['medbay'].add_connection(waypoint_medbay_out)
    waypoint_medbay_out.add_connection(nodes['hypersleep'], 'B3')
    
    nodes['galley'].add_connection(waypoint_galley_down)
    waypoint_galley_down.add_connection(waypoint_galley_mid)
    waypoint_galley_mid.add_connection(waypoint_crew_left_entry, 'B4')
    waypoint_crew_left_entry.add_connection(nodes['crew'])
    
    nodes['medbay'].add_connection(waypoint_medbay_down)
    waypoint_medbay_down.add_connection(waypoint_medbay_mid)
    waypoint_medbay_mid.add_connection(waypoint_crew_right_entry, 'B5')
    waypoint_crew_right_entry.add_connection(nodes['crew'])
    
    nodes['engineering'].add_connection(waypoint_eng_out)
    waypoint_eng_out.add_connection(waypoint_crew_left_entry)
    
    nodes['crew'].add_connection(waypoint_crew_right_entry)
    waypoint_crew_right_entry.add_connection(waypoint_reactor_entry)
    waypoint_reactor_entry.add_connection(nodes['reactor'])
    
    nodes['engineering'].add_connection(waypoint_eng_down)
    waypoint_eng_down.add_connection(nodes['cargo_left'], 'B6')
    
    nodes['crew'].add_connection(waypoint_crew_down)
    waypoint_crew_down.add_connection(nodes['cargo_center'], 'B7')
    
    nodes['reactor'].add_connection(waypoint_reactor_down)
    waypoint_reactor_down.add_connection(nodes['cargo_right'], 'B8')
    
    nodes['cargo_left'].add_connection(nodes['cargo_center'])
    nodes['cargo_center'].add_connection(nodes['cargo_right'])
    
    all_navigation_nodes = list(nodes.values()) + [
        waypoint_bridge_out, waypoint_galley_out_right,
        waypoint_galley_down, waypoint_galley_mid,
        waypoint_medbay_down, waypoint_medbay_mid,
        waypoint_medbay_out, waypoint_eng_out,
        waypoint_crew_left_entry, waypoint_crew_right_entry,
        waypoint_reactor_entry, waypoint_eng_down,
        waypoint_crew_down, waypoint_reactor_down
    ]
    
    alien = Alien(nodes['hypersleep'], nodes['bridge'])
    
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
                            if bh in ['B6', 'B7', 'B8']:
                                if all(bulkheads[b].sealed for b in ['B6', 'B7', 'B8']):
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
                            if target in ['B6', 'B7', 'B8']:
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
        
        draw_corridor(screen, 180, 90, 240, 90)
        draw_corridor(screen, 360, 90, 420, 90)
        draw_corridor(screen, 560, 90, 620, 90)
        draw_corridor(screen, 300, 130, 300, 270)
        draw_corridor(screen, 490, 140, 490, 270)
        draw_corridor(screen, 240, 300, 320, 300)
        draw_corridor(screen, 440, 300, 520, 300)
        draw_corridor(screen, 160, 360, 160, 440)
        draw_corridor(screen, 380, 340, 380, 440)
        draw_corridor(screen, 580, 350, 580, 440)
        
        for room in rooms.values():
            room.draw(screen, font_small)
        
        pygame.draw.circle(screen, BRIGHT_GREEN, player_pos, 7)
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            pygame.draw.circle(screen, BRIGHT_GREEN, player_pos, 12, 2)
        
        screen.blit(font_medium.render('⚕', True, TERMINAL_GREEN), (485, 85))
        screen.blit(font_medium.render('⚠ ⚠', True, BRIGHT_GREEN), (540, 295))
        for i in range(3):
            color = BRIGHT_GREEN if (pygame.time.get_ticks() // 400) % 2 else TERMINAL_GREEN
            pygame.draw.circle(screen, color, (570 + i * 20, 285), 7)
        
        for i in range(20):
            pygame.draw.rect(screen, DIM_GREEN, (100 + i * 28, 480, 15, 15))
            pygame.draw.rect(screen, DIM_GREEN, (100 + i * 28, 550, 15, 15))
        
        airlock_color = BRIGHT_GREEN if cargo_sealed else DIM_GREEN
        airlock_points = [(600, 510), (650, 510), (660, 525), (650, 540), (600, 540)]
        pygame.draw.polygon(screen, airlock_color, airlock_points, 3)
        screen.blit(font_small.render('AIRLOCK', True, airlock_color), (610, 522))
        
        for bh in bulkheads.values():
            bh.draw(screen, font_small)
        if not game_won:
            alien.draw(screen)
        
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
        
        help_lines = [
            'COMMANDS:', 
            'SEAL B1-B8', 
            'OPEN B1-B8', 
            'OPEN AIRLOCK', 
            '',
            'Seal B1 to protect bridge',
            'Control descent routes (B4/B5)',
            'Herd alien to cargo bay',
            'Seal B6, B7, B8',
            'Then open airlock'
        ]
        for i, line in enumerate(help_lines):
            screen.blit(font_small.render(line, True, DIM_GREEN), (ui_x, HEIGHT - 220 + i * 20))
        
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
Can still pass through B8 when sealed in the cargo hold!
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
        
#         if self.name == 'HYPERSLEEP':
#             text_y = self.center_y + 10
#         elif self.name == 'REACTOR':
#             text_y = self.center_y + 8
#         else:
#             text_y = self.y + 15
        
#         text = font.render(self.name, True, TERMINAL_GREEN)
#         text_rect = text.get_rect(center=(self.center_x, text_y))
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
#     def __init__(self, start_node, bridge_node):
#         self.x = float(start_node.x)
#         self.y = float(start_node.y)
#         self.current_node = start_node
#         self.bridge_node = bridge_node
#         self.path = []
#         self.move_speed = 1.5
#         self.state = 'idle'
#         self.idle_timer = 0
#         self.blocked_timer = 0
#         self.blocked_position = None
    
#     def get_open_connections(self, node, bulkheads):
#         open_connections = []
#         for connected_node, bulkhead_name in node.connections:
#             if bulkhead_name is None:
#                 open_connections.append(connected_node)
#             elif bulkhead_name not in bulkheads or not bulkheads[bulkhead_name].sealed:
#                 open_connections.append(connected_node)
#         return open_connections
    
#     def find_path_bfs(self, target_node, bulkheads):
#         if self.current_node == target_node:
#             return []
        
#         visited = {self.current_node}
#         queue = [(self.current_node, [])]
        
#         while queue:
#             node, path = queue.pop(0)
#             for next_node in self.get_open_connections(node, bulkheads):
#                 if next_node == target_node:
#                     return path + [next_node]
#                 if next_node not in visited:
#                     visited.add(next_node)
#                     queue.append((next_node, path + [next_node]))
        
#         return None
    
#     def choose_destination(self, all_nodes, bulkheads, hunting):
#         if hunting:
#             return self.bridge_node
#         else:
#             valid_targets = [n for n in all_nodes 
#                              if n.name != 'waypoint' 
#                              and n != self.current_node]
#             if valid_targets:
#                 return random.choice(valid_targets)
#             return None
    
#     def update(self, all_nodes, bulkheads, player_pos):
#         dist_to_player = math.hypot(self.x - player_pos[0], self.y - player_pos[1])
#         hunting = dist_to_player < 400
        
#         if self.state == 'blocked':
#             self.blocked_timer -= 1
#             offset = math.sin(pygame.time.get_ticks() / 400) * 10
#             if self.blocked_position:
#                 self.x = self.blocked_position[0] + offset
#                 self.y = self.blocked_position[1]
#             if self.blocked_timer <= 0:
#                 self.state = 'idle'
#                 self.blocked_position = None
#                 self.idle_timer = 60
#             return
        
#         if self.state == 'idle':
#             self.idle_timer -= 1
#             if self.idle_timer <= 0:
#                 self.state = 'choosing'
#             return
        
#         if self.state == 'choosing':
#             destination = self.choose_destination(all_nodes, bulkheads, hunting)
#             if destination:
#                 new_path = self.find_path_bfs(destination, bulkheads)
#                 if new_path:
#                     self.path = new_path
#                     self.state = 'moving'
#                 else:
#                     if hunting:
#                         wander_dest = self.choose_destination(all_nodes, bulkheads, False)
#                         if wander_dest:
#                             wander_path = self.find_path_bfs(wander_dest, bulkheads)
#                             if wander_path:
#                                 self.path = wander_path
#                                 self.state = 'moving'
#                                 return
#                     self.state = 'blocked'
#                     self.blocked_timer = 120
#                     self.blocked_position = (self.x, self.y)
#             else:
#                 self.state = 'idle'
#                 self.idle_timer = 90
#             return
        
#         # MOVING state - strengthened checks
#         if self.state == 'moving':
#             if not self.path:
#                 self.state = 'idle'
#                 self.idle_timer = random.randint(40, 100) if not hunting else 20
#                 return
            
#             next_node = self.path[0]
            
#             # DOUBLE CHECK: current segment must still be open every frame
#             if next_node not in self.get_open_connections(self.current_node, bulkheads):
#                 self.path = []
#                 self.state = 'blocked'
#                 self.blocked_timer = 150
#                 self.blocked_position = (self.x, self.y)
#                 return
            
#             dx = next_node.x - self.x
#             dy = next_node.y - self.y
#             distance = math.hypot(dx, dy)
            
#             if distance < 3.0:  # Slightly larger threshold to be safe
#                 self.current_node = next_node
#                 self.x = float(next_node.x)
#                 self.y = float(next_node.y)
#                 self.path.pop(0)
                
#                 # Re-check next segment immediately after arriving
#                 if self.path:
#                     next_next = self.path[0]
#                     if next_next not in self.get_open_connections(self.current_node, bulkheads):
#                         self.path = []
#                         self.state = 'blocked'
#                         self.blocked_timer = 150
#                         self.blocked_position = (self.x, self.y)
#                 return
            
#             speed = self.move_speed * (2.0 if hunting else 1.0)
#             self.x += (dx / distance) * speed
#             self.y += (dy / distance) * speed
    
#     def draw(self, surface):
#         pulse = math.sin(pygame.time.get_ticks() / 200) * 2 + 10
#         if self.state == 'blocked':
#             pulse += 2
#             color = BRIGHT_GREEN
#         else:
#             color = BRIGHT_GREEN if self.state == 'moving' else TERMINAL_GREEN
        
#         points = [
#             (self.x, self.y - pulse),
#             (self.x + pulse, self.y),
#             (self.x, self.y + pulse),
#             (self.x - pulse, self.y)
#         ]
#         pygame.draw.polygon(surface, color, points)
#         pygame.draw.polygon(surface, BRIGHT_GREEN, points, 2)
        
#         if (pygame.time.get_ticks() // 300) % 2 == 0:
#             pygame.draw.circle(surface, color, (int(self.x), int(self.y)), int(pulse + 5), 1)

# def draw_corridor(surface, x1, y1, x2, y2, width=35):
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
#         'B1': Bulkhead('B1', 195, 90, 'v'),
#         'B2': Bulkhead('B2', 365, 90, 'v'),
#         'B3': Bulkhead('B3', 585, 90, 'v'),
#         'B4': Bulkhead('B4', 300, 195, 'h'),
#         'B5': Bulkhead('B5', 490, 195, 'h'),
#         'B6': Bulkhead('B6', 160, 405, 'h'),
#         'B7': Bulkhead('B7', 380, 405, 'h'),
#         'B8': Bulkhead('B8', 580, 405, 'h'),
#     }
    
#     # Waypoints - B5 now forces full vertical travel before horizontal entry
#     waypoint_bridge_out = PathNode(180, 90, 'waypoint')
#     waypoint_galley_out_right = PathNode(360, 90, 'waypoint')
#     waypoint_galley_down = PathNode(300, 130, 'waypoint')
#     waypoint_galley_mid = PathNode(300, 195, 'waypoint')
#     waypoint_medbay_down = PathNode(490, 140, 'waypoint')
#     waypoint_medbay_mid = PathNode(490, 195, 'waypoint')
#     waypoint_medbay_out = PathNode(560, 90, 'waypoint')
    
#     waypoint_eng_out = PathNode(240, 300, 'waypoint')
#     waypoint_crew_left_entry = PathNode(320, 300, 'waypoint')
#     waypoint_crew_right_entry = PathNode(440, 300, 'waypoint')
#     waypoint_reactor_entry = PathNode(520, 300, 'waypoint')
    
#     waypoint_eng_down = PathNode(160, 360, 'waypoint')
#     waypoint_crew_down = PathNode(380, 340, 'waypoint')
#     waypoint_reactor_down = PathNode(580, 350, 'waypoint')
    
#     # Connections
#     nodes['bridge'].add_connection(waypoint_bridge_out)
#     waypoint_bridge_out.add_connection(nodes['galley'], 'B1')
    
#     nodes['galley'].add_connection(waypoint_galley_out_right)
#     waypoint_galley_out_right.add_connection(nodes['medbay'], 'B2')
    
#     nodes['medbay'].add_connection(waypoint_medbay_out)
#     waypoint_medbay_out.add_connection(nodes['hypersleep'], 'B3')
    
#     nodes['galley'].add_connection(waypoint_galley_down)
#     waypoint_galley_down.add_connection(waypoint_galley_mid)
#     waypoint_galley_mid.add_connection(waypoint_crew_left_entry, 'B4')
#     waypoint_crew_left_entry.add_connection(nodes['crew'])
    
#     nodes['medbay'].add_connection(waypoint_medbay_down)
#     waypoint_medbay_down.add_connection(waypoint_medbay_mid)
#     waypoint_medbay_mid.add_connection(waypoint_crew_right_entry, 'B5')
#     waypoint_crew_right_entry.add_connection(nodes['crew'])
    
#     nodes['engineering'].add_connection(waypoint_eng_out)
#     waypoint_eng_out.add_connection(waypoint_crew_left_entry)
    
#     nodes['crew'].add_connection(waypoint_crew_right_entry)
#     waypoint_crew_right_entry.add_connection(waypoint_reactor_entry)
#     waypoint_reactor_entry.add_connection(nodes['reactor'])
    
#     nodes['engineering'].add_connection(waypoint_eng_down)
#     waypoint_eng_down.add_connection(nodes['cargo_left'], 'B6')
    
#     nodes['crew'].add_connection(waypoint_crew_down)
#     waypoint_crew_down.add_connection(nodes['cargo_center'], 'B7')
    
#     nodes['reactor'].add_connection(waypoint_reactor_down)
#     waypoint_reactor_down.add_connection(nodes['cargo_right'], 'B8')
    
#     nodes['cargo_left'].add_connection(nodes['cargo_center'])
#     nodes['cargo_center'].add_connection(nodes['cargo_right'])
    
#     all_navigation_nodes = list(nodes.values()) + [
#         waypoint_bridge_out, waypoint_galley_out_right,
#         waypoint_galley_down, waypoint_galley_mid,
#         waypoint_medbay_down, waypoint_medbay_mid,
#         waypoint_medbay_out, waypoint_eng_out,
#         waypoint_crew_left_entry, waypoint_crew_right_entry,
#         waypoint_reactor_entry, waypoint_eng_down,
#         waypoint_crew_down, waypoint_reactor_down
#     ]
    
#     alien = Alien(nodes['hypersleep'], nodes['bridge'])
    
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
#                             if bh in ['B6', 'B7', 'B8']:
#                                 if all(bulkheads[b].sealed for b in ['B6', 'B7', 'B8']):
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
#                             if target in ['B6', 'B7', 'B8']:
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
        
#         # Corridors - nice long B4/B5 that stop just before middle deck
#         draw_corridor(screen, 180, 90, 240, 90)
#         draw_corridor(screen, 360, 90, 420, 90)
#         draw_corridor(screen, 560, 90, 620, 90)
#         draw_corridor(screen, 300, 130, 300, 270)
#         draw_corridor(screen, 490, 140, 490, 270)
#         draw_corridor(screen, 240, 300, 320, 300)
#         draw_corridor(screen, 440, 300, 520, 300)
#         draw_corridor(screen, 160, 360, 160, 440)
#         draw_corridor(screen, 380, 340, 380, 440)
#         draw_corridor(screen, 580, 350, 580, 440)
        
#         for room in rooms.values():
#             room.draw(screen, font_small)
        
#         pygame.draw.circle(screen, BRIGHT_GREEN, player_pos, 7)
#         if (pygame.time.get_ticks() // 500) % 2 == 0:
#             pygame.draw.circle(screen, BRIGHT_GREEN, player_pos, 12, 2)
        
#         screen.blit(font_medium.render('⚕', True, TERMINAL_GREEN), (485, 85))
#         screen.blit(font_medium.render('⚠ ⚠', True, BRIGHT_GREEN), (540, 295))
#         for i in range(3):
#             color = BRIGHT_GREEN if (pygame.time.get_ticks() // 400) % 2 else TERMINAL_GREEN
#             pygame.draw.circle(screen, color, (570 + i * 20, 285), 7)
        
#         for i in range(20):
#             pygame.draw.rect(screen, DIM_GREEN, (100 + i * 28, 480, 15, 15))
#             pygame.draw.rect(screen, DIM_GREEN, (100 + i * 28, 550, 15, 15))
        
#         airlock_color = BRIGHT_GREEN if cargo_sealed else DIM_GREEN
#         airlock_points = [(600, 510), (650, 510), (660, 525), (650, 540), (600, 540)]
#         pygame.draw.polygon(screen, airlock_color, airlock_points, 3)
#         screen.blit(font_small.render('AIRLOCK', True, airlock_color), (610, 522))
        
#         for bh in bulkheads.values():
#             bh.draw(screen, font_small)
#         if not game_won:
#             alien.draw(screen)
        
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
        
#         help_lines = [
#             'COMMANDS:', 
#             'SEAL B1-B8', 
#             'OPEN B1-B8', 
#             'OPEN AIRLOCK', 
#             '',
#             'Seal B1 to protect bridge',
#             'Control descent routes (B4/B5)',
#             'Herd alien to cargo bay',
#             'Seal B6, B7, B8',
#             'Then open airlock'
#         ]
#         for i, line in enumerate(help_lines):
#             screen.blit(font_small.render(line, True, DIM_GREEN), (ui_x, HEIGHT - 220 + i * 20))
        
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
Really good, just a couple of minor things to fix:
Alien still sometimes passes through sealed bulkheads
Sometimes shortcuts B5 corridor
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
        
#         # Label adjustments
#         if self.name == 'HYPERSLEEP':
#             text_y = self.center_y + 10
#         elif self.name == 'REACTOR':
#             text_y = self.center_y + 8
#         else:
#             text_y = self.y + 15
        
#         text = font.render(self.name, True, TERMINAL_GREEN)
#         text_rect = text.get_rect(center=(self.center_x, text_y))
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
#     def __init__(self, start_node, bridge_node):
#         self.x = float(start_node.x)
#         self.y = float(start_node.y)
#         self.current_node = start_node
#         self.bridge_node = bridge_node
#         self.path = []
#         self.move_speed = 1.5
#         self.state = 'idle'
#         self.idle_timer = 0
#         self.blocked_timer = 0
#         self.blocked_position = None
    
#     def get_open_connections(self, node, bulkheads):
#         open_connections = []
#         for connected_node, bulkhead_name in node.connections:
#             if bulkhead_name is None:
#                 open_connections.append(connected_node)
#             elif bulkhead_name not in bulkheads or not bulkheads[bulkhead_name].sealed:
#                 open_connections.append(connected_node)
#         return open_connections
    
#     def find_path_bfs(self, target_node, bulkheads):
#         if self.current_node == target_node:
#             return []
        
#         visited = {self.current_node}
#         queue = [(self.current_node, [])]
        
#         while queue:
#             node, path = queue.pop(0)
#             for next_node in self.get_open_connections(node, bulkheads):
#                 if next_node == target_node:
#                     return path + [next_node]
#                 if next_node not in visited:
#                     visited.add(next_node)
#                     queue.append((next_node, path + [next_node]))
        
#         return None
    
#     def choose_destination(self, all_nodes, bulkheads, hunting):
#         if hunting:
#             return self.bridge_node
#         else:
#             valid_targets = [n for n in all_nodes 
#                              if n.name != 'waypoint' 
#                              and n != self.current_node]
#             if valid_targets:
#                 return random.choice(valid_targets)
#             return None
    
#     def update(self, all_nodes, bulkheads, player_pos):
#         dist_to_player = math.hypot(self.x - player_pos[0], self.y - player_pos[1])
#         hunting = dist_to_player < 400
        
#         if self.state == 'blocked':
#             self.blocked_timer -= 1
#             offset = math.sin(pygame.time.get_ticks() / 400) * 10
#             if self.blocked_position:
#                 self.x = self.blocked_position[0] + offset
#                 self.y = self.blocked_position[1]
#             if self.blocked_timer <= 0:
#                 self.state = 'idle'
#                 self.blocked_position = None
#                 self.idle_timer = 60
#             return
        
#         if self.state == 'idle':
#             self.idle_timer -= 1
#             if self.idle_timer <= 0:
#                 self.state = 'choosing'
#             return
        
#         if self.state == 'choosing':
#             destination = self.choose_destination(all_nodes, bulkheads, hunting)
#             if destination:
#                 new_path = self.find_path_bfs(destination, bulkheads)
#                 if new_path:
#                     self.path = new_path
#                     self.state = 'moving'
#                 else:
#                     if hunting:
#                         wander_dest = self.choose_destination(all_nodes, bulkheads, False)
#                         if wander_dest:
#                             wander_path = self.find_path_bfs(wander_dest, bulkheads)
#                             if wander_path:
#                                 self.path = wander_path
#                                 self.state = 'moving'
#                                 return
#                     self.state = 'blocked'
#                     self.blocked_timer = 120
#                     self.blocked_position = (self.x, self.y)
#             else:
#                 self.state = 'idle'
#                 self.idle_timer = 90
#             return
        
#         if self.state == 'moving':
#             if not self.path:
#                 self.state = 'idle'
#                 self.idle_timer = random.randint(40, 100) if not hunting else 20
#                 return
            
#             next_node = self.path[0]
            
#             if next_node not in self.get_open_connections(self.current_node, bulkheads):
#                 self.path = []
#                 self.state = 'blocked'
#                 self.blocked_timer = 150
#                 self.blocked_position = (self.x, self.y)
#                 return
            
#             dx = next_node.x - self.x
#             dy = next_node.y - self.y
#             distance = math.hypot(dx, dy)
            
#             if distance < 2.0:
#                 self.current_node = next_node
#                 self.x = float(next_node.x)
#                 self.y = float(next_node.y)
#                 self.path.pop(0)
                
#                 if self.path:
#                     next_next = self.path[0]
#                     if next_next not in self.get_open_connections(self.current_node, bulkheads):
#                         self.path = []
#                         self.state = 'blocked'
#                         self.blocked_timer = 150
#                         self.blocked_position = (self.x, self.y)
#                 return
            
#             speed = self.move_speed * (2.0 if hunting else 1.0)
#             self.x += (dx / distance) * speed
#             self.y += (dy / distance) * speed
    
#     def draw(self, surface):
#         pulse = math.sin(pygame.time.get_ticks() / 200) * 2 + 10
#         if self.state == 'blocked':
#             pulse += 2
#             color = BRIGHT_GREEN
#         else:
#             color = BRIGHT_GREEN if self.state == 'moving' else TERMINAL_GREEN
        
#         points = [
#             (self.x, self.y - pulse),
#             (self.x + pulse, self.y),
#             (self.x, self.y + pulse),
#             (self.x - pulse, self.y)
#         ]
#         pygame.draw.polygon(surface, color, points)
#         pygame.draw.polygon(surface, BRIGHT_GREEN, points, 2)
        
#         if (pygame.time.get_ticks() // 300) % 2 == 0:
#             pygame.draw.circle(surface, color, (int(self.x), int(self.y)), int(pulse + 5), 1)

# def draw_corridor(surface, x1, y1, x2, y2, width=35):
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
#         'B1': Bulkhead('B1', 195, 90, 'v'),
#         'B2': Bulkhead('B2', 365, 90, 'v'),
#         'B3': Bulkhead('B3', 585, 90, 'v'),   # Pulled back from Hypersleep
#         'B4': Bulkhead('B4', 300, 195, 'h'),
#         'B5': Bulkhead('B5', 490, 195, 'h'),
#         'B6': Bulkhead('B6', 160, 405, 'h'),
#         'B7': Bulkhead('B7', 380, 405, 'h'),
#         'B8': Bulkhead('B8', 580, 405, 'h'),
#     }
    
#     # Waypoints - restored proper length for B4/B5 corridors while keeping horizontal entry
#     waypoint_bridge_out = PathNode(180, 90, 'waypoint')
#     waypoint_galley_out_right = PathNode(360, 90, 'waypoint')
#     waypoint_galley_down = PathNode(300, 130, 'waypoint')
#     waypoint_galley_mid = PathNode(300, 195, 'waypoint')   # Full length to B4
#     waypoint_medbay_down = PathNode(490, 140, 'waypoint')
#     waypoint_medbay_mid = PathNode(490, 195, 'waypoint')   # Full length to B5
#     waypoint_medbay_out = PathNode(560, 90, 'waypoint')
    
#     waypoint_eng_out = PathNode(240, 300, 'waypoint')
#     waypoint_crew_left_entry = PathNode(320, 300, 'waypoint')
#     waypoint_crew_right_entry = PathNode(440, 300, 'waypoint')
#     waypoint_reactor_entry = PathNode(520, 300, 'waypoint')
    
#     waypoint_eng_down = PathNode(160, 360, 'waypoint')
#     waypoint_crew_down = PathNode(380, 340, 'waypoint')
#     waypoint_reactor_down = PathNode(580, 350, 'waypoint')
    
#     # Connections - now with horizontal stubs to eliminate diagonal
#     nodes['bridge'].add_connection(waypoint_bridge_out)
#     waypoint_bridge_out.add_connection(nodes['galley'], 'B1')
    
#     nodes['galley'].add_connection(waypoint_galley_out_right)
#     waypoint_galley_out_right.add_connection(nodes['medbay'], 'B2')
    
#     nodes['medbay'].add_connection(waypoint_medbay_out)
#     waypoint_medbay_out.add_connection(nodes['hypersleep'], 'B3')
    
#     # Galley → Crew (vertical + short horizontal stub)
#     nodes['galley'].add_connection(waypoint_galley_down)
#     waypoint_galley_down.add_connection(waypoint_galley_mid)
#     waypoint_galley_mid.add_connection(waypoint_crew_left_entry, 'B4')
#     waypoint_crew_left_entry.add_connection(nodes['crew'])
    
#     # Medbay → Crew (vertical + short horizontal stub)
#     nodes['medbay'].add_connection(waypoint_medbay_down)
#     waypoint_medbay_down.add_connection(waypoint_medbay_mid)
#     waypoint_medbay_mid.add_connection(waypoint_crew_right_entry, 'B5')
#     waypoint_crew_right_entry.add_connection(nodes['crew'])
    
#     nodes['engineering'].add_connection(waypoint_eng_out)
#     waypoint_eng_out.add_connection(waypoint_crew_left_entry)
    
#     nodes['crew'].add_connection(waypoint_crew_right_entry)
#     waypoint_crew_right_entry.add_connection(waypoint_reactor_entry)
#     waypoint_reactor_entry.add_connection(nodes['reactor'])
    
#     nodes['engineering'].add_connection(waypoint_eng_down)
#     waypoint_eng_down.add_connection(nodes['cargo_left'], 'B6')
    
#     nodes['crew'].add_connection(waypoint_crew_down)
#     waypoint_crew_down.add_connection(nodes['cargo_center'], 'B7')
    
#     nodes['reactor'].add_connection(waypoint_reactor_down)
#     waypoint_reactor_down.add_connection(nodes['cargo_right'], 'B8')
    
#     nodes['cargo_left'].add_connection(nodes['cargo_center'])
#     nodes['cargo_center'].add_connection(nodes['cargo_right'])
    
#     all_navigation_nodes = list(nodes.values()) + [
#         waypoint_bridge_out, waypoint_galley_out_right,
#         waypoint_galley_down, waypoint_galley_mid,
#         waypoint_medbay_down, waypoint_medbay_mid,
#         waypoint_medbay_out, waypoint_eng_out,
#         waypoint_crew_left_entry, waypoint_crew_right_entry,
#         waypoint_reactor_entry, waypoint_eng_down,
#         waypoint_crew_down, waypoint_reactor_down
#     ]
    
#     alien = Alien(nodes['hypersleep'], nodes['bridge'])
    
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
#                             if bh in ['B6', 'B7', 'B8']:
#                                 if all(bulkheads[b].sealed for b in ['B6', 'B7', 'B8']):
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
#                             if target in ['B6', 'B7', 'B8']:
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
        
#         # Corridors - full length B4/B5 verticals that stop just before middle deck
#         draw_corridor(screen, 180, 90, 240, 90)
#         draw_corridor(screen, 360, 90, 420, 90)
#         draw_corridor(screen, 560, 90, 620, 90)
#         draw_corridor(screen, 300, 130, 300, 270)   # Long enough but stops before overlapping
#         draw_corridor(screen, 490, 140, 490, 270)   # Long enough but stops before overlapping
#         draw_corridor(screen, 240, 300, 320, 300)
#         draw_corridor(screen, 440, 300, 520, 300)
#         draw_corridor(screen, 160, 360, 160, 440)
#         draw_corridor(screen, 380, 340, 380, 440)
#         draw_corridor(screen, 580, 350, 580, 440)
        
#         for room in rooms.values():
#             room.draw(screen, font_small)
        
#         pygame.draw.circle(screen, BRIGHT_GREEN, player_pos, 7)
#         if (pygame.time.get_ticks() // 500) % 2 == 0:
#             pygame.draw.circle(screen, BRIGHT_GREEN, player_pos, 12, 2)
        
#         screen.blit(font_medium.render('⚕', True, TERMINAL_GREEN), (485, 85))
#         screen.blit(font_medium.render('⚠ ⚠', True, BRIGHT_GREEN), (540, 295))
#         for i in range(3):
#             color = BRIGHT_GREEN if (pygame.time.get_ticks() // 400) % 2 else TERMINAL_GREEN
#             pygame.draw.circle(screen, color, (570 + i * 20, 285), 7)
        
#         for i in range(20):
#             pygame.draw.rect(screen, DIM_GREEN, (100 + i * 28, 480, 15, 15))
#             pygame.draw.rect(screen, DIM_GREEN, (100 + i * 28, 550, 15, 15))
        
#         airlock_color = BRIGHT_GREEN if cargo_sealed else DIM_GREEN
#         airlock_points = [(600, 510), (650, 510), (660, 525), (650, 540), (600, 540)]
#         pygame.draw.polygon(screen, airlock_color, airlock_points, 3)
#         screen.blit(font_small.render('AIRLOCK', True, airlock_color), (610, 522))
        
#         for bh in bulkheads.values():
#             bh.draw(screen, font_small)
#         if not game_won:
#             alien.draw(screen)
        
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
        
#         help_lines = [
#             'COMMANDS:', 
#             'SEAL B1-B8', 
#             'OPEN B1-B8', 
#             'OPEN AIRLOCK', 
#             '',
#             'Seal B1 to protect bridge',
#             'Control descent routes (B4/B5)',
#             'Herd alien to cargo bay',
#             'Seal B6, B7, B8',
#             'Then open airlock'
#         ]
#         for i, line in enumerate(help_lines):
#             screen.blit(font_small.render(line, True, DIM_GREEN), (ui_x, HEIGHT - 220 + i * 20))
        
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
Working to tweak the slight flaws now
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
        
#         # Special label adjustments
#         if self.name == 'HYPERSLEEP':
#             text_y = self.center_y + 10
#         elif self.name == 'REACTOR':
#             text_y = self.center_y + 8   # Moved down slightly
#         else:
#             text_y = self.y + 15
        
#         text = font.render(self.name, True, TERMINAL_GREEN)
#         text_rect = text.get_rect(center=(self.center_x, text_y))
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
#     def __init__(self, start_node, bridge_node):
#         self.x = float(start_node.x)
#         self.y = float(start_node.y)
#         self.current_node = start_node
#         self.bridge_node = bridge_node
#         self.path = []
#         self.move_speed = 1.5
#         self.state = 'idle'
#         self.idle_timer = 0
#         self.blocked_timer = 0
#         self.blocked_position = None
    
#     def get_open_connections(self, node, bulkheads):
#         open_connections = []
#         for connected_node, bulkhead_name in node.connections:
#             if bulkhead_name is None:
#                 open_connections.append(connected_node)
#             elif bulkhead_name not in bulkheads or not bulkheads[bulkhead_name].sealed:
#                 open_connections.append(connected_node)
#         return open_connections
    
#     def find_path_bfs(self, target_node, bulkheads):
#         if self.current_node == target_node:
#             return []
        
#         visited = {self.current_node}
#         queue = [(self.current_node, [])]
        
#         while queue:
#             node, path = queue.pop(0)
#             for next_node in self.get_open_connections(node, bulkheads):
#                 if next_node == target_node:
#                     return path + [next_node]
#                 if next_node not in visited:
#                     visited.add(next_node)
#                     queue.append((next_node, path + [next_node]))
        
#         return None
    
#     def choose_destination(self, all_nodes, bulkheads, hunting):
#         if hunting:
#             return self.bridge_node
#         else:
#             valid_targets = [n for n in all_nodes 
#                              if n.name != 'waypoint' 
#                              and n != self.current_node]
#             if valid_targets:
#                 return random.choice(valid_targets)
#             return None
    
#     def update(self, all_nodes, bulkheads, player_pos):
#         dist_to_player = math.hypot(self.x - player_pos[0], self.y - player_pos[1])
#         hunting = dist_to_player < 400
        
#         if self.state == 'blocked':
#             self.blocked_timer -= 1
#             offset = math.sin(pygame.time.get_ticks() / 400) * 10
#             if self.blocked_position:
#                 self.x = self.blocked_position[0] + offset
#                 self.y = self.blocked_position[1]
#             if self.blocked_timer <= 0:
#                 self.state = 'idle'
#                 self.blocked_position = None
#                 self.idle_timer = 60
#             return
        
#         if self.state == 'idle':
#             self.idle_timer -= 1
#             if self.idle_timer <= 0:
#                 self.state = 'choosing'
#             return
        
#         if self.state == 'choosing':
#             destination = self.choose_destination(all_nodes, bulkheads, hunting)
#             if destination:
#                 new_path = self.find_path_bfs(destination, bulkheads)
#                 if new_path:
#                     self.path = new_path
#                     self.state = 'moving'
#                 else:
#                     if hunting:
#                         wander_dest = self.choose_destination(all_nodes, bulkheads, False)
#                         if wander_dest:
#                             wander_path = self.find_path_bfs(wander_dest, bulkheads)
#                             if wander_path:
#                                 self.path = wander_path
#                                 self.state = 'moving'
#                                 return
#                     self.state = 'blocked'
#                     self.blocked_timer = 120
#                     self.blocked_position = (self.x, self.y)
#             else:
#                 self.state = 'idle'
#                 self.idle_timer = 90
#             return
        
#         if self.state == 'moving':
#             if not self.path:
#                 self.state = 'idle'
#                 self.idle_timer = random.randint(40, 100) if not hunting else 20
#                 return
            
#             next_node = self.path[0]
            
#             if next_node not in self.get_open_connections(self.current_node, bulkheads):
#                 self.path = []
#                 self.state = 'blocked'
#                 self.blocked_timer = 150
#                 self.blocked_position = (self.x, self.y)
#                 return
            
#             dx = next_node.x - self.x
#             dy = next_node.y - self.y
#             distance = math.hypot(dx, dy)
            
#             if distance < 2.0:
#                 self.current_node = next_node
#                 self.x = float(next_node.x)
#                 self.y = float(next_node.y)
#                 self.path.pop(0)
                
#                 if self.path:
#                     next_next = self.path[0]
#                     if next_next not in self.get_open_connections(self.current_node, bulkheads):
#                         self.path = []
#                         self.state = 'blocked'
#                         self.blocked_timer = 150
#                         self.blocked_position = (self.x, self.y)
#                 return
            
#             speed = self.move_speed * (2.0 if hunting else 1.0)
#             self.x += (dx / distance) * speed
#             self.y += (dy / distance) * speed
    
#     def draw(self, surface):
#         pulse = math.sin(pygame.time.get_ticks() / 200) * 2 + 10
#         if self.state == 'blocked':
#             pulse += 2
#             color = BRIGHT_GREEN
#         else:
#             color = BRIGHT_GREEN if self.state == 'moving' else TERMINAL_GREEN
        
#         points = [
#             (self.x, self.y - pulse),
#             (self.x + pulse, self.y),
#             (self.x, self.y + pulse),
#             (self.x - pulse, self.y)
#         ]
#         pygame.draw.polygon(surface, color, points)
#         pygame.draw.polygon(surface, BRIGHT_GREEN, points, 2)
        
#         if (pygame.time.get_ticks() // 300) % 2 == 0:
#             pygame.draw.circle(surface, color, (int(self.x), int(self.y)), int(pulse + 5), 1)

# def draw_corridor(surface, x1, y1, x2, y2, width=35):
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
#         'B1': Bulkhead('B1', 195, 90, 'v'),
#         'B2': Bulkhead('B2', 365, 90, 'v'),
#         'B3': Bulkhead('B3', 555, 90, 'v'),
#         'B4': Bulkhead('B4', 300, 195, 'h'),
#         'B5': Bulkhead('B5', 490, 195, 'h'),
#         'B6': Bulkhead('B6', 160, 405, 'h'),
#         'B7': Bulkhead('B7', 380, 405, 'h'),
#         'B8': Bulkhead('B8', 580, 405, 'h'),
#     }
    
#     # Waypoints
#     waypoint_bridge_out = PathNode(180, 90, 'waypoint')
#     waypoint_galley_out_right = PathNode(360, 90, 'waypoint')
#     waypoint_galley_down = PathNode(300, 130, 'waypoint')
#     waypoint_galley_mid = PathNode(300, 195, 'waypoint')
#     waypoint_medbay_down = PathNode(490, 140, 'waypoint')
#     waypoint_medbay_mid = PathNode(490, 195, 'waypoint')
#     waypoint_medbay_out = PathNode(560, 90, 'waypoint')
    
#     waypoint_eng_out = PathNode(240, 300, 'waypoint')
#     waypoint_crew_left_entry = PathNode(320, 300, 'waypoint')
#     waypoint_crew_right_entry = PathNode(440, 300, 'waypoint')
#     waypoint_reactor_entry = PathNode(520, 300, 'waypoint')
    
#     waypoint_eng_down = PathNode(160, 360, 'waypoint')
#     waypoint_crew_down = PathNode(380, 340, 'waypoint')
#     waypoint_reactor_down = PathNode(580, 350, 'waypoint')
    
#     # Connections – now with extra waypoint on right side to eliminate diagonal
#     nodes['bridge'].add_connection(waypoint_bridge_out)
#     waypoint_bridge_out.add_connection(nodes['galley'], 'B1')
    
#     nodes['galley'].add_connection(waypoint_galley_out_right)
#     waypoint_galley_out_right.add_connection(nodes['medbay'], 'B2')
    
#     nodes['medbay'].add_connection(waypoint_medbay_out)
#     waypoint_medbay_out.add_connection(nodes['hypersleep'], 'B3')
    
#     nodes['galley'].add_connection(waypoint_galley_down)
#     waypoint_galley_down.add_connection(waypoint_galley_mid)
#     waypoint_galley_mid.add_connection(waypoint_crew_left_entry, 'B4')
#     waypoint_crew_left_entry.add_connection(nodes['crew'])
    
#     nodes['medbay'].add_connection(waypoint_medbay_down)
#     waypoint_medbay_down.add_connection(waypoint_medbay_mid)
#     waypoint_medbay_mid.add_connection(waypoint_crew_right_entry, 'B5')
#     waypoint_crew_right_entry.add_connection(nodes['crew'])
    
#     nodes['engineering'].add_connection(waypoint_eng_out)
#     waypoint_eng_out.add_connection(waypoint_crew_left_entry)
    
#     # Fixed: Crew → Reactor now goes left-to-right horizontally with no diagonal
#     nodes['crew'].add_connection(waypoint_crew_right_entry)
#     waypoint_crew_right_entry.add_connection(waypoint_reactor_entry)
#     waypoint_reactor_entry.add_connection(nodes['reactor'])
    
#     nodes['engineering'].add_connection(waypoint_eng_down)
#     waypoint_eng_down.add_connection(nodes['cargo_left'], 'B6')
    
#     nodes['crew'].add_connection(waypoint_crew_down)
#     waypoint_crew_down.add_connection(nodes['cargo_center'], 'B7')
    
#     nodes['reactor'].add_connection(waypoint_reactor_down)
#     waypoint_reactor_down.add_connection(nodes['cargo_right'], 'B8')
    
#     nodes['cargo_left'].add_connection(nodes['cargo_center'])
#     nodes['cargo_center'].add_connection(nodes['cargo_right'])
    
#     all_navigation_nodes = list(nodes.values()) + [
#         waypoint_bridge_out, waypoint_galley_out_right,
#         waypoint_galley_down, waypoint_galley_mid,
#         waypoint_medbay_down, waypoint_medbay_mid,
#         waypoint_medbay_out, waypoint_eng_out,
#         waypoint_crew_left_entry, waypoint_crew_right_entry,
#         waypoint_reactor_entry, waypoint_eng_down,
#         waypoint_crew_down, waypoint_reactor_down
#     ]
    
#     alien = Alien(nodes['hypersleep'], nodes['bridge'])
    
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
#                             if bh in ['B6', 'B7', 'B8']:
#                                 if all(bulkheads[b].sealed for b in ['B6', 'B7', 'B8']):
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
#                             if target in ['B6', 'B7', 'B8']:
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
        
#         # Corridors – extended middle horizontal to fully connect Crew → Reactor
#         draw_corridor(screen, 180, 90, 240, 90)
#         draw_corridor(screen, 360, 90, 420, 90)
#         draw_corridor(screen, 560, 90, 620, 90)
#         draw_corridor(screen, 300, 130, 300, 300)
#         draw_corridor(screen, 490, 140, 490, 300)
#         draw_corridor(screen, 240, 300, 320, 300)   # Eng → Crew left
#         draw_corridor(screen, 440, 300, 520, 300)   # Crew right → Reactor (now fully reaches reactor entry)
#         draw_corridor(screen, 160, 360, 160, 440)
#         draw_corridor(screen, 380, 340, 380, 440)
#         draw_corridor(screen, 580, 350, 580, 440)
        
#         for room in rooms.values():
#             room.draw(screen, font_small)
        
#         pygame.draw.circle(screen, BRIGHT_GREEN, player_pos, 7)
#         if (pygame.time.get_ticks() // 500) % 2 == 0:
#             pygame.draw.circle(screen, BRIGHT_GREEN, player_pos, 12, 2)
        
#         screen.blit(font_medium.render('⚕', True, TERMINAL_GREEN), (485, 85))
#         screen.blit(font_medium.render('⚠ ⚠', True, BRIGHT_GREEN), (540, 295))
#         for i in range(3):
#             color = BRIGHT_GREEN if (pygame.time.get_ticks() // 400) % 2 else TERMINAL_GREEN
#             pygame.draw.circle(screen, color, (570 + i * 20, 300), 7)
        
#         for i in range(20):
#             pygame.draw.rect(screen, DIM_GREEN, (100 + i * 28, 480, 15, 15))
#             pygame.draw.rect(screen, DIM_GREEN, (100 + i * 28, 550, 15, 15))
        
#         airlock_color = BRIGHT_GREEN if cargo_sealed else DIM_GREEN
#         airlock_points = [(600, 510), (650, 510), (660, 525), (650, 540), (600, 540)]
#         pygame.draw.polygon(screen, airlock_color, airlock_points, 3)
#         screen.blit(font_small.render('AIRLOCK', True, airlock_color), (610, 522))
        
#         for bh in bulkheads.values():
#             bh.draw(screen, font_small)
#         if not game_won:
#             alien.draw(screen)
        
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
        
#         help_lines = [
#             'COMMANDS:', 
#             'SEAL B1-B8', 
#             'OPEN B1-B8', 
#             'OPEN AIRLOCK', 
#             '',
#             'Seal B1 to protect bridge',
#             'Control descent routes (B4/B5)',
#             'Herd alien to cargo bay',
#             'Seal B6, B7, B8',
#             'Then open airlock'
#         ]
#         for i, line in enumerate(help_lines):
#             screen.blit(font_small.render(line, True, DIM_GREEN), (ui_x, HEIGHT - 220 + i * 20))
        
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
Mechanics are working and improving! Now to just try and fix minor edits and corridor graphics.
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
        
#         # Special adjustment for Hypersleep label
#         if self.name == 'HYPERSLEEP':
#             text = font.render(self.name, True, TERMINAL_GREEN)
#             text_rect = text.get_rect(center=(self.center_x, self.center_y + 10))
#         else:
#             text = font.render(self.name, True, TERMINAL_GREEN)
#             text_rect = text.get_rect(center=(self.center_x, self.y + 15))
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
#     def __init__(self, start_node, bridge_node):
#         self.x = float(start_node.x)
#         self.y = float(start_node.y)
#         self.current_node = start_node
#         self.bridge_node = bridge_node
#         self.path = []
#         self.move_speed = 1.5
#         self.state = 'idle'
#         self.idle_timer = 0
#         self.blocked_timer = 0
#         self.blocked_position = None
    
#     def get_open_connections(self, node, bulkheads):
#         open_connections = []
#         for connected_node, bulkhead_name in node.connections:
#             if bulkhead_name is None:
#                 open_connections.append(connected_node)
#             elif bulkhead_name not in bulkheads or not bulkheads[bulkhead_name].sealed:
#                 open_connections.append(connected_node)
#         return open_connections
    
#     def find_path_bfs(self, target_node, bulkheads):
#         if self.current_node == target_node:
#             return []
        
#         visited = {self.current_node}
#         queue = [(self.current_node, [])]
        
#         while queue:
#             node, path = queue.pop(0)
#             for next_node in self.get_open_connections(node, bulkheads):
#                 if next_node == target_node:
#                     return path + [next_node]
#                 if next_node not in visited:
#                     visited.add(next_node)
#                     queue.append((next_node, path + [next_node]))
        
#         return None
    
#     def choose_destination(self, all_nodes, bulkheads, hunting):
#         if hunting:
#             return self.bridge_node
#         else:
#             valid_targets = [n for n in all_nodes 
#                              if n.name != 'waypoint' 
#                              and n != self.current_node]
#             if valid_targets:
#                 return random.choice(valid_targets)
#             return None
    
#     def update(self, all_nodes, bulkheads, player_pos):
#         dist_to_player = math.hypot(self.x - player_pos[0], self.y - player_pos[1])
#         hunting = dist_to_player < 400
        
#         if self.state == 'blocked':
#             self.blocked_timer -= 1
#             offset = math.sin(pygame.time.get_ticks() / 400) * 10
#             if self.blocked_position:
#                 self.x = self.blocked_position[0] + offset
#                 self.y = self.blocked_position[1]
#             if self.blocked_timer <= 0:
#                 self.state = 'idle'
#                 self.blocked_position = None
#                 self.idle_timer = 60
#             return
        
#         if self.state == 'idle':
#             self.idle_timer -= 1
#             if self.idle_timer <= 0:
#                 self.state = 'choosing'
#             return
        
#         if self.state == 'choosing':
#             destination = self.choose_destination(all_nodes, bulkheads, hunting)
#             if destination:
#                 new_path = self.find_path_bfs(destination, bulkheads)
#                 if new_path:
#                     self.path = new_path
#                     self.state = 'moving'
#                 else:
#                     if hunting:
#                         wander_dest = self.choose_destination(all_nodes, bulkheads, False)
#                         if wander_dest:
#                             wander_path = self.find_path_bfs(wander_dest, bulkheads)
#                             if wander_path:
#                                 self.path = wander_path
#                                 self.state = 'moving'
#                                 return
#                     self.state = 'blocked'
#                     self.blocked_timer = 120
#                     self.blocked_position = (self.x, self.y)
#             else:
#                 self.state = 'idle'
#                 self.idle_timer = 90
#             return
        
#         if self.state == 'moving':
#             if not self.path:
#                 self.state = 'idle'
#                 self.idle_timer = random.randint(40, 100) if not hunting else 20
#                 return
            
#             next_node = self.path[0]
            
#             if next_node not in self.get_open_connections(self.current_node, bulkheads):
#                 self.path = []
#                 self.state = 'blocked'
#                 self.blocked_timer = 150
#                 self.blocked_position = (self.x, self.y)
#                 return
            
#             dx = next_node.x - self.x
#             dy = next_node.y - self.y
#             distance = math.hypot(dx, dy)
            
#             if distance < 2.0:
#                 self.current_node = next_node
#                 self.x = float(next_node.x)
#                 self.y = float(next_node.y)
#                 self.path.pop(0)
                
#                 if self.path:
#                     next_next = self.path[0]
#                     if next_next not in self.get_open_connections(self.current_node, bulkheads):
#                         self.path = []
#                         self.state = 'blocked'
#                         self.blocked_timer = 150
#                         self.blocked_position = (self.x, self.y)
#                 return
            
#             speed = self.move_speed * (2.0 if hunting else 1.0)
#             self.x += (dx / distance) * speed
#             self.y += (dy / distance) * speed
    
#     def draw(self, surface):
#         pulse = math.sin(pygame.time.get_ticks() / 200) * 2 + 10
#         if self.state == 'blocked':
#             pulse += 2
#             color = BRIGHT_GREEN
#         else:
#             color = BRIGHT_GREEN if self.state == 'moving' else TERMINAL_GREEN
        
#         points = [
#             (self.x, self.y - pulse),
#             (self.x + pulse, self.y),
#             (self.x, self.y + pulse),
#             (self.x - pulse, self.y)
#         ]
#         pygame.draw.polygon(surface, color, points)
#         pygame.draw.polygon(surface, BRIGHT_GREEN, points, 2)
        
#         if (pygame.time.get_ticks() // 300) % 2 == 0:
#             pygame.draw.circle(surface, color, (int(self.x), int(self.y)), int(pulse + 5), 1)

# def draw_corridor(surface, x1, y1, x2, y2, width=35):
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
    
#     # Renumbered bulkheads: B1 (top) → B8 (bottom)
#     bulkheads = {
#         'B1': Bulkhead('B1', 195, 90, 'v'),   # Bridge → Galley
#         'B2': Bulkhead('B2', 365, 90, 'v'),   # Galley → Medbay
#         'B3': Bulkhead('B3', 555, 90, 'v'),   # Medbay → Hypersleep
#         'B4': Bulkhead('B4', 300, 195, 'h'),  # Galley down
#         'B5': Bulkhead('B5', 490, 195, 'h'),  # Medbay down
#         'B6': Bulkhead('B6', 160, 405, 'h'),  # Engineering → Cargo Left
#         'B7': Bulkhead('B7', 380, 405, 'h'),  # Crew → Cargo Center
#         'B8': Bulkhead('B8', 580, 405, 'h'),  # Reactor → Cargo Right
#     }
    
#     # Waypoints
#     waypoint_bridge_out = PathNode(180, 90, 'waypoint')
#     waypoint_galley_out_right = PathNode(360, 90, 'waypoint')
#     waypoint_galley_down = PathNode(300, 130, 'waypoint')
#     waypoint_galley_mid = PathNode(300, 195, 'waypoint')
#     waypoint_medbay_down = PathNode(490, 140, 'waypoint')
#     waypoint_medbay_mid = PathNode(490, 195, 'waypoint')
#     waypoint_medbay_out = PathNode(560, 90, 'waypoint')
    
#     waypoint_eng_out = PathNode(240, 300, 'waypoint')
#     waypoint_crew_left_entry = PathNode(320, 300, 'waypoint')
#     waypoint_crew_right_entry = PathNode(440, 300, 'waypoint')
#     waypoint_reactor_entry = PathNode(520, 300, 'waypoint')
    
#     waypoint_eng_down = PathNode(160, 360, 'waypoint')
#     waypoint_crew_down = PathNode(380, 340, 'waypoint')
#     waypoint_reactor_down = PathNode(580, 350, 'waypoint')
    
#     # Connections
#     nodes['bridge'].add_connection(waypoint_bridge_out)
#     waypoint_bridge_out.add_connection(nodes['galley'], 'B1')
    
#     nodes['galley'].add_connection(waypoint_galley_out_right)
#     waypoint_galley_out_right.add_connection(nodes['medbay'], 'B2')
    
#     nodes['medbay'].add_connection(waypoint_medbay_out)
#     waypoint_medbay_out.add_connection(nodes['hypersleep'], 'B3')
    
#     nodes['galley'].add_connection(waypoint_galley_down)
#     waypoint_galley_down.add_connection(waypoint_galley_mid)
#     waypoint_galley_mid.add_connection(waypoint_crew_left_entry, 'B4')
#     waypoint_crew_left_entry.add_connection(nodes['crew'])
    
#     nodes['medbay'].add_connection(waypoint_medbay_down)
#     waypoint_medbay_down.add_connection(waypoint_medbay_mid)
#     waypoint_medbay_mid.add_connection(waypoint_crew_right_entry, 'B5')
#     waypoint_crew_right_entry.add_connection(nodes['crew'])
    
#     nodes['engineering'].add_connection(waypoint_eng_out)
#     waypoint_eng_out.add_connection(waypoint_crew_left_entry)
    
#     nodes['crew'].add_connection(waypoint_crew_right_entry)
#     waypoint_crew_right_entry.add_connection(waypoint_reactor_entry)
#     waypoint_reactor_entry.add_connection(nodes['reactor'])
    
#     nodes['engineering'].add_connection(waypoint_eng_down)
#     waypoint_eng_down.add_connection(nodes['cargo_left'], 'B6')
    
#     nodes['crew'].add_connection(waypoint_crew_down)
#     waypoint_crew_down.add_connection(nodes['cargo_center'], 'B7')
    
#     nodes['reactor'].add_connection(waypoint_reactor_down)
#     waypoint_reactor_down.add_connection(nodes['cargo_right'], 'B8')
    
#     nodes['cargo_left'].add_connection(nodes['cargo_center'])
#     nodes['cargo_center'].add_connection(nodes['cargo_right'])
    
#     all_navigation_nodes = list(nodes.values()) + [
#         waypoint_bridge_out, waypoint_galley_out_right,
#         waypoint_galley_down, waypoint_galley_mid,
#         waypoint_medbay_down, waypoint_medbay_mid,
#         waypoint_medbay_out, waypoint_eng_out,
#         waypoint_crew_left_entry, waypoint_crew_right_entry,
#         waypoint_reactor_entry, waypoint_eng_down,
#         waypoint_crew_down, waypoint_reactor_down
#     ]
    
#     alien = Alien(nodes['hypersleep'], nodes['bridge'])
    
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
#                             if bh in ['B6', 'B7', 'B8']:
#                                 if all(bulkheads[b].sealed for b in ['B6', 'B7', 'B8']):
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
#                             if target in ['B6', 'B7', 'B8']:
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
        
#         # Extended vertical corridors to connect fully with middle deck
#         draw_corridor(screen, 180, 90, 240, 90)
#         draw_corridor(screen, 360, 90, 420, 90)
#         draw_corridor(screen, 560, 90, 620, 90)
#         draw_corridor(screen, 300, 130, 300, 300)   # Extended down to middle deck
#         draw_corridor(screen, 490, 140, 490, 300)   # Extended down to middle deck
#         draw_corridor(screen, 240, 300, 320, 300)
#         draw_corridor(screen, 440, 300, 520, 300)
#         draw_corridor(screen, 160, 360, 160, 440)
#         draw_corridor(screen, 380, 340, 380, 440)
#         draw_corridor(screen, 580, 350, 580, 440)
        
#         for room in rooms.values():
#             room.draw(screen, font_small)
        
#         pygame.draw.circle(screen, BRIGHT_GREEN, player_pos, 7)
#         if (pygame.time.get_ticks() // 500) % 2 == 0:
#             pygame.draw.circle(screen, BRIGHT_GREEN, player_pos, 12, 2)
        
#         screen.blit(font_medium.render('⚕', True, TERMINAL_GREEN), (485, 85))
#         screen.blit(font_medium.render('⚠ ⚠', True, BRIGHT_GREEN), (540, 295))
#         for i in range(3):
#             color = BRIGHT_GREEN if (pygame.time.get_ticks() // 400) % 2 else TERMINAL_GREEN
#             pygame.draw.circle(screen, color, (570 + i * 20, 300), 7)
        
#         for i in range(20):
#             pygame.draw.rect(screen, DIM_GREEN, (100 + i * 28, 480, 15, 15))
#             pygame.draw.rect(screen, DIM_GREEN, (100 + i * 28, 550, 15, 15))
        
#         airlock_color = BRIGHT_GREEN if cargo_sealed else DIM_GREEN
#         airlock_points = [(600, 510), (650, 510), (660, 525), (650, 540), (600, 540)]
#         pygame.draw.polygon(screen, airlock_color, airlock_points, 3)
#         # Smaller font for AIRLOCK label
#         screen.blit(font_small.render('AIRLOCK', True, airlock_color), (610, 522))
        
#         for bh in bulkheads.values():
#             bh.draw(screen, font_small)
#         if not game_won:
#             alien.draw(screen)
        
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
        
#         help_lines = [
#             'COMMANDS:', 
#             'SEAL B1-B8', 
#             'OPEN B1-B8', 
#             'OPEN AIRLOCK', 
#             '',
#             'Seal B1 to protect bridge',
#             'Control descent routes (B4/B5)',
#             'Herd alien to cargo bay',
#             'Seal B6, B7, B8',
#             'Then open airlock'
#         ]
#         for i, line in enumerate(help_lines):
#             screen.blit(font_small.render(line, True, DIM_GREEN), (ui_x, HEIGHT - 220 + i * 20))
        
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
BASIC MECHANICS ARE WORKING
Slight diagonal in/out of Crew
Lingers too long in Cargo Bay which makes the overall puzzle a little too easy
Some corridor graphics need fixed
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
#     def __init__(self, start_node, bridge_node):
#         self.x = float(start_node.x)
#         self.y = float(start_node.y)
#         self.current_node = start_node
#         self.bridge_node = bridge_node
#         self.path = []
#         self.move_speed = 1.5
#         self.state = 'idle'
#         self.idle_timer = 0
#         self.blocked_timer = 0
#         self.blocked_position = None
    
#     def get_open_connections(self, node, bulkheads):
#         open_connections = []
#         for connected_node, bulkhead_name in node.connections:
#             if bulkhead_name is None:
#                 open_connections.append(connected_node)
#             elif bulkhead_name not in bulkheads or not bulkheads[bulkhead_name].sealed:
#                 open_connections.append(connected_node)
#         return open_connections
    
#     def find_path_bfs(self, target_node, bulkheads):
#         if self.current_node == target_node:
#             return []
        
#         visited = {self.current_node}
#         queue = [(self.current_node, [])]
        
#         while queue:
#             node, path = queue.pop(0)
#             for next_node in self.get_open_connections(node, bulkheads):
#                 if next_node == target_node:
#                     return path + [next_node]
#                 if next_node not in visited:
#                     visited.add(next_node)
#                     queue.append((next_node, path + [next_node]))
        
#         return None
    
#     def choose_destination(self, all_nodes, bulkheads, hunting):
#         if hunting:
#             return self.bridge_node
#         else:
#             valid_targets = [n for n in all_nodes 
#                              if n.name != 'waypoint' 
#                              and n != self.current_node]
#             if valid_targets:
#                 return random.choice(valid_targets)
#             return None
    
#     def update(self, all_nodes, bulkheads, player_pos):
#         dist_to_player = math.hypot(self.x - player_pos[0], self.y - player_pos[1])
#         hunting = dist_to_player < 400
        
#         if self.state == 'blocked':
#             self.blocked_timer -= 1
#             offset = math.sin(pygame.time.get_ticks() / 400) * 10
#             if self.blocked_position:
#                 self.x = self.blocked_position[0] + offset
#                 self.y = self.blocked_position[1]
#             if self.blocked_timer <= 0:
#                 self.state = 'idle'
#                 self.blocked_position = None
#                 self.idle_timer = 60
#             return
        
#         if self.state == 'idle':
#             self.idle_timer -= 1
#             if self.idle_timer <= 0:
#                 self.state = 'choosing'
#             return
        
#         if self.state == 'choosing':
#             destination = self.choose_destination(all_nodes, bulkheads, hunting)
#             if destination:
#                 new_path = self.find_path_bfs(destination, bulkheads)
#                 if new_path:
#                     self.path = new_path
#                     self.state = 'moving'
#                 else:
#                     if hunting:
#                         wander_dest = self.choose_destination(all_nodes, bulkheads, False)
#                         if wander_dest:
#                             wander_path = self.find_path_bfs(wander_dest, bulkheads)
#                             if wander_path:
#                                 self.path = wander_path
#                                 self.state = 'moving'
#                                 return
#                     self.state = 'blocked'
#                     self.blocked_timer = 120
#                     self.blocked_position = (self.x, self.y)
#             else:
#                 self.state = 'idle'
#                 self.idle_timer = 90
#             return
        
#         if self.state == 'moving':
#             if not self.path:
#                 self.state = 'idle'
#                 self.idle_timer = random.randint(40, 100) if not hunting else 20
#                 return
            
#             next_node = self.path[0]
            
#             if next_node not in self.get_open_connections(self.current_node, bulkheads):
#                 self.path = []
#                 self.state = 'blocked'
#                 self.blocked_timer = 150
#                 self.blocked_position = (self.x, self.y)
#                 return
            
#             dx = next_node.x - self.x
#             dy = next_node.y - self.y
#             distance = math.hypot(dx, dy)
            
#             if distance < 2.0:
#                 self.current_node = next_node
#                 self.x = float(next_node.x)
#                 self.y = float(next_node.y)
#                 self.path.pop(0)
                
#                 if self.path:
#                     next_next = self.path[0]
#                     if next_next not in self.get_open_connections(self.current_node, bulkheads):
#                         self.path = []
#                         self.state = 'blocked'
#                         self.blocked_timer = 150
#                         self.blocked_position = (self.x, self.y)
#                 return
            
#             speed = self.move_speed * (2.0 if hunting else 1.0)
#             self.x += (dx / distance) * speed
#             self.y += (dy / distance) * speed
    
#     def draw(self, surface):
#         pulse = math.sin(pygame.time.get_ticks() / 200) * 2 + 10
#         if self.state == 'blocked':
#             pulse += 2
#             color = BRIGHT_GREEN
#         else:
#             color = BRIGHT_GREEN if self.state == 'moving' else TERMINAL_GREEN
        
#         points = [
#             (self.x, self.y - pulse),
#             (self.x + pulse, self.y),
#             (self.x, self.y + pulse),
#             (self.x - pulse, self.y)
#         ]
#         pygame.draw.polygon(surface, color, points)
#         pygame.draw.polygon(surface, BRIGHT_GREEN, points, 2)
        
#         if (pygame.time.get_ticks() // 300) % 2 == 0:
#             pygame.draw.circle(surface, color, (int(self.x), int(self.y)), int(pulse + 5), 1)

# def draw_corridor(surface, x1, y1, x2, y2, width=35):
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
#         'B6': Bulkhead('B6', 300, 195, 'h'),
#         'B7': Bulkhead('B7', 490, 195, 'h'),
#     }
    
#     # Waypoints - now with dedicated entry/exit points for the Crew room
#     waypoint_bridge_out = PathNode(180, 90, 'waypoint')
#     waypoint_galley_out_right = PathNode(360, 90, 'waypoint')
#     waypoint_galley_down = PathNode(300, 130, 'waypoint')
#     waypoint_galley_mid = PathNode(300, 195, 'waypoint')
#     waypoint_medbay_down = PathNode(490, 140, 'waypoint')
#     waypoint_medbay_mid = PathNode(490, 195, 'waypoint')
#     waypoint_medbay_out = PathNode(560, 90, 'waypoint')
    
#     # Middle deck entry/exit waypoints
#     waypoint_eng_out = PathNode(240, 300, 'waypoint')           # Engineering → middle corridor
#     waypoint_crew_left_entry = PathNode(320, 300, 'waypoint')   # Left entry to Crew room
#     waypoint_crew_right_entry = PathNode(440, 300, 'waypoint')  # Right entry to Crew room
#     waypoint_reactor_entry = PathNode(520, 300, 'waypoint')     # Reactor → middle corridor
    
#     # Cargo drops
#     waypoint_eng_down = PathNode(160, 360, 'waypoint')
#     waypoint_crew_down = PathNode(380, 340, 'waypoint')
#     waypoint_reactor_down = PathNode(580, 350, 'waypoint')
    
#     # Connections - all paths now force the alien to use proper corridor entrances
#     nodes['bridge'].add_connection(waypoint_bridge_out)
#     waypoint_bridge_out.add_connection(nodes['galley'], 'B0')
    
#     nodes['galley'].add_connection(waypoint_galley_out_right)
#     waypoint_galley_out_right.add_connection(nodes['medbay'], 'B1')
    
#     nodes['medbay'].add_connection(waypoint_medbay_out)
#     waypoint_medbay_out.add_connection(nodes['hypersleep'], 'B2')
    
#     # Galley → Crew
#     nodes['galley'].add_connection(waypoint_galley_down)
#     waypoint_galley_down.add_connection(waypoint_galley_mid)
#     waypoint_galley_mid.add_connection(waypoint_crew_left_entry, 'B6')
#     waypoint_crew_left_entry.add_connection(nodes['crew'])
    
#     # Medbay → Crew
#     nodes['medbay'].add_connection(waypoint_medbay_down)
#     waypoint_medbay_down.add_connection(waypoint_medbay_mid)
#     waypoint_medbay_mid.add_connection(waypoint_crew_right_entry, 'B7')
#     waypoint_crew_right_entry.add_connection(nodes['crew'])
    
#     # Engineering → Crew (horizontal middle deck)
#     nodes['engineering'].add_connection(waypoint_eng_out)
#     waypoint_eng_out.add_connection(waypoint_crew_left_entry)
    
#     # Crew → Reactor
#     nodes['crew'].add_connection(waypoint_crew_right_entry)
#     waypoint_crew_right_entry.add_connection(waypoint_reactor_entry)
#     waypoint_reactor_entry.add_connection(nodes['reactor'])
    
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
    
#     all_navigation_nodes = list(nodes.values()) + [
#         waypoint_bridge_out, waypoint_galley_out_right,
#         waypoint_galley_down, waypoint_galley_mid,
#         waypoint_medbay_down, waypoint_medbay_mid,
#         waypoint_medbay_out, waypoint_eng_out,
#         waypoint_crew_left_entry, waypoint_crew_right_entry,
#         waypoint_reactor_entry, waypoint_eng_down,
#         waypoint_crew_down, waypoint_reactor_down
#     ]
    
#     alien = Alien(nodes['hypersleep'], nodes['bridge'])
    
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
        
#         # Corridors (unchanged)
#         draw_corridor(screen, 180, 90, 240, 90)
#         draw_corridor(screen, 360, 90, 420, 90)
#         draw_corridor(screen, 560, 90, 620, 90)
#         draw_corridor(screen, 300, 130, 300, 260)
#         draw_corridor(screen, 490, 140, 490, 260)
#         draw_corridor(screen, 240, 300, 320, 300)   # Engineering to Crew left entry
#         draw_corridor(screen, 440, 300, 520, 300)   # Crew right entry to Reactor
#         draw_corridor(screen, 160, 360, 160, 440)
#         draw_corridor(screen, 380, 340, 380, 440)
#         draw_corridor(screen, 580, 350, 580, 440)
        
#         for room in rooms.values():
#             room.draw(screen, font_small)
        
#         pygame.draw.circle(screen, BRIGHT_GREEN, player_pos, 7)
#         if (pygame.time.get_ticks() // 500) % 2 == 0:
#             pygame.draw.circle(screen, BRIGHT_GREEN, player_pos, 12, 2)
        
#         screen.blit(font_medium.render('⚕', True, TERMINAL_GREEN), (485, 85))
#         screen.blit(font_medium.render('⚠ ⚠', True, BRIGHT_GREEN), (540, 295))
#         for i in range(3):
#             color = BRIGHT_GREEN if (pygame.time.get_ticks() // 400) % 2 else TERMINAL_GREEN
#             pygame.draw.circle(screen, color, (570 + i * 20, 300), 7)
        
#         for i in range(20):
#             pygame.draw.rect(screen, DIM_GREEN, (100 + i * 28, 480, 15, 15))
#             pygame.draw.rect(screen, DIM_GREEN, (100 + i * 28, 550, 15, 15))
        
#         airlock_color = BRIGHT_GREEN if cargo_sealed else DIM_GREEN
#         airlock_points = [(600, 510), (650, 510), (660, 525), (650, 540), (600, 540)]
#         pygame.draw.polygon(screen, airlock_color, airlock_points, 3)
#         screen.blit(font_small.render('AIRLOCK', True, airlock_color), (605, 520))
        
#         for bh in bulkheads.values():
#             bh.draw(screen, font_small)
#         if not game_won:
#             alien.draw(screen)
        
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
        
#         if game_won:
#             text = font_large.render('AIRLOCK OPENED', True, BRIGHT_GREEN)
#             screen.blit(text, text.get_rect(center=(WIDTH//2, HEIGHT//2)))
#         if game_over:
#             text = font_large.render('LIFE SIGNS NEGATIVE', True, (255, 68, 68))
#             screen.blit(text, text.get_rect(center=(WIDTH//2, HEIGHT//2)))
        
#         apply_crt_effects(screen)
#         pygame.display.flip()
#         clock.tick(60)

# if __name__ == "__main__":
#     run_airlock_puzzle("Player")




"""
Close! Just need to fix the diagonal move in/out of the "Crew" room, all other rooms seem OK.

Maybe lingers too long in Cargo Bay which makes it too easy but that can be fixed later. 
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
#     def __init__(self, start_node, bridge_node):
#         self.x = float(start_node.x)
#         self.y = float(start_node.y)
#         self.current_node = start_node
#         self.bridge_node = bridge_node
#         self.path = []
#         self.move_speed = 1.5
#         self.state = 'idle'
#         self.idle_timer = 0
#         self.blocked_timer = 0
#         self.blocked_position = None
    
#     def get_open_connections(self, node, bulkheads):
#         open_connections = []
#         for connected_node, bulkhead_name in node.connections:
#             if bulkhead_name is None:
#                 open_connections.append(connected_node)
#             elif bulkhead_name not in bulkheads or not bulkheads[bulkhead_name].sealed:
#                 open_connections.append(connected_node)
#         return open_connections
    
#     def find_path_bfs(self, target_node, bulkheads):
#         if self.current_node == target_node:
#             return []
        
#         visited = {self.current_node}
#         queue = [(self.current_node, [])]
        
#         while queue:
#             node, path = queue.pop(0)
#             for next_node in self.get_open_connections(node, bulkheads):
#                 if next_node == target_node:
#                     return path + [next_node]
#                 if next_node not in visited:
#                     visited.add(next_node)
#                     queue.append((next_node, path + [next_node]))
        
#         return None
    
#     def choose_destination(self, all_nodes, bulkheads, hunting):
#         if hunting:
#             return self.bridge_node
#         else:
#             # Allow cargo rooms – alien can now explore the whole ship including cargo
#             valid_targets = [n for n in all_nodes 
#                              if n.name != 'waypoint' 
#                              and n != self.current_node]
#             if valid_targets:
#                 return random.choice(valid_targets)
#             return None
    
#     def update(self, all_nodes, bulkheads, player_pos):
#         dist_to_player = math.hypot(self.x - player_pos[0], self.y - player_pos[1])
#         hunting = dist_to_player < 400
        
#         # BLOCKED
#         if self.state == 'blocked':
#             self.blocked_timer -= 1
#             offset = math.sin(pygame.time.get_ticks() / 400) * 10
#             if self.blocked_position:
#                 self.x = self.blocked_position[0] + offset
#                 self.y = self.blocked_position[1]
#             if self.blocked_timer <= 0:
#                 self.state = 'idle'
#                 self.blocked_position = None
#                 self.idle_timer = 60
#             return
        
#         # IDLE
#         if self.state == 'idle':
#             self.idle_timer -= 1
#             if self.idle_timer <= 0:
#                 self.state = 'choosing'
#             return
        
#         # CHOOSING
#         if self.state == 'choosing':
#             destination = self.choose_destination(all_nodes, bulkheads, hunting)
#             if destination:
#                 new_path = self.find_path_bfs(destination, bulkheads)
#                 if new_path:
#                     self.path = new_path
#                     self.state = 'moving'
#                 else:
#                     if hunting:
#                         wander_dest = self.choose_destination(all_nodes, bulkheads, False)
#                         if wander_dest:
#                             wander_path = self.find_path_bfs(wander_dest, bulkheads)
#                             if wander_path:
#                                 self.path = wander_path
#                                 self.state = 'moving'
#                                 return
#                     self.state = 'blocked'
#                     self.blocked_timer = 120
#                     self.blocked_position = (self.x, self.y)
#             else:
#                 self.state = 'idle'
#                 self.idle_timer = 90
#             return
        
#         # MOVING
#         if self.state == 'moving':
#             if not self.path:
#                 self.state = 'idle'
#                 self.idle_timer = random.randint(40, 100) if not hunting else 20
#                 return
            
#             next_node = self.path[0]
            
#             # Prevent passing through a bulkhead sealed mid-movement
#             if next_node not in self.get_open_connections(self.current_node, bulkheads):
#                 self.path = []
#                 self.state = 'blocked'
#                 self.blocked_timer = 150
#                 self.blocked_position = (self.x, self.y)
#                 return
            
#             dx = next_node.x - self.x
#             dy = next_node.y - self.y
#             distance = math.hypot(dx, dy)
            
#             if distance < 2.0:
#                 self.current_node = next_node
#                 self.x = float(next_node.x)
#                 self.y = float(next_node.y)
#                 self.path.pop(0)
                
#                 if self.path:
#                     next_next = self.path[0]
#                     if next_next not in self.get_open_connections(self.current_node, bulkheads):
#                         self.path = []
#                         self.state = 'blocked'
#                         self.blocked_timer = 150
#                         self.blocked_position = (self.x, self.y)
#                 return
            
#             speed = self.move_speed * (2.0 if hunting else 1.0)
#             self.x += (dx / distance) * speed
#             self.y += (dy / distance) * speed
    
#     def draw(self, surface):
#         pulse = math.sin(pygame.time.get_ticks() / 200) * 2 + 10
#         if self.state == 'blocked':
#             pulse += 2
#             color = BRIGHT_GREEN
#         else:
#             color = BRIGHT_GREEN if self.state == 'moving' else TERMINAL_GREEN
        
#         points = [
#             (self.x, self.y - pulse),
#             (self.x + pulse, self.y),
#             (self.x, self.y + pulse),
#             (self.x - pulse, self.y)
#         ]
#         pygame.draw.polygon(surface, color, points)
#         pygame.draw.polygon(surface, BRIGHT_GREEN, points, 2)
        
#         if (pygame.time.get_ticks() // 300) % 2 == 0:
#             pygame.draw.circle(surface, color, (int(self.x), int(self.y)), int(pulse + 5), 1)

# def draw_corridor(surface, x1, y1, x2, y2, width=35):
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
#         'B6': Bulkhead('B6', 300, 195, 'h'),
#         'B7': Bulkhead('B7', 490, 195, 'h'),
#     }
    
#     # Waypoints
#     waypoint_bridge_out = PathNode(180, 90, 'waypoint')
#     waypoint_galley_out_right = PathNode(360, 90, 'waypoint')
#     waypoint_galley_down = PathNode(300, 130, 'waypoint')
#     waypoint_galley_mid = PathNode(300, 195, 'waypoint')
#     waypoint_medbay_down = PathNode(490, 140, 'waypoint')
#     waypoint_medbay_mid = PathNode(490, 195, 'waypoint')
#     waypoint_medbay_out = PathNode(560, 90, 'waypoint')
#     waypoint_eng_out = PathNode(240, 300, 'waypoint')
#     waypoint_crew_out_right = PathNode(440, 300, 'waypoint')
#     waypoint_eng_down = PathNode(160, 360, 'waypoint')
#     waypoint_crew_down = PathNode(380, 340, 'waypoint')
#     waypoint_reactor_down = PathNode(580, 350, 'waypoint')
    
#     # Connections – all vertical paths now properly routed through corridors
#     nodes['bridge'].add_connection(waypoint_bridge_out)
#     waypoint_bridge_out.add_connection(nodes['galley'], 'B0')
    
#     nodes['galley'].add_connection(waypoint_galley_out_right)
#     waypoint_galley_out_right.add_connection(nodes['medbay'], 'B1')
    
#     nodes['medbay'].add_connection(waypoint_medbay_out)
#     waypoint_medbay_out.add_connection(nodes['hypersleep'], 'B2')
    
#     # Galley → Crew
#     nodes['galley'].add_connection(waypoint_galley_down)
#     waypoint_galley_down.add_connection(waypoint_galley_mid)
#     waypoint_galley_mid.add_connection(nodes['crew'], 'B6')
    
#     # Medbay → Crew (fixed – no diagonal floating)
#     nodes['medbay'].add_connection(waypoint_medbay_down)
#     waypoint_medbay_down.add_connection(waypoint_medbay_mid)
#     waypoint_medbay_mid.add_connection(nodes['crew'], 'B7')
    
#     # Middle deck horizontal
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
    
#     all_navigation_nodes = list(nodes.values()) + [
#         waypoint_bridge_out, waypoint_galley_out_right,
#         waypoint_galley_down, waypoint_galley_mid,
#         waypoint_medbay_down, waypoint_medbay_mid,
#         waypoint_medbay_out, waypoint_eng_out,
#         waypoint_crew_out_right, waypoint_eng_down,
#         waypoint_crew_down, waypoint_reactor_down
#     ]
    
#     alien = Alien(nodes['hypersleep'], nodes['bridge'])
    
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
        
#         # Corridors
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
        
#         # Rooms
#         for room in rooms.values():
#             room.draw(screen, font_small)
        
#         # Player
#         pygame.draw.circle(screen, BRIGHT_GREEN, player_pos, 7)
#         if (pygame.time.get_ticks() // 500) % 2 == 0:
#             pygame.draw.circle(screen, BRIGHT_GREEN, player_pos, 12, 2)
        
#         # Details
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
        
#         # Bulkheads & alien
#         for bh in bulkheads.values():
#             bh.draw(screen, font_small)
#         if not game_won:
#             alien.draw(screen)
        
#         # Terminal
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

# if __name__ == "__main__":
#     run_airlock_puzzle("Player")




"""
Looking better: Alien now respects bulkheads and moves around more fluedly; sorting rogue Crew diagonal move.

Alien never moves down to Cargo Bay; has to explore whole ship.
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
#     def __init__(self, start_node, bridge_node):
#         self.x = float(start_node.x)
#         self.y = float(start_node.y)
#         self.current_node = start_node
#         self.bridge_node = bridge_node
#         self.path = []
#         self.move_speed = 1.5
#         self.state = 'idle'  # idle, moving, blocked, choosing
#         self.idle_timer = 0
#         self.blocked_timer = 0
#         self.blocked_position = None
    
#     def get_open_connections(self, node, bulkheads):
#         """Get all connections from a node that aren't blocked by sealed bulkheads"""
#         open_connections = []
#         for connected_node, bulkhead_name in node.connections:
#             if bulkhead_name is None:
#                 open_connections.append(connected_node)
#             elif bulkhead_name not in bulkheads or not bulkheads[bulkhead_name].sealed:
#                 open_connections.append(connected_node)
#         return open_connections
    
#     def find_path_bfs(self, target_node, bulkheads):
#         """Find shortest path using BFS, respecting sealed bulkheads"""
#         if self.current_node == target_node:
#             return []
        
#         visited = {self.current_node}
#         queue = [(self.current_node, [])]
        
#         while queue:
#             node, path = queue.pop(0)
            
#             for next_node in self.get_open_connections(node, bulkheads):
#                 if next_node == target_node:
#                     return path + [next_node]
                
#                 if next_node not in visited:
#                     visited.add(next_node)
#                     queue.append((next_node, path + [next_node]))
        
#         return None  # No path found
    
#     def choose_destination(self, all_nodes, bulkheads, hunting):
#         """Choose where to go next"""
#         if hunting:
#             return self.bridge_node
#         else:
#             valid_targets = [n for n in all_nodes 
#                            if n.name not in ['waypoint', 'cargo'] 
#                            and n != self.current_node]
#             if valid_targets:
#                 return random.choice(valid_targets)
#             return None
    
#     def update(self, all_nodes, bulkheads, player_pos):
#         """Update alien position and behavior"""
        
#         dist_to_player = math.hypot(self.x - player_pos[0], self.y - player_pos[1])
#         hunting = dist_to_player < 400
        
#         # BLOCKED state
#         if self.state == 'blocked':
#             self.blocked_timer -= 1
#             offset = math.sin(pygame.time.get_ticks() / 400) * 10
#             if self.blocked_position:
#                 self.x = self.blocked_position[0] + offset
#                 self.y = self.blocked_position[1]
            
#             if self.blocked_timer <= 0:
#                 self.state = 'idle'
#                 self.blocked_position = None
#                 self.idle_timer = 60
#             return
        
#         # IDLE state
#         if self.state == 'idle':
#             self.idle_timer -= 1
#             if self.idle_timer <= 0:
#                 self.state = 'choosing'
#             return
        
#         # CHOOSING state
#         if self.state == 'choosing':
#             destination = self.choose_destination(all_nodes, bulkheads, hunting)
#             if destination:
#                 new_path = self.find_path_bfs(destination, bulkheads)
#                 if new_path:
#                     self.path = new_path
#                     self.state = 'moving'
#                 else:
#                     # Can't reach chosen destination
#                     if hunting:
#                         # Bridge unreachable while hunting → try wandering instead
#                         wander_dest = self.choose_destination(all_nodes, bulkheads, False)
#                         if wander_dest:
#                             wander_path = self.find_path_bfs(wander_dest, bulkheads)
#                             if wander_path:
#                                 self.path = wander_path
#                                 self.state = 'moving'
#                                 return
#                     # Still no path → become blocked
#                     self.state = 'blocked'
#                     self.blocked_timer = 120
#                     self.blocked_position = (self.x, self.y)
#             else:
#                 self.state = 'idle'
#                 self.idle_timer = 90
#             return
        
#         # MOVING state
#         if self.state == 'moving':
#             if not self.path:
#                 self.state = 'idle'
#                 self.idle_timer = random.randint(40, 100) if not hunting else 20
#                 return
            
#             next_node = self.path[0]
            
#             # Critical fix: check if the CURRENT segment is still open
#             if next_node not in self.get_open_connections(self.current_node, bulkheads):
#                 self.path = []
#                 self.state = 'blocked'
#                 self.blocked_timer = 150
#                 self.blocked_position = (self.x, self.y)
#                 return
            
#             dx = next_node.x - self.x
#             dy = next_node.y - self.y
#             distance = math.hypot(dx, dy)
            
#             if distance < 2.0:
#                 self.current_node = next_node
#                 self.x = float(next_node.x)
#                 self.y = float(next_node.y)
#                 self.path.pop(0)
                
#                 # Check next segment after arriving at node
#                 if self.path:
#                     next_next = self.path[0]
#                     if next_next not in self.get_open_connections(self.current_node, bulkheads):
#                         self.path = []
#                         self.state = 'blocked'
#                         self.blocked_timer = 150
#                         self.blocked_position = (self.x, self.y)
#                 return
            
#             speed = self.move_speed * (2.0 if hunting else 1.0)
#             self.x += (dx / distance) * speed
#             self.y += (dy / distance) * speed
    
#     def draw(self, surface):
#         pulse = math.sin(pygame.time.get_ticks() / 200) * 2 + 10
        
#         if self.state == 'blocked':
#             pulse += 2
#             color = BRIGHT_GREEN
#         else:
#             color = BRIGHT_GREEN if self.state == 'moving' else TERMINAL_GREEN
        
#         points = [
#             (self.x, self.y - pulse),
#             (self.x + pulse, self.y),
#             (self.x, self.y + pulse),
#             (self.x - pulse, self.y)
#         ]
#         pygame.draw.polygon(surface, color, points)
#         pygame.draw.polygon(surface, BRIGHT_GREEN, points, 2)
        
#         if (pygame.time.get_ticks() // 300) % 2 == 0:
#             pygame.draw.circle(surface, color, (int(self.x), int(self.y)), int(pulse + 5), 1)

# def draw_corridor(surface, x1, y1, x2, y2, width=35):
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
    
#     # Waypoint nodes
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
    
#     # Connections
#     nodes['bridge'].add_connection(waypoint_bridge_out)
#     waypoint_bridge_out.add_connection(nodes['galley'], 'B0')
    
#     nodes['galley'].add_connection(waypoint_galley_out_right)
#     waypoint_galley_out_right.add_connection(nodes['medbay'], 'B1')
    
#     nodes['medbay'].add_connection(waypoint_medbay_out)
#     waypoint_medbay_out.add_connection(nodes['hypersleep'], 'B2')
    
#     nodes['galley'].add_connection(waypoint_galley_down)
#     waypoint_galley_down.add_connection(waypoint_galley_mid)
#     waypoint_galley_mid.add_connection(nodes['crew'], 'B6')
    
#     nodes['medbay'].add_connection(waypoint_medbay_down)
#     waypoint_medbay_down.add_connection(waypoint_medbay_mid)
#     waypoint_medbay_mid.add_connection(nodes['crew'], 'B7')
    
#     nodes['engineering'].add_connection(waypoint_eng_out)
#     waypoint_eng_out.add_connection(nodes['crew'])
    
#     nodes['crew'].add_connection(waypoint_crew_out_right)
#     waypoint_crew_out_right.add_connection(nodes['reactor'])
    
#     nodes['engineering'].add_connection(waypoint_eng_down)
#     waypoint_eng_down.add_connection(nodes['cargo_left'], 'B3')
    
#     nodes['crew'].add_connection(waypoint_crew_down)
#     waypoint_crew_down.add_connection(nodes['cargo_center'], 'B4')
    
#     nodes['reactor'].add_connection(waypoint_reactor_down)
#     waypoint_reactor_down.add_connection(nodes['cargo_right'], 'B5')
    
#     nodes['cargo_left'].add_connection(nodes['cargo_center'])
#     nodes['cargo_center'].add_connection(nodes['cargo_right'])
    
#     all_navigation_nodes = list(nodes.values()) + [
#         waypoint_bridge_out, waypoint_galley_out_right, waypoint_galley_down, waypoint_galley_mid,
#         waypoint_medbay_out, waypoint_medbay_down, waypoint_medbay_mid, waypoint_eng_out,
#         waypoint_crew_out_right, waypoint_eng_down, waypoint_crew_down, waypoint_reactor_down
#     ]
    
#     alien = Alien(nodes['hypersleep'], nodes['bridge'])
    
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
        
#         for room in rooms.values():
#             room.draw(screen, font_small)
        
#         pygame.draw.circle(screen, BRIGHT_GREEN, player_pos, 7)
#         if (pygame.time.get_ticks() // 500) % 2 == 0:
#             pygame.draw.circle(screen, BRIGHT_GREEN, player_pos, 12, 2)
        
#         screen.blit(font_medium.render('⚕', True, TERMINAL_GREEN), (485, 85))
#         screen.blit(font_medium.render('⚠ ⚠', True, BRIGHT_GREEN), (540, 295))
#         for i in range(3):
#             color = BRIGHT_GREEN if (pygame.time.get_ticks() // 400) % 2 else TERMINAL_GREEN
#             pygame.draw.circle(screen, color, (570 + i * 20, 300), 7)
        
#         for i in range(20):
#             pygame.draw.rect(screen, DIM_GREEN, (100 + i * 28, 480, 15, 15))
#             pygame.draw.rect(screen, DIM_GREEN, (100 + i * 28, 550, 15, 15))
        
#         airlock_color = BRIGHT_GREEN if cargo_sealed else DIM_GREEN
#         airlock_points = [(600, 510), (650, 510), (660, 525), (650, 540), (600, 540)]
#         pygame.draw.polygon(screen, airlock_color, airlock_points, 3)
#         screen.blit(font_small.render('AIRLOCK', True, airlock_color), (605, 520))
        
#         for bh in bulkheads.values():
#             bh.draw(screen, font_small)
#         if not game_won:
#             alien.draw(screen)
        
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
        
#         if game_won:
#             text = font_large.render('AIRLOCK OPENED', True, BRIGHT_GREEN)
#             screen.blit(text, text.get_rect(center=(WIDTH//2, HEIGHT//2)))
#         if game_over:
#             text = font_large.render('LIFE SIGNS NEGATIVE', True, (255, 68, 68))
#             screen.blit(text, text.get_rect(center=(WIDTH//2, HEIGHT//2)))
        
#         apply_crt_effects(screen)
#         pygame.display.flip()
#         clock.tick(60)






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
#     def __init__(self, start_node, bridge_node):
#         self.x = float(start_node.x)
#         self.y = float(start_node.y)
#         self.current_node = start_node
#         self.bridge_node = bridge_node
#         self.path = []
#         self.move_speed = 1.5
#         self.state = 'idle'  # idle, moving, blocked
#         self.idle_timer = 0
#         self.blocked_timer = 0
#         self.blocked_position = None
    
#     def get_open_connections(self, node, bulkheads):
#         """Get all connections from a node that aren't blocked by sealed bulkheads"""
#         open_connections = []
#         for connected_node, bulkhead_name in node.connections:
#             if bulkhead_name is None:
#                 # No bulkhead, always open
#                 open_connections.append(connected_node)
#             elif bulkhead_name not in bulkheads or not bulkheads[bulkhead_name].sealed:
#                 # Bulkhead exists but not sealed, or doesn't exist
#                 open_connections.append(connected_node)
#         return open_connections
    
#     def find_path_bfs(self, target_node, bulkheads):
#         """Find shortest path using BFS, respecting sealed bulkheads"""
#         if self.current_node == target_node:
#             return []
        
#         visited = {self.current_node}
#         queue = [(self.current_node, [])]
        
#         while queue:
#             node, path = queue.pop(0)
            
#             for next_node in self.get_open_connections(node, bulkheads):
#                 if next_node == target_node:
#                     return path + [next_node]
                
#                 if next_node not in visited:
#                     visited.add(next_node)
#                     queue.append((next_node, path + [next_node]))
        
#         return None  # No path found
    
#     def choose_destination(self, all_nodes, bulkheads, hunting):
#         """Choose where to go next"""
#         if hunting:
#             # Try to reach the bridge
#             return self.bridge_node
#         else:
#             # Wander to a random accessible room (not waypoints or cargo)
#             valid_targets = [n for n in all_nodes 
#                            if n.name not in ['waypoint', 'cargo'] 
#                            and n != self.current_node]
            
#             if valid_targets:
#                 return random.choice(valid_targets)
#             return None
    
#     def update(self, all_nodes, bulkheads, player_pos):
#         """Update alien position and behavior"""
        
#         # Determine if hunting based on distance to player
#         dist_to_player = math.hypot(self.x - player_pos[0], self.y - player_pos[1])
#         hunting = dist_to_player < 400
        
#         # State: BLOCKED - trying to get through sealed bulkhead
#         if self.state == 'blocked':
#             self.blocked_timer -= 1
#             # Prowl near the blocked position
#             offset = math.sin(pygame.time.get_ticks() / 400) * 10
#             if self.blocked_position:
#                 self.x = self.blocked_position[0] + offset
#                 self.y = self.blocked_position[1]
            
#             if self.blocked_timer <= 0:
#                 self.state = 'idle'
#                 self.blocked_position = None
#                 self.idle_timer = 60
#             return
        
#         # State: IDLE - waiting/thinking
#         if self.state == 'idle':
#             self.idle_timer -= 1
#             if self.idle_timer <= 0:
#                 self.state = 'choosing'
#             return
        
#         # State: CHOOSING - pick new destination
#         if self.state == 'choosing':
#             destination = self.choose_destination(all_nodes, bulkheads, hunting)
#             if destination:
#                 new_path = self.find_path_bfs(destination, bulkheads)
#                 if new_path:
#                     self.path = new_path
#                     self.state = 'moving'
#                 else:
#                     # Path blocked - investigate the blockage
#                     self.state = 'blocked'
#                     self.blocked_timer = 120
#                     self.blocked_position = (self.x, self.y)
#             else:
#                 # No valid destinations
#                 self.state = 'idle'
#                 self.idle_timer = 90
#             return
        
#         # State: MOVING - follow the path
#         if self.state == 'moving':
#             if not self.path:
#                 # Reached destination
#                 self.state = 'idle'
#                 self.idle_timer = random.randint(40, 100) if not hunting else 20
#                 return
            
#             # Get next waypoint
#             next_node = self.path[0]
#             dx = next_node.x - self.x
#             dy = next_node.y - self.y
#             distance = math.hypot(dx, dy)
            
#             # Check if we've reached this waypoint
#             if distance < 2.0:
#                 self.current_node = next_node
#                 self.x = float(next_node.x)
#                 self.y = float(next_node.y)
#                 self.path.pop(0)
                
#                 # Check if next step in path is blocked
#                 if self.path:
#                     next_next = self.path[0]
#                     if next_next not in self.get_open_connections(self.current_node, bulkheads):
#                         # Path blocked mid-journey
#                         self.path = []
#                         self.state = 'blocked'
#                         self.blocked_timer = 150
#                         self.blocked_position = (self.x, self.y)
#                 return
            
#             # Move toward next waypoint
#             speed = self.move_speed * (2.0 if hunting else 1.0)
#             self.x += (dx / distance) * speed
#             self.y += (dy / distance) * speed
    
#     def draw(self, surface):
#         """Draw the alien as a pulsing diamond"""
#         pulse = math.sin(pygame.time.get_ticks() / 200) * 2 + 10
        
#         # Larger pulse when hunting or blocked
#         if self.state == 'blocked':
#             pulse += 2
#             color = BRIGHT_GREEN
#         else:
#             color = BRIGHT_GREEN if self.state == 'moving' else TERMINAL_GREEN
        
#         # Diamond shape
#         points = [
#             (self.x, self.y - pulse),
#             (self.x + pulse, self.y),
#             (self.x, self.y + pulse),
#             (self.x - pulse, self.y)
#         ]
#         pygame.draw.polygon(surface, color, points)
#         pygame.draw.polygon(surface, BRIGHT_GREEN, points, 2)
        
#         # Scanning ring
#         if (pygame.time.get_ticks() // 300) % 2 == 0:
#             pygame.draw.circle(surface, color, (int(self.x), int(self.y)), int(pulse + 5), 1)

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
    
#     # Vertical drops with bulkheads
#     nodes['galley'].add_connection(waypoint_galley_down)
#     waypoint_galley_down.add_connection(waypoint_galley_mid)
#     waypoint_galley_mid.add_connection(nodes['crew'], 'B6')
    
#     nodes['medbay'].add_connection(waypoint_medbay_down)
#     waypoint_medbay_down.add_connection(waypoint_medbay_mid)
#     waypoint_medbay_mid.add_connection(nodes['crew'], 'B7')
    
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
    
#     # All nodes for pathfinding
#     all_navigation_nodes = list(nodes.values()) + [
#         waypoint_bridge_out, waypoint_galley_out_right, waypoint_galley_down, waypoint_galley_mid,
#         waypoint_medbay_out, waypoint_medbay_down, waypoint_medbay_mid, waypoint_eng_out,
#         waypoint_crew_out_right, waypoint_eng_down, waypoint_crew_down, waypoint_reactor_down
#     ]
    
#     # Initialize alien - start at hypersleep
#     alien = Alien(nodes['hypersleep'], nodes['bridge'])
    
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
