"""
Maze routing game for ALIEN: CHRONOS
"""

import pygame
import sys
from config import (CELL_SIZE, GRID_WIDTH, GRID_HEIGHT, TERMINAL_GREEN, 
                   BRIGHT_GREEN, DIM_GREEN, TERMINAL_BLACK, POWER_COLOR, 
                   DATA_COLOR, COOLANT_COLOR)

def add_wall_segments(walls, wall_type, positions):
    """Helper to add multiple wall segments of same type"""
    for x, y, length in positions:
        walls.append((wall_type, x, y, length))

def create_maze_walls():
    """Generate the maze wall structure"""
    walls = []
    
    # Border walls with gaps for entry/exit points
    border_walls = [
        ('h', 0, 0, 50),
        ('h', 0, 24, 50),
        ('v', 0, 0, 6), ('v', 0, 7, 5), ('v', 0, 13, 5), ('v', 0, 19, 6),
        ('v', 49, 0, 6), ('v', 49, 7, 5), 
        ('v', 49, 13, 5), ('v', 49, 19, 6)
    ]
    walls.extend(border_walls)
    
    # Horizontal corridors
    corridor_patterns = [
        (2, [(3,3), (8,3), (13,3), (18,3), (23,3), (28,3), (33,3), (38,3), (43,4)]),
        (5, [(4,3), (9,3), (14,3), (19,3), (24,3), (29,3), (34,3), (39,3), (44,3)]),
        (8, [(5,3), (10,3), (15,3), (20,3), (25,3), (30,3), (35,3), (40,3), (45,2)]),
        (12, [(6,2), (11,2), (16,2), (21,2), (26,2), (31,2), (36,2), (41,2), (46,1)]),
        (16, [(4,3), (9,3), (14,3), (19,3), (24,3), (29,3), (34,3), (39,3), (44,3)]),
        (19, [(3,3), (8,3), (13,3), (18,3), (23,3), (28,3), (33,3), (38,3), (43,4)]),
        (22, [(5,3), (10,3), (15,3), (20,3), (25,3), (30,3), (35,3), (40,3), (45,2)])
    ]
    
    for y, segments in corridor_patterns:
        add_wall_segments(walls, 'h', [(x, y, length) for x, length in segments])
    
    # Vertical barriers
    vertical_columns = [
        (4, [(3,1), (6,1), (9,1), (12,1), (15,1), (18,1), (21,1)]),
        (7, [(1,1), (4,1), (7,1), (10,1), (13,1), (16,1), (19,1), (22,1)]),
        (11, [(1,1), (4,1), (7,1), (10,1), (13,1), (16,1), (19,1), (22,1)]),
        (15, [(2,1), (5,1), (8,1), (11,1), (14,1), (17,1), (20,1), (23,1)]),
        (19, [(1,1), (4,1), (7,1), (10,1), (13,1), (16,1), (19,1), (22,1)]),
        (23, [(2,1), (5,1), (8,1), (11,1), (14,1), (17,1), (20,1), (23,1)]),
        (27, [(1,1), (4,1), (7,1), (10,1), (13,1), (16,1), (19,1), (22,1)]),
        (31, [(2,1), (5,1), (8,1), (11,1), (14,1), (17,1), (20,1), (23,1)]),
        (35, [(1,1), (4,1), (7,1), (10,1), (13,1), (16,1), (19,1), (22,1)]),
        (39, [(2,1), (5,1), (8,1), (11,1), (14,1), (17,1), (20,1), (23,1)]),
        (43, [(1,1), (4,1), (7,1), (10,1), (13,1), (16,1), (19,1), (22,1)]),
        (47, [(2,1), (5,1), (8,1), (11,1), (14,1), (17,1), (20,1), (23,1)])
    ]
    
    for x, segments in vertical_columns:
        add_wall_segments(walls, 'v', [(x, y, length) for y, length in segments])
    
    # Additional vertical barriers
    varied_barriers = [
        ('v', 21, 21, 1),
        ('v', 25, 1, 2), ('v', 25, 7, 1), ('v', 25, 11, 1), ('v', 25, 15, 2), ('v', 25, 21, 1),
        ('v', 28, 2, 1), ('v', 28, 6, 2), ('v', 28, 11, 2), ('v', 28, 16, 1), ('v', 28, 20, 2),
        ('v', 32, 1, 2), ('v', 32, 6, 1), ('v', 32, 10, 2), ('v', 32, 16, 1), ('v', 32, 20, 1),
        ('v', 35, 2, 2), ('v', 35, 8, 1), ('v', 35, 13, 2), ('v', 35, 18, 1), ('v', 35, 22, 1),
        ('v', 38, 1, 1), ('v', 38, 5, 2), ('v', 38, 10, 2), ('v', 38, 15, 1), ('v', 38, 19, 2),
        ('v', 41, 3, 2), ('v', 41, 9, 1), ('v', 41, 14, 2), ('v', 41, 19, 1),
        ('v', 44, 1, 2), ('v', 44, 6, 1), ('v', 44, 10, 2), ('v', 44, 15, 1), ('v', 44, 19, 1),
        ('v', 47, 2, 1), ('v', 47, 6, 2), ('v', 47, 11, 1), ('v', 47, 15, 2), ('v', 47, 20, 1)
    ]
    walls.extend(varied_barriers)
    
    # Strategic longer walls
    strategic_walls = [
        ('h', 15, 3, 5), ('h', 30, 6, 4), ('h', 8, 10, 6), 
        ('h', 35, 14, 5), ('h', 20, 18, 5), ('h', 40, 20, 4)
    ]
    walls.extend(strategic_walls)
    
    # Narrow passages
    narrow_passages = [
        ('v', 22, 9, 2), ('v', 36, 11, 2), ('v', 16, 15, 2), 
        ('v', 30, 7, 2), ('v', 42, 17, 2)
    ]
    walls.extend(narrow_passages)
    
    return walls

