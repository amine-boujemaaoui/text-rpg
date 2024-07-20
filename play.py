import time
import curses

from utils import draw_bar, draw_outline, p, print_stat, format_line as fl, add_notif, display, Colors, cleanup as cl
from tile import ascii_art
from game import Direction
from enum import Enum

class PlayStates(Enum):
    PLAYING  = 0
    COMMANDS = 1
    FIGHTING = 2
    SHOPPING = 3
    QUITTING = 4

class Play:
    def __init__(self, g) -> None:
        self.g = g
        self.play_state = PlayStates.PLAYING

    def draw_map(self) -> list:
        map_lines = []
        x, y = self.g.player.position['x'], self.g.player.position['y']
        for row_idx, row in enumerate(self.g.map.data):
            row_str = " "
            for col_idx, tile in enumerate(row):
                if row_idx == y and col_idx == x:
                    row_str += 'P'
                else:
                    row_str += tile.symbol
            map_lines.append(row_str)
            
        return draw_outline(42, [line for line in map_lines], "Map") 
    
    def display_map(self, stdscr, map_x, map_y) -> None:
        x, y = self.g.player.position['x'], self.g.player.position['y']
        map_content = []

        for row_idx, row in enumerate(self.g.map.data):
            row_str = ""
            for col_idx, tile in enumerate(row):
                symbol = 'P' if row_idx == y and col_idx == x else tile.value.symbol
                row_str += symbol
            map_content.append(row_str)
        
        outlined_map = draw_outline(len(map_content[0]) + 2, map_content, "Map")
        
        for i, line in enumerate(outlined_map):
            stdscr.addstr(i, 0, line, p(Colors.CYAN))
        
        for row_idx, row in enumerate(self.g.map.data):
            for col_idx, tile in enumerate(row):
                if row_idx == y and col_idx == x:
                    symbol = 'P'
                    color  = Colors.RED
                else:
                    symbol = tile.value.symbol
                    color  = tile.value.color
                stdscr.addstr(row_idx + 3, col_idx + 1, symbol, p(color))
    
    def draw_stats(self) -> list:
        MAX_LENGTH = 28

        x, y = self.g.player.position['x'], self.g.player.position['y']
        hp_bar   = draw_bar(self.g.player.stats['hp'],   self.g.player.stats['max_hp'],   14)
        mana_bar = draw_bar(self.g.player.stats['mana'], self.g.player.stats['max_mana'], 14)
        exp_bar  = draw_bar(self.g.player.stats['exp'],  self.g.exp_table[self.g.player.stats['level']], 14)

        content = [
            fl(" HP       ?", hp_bar,   MAX_LENGTH),
            fl(" Exp:     ?", exp_bar,  MAX_LENGTH),
            fl(" Mana     ?", mana_bar, MAX_LENGTH),
            "                          ",
            fl(" Level    ?", str(self.g.player.stats['level']),      MAX_LENGTH),
            fl(" Gold     ?", str(self.g.player.stats['gold']) + '$', MAX_LENGTH),
            fl(" Attack   ?", str(self.g.player.stats['attack']),     MAX_LENGTH),
            fl(" Defense  ?", str(self.g.player.stats['defense']),    MAX_LENGTH),
            fl(" Speed    ?", str(self.g.player.stats['speed']),      MAX_LENGTH),
            "                          ",
            fl(" Position ?", f"({x:>2},{y:>2})", MAX_LENGTH),
        ]
        return draw_outline(MAX_LENGTH, content, self.g.player.name)

    def display_stats(self, stdscr, stats_x, stats_y):
        stats_frame = self.draw_stats()
        for i, line in enumerate(stats_frame):
            print_stat(stdscr, stats_y + i, stats_x, line, p(Colors.WHITE), p(Colors.BLUE), p(Colors.CYAN))
 
    def draw_equipment(self) -> list:
        MAX_LENGTH = 28

        weapon_name = self.g.player.equipment['weapon'].name
        armor_name = self.g.player.equipment['armor'].name
        healing_potions = str(self.g.player.equipment['potions'].get('healing', 0))
        mana_potions = str(self.g.player.equipment['potions'].get('mana', 0))

        content = [
            fl(" Weapon    ?", weapon_name,     MAX_LENGTH),
            fl(" Armor     ?", armor_name,      MAX_LENGTH),
               " Potions   ?              ",
            fl(" - healing ?", healing_potions, MAX_LENGTH),
            fl(" - mana    ?", mana_potions,    MAX_LENGTH),
        ]
        return draw_outline(MAX_LENGTH, content, "Equipment")

    def display_equipment(self, stdscr, equip_x, equip_y):
        equip_frame = self.draw_equipment()
        for i, line in enumerate(equip_frame):
            print_stat(stdscr, equip_y + i, equip_x, line, p(Colors.WHITE), p(Colors.GREEN), p(Colors.CYAN))

    def draw_commands(self) -> list:
        content = [
            "           ",
            "  help     ",
            "  save     ",
            "  equip    ",
            "  quit     ",
            "           ",
        ]
        outlined_commands = draw_outline(13, content)
        lines_with_colors = []
        for i, line in enumerate(outlined_commands):
            if self.play_state == PlayStates.COMMANDS and i == self.g.current_option + 2:
                lines_with_colors.append((line, Colors.YELLOW))  # Highlight the selected option
            else:
                lines_with_colors.append((line, Colors.CYAN))
        return lines_with_colors

    def draw_notifications(self) -> list:
        MAX_LENGTH = 44
        content = self.g.notif[:6]

        # Remplir le contenu pour s'assurer qu'il y a toujours 6 lignes
        while len(content) < 6:
            content.append({'t': "", 'c': Colors.WHITE})

        outlined_content = draw_outline(MAX_LENGTH, [notif['t'] for notif in content])

        lines_with_colors = []

        for i, line in enumerate(outlined_content):
            if i == 0 or i == len(outlined_content) - 1:
                lines_with_colors.append((line, Colors.CYAN))
            else:
                lines_with_colors.append((line, content[i - 1]['c']))
        
        return lines_with_colors

    def display_notifications(self, stdscr, notif_x, notif_y) -> None:
        notif_frame = self.draw_notifications()
        for i, (line, color) in enumerate(notif_frame):
            stdscr.addstr(notif_y + i, notif_x, line, p(Colors.CYAN))
            stdscr.addstr(notif_y + i, notif_x , '│', p(Colors.CYAN))
            stdscr.addstr(notif_y + i, notif_x + 3, line.split('│')[1], p(color))
            stdscr.addstr(notif_y + i, notif_x + 43 , '', p(Colors.CYAN))

    def draw_biome(self) -> list:
        # Récupérer les coordonnées actuelles du joueur
        x, y = self.g.player.position['x'], self.g.player.position['y']
        
        # Récupérer la tuile à la position actuelle du joueur
        current_tile = self.g.map.data[y][x]
        
        # Récupérer le nom du biome et le dessin ASCII correspondant
        biome_name  = current_tile.name
        biome_color = current_tile.value.color
        biome_art   = ascii_art[biome_name]
        
        outlined_biome = draw_outline(13, biome_art, biome_name.capitalize())
        
        # Créer la liste de tuples (ligne, couleur)
        lines_with_colors    = [(line, biome_color) for line in outlined_biome]
        lines_with_colors[2] = (lines_with_colors[2][0], Colors.CYAN)
        
        return lines_with_colors
        
    def draw(self) -> None:
        # Clear the screen
        self.g.stdscr.clear()

        # Draw each section at its fixed position
        map_x, map_y = 0, 0
        stats_x, stats_y = 42, 0
        equip_x, equip_y = 42, 15
        cmd_x, cmd_y = 0, 24
        notif_x, notif_y = 13, 24
        biome_x, biome_y = 57, 24
        
        # Draw the map
        self.display_map(self.g.stdscr, map_x, map_y)

        # Draw the player stats
        self.display_stats(self.g.stdscr, stats_x, stats_y)

        # Draw the equipment
        self.display_equipment(self.g.stdscr, equip_x, equip_y)

        # Draw the commands
        display(self.g.stdscr, self.draw_commands(), cmd_x, cmd_y, 13)

        # Draw the notifications
        display(self.g.stdscr, self.draw_notifications(), notif_x, notif_y, 44, 1)

        # Draw the biome
        display(self.g.stdscr, self.draw_biome(), biome_x, biome_y, 13)

        # Refresh the screen
        self.g.stdscr.refresh()

    def run(self) -> None:
        run = True
        while run:
            self.draw()
            key = self.g.stdscr.getch()

            if self.play_state == PlayStates.PLAYING:
                if key == ord('w'):
                    if not self.g.player.move(0, -1):
                        add_notif(self.g, "You went north.", Colors.YELLOW)
                        self.g.generate_map(Direction.NORTH)
                        
                elif key == ord('s'):
                    if not self.g.player.move(0, 1):
                        add_notif(self.g, "You went south.", Colors.MAGENTA)
                        self.g.generate_map(Direction.SOUTH)
                        
                elif key == ord('a'):
                    if not self.g.player.move(-1, 0):
                        add_notif(self.g, "You went west.", Colors.RED)
                        self.g.generate_map(Direction.WEST)
                        
                elif key == ord('d'):
                    if not self.g.player.move(1, 0):
                        add_notif(self.g, "You went east.", Colors.GREEN)
                        self.g.generate_map(Direction.EAST)
                        
                elif key == ord('h'):
                    if self.g.player.use_potion('healing'):
                        add_notif(self.g, "You used a healing potion.", Colors.CYAN)
                    else:
                        add_notif(self.g, "You don't have any healing potions.", Colors.RED)
                
                elif key == ord('j'):
                    if self.g.player.use_potion('mana'):
                        add_notif(self.g, "You used a mana potion.", Colors.CYAN)
                    else:
                        add_notif(self.g, "You don't have any mana potions.", Colors.RED)
                
                elif key == ord('\x1b'):
                    self.g.current_option = 0
                    self.play_state = PlayStates.COMMANDS

            elif self.play_state == PlayStates.COMMANDS:
                if key == curses.KEY_UP or key == ord('w'):
                    self.g.current_option = max(0, self.g.current_option - 1)
                elif key == curses.KEY_DOWN or key == ord('s'):
                    self.g.current_option = min(3, self.g.current_option + 1)
                elif key == ord('\x1b'):
                    self.play_state = PlayStates.PLAYING
                elif key == ord('\n'):
                    if self.g.current_option == 3:
                        self.g.current_option = 0
                        self.play_state = PlayStates.QUITTING
                        add_notif(self.g, "Quiting the game...", Colors.RED)
                        self.draw()
                        time.sleep(1)
                        run = False
                    else: 
                        self.execute_command()
                        self.play_state = PlayStates.PLAYING
                
                    

    def execute_command(self):
        match self.g.current_option:
            case 0:
                add_notif(self.g, "Help selected", Colors.CYAN)
            case 1:
                add_notif(self.g, "Save selected", Colors.CYAN)
            case 2:
                add_notif(self.g, "Equip selected", Colors.CYAN)
