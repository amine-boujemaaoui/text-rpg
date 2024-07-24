import time
import random
import curses

from utils import draw_bar, draw_outline, p, print_stat, format_line as fl, add_notif, display, Colors as C, cleanup as cl, save_game, clear_notif, create_ui
from tile import ascii_art
from game import Direction
from objects import SHOP_WEAPONS, SHOP_ARMORS, Weapons as W, Armors as A, Rarity
from enum import Enum
from entities import ARTS

class PlayStates(Enum):
    PLAYING   = 0
    COMMANDS  = 1
    FIGHTING  = 2
    SHOPPING  = 3
    QUITTING  = 4
    INVENTORY = 5
    HELP      = 6
    
class FightStates(Enum):
    PLAYER_TURN = 0
    ENEMY_TURN  = 1

class Play:
    def __init__(self, g) -> None:
        self.g = g
        self.state_stack = [PlayStates.PLAYING]
        self.current_enemy = None
        self.fight_state = FightStates.PLAYER_TURN
        self.counter = 0
        
        self.commands = create_ui("Commands", [
                "              ┌──────────────────────────────────────────────────────────┐            ",
                "              │             MENU, COMMANDS, SHOP, INVENTORY              │            ",
                "              ├─────────────────────────────┬────────────────────────────┤            ",
                "              │ up, down, w, s:             │ Navigate through the menu. │            ",
                "              │ enter:                      │ Select an option.          │            ",
                "              ├─────────────────────────────┴────────────────────────────┤            ",
                "              │                           GAME                           │            ",
                "              ├─────────────────────────────┬────────────────────────────┤            ",
                "              │ w, a, s, d:                 │ Mobe the player.           │            ",
                "              │ i:                          │ Open the inventory.        │            ",
                "              │ ESC:                        │ Enter in commands menu.    │            ",
                "              │ e:                          │ Show Equipments view.      │            ",
                "              ├─────────────────────────────┴────────────────────────────┤            ",
                "              │                           FIGHT                          │            ",
                "              ├─────────────────────────────┬────────────────────────────┤            ",
                "              │ space:                      │ Attack the enemy.          │            ",
                "              │ 1, 2:                       │ Use a potion (heal, mana). │            ",
                "              │ ESC:                        │ Enter in commands menu.    │            ",
                "              └─────────────────────────────┴────────────────────────────┘            ",
            ])
        
        self.show_equipment = False

    def push_state(self, state: PlayStates) -> None:
        self.state_stack.append(state)

    def pop_state(self) -> PlayStates:
        if len(self.state_stack) > 1:
            return self.state_stack.pop()
        return self.state_stack[-1]

    @property
    def play_state(self) -> PlayStates:
        return self.state_stack[-1]

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
            stdscr.addstr(map_y + i, map_x, line, p(C.CYAN))
        
        for row_idx, row in enumerate(self.g.map.data):
            for col_idx, tile in enumerate(row):
                if row_idx == y and col_idx == x:
                    symbol = 'P'
                    color  = C.RED
                else:
                    symbol = tile.value.symbol
                    color  = tile.value.color
                stdscr.addstr(row_idx + 3 + map_y, col_idx + 1 + map_x, symbol, p(color))
    
    def draw_stats(self) -> list:
        MAX_LENGTH = 28

        x, y = self.g.player.position['x'], self.g.player.position['y']
        hp_bar   = draw_bar(self.g.player.stats['hp'],   self.g.player.stats['max_hp'],   14)
        mana_bar = draw_bar(self.g.player.stats['mana'], self.g.player.stats['max_mana'], 14)
        exp_bar  = draw_bar(self.g.player.stats['exp'],  self.g.exp_table[self.g.player.stats['level']], 14)
        
        empty = (" " * (MAX_LENGTH - 2), C.WHITE, C.BLACK)

        content = [
            (fl(" Name     ?", self.g.player.name,                      MAX_LENGTH), C.WHITE,  C.BLACK),
            empty,
            (fl(" HP       ?", hp_bar,                                  MAX_LENGTH), C.RED,    C.BLACK),
            (fl(" Mana     ?", mana_bar,                                MAX_LENGTH), C.BLUE,   C.BLACK),
            (fl(" Exp:     ?", exp_bar,                                 MAX_LENGTH), C.GREEN,  C.BLACK),
            empty,
            (fl(" Level    ?", str(self.g.player.stats['level']),       MAX_LENGTH), C.GREEN,  C.BLACK),
            (fl(" Gold     ?", str(self.g.player.stats['gold']) + '$',  MAX_LENGTH), C.YELLOW, C.BLACK),
            (fl(" Attack   ?", str(self.g.player.stats['attack']),      MAX_LENGTH), C.WHITE,  C.BLACK),
            (fl(" Base ATK ?", str(self.g.player.stats['base_attack']), MAX_LENGTH), C.WHITE,  C.BLACK),
            (fl(" Defense  ?", str(self.g.player.stats['defense']),     MAX_LENGTH), C.WHITE,  C.BLACK),
            (fl(" Base DEF ?", str(self.g.player.stats['base_defense']),MAX_LENGTH), C.WHITE,  C.BLACK),
            empty,
            (fl(" Position ?", f"({x:>2},{y:>2})",                     MAX_LENGTH), C.WHITE , C.BLACK),
        ]
        for _ in range(21 - len(content)):
            content.append(empty)
        return draw_outline(MAX_LENGTH, content, "Player Stats")

    def display_stats(self, stdscr, stats_x, stats_y):
        stats_frame = self.draw_stats()
        for i, (line, fg, bg) in enumerate(stats_frame):
            print_stat(stdscr, stats_y + i, stats_x, line, p(C.GRAY), p(fg, bg), p(C.CYAN))
 
    def draw_equipment(self) -> list:
        MAX_LENGTH = 28

        weapon = W[self.g.player.equipment['weapon']].value
        armor  = A[self.g.player.equipment['armor']].value
        healing_potions = str(self.g.player.equipment['potions'].get('healing', 0))
        mana_potions = str(self.g.player.equipment['potions'].get('mana', 0))
        
        weapon_rarity_color = C.WHITE
        match weapon.rarity:
            case Rarity.COMMON:
                weapon_rarity_color = C.GREEN
            case Rarity.RARE:
                weapon_rarity_color = C.BLUE
            case Rarity.EPIC:
                weapon_rarity_color = C.MAGENTA
                
        armor_rarity_color = C.WHITE
        match armor.rarity:
            case Rarity.COMMON:
                armor_rarity_color = C.GREEN
            case Rarity.RARE:
                armor_rarity_color = C.BLUE
            case Rarity.EPIC:
                armor_rarity_color = C.MAGENTA
                
        empty = ("", C.WHITE, C.BLACK)

        content = [
               (" Weapon    ?              ",                 C.WHITE, C.BLACK),
            (fl("  - name   ?", weapon.name,     MAX_LENGTH), C.WHITE, C.BLACK),
            (fl("  - ATK    ?", str(weapon.attack),   MAX_LENGTH), C.WHITE, C.BLACK),
            (fl("  - rarity ?", weapon.rarity.value,   MAX_LENGTH), weapon_rarity_color, C.BLACK),
                empty,
               (" Armor     ?              ",                 C.WHITE, C.BLACK),
            (fl("  - name   ?", armor.name,      MAX_LENGTH), C.WHITE, C.BLACK),
            (fl("  - DEF    ?", str(armor.defense),   MAX_LENGTH), C.WHITE, C.BLACK),
            (fl("  - rarity ?", armor.rarity.value,   MAX_LENGTH), armor_rarity_color, C.BLACK),
                empty,
               (" Potions   ?              ",                 C.WHITE, C.BLACK),
            (fl(" - healing ?", healing_potions, MAX_LENGTH), C.RED  , C.BLACK),
            (fl(" - mana    ?", mana_potions,    MAX_LENGTH), C.BLUE , C.BLACK),
        ]
        for _ in range(21 - len(content)):
            content.append(empty)
        return draw_outline(MAX_LENGTH, content, "Equipment")

    def display_equipment(self, stdscr, equip_x, equip_y):
        equip_frame = self.draw_equipment()
        for i, (line, fg, bg) in enumerate(equip_frame):
            print_stat(stdscr, equip_y + i, equip_x, line, p(C.GRAY), p(fg, bg), p(C.CYAN))

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
                lines_with_colors.append((line, C.BLACK, C.YELLOW))
            else:
                lines_with_colors.append((line, C.WHITE, C.BLACK))
        return lines_with_colors

    def draw_notifications(self) -> list:
        MAX_LENGTH = 44 + 20
        content = self.g.notif[:6]

        outlined_content = draw_outline(MAX_LENGTH, content)

        lines_with_colors = []

        for i, (line, fg, bg) in enumerate(outlined_content):
            if i == 0 or i == len(outlined_content) - 1:
                lines_with_colors.append((line, C.CYAN, C.BLACK))
            else:
                lines_with_colors.append((line, fg, bg))
        
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
        lines_with_colors    = [(line, biome_color, C.BLACK) for line in outlined_biome]
        lines_with_colors[2] = (lines_with_colors[2][0], C.CYAN, C.BLACK)
        
        return lines_with_colors
    
    def draw_fight(self) -> list:
        MAX_LENGTH = 42 + 20

        enemy = self.current_enemy
        # ASCII art for the enemy (example for Goblin)
        enemy_art = ARTS[enemy.key]
        
        empty = ("", C.CYAN, C.BLACK)
        
        # Enemy information
        enemy_info = [
            f" Max HP:   {enemy.stats['max_hp']}",
            f" Attack:   {enemy.stats['attack']}"
        ]

        # Player weapon and armor information
        weapon_info = [
            " Weapon:     ",
            f"   - Name:      {enemy.weapon.value.name if enemy.weapon else 'None'}",
            f"   - Attack:    {enemy.weapon.value.attack if enemy.weapon else 0}"
        ]

        armor_info = [
            " Armor:      ",
            f"   - Name:      {enemy.armor.value.name if enemy.armor else 'None'}",
            f"   - Defense:   {enemy.armor.value.defense if enemy.armor else enemy.stats['defense']}"
        ]

        # Combine all content with their respective colors
        content = [
            *[(" " + line, C.YELLOW, C.BLACK) for line in enemy_art],
            empty,
            *[(" " + line, C.WHITE, C.BLACK)  for line in enemy_info],
            empty,
            *[(" " + line, C.WHITE, C.BLACK)  for line in weapon_info],
            empty,
            *[(" " + line, C.WHITE, C.BLACK)  for line in armor_info],
            empty,
            empty,
            empty,
        ]

        return draw_outline(MAX_LENGTH, content, "Fight !")
    
    def display_fight(self, stdscr, fight_x, fight_y) -> None:
        display(stdscr, self.draw_fight(), fight_x, fight_y, 42 + 20)
        
        enemy_max_hp = self.current_enemy.stats['max_hp']
        enemy_bar = draw_bar(self.current_enemy.stats['hp'], enemy_max_hp, 32, '█', '░')
        stdscr.addstr(fight_y + 5, fight_x + 17, enemy_bar, p(C.RED))
        stdscr.addstr(fight_y + 4, fight_x + 17, f"{self.current_enemy.name}", p(C.RED))
        
        turn = self.g.player.name if self.fight_state == FightStates.PLAYER_TURN else self.current_enemy.name
        time_left = 5 - self.counter // 100 if self.fight_state == FightStates.PLAYER_TURN else 2 - self.counter // 100
        stdscr.addstr(fight_y + 7, fight_x + 17, f"{turn}'s turn", p(C.CYAN))
        stdscr.addstr(fight_y + 8, fight_x + 17, f"Time left: {str(time_left).rjust(2)}s" if self.fight_state == FightStates.PLAYER_TURN else "", p(C.WHITE))
        if self.play_state == PlayStates.COMMANDS:
            stdscr.addstr(fight_y + 8, fight_x + 17, "PAUSED        ", p(C.WHITE))
            
    def draw_shop(self) -> list:
        MAX_LENGTH = 62
        offset = 12
        empty = ("", C.WHITE, C.BLACK)
        
        # === Weapons ===============================================
        fg_main, bg_main = C.BLACK, C.WHITE
        fg_sub,  bg_sub  = C.WHITE, C.BLACK
        
        if self.play_state == PlayStates.SHOPPING and self.g.current_option == 0:
            fg_main, bg_main = C.BLACK, C.YELLOW
            
        content = [
            empty,
            ("Weapons".center(MAX_LENGTH), fg_main, bg_main),
            empty,
        ]
        for i, weapon_enum in enumerate(SHOP_WEAPONS):
            weapon, price = weapon_enum.value
            if self.g.current_option == 0 and self.g.current_sub_option == i:
                fg_sub,  bg_sub  = C.YELLOW, C.BLACK
            else:
                fg_sub,  bg_sub  = C.WHITE, C.BLACK
            content.append((f"   {weapon.value.name.ljust(offset)} - {price}$  ATK: {str(weapon.value.attack).ljust(4)}  Rarity: {weapon.value.rarity.value.capitalize()}",  fg_sub, bg_sub))  
        # ===========================================================
        
        # === Armors ================================================
        fg_main, bg_main = C.BLACK, C.WHITE
        fg_sub,  bg_sub  = C.WHITE, C.BLACK
        
        if self.play_state == PlayStates.SHOPPING and self.g.current_option == 1:
            fg_main, bg_main = C.BLACK, C.YELLOW
        
        content.extend([
            empty,
            ("Armors".center(MAX_LENGTH), fg_main, bg_main),
            empty,
        ])
        for i, armor_enum in enumerate(SHOP_ARMORS):
            armor, price = armor_enum.value
            if self.g.current_option == 1 and self.g.current_sub_option == i:
                fg_sub,  bg_sub  = C.YELLOW, C.BLACK
            else:
                fg_sub,  bg_sub  = C.WHITE, C.BLACK
            content.append((f"   {armor.value.name.ljust(offset)} - {price}$  DEF: {str(armor.value.defense).ljust(4)}  Rarity: {armor.value.rarity.value.capitalize()}",  fg_sub, bg_sub))
        # ===========================================================
        
        # === Potions ===============================================
        fg_main, bg_main = C.BLACK, C.WHITE
        fg_sub,  bg_sub  = C.WHITE, C.BLACK
        
        if self.play_state == PlayStates.SHOPPING and self.g.current_option == 2:
            fg_main, bg_main = C.BLACK, C.YELLOW
        
        content.extend([
            empty,
            ("Potions".center(MAX_LENGTH), fg_main, bg_main),
            empty,
        ])
        if self.g.current_option == 2 and self.g.current_sub_option == 0:
                fg_sub,  bg_sub  = C.YELLOW, C.BLACK
        lines = ["   Healing Potion".ljust(offset*2 + 3) + " - 10$", "   Mana Potion".ljust(offset*2 + 3) + " - 5$"]
        for i, line in enumerate(lines):
            if self.g.current_option == 2 and self.g.current_sub_option == i:
                fg_sub,  bg_sub  = C.YELLOW, C.BLACK
            else:
                fg_sub,  bg_sub  = C.WHITE, C.BLACK
            content.append((line, fg_sub, bg_sub))
        
        # ===========================================================
        for _ in range(21 - len(content)):
            content.append(empty)
        return draw_outline(MAX_LENGTH, content, "Shop")
    
    def draw_inventory(self) -> list:
        MAX_LENGTH = 62
        offset = 12
        empty = ("", C.WHITE, C.BLACK)
        
        # === Weapons ===============================================
        fg_main, bg_main = C.BLACK, C.WHITE
        fg_sub,  bg_sub  = C.WHITE, C.BLACK
        
        if self.play_state == PlayStates.INVENTORY and self.g.current_option == 0:
            fg_main, bg_main = C.BLACK, C.YELLOW
            
        content = [
            empty,
            ("Weapons".center(MAX_LENGTH), fg_main, bg_main),
            empty,
        ]
        for i, weapon in enumerate(self.g.player.inventory['weapons']):
                if self.play_state == PlayStates.INVENTORY and self.g.current_option == 0 and self.g.current_sub_option == i:
                    fg_sub,  bg_sub  = C.YELLOW, C.BLACK
                else:
                    fg_sub,  bg_sub  = C.WHITE, C.BLACK
                w = W[weapon].value
                content.append((f"   {w.name.ljust(offset)} - ATK: {str(w.attack).ljust(4)}  ({w.rarity.value.capitalize()})",  fg_sub, bg_sub)) 
        # ===========================================================
        
        # === Armors ================================================
        fg_main, bg_main = C.BLACK, C.WHITE
        fg_sub,  bg_sub  = C.WHITE, C.BLACK
        
        if self.play_state == PlayStates.INVENTORY and self.g.current_option == 1:
            fg_main, bg_main = C.BLACK, C.YELLOW
        
        content.extend([
            empty,
            ("Armors".center(MAX_LENGTH), fg_main, bg_main),
            empty,
        ])
        for i, armor in enumerate(self.g.player.inventory['armors']):
            if self.play_state == PlayStates.INVENTORY and self.g.current_option == 1 and self.g.current_sub_option == i:
                fg_sub,  bg_sub  = C.YELLOW, C.BLACK
            else:
                fg_sub,  bg_sub  = C.WHITE, C.BLACK
            a = A[armor].value
            content.append((f"   {a.name.ljust(offset)} - DEF: {str(a.defense).ljust(4)}  ({a.rarity.value.capitalize()})",  fg_sub, bg_sub)) 
        # ===========================================================
        for _ in range(21 - len(content)):
            content.append(empty)
        return draw_outline(MAX_LENGTH, content, "Inventory")

    def battle(self) -> None:
        # Récupérer le biome actuel
        x, y = self.g.player.position['x'], self.g.player.position['y']
        biome = self.g.map.data[y][x].value
        
        # Vérifier si le joueur est debout et s'il y a une chance de rencontrer un ennemi
        if not self.g.player.standing and biome.enemy and random.randint(0, 100) <= biome.rate:
            # Choisir un ennemi aléatoire
            enemy_key = random.choice(list(self.g.enemies.keys()))
            enemy = self.g.enemies[enemy_key]

            # Vérifier si l'ennemi peut apparaître dans le biome actuel
            if enemy.biome.value.name == biome.name:
                add_notif(self.g, "", C.WHITE, C.RED)
                add_notif(self.g, "", C.WHITE, C.RED)
                add_notif(self.g, "", C.WHITE, C.RED)
                add_notif(self.g, "", C.WHITE, C.RED)
                add_notif(self.g, f"You encountered a {enemy.name}!".center(40 + 20), C.WHITE, C.RED)
                add_notif(self.g, "", C.WHITE, C.RED)
                self.draw()
                time.sleep(2)
                self.current_enemy = enemy
                self.push_state(PlayStates.FIGHTING)
                self.g.player.standing = True
                
    def fight(self) -> None:
        clear_notif(self.g)
        while self.play_state == PlayStates.FIGHTING:
            self.draw()
            key = self.g.stdscr.getch()
            try:
                if key == ord('\x1b'):
                    self.pop_state()
                    break
                
                if self.fight_state == FightStates.PLAYER_TURN:
                    self.counter += 1

                    # Check if the player has 5 seconds to act
                    if self.counter >= 500:
                        self.fight_state = FightStates.ENEMY_TURN
                        self.counter     = 0
                        continue
                    
                    if key == ord(' '):
                        if not self.g.player.attack(self.current_enemy):
                            self.fight_state = FightStates.ENEMY_TURN
                            self.counter     = 0
                        else:
                            self.pop_state()
                            self.g.player.standing = False
                            self.current_enemy = None
                            self.counter = 0
                            break

                    elif key == ord('1'):
                        self.g.player.use_potion('healing')
                        self.fight_state = FightStates.ENEMY_TURN
                        self.counter     = 0
                        
                    elif key == ord('2'):
                        self.g.player.use_potion('mana')
                        self.fight_state = FightStates.ENEMY_TURN
                        self.counter     = 0

                elif self.fight_state == FightStates.ENEMY_TURN:
                    self.counter += 1
                    if self.counter >= 100: 
                        if not self.current_enemy.attack(self.g.player):
                            self.fight_state = FightStates.PLAYER_TURN
                            self.counter = 0
                        else:
                            self.push_state(PlayStates.PLAYING)
                            self.g.player.standing = False
                            self.current_enemy.stats['hp'] = self.current_enemy.stats['max_hp']
                            self.current_enemy = None
                            self.counter = 0
                            
                            gold_lost  = random.randint(20, 50)
                            level_lost = random.randint(1, 2)
                            
                            for _ in range(level_lost):
                                self.g.player.level_down()
                            
                            self.g.player.stats['gold']  -= gold_lost
                            
                            if self.g.player.stats['gold'] < 0:
                                self.g.player.stats['gold'] = 0
                                
                            add_notif(self.g, f"You lost {gold_lost}$ and {level_lost} level(s)!", C.RED)
                            add_notif(self.g, "You died! Game Over.", C.RED)
                            self.g.stdscr.refresh()   
                            time.sleep(2)
                            break
            
            except Exception as e:
                self.g.stdscr.addstr(0, 0, f"(play.py -> fight) An error occurred: {e}", p(C.RED))
                self.g.stdscr.refresh()
                time.sleep(4)
                break
            
    def check_tile(self) -> None:
        x, y = self.g.player.position['x'], self.g.player.position['y']
        tile = self.g.map.data[y][x].name
        
        if tile == 'SHOP':
            self.g.current_option = 0
            self.push_state(PlayStates.SHOPPING)
                
    def execute_command(self):
        match self.g.current_option:
            case 0:
                self.push_state(PlayStates.HELP)
                self.push_state(PlayStates.HELP)
            case 1:
                save_game(self.g)
                add_notif(self.g, f"Saved game as '{self.g.player.name}'", C.GREEN)
            case 2:
                add_notif(self.g, "Equip selected", C.CYAN)
            case 3:
                self.push_state(PlayStates.QUITTING)
                self.push_state(PlayStates.QUITTING)
                
    def draw_try(self, msg, error) -> None:
        self.g.stdscr.addstr(0, 0, f"{msg} An error occurred: {error}", p(C.RED))
        self.g.stdscr.refresh()
        time.sleep(4)
        self.push_state(PlayStates.QUITTING)
                
    def draw(self) -> None:
        # Clear the screen
        self.g.stdscr.clear()

        # Draw each section at its fixed position
        map_x,   map_y   =  0     ,  0
        fight_x, fight_y =  0     ,  0 
        stats_x, stats_y = 42 + 20,  0
        equip_x, equip_y = 42 + 20,  0
        cmd_x,   cmd_y   =  0     , 24 + 1
        notif_x, notif_y = 13     , 24 + 1
        biome_x, biome_y = 57 + 20, 24 + 1
        
        
        empty_box = draw_outline(42 + 20, [("", C.WHITE, C.BLACK) for _ in range(23)])
        
        msg = ""
        try:
            if not self.play_state == PlayStates.HELP:
                # Draw the map or the fight
                if self.play_state == PlayStates.FIGHTING or (self.play_state == PlayStates.COMMANDS and self.state_stack[-2] == PlayStates.FIGHTING):
                    msg = "(play, draw, display_fight)"
                    self.display_fight(self.g.stdscr, fight_x, fight_y)
                elif self.play_state == PlayStates.PLAYING or (self.play_state == PlayStates.COMMANDS and self.state_stack[-2] == PlayStates.PLAYING):
                    msg = "(play, draw, display_map)"
                    self.display_map(self.g.stdscr, map_x, map_y)
                elif self.play_state == PlayStates.SHOPPING or (self.play_state == PlayStates.COMMANDS and self.state_stack[-2] == PlayStates.SHOPPING):
                    msg = "(play, draw, display, shop)"
                    display(self.g.stdscr, self.draw_shop(), 0, 0, 42 + 20, 2, 2, True)
                elif self.play_state == PlayStates.QUITTING:
                    msg = "(play, draw, display, empty_box)"
                    display(self.g.stdscr, empty_box, 0, 0, 42 + 20)
                elif self.play_state == PlayStates.INVENTORY or (self.play_state == PlayStates.COMMANDS and self.state_stack[-2] == PlayStates.INVENTORY):
                    msg = "(play, draw, display, inventory)"
                    display(self.g.stdscr, self.draw_inventory(), 0, 0, 42 + 20, 2, 2, True)
                
                # Draw the player stats
                msg = "(play, draw, display_stats)"
                self.display_stats(self.g.stdscr, stats_x, stats_y)

                # Draw the equipment
                if self.show_equipment:
                    msg = "(play, draw, display_equipment)"
                    self.display_equipment(self.g.stdscr, equip_x, equip_y)

                # Draw the commands
                msg = "(play, draw, display, commands)"
                display(self.g.stdscr, self.draw_commands(), cmd_x, cmd_y, 13, 1, 1)

                # Draw the notifications
                msg = "(play, draw, display, notifications)"
                display(self.g.stdscr, self.draw_notifications(), notif_x, notif_y, 44 + 20)

                # Draw the biome
                msg = "(play, draw, display, biome)"
                display(self.g.stdscr, self.draw_biome(), biome_x, biome_y, 13)
                
            else:
                for i, line in enumerate(self.commands):
                    self.g.stdscr.addstr(i, 0, line, p(C.CYAN))
                
                self.g.stdscr.refresh()
        
        except Exception as e:
            self.draw_try(msg, e)

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
                            self.check_tile()
                            
                    elif key == ord('s'):
                        if not self.g.player.move(0, 1):
                            add_notif(self.g, "↓ You went south.")
                            self.g.generate_map(Direction.SOUTH)
                        if not self.g.player.standing:
                            self.battle()
                            self.check_tile()
                            
                    elif key == ord('a'):
                        if not self.g.player.move(-1, 0):
                            add_notif(self.g, "← You went west.")
                            self.g.generate_map(Direction.WEST)
                        if not self.g.player.standing:
                            self.battle()
                            self.check_tile()
                            
                    elif key == ord('d'):
                        if not self.g.player.move(1, 0):
                            add_notif(self.g, "→ You went east.")
                            self.g.generate_map(Direction.EAST)
                        if not self.g.player.standing:
                            self.battle()
                            self.check_tile()
                            
                    elif key == ord('h'):
                        self.g.player.use_potion('healing')
                    
                    elif key == ord('j'):
                        self.g.player.use_potion('mana')
                    
                    elif key == ord('\x1b'):
                        self.g.current_option = 0
                        self.push_state(PlayStates.COMMANDS)
                    
                    elif key == ord('i'):
                        self.g.current_option = 0
                        self.push_state(PlayStates.INVENTORY)
                    

                elif self.play_state == PlayStates.COMMANDS:
                    if key == curses.KEY_UP or key == ord('w'):
                        self.g.current_option = max(0, self.g.current_option - 1)
                    elif key == curses.KEY_DOWN or key == ord('s'):
                        self.g.current_option = min(3, self.g.current_option + 1)
                    elif key == ord('\x1b'):
                        self.pop_state()
                    elif key == ord('\n'):
                        self.execute_command()
                        self.pop_state()
                    elif key == ord('i'):
                        self.g.current_option = 0
                        self.push_state(PlayStates.INVENTORY)
                            
                elif self.play_state == PlayStates.FIGHTING:
                    self.fight()
                    
                elif self.play_state == PlayStates.QUITTING:
                    add_notif(self.g, "Quitting the game...", C.RED)
                    self.state_stack = [PlayStates.PLAYING]
                    self.draw()
                    time.sleep(1)
                    run = False
                    break
                
                elif self.play_state == PlayStates.SHOPPING:
                    if self.g.current_sub_option == -1:
                        if key == ord('\x1b'):
                            self.g.current_option = 0
                            self.push_state(PlayStates.COMMANDS)
                        elif key == curses.KEY_UP or key == ord('w'):
                            self.g.current_option = max(0, self.g.current_option - 1)
                        elif key == curses.KEY_DOWN or key == ord('s'):
                            self.g.current_option = min(2, self.g.current_option + 1)
                        elif key == ord('\n'):
                            self.g.current_sub_option = 0
                        elif key == ord('i'):
                            self.g.current_option = 0
                            self.push_state(PlayStates.INVENTORY)
                        elif key == ord('e'):
                            self.g.current_option = 0
                            self.pop_state()
                            
                    else:
                        if key == ord('\x1b'):
                            self.g.current_sub_option = -1
                        elif key == curses.KEY_UP or key == ord('w'):
                            self.g.current_sub_option = max(0, self.g.current_sub_option - 1)
                        elif key == curses.KEY_DOWN or key == ord('s'):
                            max_option = (len(SHOP_WEAPONS) - 1) if self.g.current_option == 0 else (len(SHOP_ARMORS) - 1)
                            self.g.current_sub_option = min(max_option, self.g.current_sub_option + 1)
                        elif key == ord('\n'):
                            try:
                                if self.g.current_option == 0:
                                    weapon, price = list(SHOP_WEAPONS)[self.g.current_sub_option].value
                                    if self.g.player.stats['gold'] >= price:
                                        self.g.player.stats['gold'] -= price
                                        self.g.player.inventory['weapons'].append(weapon.name)
                                        add_notif(self.g, f"You bought a {weapon.value.name} for {price}$", C.GREEN)
                                    else:
                                        add_notif(self.g, "You don't have enough gold!", C.RED)
                                elif self.g.current_option == 1:
                                    armor, price = list(SHOP_ARMORS)[self.g.current_sub_option].value
                                    if self.g.player.stats['gold'] >= price:
                                        self.g.player.stats['gold'] -= price
                                        self.g.player.inventory['armors'].append(armor.name)
                                        add_notif(self.g, f"You bought a {armor.value.name} for {price}$", C.GREEN)
                                    else:
                                        add_notif(self.g, "You don't have enough gold!", C.RED)
                                elif self.g.current_option == 2:
                                    if self.g.current_sub_option == 0:
                                        if self.g.player.stats['gold'] >= 10:
                                            self.g.player.stats['gold'] -= 10
                                            self.g.player.equipment['potions']['healing'] += 1
                                            add_notif(self.g, "You bought a healing potion for 10$", C.GREEN)
                                        else:
                                            add_notif(self.g, "You don't have enough gold!", C.RED)
                                    elif self.g.current_sub_option == 1:
                                        if self.g.player.stats['gold'] >= 5:
                                            self.g.player.stats['gold'] -= 5
                                            self.g.player.equipment['potions']['mana'] += 1
                                            add_notif(self.g, "You bought a mana potion for 5$", C.GREEN)
                                        else:
                                            add_notif(self.g, "You don't have enough gold!", C.RED)
                                        
                            except Exception as e:
                                self.g.stdscr.addstr(1, 0, f"(play.py -> run, buy) An error occurred: {e}", p(C.RED))
                                self.g.stdscr.refresh()
                                time.sleep(4)
                                run = False
                                break
                
                elif self.play_state == PlayStates.INVENTORY:
                    if self.g.current_sub_option == -1:
                        if key == ord('\x1b'):
                            self.g.current_option = 0
                            self.push_state(PlayStates.COMMANDS)
                        elif key == ord('\n'):
                            self.g.current_sub_option = 0
                        elif key == ord('i'):
                            self.g.current_option = 0
                            self.pop_state()
                        elif key == ord('w'):
                            self.g.current_option = max(0, self.g.current_option - 1)
                        elif key == ord('s'):
                            self.g.current_option = min(1, self.g.current_option + 1)
                    else:
                        if key == ord('\x1b'):
                            self.g.current_sub_option = -1
                        elif key == curses.KEY_UP or key == ord('w'):
                            self.g.current_sub_option = max(0, self.g.current_sub_option - 1)
                        elif key == curses.KEY_DOWN or key == ord('s'):
                            max_option = (len(self.g.player.inventory['weapons']) - 1) if self.g.current_option == 0 else (len(self.g.player.inventory['armors']) - 1)
                            self.g.current_sub_option = min(max_option, self.g.current_sub_option + 1)
                        elif key == ord('\n'):
                            try:
                                if self.g.current_option == 0:
                                    weapon = self.g.player.inventory['weapons'][self.g.current_sub_option]
                                    self.g.player.equipment['weapon'] = weapon
                                    self.g.player.stats['attack'] = self.g.player.stats['base_attack'] + W[weapon].value.attack
                                    add_notif(self.g, f"You equipped a {W[weapon].value.name}", C.GREEN)
                                elif self.g.current_option == 1:
                                    armor = self.g.player.inventory['armors'][self.g.current_sub_option]
                                    self.g.player.equipment['armor'] = armor
                                    self.g.player.stats['defense'] = self.g.player.stats['base_defense'] + A[armor].value.defense
                                    add_notif(self.g, f"You equipped a {A[armor].value.name}", C.GREEN)
                            except Exception as e:
                                self.g.stdscr.addstr(0, 0, f"(play.py -> run, equip) An error occurred: {e}", p(C.RED))
                                self.g.stdscr.refresh()
                                time.sleep(4)
                                run = False
                                break
                
                elif self.play_state == PlayStates.HELP:
                    if key == ord('\x1b') or key == ord(' ') or key == ord('\n'):
                        self.pop_state()
                
                if key == ord('e'):
                    self.show_equipment = not self.show_equipment


            except Exception as e:
                self.g.stdscr.addstr(0, 0, f"(play.py -> run) An error occurred:  {e})", p(C.RED))
                self.g.stdscr.refresh()
                time.sleep(4)
                run = False
                break
