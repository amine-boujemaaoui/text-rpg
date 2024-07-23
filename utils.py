import curses
import json
import time

from curses.textpad import Textbox
from objects import Weapons, Armors
from enum import Enum

class Colors(Enum):
    BLACK   = curses.COLOR_BLACK
    RED     = curses.COLOR_RED
    GREEN   = curses.COLOR_GREEN
    YELLOW  = curses.COLOR_YELLOW
    BLUE    = curses.COLOR_BLUE
    MAGENTA = curses.COLOR_MAGENTA
    CYAN    = curses.COLOR_CYAN
    WHITE   = curses.COLOR_WHITE
    GRAY    = 8
    DARK_GREEN = 9

def i(stdscr, x, y, n, text) -> str:
    stdscr.nodelay(0)
    curses.curs_set(1)

    stdscr.addstr(y, x, text, curses.A_BOLD)
    stdscr.refresh()
    win = curses.newwin(1, n + 1, y, x + len(text) + 1)
    box = Textbox(win)
    box.edit()
    user_input = box.gather().strip()

    curses.curs_set(0) 
    stdscr.nodelay(1)

    return user_input

def save_game(g, filename = '', first = False) -> None:
    if not filename:
        filename = g.player.name
    game_data = {
        "player": {
            "name":     g.player.name,
            "position": g.player.position,
            "stats":    g.player.stats,
            "equipment": {
                "weapon":  g.player.equipment['weapon'].name if first else g.player.equipment['weapon'],
                "armor":   g.player.equipment['armor'].name  if first else g.player.equipment['armor'],
                "potions": g.player.equipment['potions']
            },
            "inventory": {
                "weapons": [weapon.name for weapon in g.player.inventory['weapons']] if first else [weapon for weapon in g.player.inventory['weapons']],
                "armors":  [armor.name for armor in g.player.inventory['armors']]    if first else [armor for armor in g.player.inventory['armors']]
            }
        }
    }

    with open(f"saves/{filename}.json", 'w') as f:
        json.dump(game_data, f, indent=4)

def load_game(g, filename="savegame") -> None:
    with open(f"saves/{filename}.json", 'r') as f:
        game_data = json.load(f)

    player_data = game_data["player"]

    g.player.name      = player_data["name"]
    g.player.position  = player_data["position"]
    g.player.stats     = player_data["stats"]
    g.player.equipment = {
        "weapon":  Weapons[player_data["equipment"]["weapon"]].name,
        "armor":   Armors[player_data["equipment"]["armor"]].name,
        "potions": player_data["equipment"]["potions"]
    }
    g.player.inventory = {
        'weapons': [Weapons[item].name for item in player_data["inventory"]["weapons"]],
        'armors':  [Armors[item].name   for item in player_data["inventory"]["armors"]],
    }

def format_line(prefix: str, value: str, max_length: str) -> str:
    total_length = len(prefix) + len(value) + 4
    return f"{prefix}{value}{' ' * (max_length - total_length)}"

def draw_bar(value, value_max, size, fill='█', empty='░') -> str:
    filled_length = int(size * value / value_max)
    bar = fill * filled_length + empty * (size - filled_length)
    return bar

def draw_outline(length: int, content: list, title: str = "") -> list:
    top_border = f"┌{'─' * (length - 2)}┐"
    bottom_border = f"└{'─' * (length - 2)}┘"
    
    if title:
        title_line = f"│{title.center(length - 2)}│"
        separator = f"├{'─' * (length - 2)}┤"
        outlined_content = [top_border, title_line, separator]
    else:
        outlined_content = [top_border]
    
    if content and isinstance(content[0], tuple):
        # Content is a list of tuples (line, fg, bg)
        outlined_content = [(top_border, Colors.CYAN, Colors.BLACK)]
        if title:
            outlined_content.extend([(title_line, Colors.CYAN, Colors.BLACK), (separator, Colors.CYAN, Colors.BLACK)])
        
        for line, fg, bg in content:
            outlined_content.append((f"│{line.ljust(length - 2)}│", fg, bg))
        
        outlined_content.append((bottom_border, Colors.CYAN, Colors.BLACK))
    else:
        # Content is a list of strings
        for line in content:
            outlined_content.append(f"│{line.ljust(length - 2)}│")
        outlined_content.append(bottom_border)
    
    return outlined_content


def init_colors() -> None:
    curses.start_color()
    curses.use_default_colors()

    if curses.can_change_color():
        curses.init_color(Colors.GRAY.value,      500, 500, 500)
        curses.init_color(Colors.DARK_GREEN.value,  0, 300, 0)
    
    pair_number = 1
    for fg in Colors:
        for bg in Colors:
            curses.init_pair(pair_number, fg.value, bg.value)
            pair_number += 1

def p(fg: Colors, bg: Colors = Colors.BLACK, reverse=False) -> int:
    fg_index    = list(Colors).index(fg)
    bg_index    = list(Colors).index(bg)
    pair_number = fg_index * len(Colors) + bg_index + 1
    color_pair  = curses.color_pair(pair_number)
    
    if reverse:
        return color_pair | curses.A_REVERSE

    return color_pair

def print_stat(stdscr, y, x, line, title_color, value_color, border_color):
    parts = line.split('?')
    if len(parts) > 1:
        start = parts[0].split('│')
        title = start[1] + ' '
        end = parts[1].split('│')
        value = end[0]
        stdscr.addstr(y, x, "│", border_color)
        stdscr.addstr(y, x + 1, title, title_color)
        stdscr.addstr(y, x + len(title), value, value_color)
        stdscr.addstr(y, x + len(title) + len(value) + 1, "│", border_color)
    else:
        stdscr.addstr(y, x, line, border_color)

def add_notif(g, message: str, fg: Colors = Colors.WHITE, bg: Colors = Colors.BLACK) -> None:
    g.notif.insert(0, (message, fg, bg))
    if len(g.notif) > 6:
        g.notif.pop()

def clear_notif(g) -> None:
    g.notif = [ ('', Colors.WHITE, Colors.BLACK) for _ in range(6) ]

def display(stdscr, frame_with_colors, frame_x, frame_y, MAX_WIDTH, offset_l = 0, offset_r = 0, fix_title = False) -> None:
    for i, (line, fg, bg) in enumerate(frame_with_colors):
        if i == 0 or i == len(frame_with_colors) - 1:
            stdscr.addstr(frame_y + i, frame_x, line, p(Colors.CYAN))
        else:
            stdscr.addstr(frame_y + i, frame_x, line[0], p(Colors.CYAN))
            stdscr.addstr(frame_y + i, frame_x + 1 + offset_l, line[1:-1], p(fg, bg))
            if offset_r: stdscr.addstr(frame_y + i, frame_x + MAX_WIDTH - 1 - offset_r, f"{' ' *  (offset_r)}", p(Colors.CYAN))
            stdscr.addstr(frame_y + i, frame_x + MAX_WIDTH - 1, line[-1],  p(Colors.CYAN))
    if fix_title:
        line, fg, bg = frame_with_colors[2]
        stdscr.addstr(frame_y + 2, frame_x, line, p(fg, bg))
            
def cleanup(g):
    curses.nocbreak()
    g.stdscr.keypad(False)
    curses.echo()
    curses.endwin()

def fl(stdscr, t: float, color: Colors = Colors.YELLOW, msg: str = '') -> None:
    line_len = 65
    stdscr.addstr(15, 4, f"{msg}{' ' * (line_len - len(msg))}", p(color))
    stdscr.refresh()
    time.sleep(t)

