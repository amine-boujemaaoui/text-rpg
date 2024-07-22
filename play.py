import time
import random
import curses

from utils import draw_bar, draw_outline, p, print_stat, format_line as fl, add_notif, display, Colors, cleanup as cl, save_game
from tile import ascii_art
from game import Direction
from enum import Enum
from entities import ARTS

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
        self.last_state = PlayStates.PLAYING
        self.current_enemy = None

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
            (fl(" Name     ?", self.g.player.name,                     MAX_LENGTH), Colors.WHITE),
            (fl(" HP       ?", hp_bar,                                 MAX_LENGTH), Colors.RED),
            (fl(" Mana     ?", mana_bar,                               MAX_LENGTH), Colors.BLUE),
            (fl(" Exp:     ?", exp_bar,                                MAX_LENGTH), Colors.GREEN),
            ("                          ",                                          Colors.YELLOW),
            (fl(" Level    ?", str(self.g.player.stats['level']),      MAX_LENGTH), Colors.GREEN),
            (fl(" Gold     ?", str(self.g.player.stats['gold']) + '$', MAX_LENGTH), Colors.YELLOW),
            (fl(" Attack   ?", str(self.g.player.stats['attack']),     MAX_LENGTH), Colors.WHITE),
            (fl(" Defense  ?", str(self.g.player.stats['defense']),    MAX_LENGTH), Colors.WHITE),
            ("                          ",                                          Colors.WHITE),
            (fl(" Position ?", f"({x:>2},{y:>2})",                     MAX_LENGTH), Colors.WHITE),
        ]
        return draw_outline(MAX_LENGTH, content, "Player Stats")

    def display_stats(self, stdscr, stats_x, stats_y):
        stats_frame = self.draw_stats()
        for i, (line, color) in enumerate(stats_frame):
            print_stat(stdscr, stats_y + i, stats_x, line, p(Colors.GRAY), p(color), p(Colors.CYAN))
 
    def draw_equipment(self) -> list:
        MAX_LENGTH = 28

        weapon_name = self.g.player.equipment['weapon'].name
        armor_name = self.g.player.equipment['armor'].name
        healing_potions = str(self.g.player.equipment['potions'].get('healing', 0))
        mana_potions = str(self.g.player.equipment['potions'].get('mana', 0))

        content = [
            (fl(" Weapon    ?", weapon_name,     MAX_LENGTH), Colors.WHITE),
            (fl(" Armor     ?", armor_name,      MAX_LENGTH), Colors.WHITE),
               (" Potions   ?              ",                 Colors.WHITE),
            (fl(" - healing ?", healing_potions, MAX_LENGTH), Colors.RED),
            (fl(" - mana    ?", mana_potions,    MAX_LENGTH), Colors.BLUE),
        ]
        return draw_outline(MAX_LENGTH, content, "Equipment")

    def display_equipment(self, stdscr, equip_x, equip_y):
        equip_frame = self.draw_equipment()
        for i, (line, color) in enumerate(equip_frame):
            print_stat(stdscr, equip_y + i, equip_x, line, p(Colors.GRAY), p(color), p(Colors.CYAN))

    def draw_commands(self) -> list:
        content = [
            "           ",
            f"  help {self.g.test}    ",
            "  save     ",
            "  equip    ",
            "  quit     ",
            "           ",
        ]
        outlined_commands = draw_outline(13, content)
        lines_with_colors = []
        for i, line in enumerate(outlined_commands):
            if self.play_state == PlayStates.COMMANDS and i == self.g.current_option + 2:
                lines_with_colors.append((line, Colors.YELLOW))
            else:
                lines_with_colors.append((line, Colors.WHITE))
        return lines_with_colors

    def draw_notifications(self) -> list:
        MAX_LENGTH = 44
        content = self.g.notif[:6]

        # Remplir le contenu pour s'assurer qu'il y a toujours 6 lignes
        while len(content) < 6:
            content.append(('', Colors.WHITE))

        outlined_content = draw_outline(MAX_LENGTH, content)

        lines_with_colors = []

        for i, (line, color) in enumerate(outlined_content):
            if i == 0 or i == len(outlined_content) - 1:
                lines_with_colors.append((line, Colors.CYAN))
            else:
                lines_with_colors.append((line, color))
        
        return lines_with_colors

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
    
    def draw_fight(self) -> list:
        MAX_LENGTH = 42

        enemy = self.current_enemy
        # ASCII art for the enemy (example for Goblin)
        enemy_art = ARTS[enemy.key]
        
        # Enemy information
        enemy_info = [
            f" Max HP:   {enemy.stats['hp']}",
            f" Attack:   {enemy.stats['attack']}"
        ]

        # Player weapon and armor information
        weapon_info = [
            " Weapon:     ",
            f"   - Name:      {enemy.weapon.value.name if enemy.weapon else 'None'}",
            f"   - Attack:    {enemy.weapon.value.name if enemy.weapon else 0}"
        ]

        armor_info = [
            " Armor:      ",
            f"   - Name:      {enemy.armor.value.name if enemy.armor else 'None'}",
            f"   - Defense:   {enemy.armor.value.name if enemy.armor else enemy.stats['defense']}"
        ]

        # Combine all content with their respective colors
        content = [
            *[(" " + line, Colors.YELLOW) for line in enemy_art],
            ("", Colors.CYAN),
            *[(" " + line, Colors.WHITE)  for line in enemy_info],
            ("", Colors.CYAN),
            *[(" " + line, Colors.WHITE)  for line in weapon_info],
            ("", Colors.CYAN),
            *[(" " + line, Colors.WHITE)  for line in armor_info],
            ("", Colors.CYAN),
            (f"{self.g.test}", Colors.CYAN),
        ]

        return draw_outline(MAX_LENGTH, content, "Fight !")
    
    def display_fight(self, stdscr, fight_x, fight_y) -> None:
        display(stdscr, self.draw_fight(), fight_x, fight_y, 42)
        
        enemy_max_hp = self.current_enemy.stats['hp']
        enemy_bar = draw_bar(self.current_enemy.stats['hp'], enemy_max_hp, 22)
        stdscr.addstr(fight_y + 5, fight_x + 17, enemy_bar, p(Colors.RED))
        stdscr.addstr(fight_y + 4, fight_x + 17, f"{self.current_enemy.name}", p(Colors.RED))

    def battle(self) -> None:
        # Récupérer le biome actuel
        x, y = self.g.player.position['x'], self.g.player.position['y']
        biome = self.g.map.data[y][x].value
        
        # Vérifier si le joueur est debout et s'il y a une chance de rencontrer un ennemi
        if not self.g.player.standing and biome.enemy and random.randint(0, 100) <= 30:
            # Choisir un ennemi aléatoire
            enemy_key = random.choice(list(self.g.enemies.keys()))
            enemy = self.g.enemies[enemy_key]

            # Vérifier si l'ennemi peut apparaître dans le biome actuel
            if enemy.biome.value.name == biome.name:
                add_notif(self.g, f"You encountered a {enemy.name}!", Colors.RED)
                self.g.stdscr.refresh()
                time.sleep(2)
                self.current_enemy = enemy
                self.last_state = PlayStates.FIGHTING
                self.play_state = PlayStates.FIGHTING
                self.g.player.standing = True
                
    def execute_command(self):
        match self.g.current_option:
            case 0:
                add_notif(self.g, "Help selected", Colors.CYAN)
            case 1:
                save_game(self.g, "savegame")
                add_notif(self.g, "Save selected", Colors.CYAN)
            case 2:
                add_notif(self.g, "Equip selected", Colors.CYAN)
                
    def draw(self) -> None:
        # Clear the screen
        self.g.stdscr.clear()

        # Draw each section at its fixed position
        map_x,   map_y   =  0,  0
        fight_x, fight_y =  0,  0 
        stats_x, stats_y = 42,  0
        equip_x, equip_y = 42, 15
        cmd_x,   cmd_y   =  0, 24
        notif_x, notif_y = 13, 24
        biome_x, biome_y = 57, 24
        
        # Draw the map or the fight
        if self.last_state == PlayStates.FIGHTING:
            self.display_fight(self.g.stdscr, fight_x, fight_y)
        elif self.last_state == PlayStates.PLAYING:
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
            try:
                self.draw()
                key = self.g.stdscr.getch()

                if self.play_state == PlayStates.PLAYING:
                    if key == ord('w'):
                        if not self.g.player.move(0, -1):
                            add_notif(self.g, "↑ You went north.")
                            self.g.generate_map(Direction.NORTH)
                        if not self.g.player.standing:
                            self.battle()
                            
                    elif key == ord('s'):
                        if not self.g.player.move(0, 1):
                            add_notif(self.g, "↓ You went south.")
                            self.g.generate_map(Direction.SOUTH)
                        if not self.g.player.standing:
                            self.battle()
                            
                    elif key == ord('a'):
                        if not self.g.player.move(-1, 0):
                            add_notif(self.g, "← You went west.")
                            self.g.generate_map(Direction.WEST)
                        if not self.g.player.standing:
                            self.battle()
                            
                    elif key == ord('d'):
                        if not self.g.player.move(1, 0):
                            add_notif(self.g, "→ You went east.")
                            self.g.generate_map(Direction.EAST)
                        if not self.g.player.standing:
                            self.battle()
                            
                    elif key == ord('h'):
                        if self.g.player.use_potion('healing'):
                            add_notif(self.g, "() You used a healing potion.")
                        else:
                            add_notif(self.g, "() You don't have any healing potions.", Colors.RED)
                    
                    elif key == ord('j'):
                        if self.g.player.use_potion('mana'):
                            add_notif(self.g, "You used a mana potion.")
                        else:
                            add_notif(self.g, "You don't have any mana potions.", Colors.RED)
                    
                    elif key == ord('\x1b'):
                        self.g.current_option = 0
                        self.last_state = PlayStates.PLAYING
                        self.play_state = PlayStates.COMMANDS

                elif self.play_state == PlayStates.COMMANDS:
                    if key == curses.KEY_UP or key == ord('w'):
                        self.g.current_option = max(0, self.g.current_option - 1)
                    elif key == curses.KEY_DOWN or key == ord('s'):
                        self.g.current_option = min(3, self.g.current_option + 1)
                    elif key == ord('\x1b'):
                        self.play_state = self.last_state
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
                            
                elif self.play_state == PlayStates.FIGHTING:
                    if key == ord('\x1b'):
                        self.g.current_option = 0
                        self.last_state = PlayStates.FIGHTING
                        self.play_state = PlayStates.COMMANDS
                            
            except Exception as e:
                self.g.stdscr.addstr(0, 0, f"(play.py -> run) An error occurred:  {e})", p(Colors.RED))
                self.g.stdscr.refresh()
                time.sleep(4)
                run = False
                break
            