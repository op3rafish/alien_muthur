"""
Narrative sequencing for ALIEN: CHRONOS

Player enters name
Tone and stakes are established
Warning message and timer are initiated
"""

import pygame
import sys
import time
from config import WIDTH, HEIGHT, TERMINAL_GREEN, BRIGHT_GREEN, TERMINAL_BLACK, load_fonts
from engine import TypingText, apply_crt_effects, green_flash, wait_for_time, display_typing_sequence
from scenes.dialogue import OPENING_DIALOGUE, MAZE_DIALOGUE, NAVIGATION_DIALOGUE, AIRLOCK_DIALOGUE, VICTORY_DIALOGUE
from scenes.win import run_shutdown_sequence

def get_player_name(screen, y_position=100):
    """Get player name input"""
    font_large, _, _ = load_fonts()
    clock = pygame.time.Clock()
    input_text = ""
    
    prompt = TypingText(
        OPENING_DIALOGUE["player_input"]["prompt"],
        50,
        y_position,
        font_large,
        TERMINAL_GREEN
    )
    
    # Animate prompt
    while not prompt.finished:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        
        prompt.update(time.time())
        screen.fill(TERMINAL_BLACK)
        prompt.draw(screen)
        apply_crt_effects(screen)
        pygame.display.flip()
        clock.tick(60)
    
    # Get input
    input_active = True
    error_message = ""
    
    while input_active:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    # Validate input
                    if input_text.strip() and input_text.replace(" ", "").replace("-", "").replace("'", "").isalpha():
                        return input_text
                    else:
                        error_message = OPENING_DIALOGUE["player_input"]["error"]
                        input_text = ""
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                    error_message = ""
                elif event.unicode.isprintable():
                    input_text += event.unicode
                    error_message = ""
        
        # Draw
        screen.fill(TERMINAL_BLACK)
        prompt.draw(screen)
        
        # Draw input text
        input_surface = font_large.render(input_text + "_", True, BRIGHT_GREEN)
        screen.blit(input_surface, (50, y_position + 40))
        
        # Draw error if any
        if error_message:
            error_surface = font_large.render(error_message, True, TERMINAL_GREEN)
            screen.blit(error_surface, (50, y_position + 80))
        
        apply_crt_effects(screen)
        pygame.display.flip()
        clock.tick(60)

def run_opening(screen):
    """Run the opening sequence and return player name"""
    font_large, _, _ = load_fonts()
    
    # Consistent top position for all text blocks
    TOP_POSITION = 100
    
    # Helper function to convert dialogue to list
    def to_list(dialogue):
        return [dialogue] if isinstance(dialogue, str) else dialogue
    
    # Initialization
    texts = display_typing_sequence(
        [(line, font_large) for line in to_list(OPENING_DIALOGUE["initialization"])],
        screen,
        TOP_POSITION
    )
    wait_for_time(2, screen, texts)
    green_flash(screen)
    
    # Diagnostics
    screen.fill(TERMINAL_BLACK)
    texts = display_typing_sequence(
        [(line, font_large) for line in to_list(OPENING_DIALOGUE["diagnostics"])],
        screen,
        TOP_POSITION
    )
    wait_for_time(1.5, screen, texts)
    green_flash(screen)
    
    # Ship info
    screen.fill(TERMINAL_BLACK)
    texts = display_typing_sequence(
        [(line, font_large) for line in OPENING_DIALOGUE["ship_info"]],
        screen,
        TOP_POSITION,
        40
    )
    wait_for_time(1, screen, texts)
    green_flash(screen)
    
    # Get player name
    screen.fill(TERMINAL_BLACK)
    player_name = get_player_name(screen, TOP_POSITION)
    wait_for_time(1, screen, [])
    green_flash(screen)
    
    # Player match (with name substitution)
    screen.fill(TERMINAL_BLACK)
    player_match_lines = [
        line.format(player_name=player_name) for line in OPENING_DIALOGUE["player_match"]
    ]
    texts = display_typing_sequence(
        [(line, font_large) for line in player_match_lines],
        screen,
        TOP_POSITION,
        40
    )
    wait_for_time(2, screen, texts)
    green_flash(screen)
    
    # Warning
    screen.fill(TERMINAL_BLACK)
    texts = display_typing_sequence(
        [(line, font_large) for line in OPENING_DIALOGUE["warning"]],
        screen,
        TOP_POSITION,
        40,
        line_pauses={1: 2}
    )
    wait_for_time(4, screen, texts)
    green_flash(screen)

    # Special order 937
    screen.fill(TERMINAL_BLACK)
    order_937_lines = [
        line.format(player_name=player_name) for line in OPENING_DIALOGUE["order_937"]
    ]
    texts = display_typing_sequence(
        [(line, font_large) for line in order_937_lines],
        screen,
        TOP_POSITION,
        40,
        line_pauses={0: 1}
    )
    wait_for_time(3, screen, texts)
    green_flash(screen)
    
    # Maze
    screen.fill(TERMINAL_BLACK)
    texts = display_typing_sequence(
        [(line, font_large) for line in MAZE_DIALOGUE["timer_mazeintro"]],
        screen,
        TOP_POSITION,
        40
    )
    wait_for_time(2, screen, texts)
    
    return player_name


