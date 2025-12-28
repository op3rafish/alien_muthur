"""
ALIEN CHRONOS: FINAL AIRLOCK PUZZLE
"""

"""
Alien now fades in and out to make the game harder!
Looks fantastic.
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
        self.move_speed = 2.0  # Increased base speed
        self.state = 'idle'
        self.idle_timer = 0
        self.blocked_timer = 0
        self.blocked_position = None
        self.prowl_target = None  # For exploring sealed bulkheads
        self.aggression_level = 0  # Increases over time
        self.last_room_visit = {}  # Track room visits for stalking behavior
        self.fade_cycle = 0  # For smooth fading effect
    
    def get_sealed_bulkhead_position(self, node, bulkheads):
        """Find position of nearest sealed bulkhead from current node - stay on our side"""
        for connected_node, bulkhead_name in node.connections:
            if bulkhead_name and bulkhead_name in bulkheads and bulkheads[bulkhead_name].sealed:
                bh = bulkheads[bulkhead_name]
                # Calculate position on OUR side of the bulkhead (30 pixels back from it)
                dx = bh.x - node.x
                dy = bh.y - node.y
                dist = math.hypot(dx, dy)
                if dist > 0:
                    # Position 30 pixels away from bulkhead toward our current node
                    offset = 30
                    target_x = bh.x - (dx / dist) * offset
                    target_y = bh.y - (dy / dist) * offset
                    return (target_x, target_y)
        return None
    
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
            # When hunting, 80% chance to go to bridge, 20% to stalk nearby
            if random.random() < 0.8:
                return self.bridge_node
            else:
                # Stalk nearby rooms
                nearby = [n for n in all_nodes 
                         if n.name != 'waypoint' 
                         and n != self.current_node
                         and math.hypot(n.x - self.x, n.y - self.y) < 300]
                return random.choice(nearby) if nearby else self.bridge_node
        else:
            # Xenomorph behavior: prefer rooms not recently visited (stalking pattern)
            valid_targets = [n for n in all_nodes 
                             if n.name != 'waypoint' 
                             and n != self.current_node]
            if valid_targets:
                # Weight selection toward less-visited rooms
                time_now = pygame.time.get_ticks()
                weights = []
                for node in valid_targets:
                    last_visit = self.last_room_visit.get(node.name, 0)
                    time_since = time_now - last_visit
                    weight = max(1, time_since / 1000)  # More weight for rooms not visited recently
                    weights.append(weight)
                
                # Add some randomness - 30% chance to ignore weights and just pick random
                if random.random() < 0.3:
                    return random.choice(valid_targets)
                
                # Weighted random choice
                total = sum(weights)
                r = random.uniform(0, total)
                cumulative = 0
                for node, weight in zip(valid_targets, weights):
                    cumulative += weight
                    if r <= cumulative:
                        return node
                return valid_targets[-1]
            return None
    
    def update(self, all_nodes, bulkheads, player_pos):
        # Increase aggression over time (xenomorph gets more aggressive)
        self.aggression_level = min(2.0, self.aggression_level + 0.001)
        
        # Update fade cycle for smooth fading effect
        self.fade_cycle = (self.fade_cycle + 1) % 1000
        
        dist_to_player = math.hypot(self.x - player_pos[0], self.y - player_pos[1])
        hunting = dist_to_player < 350 + (self.aggression_level * 50)  # Increased detection range
        
        if self.state == 'blocked':
            self.blocked_timer -= 1
            
            # More aggressive prowling when blocked
            if self.prowl_target:
                dx = self.prowl_target[0] - self.x
                dy = self.prowl_target[1] - self.y
                dist = math.hypot(dx, dy)
                
                if dist > 5:
                    move_speed = 1.2 + self.aggression_level * 0.3  # Faster prowling
                    self.x += (dx / dist) * move_speed
                    self.y += (dy / dist) * move_speed
                else:
                    # Aggressive pacing - faster, more erratic
                    base_x = self.prowl_target[0]
                    base_y = self.prowl_target[1]
                    
                    if abs(base_x - self.current_node.x) > abs(base_y - self.current_node.y):
                        # Vertical bulkhead - prowl up/down more aggressively
                        offset_y = math.sin(pygame.time.get_ticks() / 200) * 18
                        offset_y += math.sin(pygame.time.get_ticks() / 150) * 6  # Add jitter
                        self.x = base_x
                        self.y = base_y + offset_y
                    else:
                        # Horizontal bulkhead - prowl left/right
                        offset_x = math.sin(pygame.time.get_ticks() / 200) * 18
                        offset_x += math.sin(pygame.time.get_ticks() / 150) * 6  # Add jitter
                        self.x = base_x + offset_x
                        self.y = base_y
            elif self.blocked_position:
                # Frustrated prowling
                offset = math.sin(pygame.time.get_ticks() / 300) * 12
                offset += math.sin(pygame.time.get_ticks() / 180) * 5
                self.x = self.blocked_position[0] + offset
                self.y = self.blocked_position[1]
            
            if self.blocked_timer <= 0:
                self.state = 'idle'
                self.blocked_position = None
                self.prowl_target = None
                self.idle_timer = 30 + int(30 / (self.aggression_level + 1))  # Shorter idle when aggressive
            return
        
        if self.state == 'idle':
            self.idle_timer -= 1
            # Xenomorph twitches while idle
            if random.random() < 0.1:
                self.x += random.uniform(-2, 2)
                self.y += random.uniform(-2, 2)
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
                    # Mark room as visited
                    if destination.name != 'waypoint':
                        self.last_room_visit[destination.name] = pygame.time.get_ticks()
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
                    self.blocked_timer = 150 - int(self.aggression_level * 30)  # Less patient when aggressive
                    self.blocked_position = (self.x, self.y)
                    self.prowl_target = self.get_sealed_bulkhead_position(self.current_node, bulkheads)
            else:
                self.state = 'idle'
                self.idle_timer = 60 - int(self.aggression_level * 20)
            return
        
        # MOVING - now 100% airtight against sealed bulkheads
        if self.state == 'moving':
            if not self.path:
                self.state = 'idle'
                # Shorter idle times, more aggressive
                self.idle_timer = random.randint(20, 60) if not hunting else random.randint(10, 25)
                return
            
            next_node = self.path[0]
            
            # CRITICAL: Check every single frame if the current segment is still open
            if next_node not in self.get_open_connections(self.current_node, bulkheads):
                self.path = []
                self.state = 'blocked'
                self.blocked_timer = 150 - int(self.aggression_level * 30)
                self.blocked_position = (self.x, self.y)
                self.prowl_target = self.get_sealed_bulkhead_position(self.current_node, bulkheads)
                return
            
            dx = next_node.x - self.x
            dy = next_node.y - self.y
            distance = math.hypot(dx, dy)
            
            # Only snap to node when extremely close - prevents overshooting sealed gates
            if distance < 2.0:
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
                        self.blocked_timer = 150 - int(self.aggression_level * 30)
                        self.blocked_position = (self.x, self.y)
                        self.prowl_target = self.get_sealed_bulkhead_position(self.current_node, bulkheads)
                return
            
            # Xenomorph movement - faster when hunting, unpredictable speed variations
            base_speed = self.move_speed * (1.0 + self.aggression_level * 0.3)
            if hunting:
                # Burst speed when hunting
                speed_multiplier = 1.8 + math.sin(pygame.time.get_ticks() / 400) * 0.3
            else:
                # Variable patrol speed - sometimes slow stalking, sometimes quick darts
                speed_multiplier = 0.8 + math.sin(pygame.time.get_ticks() / 800) * 0.4
                # Random speed bursts
                if random.random() < 0.05:
                    speed_multiplier = 1.5
            
            speed = min(base_speed * speed_multiplier, distance)
            self.x += (dx / distance) * speed
            self.y += (dy / distance) * speed
    
    def draw(self, surface):
        # Smooth fading in and out based on fade cycle
        fade_value = math.sin(self.fade_cycle / 80.0) * 0.5 + 0.5  # Oscillates 0-1
        
        # Heavy sensor glitches on the alien - harder to track when moving
        if self.state == 'moving':
            if fade_value < 0.25:  # Fade out more when moving
                return
            # Random dropouts when moving fast
            if random.random() < 0.15:
                return
        else:
            if fade_value < 0.15:  # Less fade-out when stationary
                return
            if random.random() < 0.08:
                return
        
        # More aggressive pulsing based on state and aggression
        base_pulse = 10 + self.aggression_level * 2
        pulse = math.sin(pygame.time.get_ticks() / 200) * 3 + base_pulse
        
        if self.state == 'blocked':
            pulse += 3
            color = BRIGHT_GREEN
        elif self.state == 'moving':
            # Pulsing gets more intense when moving
            pulse += math.sin(pygame.time.get_ticks() / 100) * 2
            color = BRIGHT_GREEN
        else:
            color = TERMINAL_GREEN
        
        # Apply fade to color brightness
        if fade_value < 0.5:
            # Fade to dim when signal is weak
            color = DIM_GREEN
        elif fade_value < 0.7 and self.state == 'moving':
            # More interference when moving
            color = DIM_GREEN
        
        points = [
            (self.x, self.y - pulse),
            (self.x + pulse, self.y),
            (self.x, self.y + pulse),
            (self.x - pulse, self.y)
        ]
        pygame.draw.polygon(surface, color, points)
        pygame.draw.polygon(surface, BRIGHT_GREEN, points, 2)
        
        # Radar rings fade with signal strength
        if fade_value > 0.4:
            if (pygame.time.get_ticks() // 250) % 2 == 0:
                pygame.draw.circle(surface, color, (int(self.x), int(self.y)), int(pulse + 6), 1)
        if self.state == 'moving' and fade_value > 0.5:
            if (pygame.time.get_ticks() // 150) % 2 == 0:
                pygame.draw.circle(surface, color, (int(self.x), int(self.y)), int(pulse + 10), 1)

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
    waypoint_crew_right_exit = PathNode(440, 300, 'waypoint')
    waypoint_crew_to_reactor = PathNode(480, 300, 'waypoint')
    waypoint_reactor_entry = PathNode(520, 300, 'waypoint')
    
    # Fix for B5 corridor - keep alien strictly in corridor bounds
    waypoint_crew_to_b5_horizontal = PathNode(490, 300, 'waypoint')
    waypoint_crew_to_b5_corner = PathNode(490, 340, 'waypoint')
    waypoint_b5_bottom = PathNode(490, 240, 'waypoint')
    waypoint_crew_up_to_b5 = PathNode(490, 195, 'waypoint')
    
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
    waypoint_medbay_mid.add_connection(waypoint_crew_up_to_b5, 'B5')
    waypoint_crew_up_to_b5.add_connection(waypoint_b5_bottom)
    waypoint_b5_bottom.add_connection(waypoint_crew_to_b5_horizontal)
    
    # Connect crew room - move horizontally first at y=300
    nodes['crew'].add_connection(waypoint_crew_right_exit)
    waypoint_crew_right_exit.add_connection(waypoint_crew_to_b5_horizontal)
    
    # Crew to Reactor path - straight along y=300 corridor
    waypoint_crew_to_b5_horizontal.add_connection(waypoint_crew_to_reactor)
    waypoint_crew_to_reactor.add_connection(waypoint_reactor_entry)
    waypoint_reactor_entry.add_connection(nodes['reactor'])
    
    nodes['engineering'].add_connection(waypoint_eng_out)
    waypoint_eng_out.add_connection(waypoint_crew_left_entry)
    
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
        waypoint_crew_right_exit, waypoint_crew_to_reactor,
        waypoint_crew_up_to_b5, waypoint_b5_bottom, 
        waypoint_crew_to_b5_horizontal,
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
        
        # Minimal system flicker - very rare
        display_glitch = random.random()
        alpha_multiplier = 1.0
        if display_glitch < 0.005:  # 0.5% rare major glitch
            alpha_multiplier = 0.6
        
        # Apply flicker effect by adjusting color brightness
        def flicker_color(color, mult=alpha_multiplier):
            if mult >= 1.0:
                return color
            return tuple(int(c * mult) for c in color)
        
        corridor_color = flicker_color(TERMINAL_GREEN)
        
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
        
        # Rooms rarely flicker
        for room in rooms.values():
            if random.random() < 0.005:  # 0.5% chance each room briefly disappears
                continue
            room.draw(screen, font_small)
        
        pygame.draw.circle(screen, BRIGHT_GREEN, player_pos, 7)
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            pygame.draw.circle(screen, BRIGHT_GREEN, player_pos, 12, 2)
        
        # Very rare flicker on medical and reactor warnings
        if random.random() > 0.01:
            screen.blit(font_medium.render('⚕', True, flicker_color(TERMINAL_GREEN)), (485, 85))
        if random.random() > 0.01:
            screen.blit(font_medium.render('⚠ ⚠', True, flicker_color(BRIGHT_GREEN)), (540, 295))
        
        for i in range(3):
            color = BRIGHT_GREEN if (pygame.time.get_ticks() // 400) % 2 else TERMINAL_GREEN
            pygame.draw.circle(screen, flicker_color(color), (570 + i * 20, 285), 7)
        
        for i in range(20):
            pygame.draw.rect(screen, flicker_color(DIM_GREEN), (100 + i * 28, 480, 15, 15))
            pygame.draw.rect(screen, flicker_color(DIM_GREEN), (100 + i * 28, 550, 15, 15))
        
        airlock_color = flicker_color(BRIGHT_GREEN if cargo_sealed else DIM_GREEN)
        airlock_points = [(600, 510), (650, 510), (660, 525), (650, 540), (600, 540)]
        pygame.draw.polygon(screen, airlock_color, airlock_points, 3)
        screen.blit(font_small.render('AIRLOCK', True, airlock_color), (520, 520))
        
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
