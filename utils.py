import curses
import json
import time
import os

from curses.textpad import Textbox
from objects import Weapons, Armors, Rarity, Rings
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

# =================================================================================================
def i(stdscr, x, y, n, text) -> str:
    stdscr.nodelay(0)
    curses.curs_set(1)

    stdscr.addstr(y, x, text, curses.A_BOLD)
    stdscr.refresh()
    win = curses.newwin(1, n + 1, y, x + len(text) + 1)
    box = Textbox(win)

    def custom_edit():
        while True:
            key = win.getch()
            if key == 27:  # ASCII value of ESC is 27
                return ""
            elif key in (curses.KEY_ENTER, ord('\n')):
                break
            elif key in (curses.KEY_BACKSPACE, 127, curses.ascii.BS, curses.ascii.DEL):
                y, x = win.getyx()
                if x > 0:
                    win.move(y, x - 1)
                    win.delch()
            else:
                y, x = win.getyx()
                if x < n:
                    win.addch(key)
        return box.gather().strip()

    result = custom_edit()

    curses.curs_set(0)
    stdscr.nodelay(1)

    return result

# =================================================================================================
def save_game(g, filename='', first=False) -> None:
    if not filename:
        filename = g.player.name

    def tuple_to_str(t):
        return f"({t[0]}, {t[1]})"

    game_data = {
        "player": {
            "name": g.player.name,
            "position": g.player.position,
            "stats": g.player.stats,
            "equipment": {
                "weapon": g.player.equipment['weapon'].name if first and g.player.equipment['weapon'] else g.player.equipment['weapon'] if g.player.equipment['weapon'] else None,
                "armor":  g.player.equipment['armor'].name  if first and g.player.equipment['armor']  else g.player.equipment['armor']  if g.player.equipment['armor']  else None,
                "ring":   g.player.equipment['ring'].name   if first and g.player.equipment['ring']   else g.player.equipment['ring']   if g.player.equipment['ring']   else None,
                "potions": g.player.equipment['potions']
            },
            "inventory": {
                "weapons": [weapon.name for weapon in g.player.inventory['weapons']] if first else [weapon for weapon in g.player.inventory['weapons']],
                "armors":  [armor.name  for armor  in g.player.inventory['armors']]  if first else [armor  for armor  in g.player.inventory['armors']],
                "rings":   [ring.name   for ring   in g.player.inventory['rings']]   if first else [ring   for ring   in g.player.inventory['rings']]
            }
        },
        "map": {
            "maps": {tuple_to_str(k): [[tile.name for tile in row] for row in v[0]] for k, v in g.map.maps.items()},
            "map_explored": {tuple_to_str(k): v[1] for k, v in g.map.maps.items()},
            "map_visited":  g.map.map_visited,
            "current_map":  g.map.current_map,
            "castle_pos":   g.map.castle_pos,
        }
    }

    class CustomEncoder(json.JSONEncoder):
        def encode(self, obj):
            if isinstance(obj, list):
                return '[' + ','.join(self.encode(el) for el in obj) + ']'
            return super().encode(obj)

    with open(f"saves/{filename}.json", 'w') as f:
        json.dump(game_data, f, indent=4, cls=CustomEncoder)

# =================================================================================================
def load_game(g, filename="savegame") -> None:
    from tile import Biome
    if not os.path.exists(f"saves/{filename}.json"):
        raise FileNotFoundError(f"Save file {filename}.json does not exist")

    with open(f"saves/{filename}.json", 'r') as f:
        try:
            game_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Error decoding JSON: {e}")

    fl(g.stdscr, 0.2, Colors.YELLOW, "Loading game...")
    
    player_data = game_data["player"]

    g.player.name      = player_data["name"]
    g.player.position  = player_data["position"]
    g.player.stats     = player_data["stats"]
    g.player.equipment = {
        "weapon":  Weapons[player_data["equipment"]["weapon"]].name if player_data["equipment"]["weapon"] else None,
        "armor":   Armors[player_data["equipment"]["armor"]].name   if player_data["equipment"]["armor"]  else None,
        "potions": player_data["equipment"]["potions"],
        "ring":   player_data["equipment"]["ring"]
    }
    g.player.inventory = {
        'weapons': [Weapons[item].name for item in player_data["inventory"]["weapons"]],
        'armors':  [Armors[item].name  for item in player_data["inventory"]["armors"]],
        'rings':   [Rings[item].name   for item in player_data["inventory"]["rings"]],
    }

    map_data = game_data["map"]

    fl(g.stdscr, 0.2, Colors.GREEN, "Loading map ...")

    def str_to_tuple(s):
        return tuple(map(int, s.strip('()').split(', ')))

    g.map.maps = {
        str_to_tuple(k): (
            [[Biome[tile_name] for tile_name in row] for row in v],
            map_data["map_explored"][k]
        )
        for k, v in map_data["maps"].items()
    }

    g.map.map_visited = map_data["map_visited"]
    g.map.current_map = tuple(map_data["current_map"])
    g.map.data, g.map.data_explored = g.map.generate_map(g.map.current_map)
    
    g.map.castle_pos = map_data["castle_pos"]

    fl(g.stdscr, 0.2, Colors.GREEN, "Map loaded successfully")
    fl(g.stdscr, 0.2, Colors.GREEN, f"Game '{filename}' loaded successfully.")
    