def run_maze_game(player_name):
    """Main function to run the maze game"""
    # Initialize Pygame
    pygame.init()
    
    WIDTH = GRID_WIDTH * CELL_SIZE
    HEIGHT = GRID_HEIGHT * CELL_SIZE
    
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("MUTHER")
    
    # Initialize maze
    maze_walls = create_maze_walls()
    
    # System positions
    start_positions = {'power': (1, 6), 'data': (1, 12), 'coolant': (1, 18)}
    target_positions = {'power': (GRID_WIDTH - 2, 6), 'data': (GRID_WIDTH - 2, 12), 'coolant': (GRID_WIDTH - 2, 18)}
    
    # System lines
    lines = {
        'power': {'path': [start_positions['power']], 'color': POWER_COLOR, 'connected': False},
        'data': {'path': [start_positions['data']], 'color': DATA_COLOR, 'connected': False},
        'coolant': {'path': [start_positions['coolant']], 'color': COOLANT_COLOR, 'connected': False}
    }
    
    # Game state
    current_line = 'power'
    game_won = False
    blink_counter = 0
    win_timer = 0
    
    def reset_game():
        """Reset all system paths to starting positions"""
        for key, start in start_positions.items():
            lines[key]['path'] = [start]
            lines[key]['connected'] = False
    
    def check_wall_collision(pos):
        """Check if position collides with any wall"""
        x, y = pos
        for wall_type, wx, wy, length in maze_walls:
            if wall_type == 'h' and y == wy and wx <= x < wx + length:
                return True
            elif wall_type == 'v' and x == wx and wy <= y < wy + length:
                return True
        return False
    
    def check_overlap():
        """Check if any system paths overlap"""
        all_positions = set()
        for line in lines.values():
            for pos in line['path'][1:]:
                if pos in all_positions:
                    return True
                all_positions.add(pos)
        return False
    
    def draw_wall_line(surface, wall):
        """Draw a double green line for walls"""
        wall_type, x, y, length = wall
        if wall_type == 'h':
            start_pixel = (x * CELL_SIZE, y * CELL_SIZE + CELL_SIZE // 2)
            end_pixel = ((x + length) * CELL_SIZE, y * CELL_SIZE + CELL_SIZE // 2)
            pygame.draw.line(surface, TERMINAL_GREEN, (start_pixel[0], start_pixel[1] - 2), (end_pixel[0], end_pixel[1] - 2), 2)
            pygame.draw.line(surface, TERMINAL_GREEN, (start_pixel[0], start_pixel[1] + 2), (end_pixel[0], end_pixel[1] + 2), 2)
        else:
            start_pixel = (x * CELL_SIZE + CELL_SIZE // 2, y * CELL_SIZE)
            end_pixel = (x * CELL_SIZE + CELL_SIZE // 2, (y + length) * CELL_SIZE)
            pygame.draw.line(surface, TERMINAL_GREEN, (start_pixel[0] - 2, start_pixel[1]), (end_pixel[0] - 2, end_pixel[1]), 2)
            pygame.draw.line(surface, TERMINAL_GREEN, (start_pixel[0] + 2, start_pixel[1]), (end_pixel[0] + 2, end_pixel[1]), 2)
    
    def handle_system_switch(key):
        """Handle switching between systems"""
        nonlocal current_line
        if key in (pygame.K_1, pygame.K_p):
            return 'power'
        elif key in (pygame.K_2, pygame.K_d):
            return 'data'
        elif key in (pygame.K_3, pygame.K_c):
            return 'coolant'
        elif key == pygame.K_TAB:
            systems = ['power', 'data', 'coolant']
            current_idx = systems.index(current_line)
            return systems[(current_idx + 1) % 3]
        return current_line
    
    def handle_movement(key):
        """Handle movement input and return new position if valid"""
        direction_map = {
            pygame.K_UP: (0, -1),
            pygame.K_DOWN: (0, 1),
            pygame.K_LEFT: (-1, 0),
            pygame.K_RIGHT: (1, 0)
        }
        
        if key not in direction_map:
            return None
            
        dx, dy = direction_map[key]
        current_path = lines[current_line]['path']
        head = current_path[-1]
        new_head = (head[0] + dx, head[1] + dy)
        
        if (0 <= new_head[0] < GRID_WIDTH and 
            0 <= new_head[1] < GRID_HEIGHT and
            not check_wall_collision(new_head) and
            new_head not in current_path):
            return new_head
        return None
    
    def draw_system_markers():
        """Draw start and target markers with labels"""
        small_font = pygame.font.Font(None, 18)
        for system in lines:
            start_pos = start_positions[system]
            target_pos = target_positions[system]
            color = lines[system]['color']
            
            # Start square
            start_pixel = (start_pos[0] * CELL_SIZE + 5, start_pos[1] * CELL_SIZE + 5)
            pygame.draw.rect(screen, color, (*start_pixel, CELL_SIZE - 10, CELL_SIZE - 10))
            
            # Label
            label_text = small_font.render(system[0].upper(), True, color)
            label_pos = (5, start_pos[1] * CELL_SIZE + CELL_SIZE // 2 - 5)
            screen.blit(label_text, label_pos)
            
            # Target square
            target_pixel = (target_pos[0] * CELL_SIZE + 5, target_pos[1] * CELL_SIZE + 5)
            target_color = BRIGHT_GREEN if lines[system]['connected'] else DIM_GREEN
            pygame.draw.rect(screen, target_color, (*target_pixel, CELL_SIZE - 10, CELL_SIZE - 10), 2)
    
    def draw_system_paths():
        """Draw all system paths and heads"""
        for system_name, line_data in lines.items():
            path, color = line_data['path'], line_data['color']
            
            # Draw path segments
            for i in range(len(path) - 1):
                start_pixel = (path[i][0] * CELL_SIZE + CELL_SIZE // 2, path[i][1] * CELL_SIZE + CELL_SIZE // 2)
                end_pixel = (path[i + 1][0] * CELL_SIZE + CELL_SIZE // 2, path[i + 1][1] * CELL_SIZE + CELL_SIZE // 2)
                pygame.draw.line(screen, color, start_pixel, end_pixel, 3)
            
            # Draw current head
            if path:
                head = path[-1]
                head_pixel = (head[0] * CELL_SIZE + CELL_SIZE // 2, head[1] * CELL_SIZE + CELL_SIZE // 2)
                
                if system_name == current_line and not game_won and blink_counter % 30 < 15:
                    pygame.draw.circle(screen, BRIGHT_GREEN, head_pixel, 8, 2)
                
                pygame.draw.circle(screen, color, head_pixel, 5)
    
    def draw_ui():
        """Draw user interface elements"""
        if game_won:
            font = pygame.font.Font(None, 36)
            text = font.render("ROUTING COMPLETE", True, BRIGHT_GREEN)
            screen.blit(text, text.get_rect(center=(WIDTH // 2, 40)))
            
        else:
            # Current system indicator
            font = pygame.font.Font(None, 24)
            system_names = {'power': 'POWER', 'data': 'DATA', 'coolant': 'COOLANT'}
            text = font.render(system_names[current_line], True, lines[current_line]['color'])
            screen.blit(text, (10, 10))
            
            # Control instructions
            small_font = pygame.font.Font(None, 18)
            controls = small_font.render("1/P  2/D  3/C  TAB", True, DIM_GREEN)
            screen.blit(controls, (10, HEIGHT - 25))
            
            movement = small_font.render("Arrow keys to move, BACKSPACE to undo", True, DIM_GREEN)
            screen.blit(movement, (10, HEIGHT - 45))
    
    # Main game loop
    clock = pygame.time.Clock()
    running = True
    
    while running:
        blink_counter += 1
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            elif event.type == pygame.KEYDOWN:
                if game_won:
                    if event.key == pygame.K_r:
                        reset_game()
                        game_won = False
                else:
                    # System switching
                    new_system = handle_system_switch(event.key)
                    if new_system != current_line:
                        current_line = new_system
                    
                    # Movement
                    elif event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT):
                        new_head = handle_movement(event.key)
                        if new_head:
                            lines[current_line]['path'].append(new_head)
                            
                            # Check if reached target
                            if new_head == target_positions[current_line]:
                                lines[current_line]['connected'] = True
                            
                            # Check for overlap and reset if found
                            if check_overlap():
                                reset_game()
                    
                    # Backtrack
                    elif event.key == pygame.K_BACKSPACE and len(lines[current_line]['path']) > 1:
                        removed_pos = lines[current_line]['path'].pop()
                        if removed_pos == target_positions[current_line]:
                            lines[current_line]['connected'] = False
        
        # Check win condition
        # game_won = all(lines[system]['connected'] for system in lines)
        
        # Check win condition: Updated to auto exit
        if not game_won and all(lines[system]['connected'] for system in lines):
            game_won = True
            win_timer = pygame.time.get_ticks() + 3000  # Show win message for 3 seconds

        # Auto-exit after win message display
        if game_won and pygame.time.get_ticks() > win_timer:
            running = False  # This exits the loop and returns to main.py

        
        # Render frame
        screen.fill(TERMINAL_BLACK)
        
        # Draw maze walls
        for wall in maze_walls:
            draw_wall_line(screen, wall)
        
        draw_system_markers()
        draw_system_paths()
        draw_ui()
        
        pygame.display.flip()
        clock.tick(60)