# MAZE GAME RUNS

# Maze completion dialogue
def run_maze_completion(screen, player_name):
    font_large, _, _ = load_fonts()
    TOP_POSITION = 100

    # Part 1
    part1_lines = [line.format(player_name=player_name) for line in MAZE_DIALOGUE["maze_completion_1"]]
    screen.fill(TERMINAL_BLACK)
    texts1 = display_typing_sequence(
        [(line, font_large) for line in part1_lines],
        screen,
        TOP_POSITION,
        40
    )
    wait_for_time(3, screen, texts1)
    green_flash(screen)

    # New screen for the warning
    screen.fill(TERMINAL_BLACK)
    part2_lines = [line.format(player_name=player_name) for line in MAZE_DIALOGUE["maze_completion_2"]]
    texts2 = display_typing_sequence(
        [(line, font_large) for line in part2_lines],
        screen,
        TOP_POSITION,
        40
    )
    wait_for_time(4, screen, texts2)
    green_flash(screen)


def run_navigation_dialogue(screen, player_name):
    font_large, _, _ = load_fonts()
    TOP_POSITION = 100

    # Part 1
    part1_lines = [line.format(player_name=player_name) for line in NAVIGATION_DIALOGUE["nav_dialogue_1"]]
    screen.fill(TERMINAL_BLACK)
    texts1 = display_typing_sequence(
        [(line, font_large) for line in part1_lines],
        screen,
        TOP_POSITION,
        40
    )
    wait_for_time(3, screen, texts1)
    green_flash(screen)

    # New screen for the warning
    screen.fill(TERMINAL_BLACK)
    part2_lines = [line.format(player_name=player_name) for line in NAVIGATION_DIALOGUE["nav_dialogue_2"]]
    texts2 = display_typing_sequence(
        [(line, font_large) for line in part2_lines],
        screen,
        TOP_POSITION,
        40
    )
    wait_for_time(4, screen, texts2)
    green_flash(screen)

def run_airlock_intro(screen):
    """Display airlock puzzle introduction"""
    font_large, _, _ = load_fonts()
    TOP_POSITION = 100
    
    screen.fill(TERMINAL_BLACK)
    texts = display_typing_sequence(
        [(line, font_large) for line in AIRLOCK_DIALOGUE["airlock_intro"]],
        screen,
        TOP_POSITION,
        40,
        line_pauses={2: 1.5, 5: 1.0}
    )
    wait_for_time(2, screen, texts)
    green_flash(screen)