# =================================================================================================
def format_line(prefix: str, value: str, max_length: str) -> str:
    total_length = len(prefix) + len(value) + 4
    return f"{prefix}{value}{' ' * (max_length - total_length)}"

# =================================================================================================
""" 
'■', '─'
'█', '░' 
"""
def draw_bar(value, value_max, size, fill='■', empty='─') -> str:
    filled_length = int(size * value / value_max)
    bar = fill * filled_length + empty * (size - filled_length)
    return bar

# =================================================================================================
def draw_outline(length: int, content: list, title: str = "", rounded=False) -> list:
    if rounded:
        top_border = f"╭{'─' * (length - 2)}╮"
        bottom_border = f"╰{'─' * (length - 2)}╯"
    else:
        top_border = f"┌{'─' * (length - 2)}┐"
        bottom_border = f"└{'─' * (length - 2)}┘"
    
    if title:
        title_line = f"│{title.center(length - 2)}│"
        separator = f"├{'─' * (length - 2)}┤"
        outlined_content = [top_border, title_line, separator]
    else:
        outlined_content = [top_border]
    
    if not isinstance(content[0], tuple):
        for line in content:
            outlined_content.append(f"│{line.ljust(length - 2)}│")
        outlined_content.append(bottom_border)
    else:
        outlined_content = [(top_border, Colors.CYAN, Colors.BLACK)]
        if title:
            outlined_content.extend([
                (title_line, Colors.CYAN, Colors.BLACK),
                (separator, Colors.CYAN, Colors.BLACK)
            ])
        
        for line, fg, bg in content:
            outlined_content.append((f"│{line.ljust(length - 2)}│", fg, bg))
        
        outlined_content.append((bottom_border, Colors.CYAN, Colors.BLACK))
    
    return outlined_content

# =================================================================================================
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

# =================================================================================================
BlackAndWhite = False
def p(fg: Colors, bg: Colors = Colors.BLACK, reverse=False, italic=False) -> int:
        
    if BlackAndWhite:
        fg_index    = list(Colors).index(Colors.WHITE)
        bg_index    = list(Colors).index(Colors.BLACK)
        color_pair  = curses.color_pair(fg_index * len(Colors) + bg_index + 1)
        if reverse:
            color_pair |= curses.A_REVERSE
        return color_pair
    
    else:
        fg_index    = list(Colors).index(fg)
        bg_index    = list(Colors).index(bg)
        pair_number = fg_index * len(Colors) + bg_index + 1
        color_pair  = curses.color_pair(pair_number)
        
        attributes = color_pair
        if reverse:
            attributes |= curses.A_REVERSE
        if italic and hasattr(curses, 'A_ITALIC'):
            attributes |= curses.A_ITALIC
        
        return attributes

# =================================================================================================
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

# =================================================================================================
def add_notif(p, message: str, fg: Colors = Colors.WHITE, bg: Colors = Colors.BLACK) -> None:
    p.notifs.insert(0, (message, fg, bg))
    if len(p.notifs) > p.max_notifs:
        p.notifs.pop()

# =================================================================================================
def clear_notif(p) -> None:
    p.notifs = [('', Colors.WHITE, Colors.BLACK) for _ in range(p.max_notifs)]

# =================================================================================================
def display(stdscr, frame_with_colors, frame_x, frame_y, offset_l=0, offset_r=0, fix_title=False) -> None:
    MAX_WIDTH = frame_with_colors[0][0].count('─') + 2
    for i, (line, fg, bg) in enumerate(frame_with_colors):
        if i == 0 or i == len(frame_with_colors) - 1:
            stdscr.addstr(frame_y + i, frame_x, line, p(Colors.CYAN))
        else:
            stdscr.addstr(frame_y + i, frame_x, line[0], p(Colors.CYAN))
            line_content = line[1:-1]
            content_width = MAX_WIDTH - 2 - offset_l - offset_r
            if content_width > 0:
                stdscr.addstr(frame_y + i, frame_x + 1 + offset_l, line_content[:content_width], p(fg, bg))
            if offset_r:
                stdscr.addstr(frame_y + i, frame_x + MAX_WIDTH - 1 - offset_r, ' ' * offset_r, p(Colors.CYAN))
            stdscr.addstr(frame_y + i, frame_x + MAX_WIDTH - 1, line[-1], p(Colors.CYAN))
    if fix_title:
        line, fg, bg = frame_with_colors[2]
        stdscr.addstr(frame_y + 2, frame_x, line, p(fg, bg))

# =================================================================================================       
def cleanup(g):
    curses.nocbreak()
    g.stdscr.keypad(False)
    curses.echo()
    curses.endwin()

# =================================================================================================
def fl(stdscr, t: float, color: Colors = Colors.YELLOW, msg: str = '') -> None:
    line_len = 65
    stdscr.addstr(31, 1, f"{msg}{' ' * (line_len - len(msg))}", p(color))
    stdscr.refresh()
    time.sleep(t)

# =================================================================================================
def create_ui(title: str, menu: list, width:int = 119, height:int = 32, box=0) -> list:
    try: 
        w = width - 2
        bow_width = 23
        middle = w // 2 - 23 // 2
        
        empty = f"│{" " * w}│"
        ui = [
            f"┌{"─" * w}┐",
            empty,
            f"│{' ██████╗  ██████╗ ███╗   ██╗██╗███████╗'.center(w)}│",
            f"│{'██╔════╝ ██╔═══██╗████╗  ██║██║██╔════╝'.center(w)}│",
            f"│{'██║  ███╗██║   ██║██╔██╗ ██║██║███████╗'.center(w)}│",
            f"│{'██║   ██║██║   ██║██║╚██╗██║██║╚════██║'.center(w)}│",
            f"│{'╚██████╔╝╚██████╔╝██║ ╚████║██║███████║'.center(w)}│",
            f"│{' ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝╚═╝╚══════╝'.center(w)}│",
            empty,
            empty,
            f"│{' ' * middle}┌─────────────────────┐{' ' * middle}│"        if title else empty,
            f"│{' ' * middle}│{title.center(bow_width -2)}│{' ' * middle}│" if title else empty,
            f"│{' ' * middle}└─────────────────────┘{' ' * middle}│"        if title else empty,
        ]
        if box > 0:
            ui.append( empty)
            ui.append( f"│{'┌─────────────────────┐'.center(w)}│")
            ui.extend([f"│{'│                     │'.center(w)}│" for _ in range(box)])
            ui.append( f"│{'└─────────────────────┘'.center(w)}│",)
        
        else:
            for line in menu:
                ui.append(f"│ {line.ljust(w - 2)} │")
        
        for _ in range(height - len(ui)):
            ui.append(empty)
        
        ui.append(f"└{"─" * w}┘")
    except Exception as e:
        print(e)
    return ui

# =================================================================================================
def get_rarity_color(rarity: Rarity) -> Colors:
    match rarity:
        case Rarity.COMMON:
            return Colors.WHITE
        case Rarity.UNCOMMON:
            return Colors.GREEN
        case Rarity.RARE:
            return Colors.BLUE
        case Rarity.EPIC:
            return Colors.MAGENTA
        case Rarity.LEGENDARY:
            return Colors.YELLOW
    return Colors.WHITE

# =================================================================================================
def list_saves(directory="saves") -> list:
    if not os.path.exists(directory):
        return []
    return [f[:-5] for f in os.listdir(directory) if f.endswith('.json')]

# =================================================================================================
def display_popup(p, content: list, x, y, w) -> None:
    display(p.g.stdscr, draw_outline(w, content), x, y)
    p.g.stdscr.refresh()
    time.sleep(3)
    
# =================================================================================================
def display_confirmation_popup(stdscr, x, y, w, message: str, options: list) -> int:
    content = [
        ("", Colors.YELLOW, Colors.BLACK),
        (message.center(w - 2), Colors.YELLOW, Colors.BLACK),
        ("", Colors.YELLOW, Colors.BLACK)
    ]
    
    for option in options:
        content.append((option.center(w - 2), Colors.WHITE, Colors.BLACK))
    content.append(("", Colors.YELLOW, Colors.BLACK))

    selected_option = 0
    while True:
        for i, line in enumerate(content):
            if 3 <= i < 3 + len(options):
                if i == 3 + selected_option:
                    content[i] = (line[0], Colors.YELLOW, Colors.BLACK)
                else:
                    content[i] = (line[0], Colors.WHITE, Colors.BLACK)
        display(stdscr, draw_outline(w, content, rounded=True), x, y)
        stdscr.refresh()
        key = stdscr.getch()
        if key in (curses.KEY_UP, ord('w')):
            selected_option = max(0, selected_option - 1)
        elif key in (curses.KEY_DOWN, ord('s')):
            selected_option = min(len(options) - 1, selected_option + 1)
        elif key in (curses.KEY_ENTER, ord('\n')):
            return selected_option  # Return the index of the selected option