def run_airlock_ending(screen, player_name, outcome):
    """Display the airlock puzzle ending based on outcome"""
    from scenes.dialogue import AIRLOCK_DIALOGUE
    
    font_large, _, _ = load_fonts()
    TOP_POSITION = 100
    
    screen.fill(TERMINAL_BLACK)
    
    if outcome == "victory":
        ending_lines = [line.format(player_name=player_name) 
                       for line in AIRLOCK_DIALOGUE["airlock_victory"]]
    else:
        ending_lines = [line.format(player_name=player_name) 
                       for line in AIRLOCK_DIALOGUE["airlock_failure"]]
    
    texts = display_typing_sequence(
        [(line, font_large) for line in ending_lines],
        screen,
        TOP_POSITION,
        40,
        line_pauses={1: 1.5, 4: 1.0}
    )
    wait_for_time(5, screen, texts)
    green_flash(screen)


# WIN DIALOGUE
# WIN DIALOGUE
def run_victory_narrative(screen, player_name):
    """Display final victory narrative before win screen"""
    font_large, _, _ = load_fonts()
    TOP_POSITION = 100
    
    # Victory confirmation
    screen.fill(TERMINAL_BLACK)
    victory_confirmation_lines = [
        line.format(player_name=player_name) for line in VICTORY_DIALOGUE["victory_confirmation"]
    ]
    texts = display_typing_sequence(
        [(line, font_large) for line in victory_confirmation_lines],
        screen,
        TOP_POSITION,
        40
    )
    wait_for_time(2, screen, texts)
    green_flash(screen)
    
    # Scanning ship
    screen.fill(TERMINAL_BLACK)
    scanning_ship_lines = [
        line.format(player_name=player_name) for line in VICTORY_DIALOGUE["scanning_ship"]
    ]
    texts = display_typing_sequence(
        [(line, font_large) for line in scanning_ship_lines],
        screen,
        TOP_POSITION,
        40
    )
    wait_for_time(3, screen, texts)
    green_flash(screen)
    
    # Plot twist
    screen.fill(TERMINAL_BLACK)
    eggs_twist_lines = [
        line.format(player_name=player_name) for line in VICTORY_DIALOGUE["eggs_twist"]
    ]
    texts = display_typing_sequence(
        [(line, font_large) for line in eggs_twist_lines],
        screen,
        TOP_POSITION,
        40
    )
    wait_for_time(3, screen, texts)
    green_flash(screen)
    
    # Thank you
    screen.fill(TERMINAL_BLACK)
    thank_you_lines = [
        line.format(player_name=player_name) for line in VICTORY_DIALOGUE["thank_you"]
    ]
    texts = display_typing_sequence(
        [(line, font_large) for line in thank_you_lines],
        screen,
        TOP_POSITION,
        40
    )
    wait_for_time(2, screen, texts)
    green_flash(screen)

    # Run shutdown sequence
    run_shutdown_sequence(screen)




# def run_victory_narrative(screen, player_name):
#     """Display final victory narrative before win screen"""
#     font_large, _, _ = load_fonts()
#     TOP_POSITION = 100
    
#     # Victory confirmation
#     screen.fill(TERMINAL_BLACK)
#     texts = display_typing_sequence(
#         [(line, font_large) for line in VICTORY_DIALOGUE["victory_confirmation"]],
#         screen,
#         TOP_POSITION,
#         40
#     )
#     wait_for_time(2, screen, texts)
#     green_flash(screen)
    
#     # Scanning ship
#     screen.fill(TERMINAL_BLACK)
#     texts = display_typing_sequence(
#         [(line, font_large) for line in VICTORY_DIALOGUE["scanning_ship"]],
#         screen,
#         TOP_POSITION,
#         40
#     )
#     wait_for_time(3, screen, texts)
#     green_flash(screen)
    
#     # Plot twist
#     screen.fill(TERMINAL_BLACK)
#     texts = display_typing_sequence(
#         [(line, font_large) for line in VICTORY_DIALOGUE["eggs_twist"]],
#         screen,
#         TOP_POSITION,
#         40
#     )
#     wait_for_time(3, screen, texts)
#     green_flash(screen)
    
#     # Thank you
#     screen.fill(TERMINAL_BLACK)
#     texts = display_typing_sequence(
#         [(line, font_large) for line in VICTORY_DIALOGUE["thank_you"]],
#         screen,
#         TOP_POSITION,
#         40
#     )
#     wait_for_time(2, screen, texts)
#     green_flash(screen)