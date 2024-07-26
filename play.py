import time
import random
import curses
import utils

from utils import draw_bar, draw_outline, p, print_stat, format_line as fl, add_notif, display, Colors as C, cleanup as cl, save_game, clear_notif, create_ui, get_rarity_color, display_popup, display_confirmation_popup
from tile import ascii_art, Biome
from game import Direction
from objects import SHOP_WEAPONS, SHOP_ARMORS, Weapons as W, Armors as A, Rarity, Rings as R
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
        
        self.player_time = 50
        self.enemy_time  = 5
        
        self.commands = create_ui("Commands", [
            "┌──────────────────────────────────────────────────────────┐".center(self.g.ui_max_length),
            "│             MENU, COMMANDS, SHOP, INVENTORY              │".center(self.g.ui_max_length),
            "├─────────────────────────────┬────────────────────────────┤".center(self.g.ui_max_length),
            "│ up, down, w, s:             │ Navigate through the menu. │".center(self.g.ui_max_length),
            "│ enter:                      │ Select an option.          │".center(self.g.ui_max_length),
            "├─────────────────────────────┴────────────────────────────┤".center(self.g.ui_max_length),
            "│                           GAME                           │".center(self.g.ui_max_length),
            "├─────────────────────────────┬────────────────────────────┤".center(self.g.ui_max_length),
            "│ w, a, s, d:                 │ Move the player.           │".center(self.g.ui_max_length),
            "│ i:                          │ Open the inventory.        │".center(self.g.ui_max_length),
            "│ ESC:                        │ Enter in commands menu.    │".center(self.g.ui_max_length),
            "│ e:                          │ Show Equipments view.      │".center(self.g.ui_max_length),
            "├─────────────────────────────┴────────────────────────────┤".center(self.g.ui_max_length),
            "│                           FIGHT                          │".center(self.g.ui_max_length),
            "├─────────────────────────────┬────────────────────────────┤".center(self.g.ui_max_length),
            "│ space:                      │ Attack the enemy.          │".center(self.g.ui_max_length),
            "│ 1, 2:                       │ Use a potion (heal, mana). │".center(self.g.ui_max_length),
            "│ ESC:                        │ Enter in commands menu.    │".center(self.g.ui_max_length),
            "└─────────────────────────────┴────────────────────────────┘".center(self.g.ui_max_length),
        ])
        
        self.max_notifs = 9
        self.notifs = []
        clear_notif(self)
        
        add_notif(self, "Press 'ESCAPE' to enter command mode.".center(60), C.GRAY)
        add_notif(self, 'Welcome to the game!'.center(60), C.YELLOW)
        add_notif(self, "")
        add_notif(self, "")
        
        self.m_x,  self.m_y,  self.m_w,  self.m_h  =  28,   0,  63,  22
        self.f_x,  self.f_y,  self.f_w,  self.f_h  =  28,   0,  63,  22
        self.s_x,  self.s_y,  self.s_w,  self.s_h  =   0,   0,  28,  22
        self.sh_x, self.sh_y, self.sh_w, self.sh_h =  28,   0,  63,  22
        self.e_x,  self.e_y,  self.e_w,  self.e_h  =  91,   0,  28,  22
        self.c_x,  self.c_y,  self.c_w,  self.c_h  =   0,  26,  14,   9
        self.n_x,  self.n_y,  self.n_w,  self.n_h  =  28,  26,  63, self.max_notifs
        self.b_x,  self.b_y,  self.b_w,  self.b_h  =  91,  26,  28,   7
        self.i_x,  self.i_y,  self.i_w,  self.i_h  =  28,   0,  63,  22
        self.bt_x, self.bt_y, self.bt_w, self.bt_h =  14,  26,  14,   9
        
        self.empty_box_x, self.empty_box_y, self.empty_box_w, self.empty_box_h = 28, 0, 63, 24
    
        self.empty_box = draw_outline(self.empty_box_w, [("", C.WHITE, C.BLACK) for _ in range(self.empty_box_h)])

    def push_state(self, state: PlayStates) -> None:
        self.state_stack.append(state)

    def pop_state(self) -> PlayStates:
        if len(self.state_stack) > 1:
            return self.state_stack.pop()
        return self.state_stack[-1]

    @property
    def play_state(self) -> PlayStates:
        return self.state_stack[-1]

    def display_map(self, stdscr, map_x, map_y) -> None:
        def get_symbol_and_color(row_idx, col_idx):
            if row_idx == y and col_idx == x:
                return 'P', C.RED
            elif self.g.map.data_explored[row_idx][col_idx] == 1:
                tile = self.g.map.data[row_idx][col_idx]
                return tile.value.symbol, tile.value.color
            else:
                return '?', None

        x, y = self.g.player.position['x'], self.g.player.position['y']
        map_content = []

        for row_idx in range(self.g.map.height):
            row_str = ""
            for col_idx in range(self.g.map.width):
                symbol, _ = get_symbol_and_color(row_idx, col_idx)
                row_str += symbol
            map_content.append(row_str)
        
        outlined_map = draw_outline(len(map_content[0]) + 2, map_content, "Map")
        
        for i, line in enumerate(outlined_map):
            stdscr.addstr(map_y + i, map_x, line, p(C.CYAN))
        
        for row_idx in range(self.g.map.height):
            for col_idx in range(self.g.map.width):
                symbol, color = get_symbol_and_color(row_idx, col_idx)
                if color is not None:
                    stdscr.addstr(row_idx + 3 + map_y, col_idx + 1 + map_x, symbol, p(color))

    
    def draw_stats(self, s_width, s_height) -> list:
        bar_size = 12
        stats    = self.g.player.stats
        exp_t    = self.g.exp_table
        x, y     = self.g.player.position['x'], self.g.player.position['y']
        hp_bar   = draw_bar(stats['hp'],   stats['max_hp'],       bar_size)
        mana_bar = draw_bar(stats['mana'], stats['max_mana'],     bar_size)
        exp_bar  = draw_bar(stats['exp'],  exp_t[stats['level']], bar_size)
        
        empty    = (" " * (s_width - 2), C.WHITE, C.BLACK)
        mx, my   = self.g.map.current_map

        st = self.g.player.stats
        name = self.g.player.name.capitalize()
        content = [
            (f" Name       ?{name                   }", C.WHITE,  C.BLACK),
            empty,   
            (f" HP         ?{hp_bar                 }", C.RED,    C.BLACK),
            (f" Mana       ?{mana_bar               }", C.BLUE,   C.BLACK),
            (f" Exp:       ?{exp_bar                }", C.GREEN,  C.BLACK),
            empty,     
            (f" Level      ?{str(st['level'])       }", C.GREEN,  C.BLACK),
            (f" Gold       ?{str(st['gold']) + '$'  }", C.YELLOW, C.BLACK),
            empty,         
            (f" Attack     ?{str(st['attack'])      }", C.WHITE,  C.BLACK),
            (f" Base ATK   ?{str(st['base_attack']) }", C.WHITE,  C.BLACK),
            (f" Critical   ?{str(st['critical'])+'%'}", C.WHITE,  C.BLACK),
            (f" Defense    ?{str(st['defense'])     }", C.WHITE,  C.BLACK),
            (f" Base DEF   ?{str(st['base_defense'])}", C.WHITE,  C.BLACK),
            empty,    
            (f" Position   ?{f"({x:>2},{y:>2})"     }", C.WHITE , C.BLACK),
            (f" Map        ?{f"({mx:>2},{my:>2})"   }", C.WHITE , C.BLACK),
        ]
        for _ in range(s_height - len(content)):
            content.append(empty)
        return draw_outline(s_width, content, "Player Stats")

    def display_stats(self, stdscr, stats_x, stats_y, stats_width, stats_height) -> None:
        stats_frame = self.draw_stats(stats_width, stats_height)
        for i, (line, fg, bg) in enumerate(stats_frame):
            print_stat(stdscr, stats_y + i, stats_x, line, p(C.GRAY), p(fg, bg), p(C.CYAN))
 
    def draw_equipment(self, e_width, e_height) -> list:
        weapon  =   W[self.g.player.equipment['weapon']].value if self.g.player.equipment['weapon'] else None
        armor   =   A[self.g.player.equipment['armor']].value  if self.g.player.equipment['armor']  else None
        ring    =   R[self.g.player.equipment['ring']].value   if self.g.player.equipment['ring']   else None
        healing = str(self.g.player.equipment['potions'].get('healing', 0))
        mana    = str(self.g.player.equipment['potions'].get('mana', 0))
        
        if weapon:
            w_name    = weapon.name
            w_attack  = str(weapon.attack)
            w_r_name  = weapon.rarity.value.capitalize()
            w_r_color = get_rarity_color(weapon.rarity)
        else:
            w_name    = '-'
            w_attack  = '-'
            w_r_name  = '-'
            w_r_color = C.WHITE
        
        if armor:
            a_name    = armor.name
            a_defense = str(armor.defense)
            a_r_color = get_rarity_color(armor.rarity)
            a_r_name  = armor.rarity.value.capitalize()
        else:
            a_name    = '-'
            a_defense = '-'
            a_r_name  = '-'
            a_r_color = C.WHITE
            
        if ring:
            r_name    = ring.name
            r_effect  = ring.effect
            r_value   = '+' + str(ring.value)
            r_r_color = get_rarity_color(ring.rarity)
            r_r_name  = ring.rarity.value.capitalize()
        else:
            r_name    = '-'
            r_effect  = '-'
            r_value   = '-'
            r_r_name  = '-'
            r_r_color = C.WHITE
        
        empty = ("", C.WHITE, C.BLACK)

        content = [
                (f" Weapon      ?{w_name   }", w_r_color, C.BLACK),
                (f"  - ATK      ?{w_attack }", w_r_color, C.BLACK),
                (f"  - rarity   ?{w_r_name }", w_r_color, C.BLACK),
                empty,
                (f" Armor       ?{a_name   }", a_r_color, C.BLACK),
                (f"  - DEF      ?{a_defense}", a_r_color, C.BLACK),
                (f"  - rarity   ?{a_r_name }", a_r_color, C.BLACK),
                empty,
                (f" Ring        ?{r_name   }", r_r_color, C.BLACK),
                (f"  - effect   ?{r_effect }", r_r_color, C.BLACK),
                (f"  - value    ?{r_value  }", r_r_color, C.BLACK),
                (f"  - rarity   ?{r_r_name }", r_r_color, C.BLACK),
                empty,
                (f" Potions     ?"           , C.WHITE,   C.BLACK),
                (f"  - healing  ?{healing  }", C.RED  ,   C.BLACK),
                (f"  - mana     ?{mana     }", C.BLUE ,   C.BLACK),
        ]
        for _ in range(e_height - len(content)):
            content.append(empty)
        return draw_outline(e_width, content, "Equipment")

    def display_equipment(self, stdscr, equip_x, equip_y, equip_width, equip_height) -> None:
        equip_frame = self.draw_equipment(equip_width, equip_height)
        for i, (line, fg, bg) in enumerate(equip_frame):
            print_stat(stdscr, equip_y + i, equip_x, line, p(C.GRAY), p(fg, bg), p(C.CYAN))

    def draw_commands(self, c_width, c_height) -> list:
        content = [
            ("          ", C.WHITE, C.BLACK),
            ("  help    ", C.WHITE, C.BLACK),
            ("  save    ", C.WHITE, C.BLACK),
            ("  colors  ", C.WHITE, C.BLACK),
            ("  quit    ", C.WHITE, C.BLACK),
            ("          ", C.WHITE, C.BLACK),
        ]
            
        for _ in range(c_height - len(content)):
            content.append(("", C.WHITE, C.BLACK))
            
        o_commands = draw_outline(c_width, content)
        if self.play_state == PlayStates.COMMANDS:
            co = self.g.current_option + 2
            o_commands[co] = (f"{o_commands[co][0][0]}>{o_commands[co][0][2:]}", C.YELLOW, C.BLACK)
        return o_commands
    
    def draw_biomes_thumbnail(self, bt_width, bt_height) -> list:
        empty = ("", C.WHITE, C.BLACK)
        content = [empty]
        for biome in Biome:
            tile = biome.value
            line = f" {tile.symbol} {tile.name.capitalize()}"
            content.append((line.ljust(bt_width), tile.color, C.BLACK))
        
        for _ in range(bt_height - len(content) ):
            content.append(empty)
        return draw_outline(bt_width, content)
    
    def draw_biome(self, b_width, b_height) -> list:
        x, y = self.g.player.position['x'], self.g.player.position['y']
        current_tile = self.g.map.data[y][x]
        biome_name  = current_tile.name
        biome_color = current_tile.value.color
        biome_art = [line.center(b_width-2) for line in ascii_art[biome_name]]
        
        for _ in range(b_height - len(biome_art)):
            biome_art.append("")
        
        outlined_biome = draw_outline(b_width, biome_art, biome_name.capitalize())
        lines_with_colors = [(line, biome_color, C.BLACK) for line in outlined_biome]
        lines_with_colors[2] = (lines_with_colors[2][0], C.CYAN, C.BLACK)
        
        return lines_with_colors
    
    def draw_fight(self, f_width, f_height) -> list:
        enemy = self.current_enemy
        enemy_art = ARTS[enemy.key]
        
        empty = ("", C.CYAN, C.BLACK)
        
        enemy_info = [
            (f"   Max HP       ?{str(enemy.stats['attack'])}", C.WHITE, C.BLACK),
            (f"   Attack       ?{str(enemy.stats['attack'])}", C.WHITE, C.BLACK),
        ]

        weapon = enemy.weapon.value if enemy.weapon else None
        
        if weapon:
            w_name    = weapon.name
            w_attack  = str(weapon.attack)
            w_r_color = get_rarity_color(weapon.rarity)
            w_r_name  = weapon.rarity.value.capitalize()
        else:
            w_name    = "-"
            w_attack  = "-"
            w_r_name  = "-"
            w_r_color = C.WHITE
            
        weapon_info = [
            (f"   Weapon       ?",           C.WHITE,   C.BLACK),
            (f"    - Name      ?{w_name  }", C.WHITE,   C.BLACK),
            (f"    - Attack    ?{w_attack}", C.WHITE,   C.BLACK),
            (f"    - Rarity    ?{w_r_name}", w_r_color, C.BLACK)
        ]

        armor = enemy.armor.value if enemy.armor else None
        if armor:
            a_name    = armor.name
            a_defense = str(armor.defense)
            a_r_color = get_rarity_color(armor.rarity)
            a_r_name  = armor.rarity.value.capitalize()
        else:
            a_name    = "_"
            a_defense = "_"
            a_r_color = C.WHITE
            a_r_name  = "_"
        armor_info = [
            (f"   Armor        ?",            C.WHITE,   C.BLACK),
            (f"    - Name      ?{a_name   }", C.WHITE,   C.BLACK),
            (f"    - Defense   ?{a_defense}", C.WHITE,   C.BLACK),
            (f"    - Rarity    ?{a_r_name }", a_r_color, C.BLACK)
        ]

        content = [
            *[(" " + line, C.YELLOW, C.BLACK) for line in enemy_art],
            empty,
            *enemy_info,
            empty,
            *weapon_info,
            empty,
            *armor_info,
            empty,
        ]
        for _ in range(f_height - len(content)):
            content.append(empty)
        return draw_outline(f_width, content, f"Fight !")

    
    def display_fight(self, stdscr, fight_x, fight_y, fight_width, fight_height) -> None:
        draw_frame = self.draw_fight(fight_width, fight_height)
        display(stdscr, draw_frame[:-10], fight_x, fight_y)

        for i, (line, fg, bg) in enumerate(draw_frame[10:]):
            print_stat(stdscr, fight_y + i + 10, fight_x, line, p(C.GRAY), p(fg, bg), p(C.CYAN))

        enemy_name = self.current_enemy.name
        if self.fight_state == FightStates.PLAYER_TURN:
            turn          = self.g.player.name
            time_max      = self.player_time
            time_left     = (time_max - self.counter) // 10
            time_left_str = str(time_left + 1).rjust(2)
        else:
            turn          = enemy_name
            time_max      = self.enemy_time
            time_left     = (time_max - self.counter) // 10
            time_left_str = "".rjust(2)

        enemy_max_hp = self.current_enemy.stats['max_hp']
        enemy_bar = draw_bar(self.current_enemy.stats['hp'], enemy_max_hp, 42, '█', '░')

        # Time bar with two colors
        time_bar_length  = 14
        passed_length    = self.counter * time_bar_length // time_max
        remaining_length = time_bar_length - passed_length

        passed_bar    = '─' * passed_length
        remaining_bar = '─' * remaining_length

        stdscr.addstr(fight_y + 5, fight_x + 17, enemy_bar, p(C.RED))
        stdscr.addstr(fight_y + 4, fight_x + 17, f"{enemy_name}", p(C.RED))

        stdscr.addstr(fight_y + 7, fight_x + 17, f"{turn}'s turn", p(C.CYAN))
        stdscr.addstr(fight_y + 9, fight_x + 17, passed_bar, p(C.RED))
        stdscr.addstr(fight_y + 9, fight_x + 17 + passed_length, remaining_bar, p(C.WHITE))
        if self.fight_state == FightStates.PLAYER_TURN:
            stdscr.addstr(fight_y + 8, fight_x + 17, f"Time left: {time_left_str}s", p(C.WHITE))
        if self.play_state == PlayStates.COMMANDS:
            stdscr.addstr(fight_y + 8, fight_x + 17, "PAUSED        ", p(C.WHITE))

            
    def draw_shop(self, s_width, s_height) -> list:
        offset = 12
        empty = ("", C.WHITE, C.BLACK)
        
        content  = self.build_shop_section(0, "Weapons", SHOP_WEAPONS, offset)
        content += self.build_shop_section(1, "Armors",  SHOP_ARMORS,  offset)
        
        fg_main, bg_main = C.BLACK, C.WHITE
        if self.play_state == PlayStates.SHOPPING and self.g.current_option == 2:
            fg_main, bg_main = C.BLACK, C.YELLOW
        
        content.extend([
            empty,
            ("Potions".center(s_width), fg_main, bg_main),
            empty,
        ])
        if self.g.current_option == 2 and self.g.current_sub_option == 0:
            fg_sub, bg_sub = C.YELLOW, C.BLACK
        lines = [
            ("Healing", 10),
            ("Mana",    15)
        ]
        for i, (line, price) in enumerate(lines):
            if self.g.current_option == 2 and self.g.current_sub_option == i:
                fg_sub, bg_sub = C.YELLOW, C.BLACK
            else:
                fg_sub, bg_sub = C.WHITE, C.BLACK
            content.append((f"   {line.ljust(offset)} - {str(price).rjust(2)}$", fg_sub, bg_sub))
        
        for _ in range(s_height - len(content)):
            content.append(empty)
        return draw_outline(s_width, content, "Shop")
    
    def draw_inventory(self, i_width, i_height) -> list:
        offset = 12
        empty = ("", C.WHITE, C.BLACK)
        
        content  = self.build_inventory_section(i_width, 0, "Weapons", self.g.player.inventory['weapons'], W, offset)
        content += self.build_inventory_section(i_width, 1, "Armors",  self.g.player.inventory['armors'],  A, offset)
        content += self.build_inventory_section(i_width, 2, "Rings",   self.g.player.inventory['rings'],   R, offset)
        
        for _ in range(i_height - len(content)):
            content.append(empty)
        return draw_outline(i_width, content, "Inventory")

    def build_shop_section(self, i:int, title: str, items: Enum, offset: int) -> list:
        fg_main, bg_main = C.BLACK, C.WHITE
        if self.play_state == PlayStates.SHOPPING and self.g.current_option == i:
            fg_main, bg_main = C.BLACK, C.YELLOW
            
        content = [
            ("", C.WHITE, C.BLACK),
            (title.center(62), fg_main, bg_main),
            ("", C.WHITE, C.BLACK),
        ]
        for j, item_enum in enumerate(items):
            item, price = item_enum.value
            fg_sub, bg_sub = (C.YELLOW, C.BLACK) if self.g.current_option == i and self.g.current_sub_option == j else (C.WHITE, C.BLACK)
            stat = "ERROR"
            if items == SHOP_WEAPONS:
                stat = f"ATK: {str(item.value.attack).ljust(4)}"
            elif items == SHOP_ARMORS:
                stat = f"DEF: {str(item.value.defense).ljust(4)}"
            content.append((f"   {item.value.name.ljust(offset)} - {price}$  {stat}  Rarity: {item.value.rarity.value.capitalize()}", fg_sub, bg_sub))  
        for _ in range(7 - len(content)):
            content.append(("", C.WHITE, C.BLACK))
        return content
    
    def build_inventory_section(self, i_width:int, i:int, title: str, items: list, enum_class: Enum, offset: int) -> list:
        fg_main, bg_main = C.BLACK, C.WHITE
        if self.play_state == PlayStates.INVENTORY and self.g.current_option == i:
            fg_main, bg_main = C.BLACK, C.YELLOW
            
        content = [
            ("", C.WHITE, C.BLACK),
            (title.center(i_width), fg_main, bg_main),
            ("", C.WHITE, C.BLACK),
        ]
        for j, item in enumerate(items):
            fg_sub, bg_sub = (C.YELLOW, C.BLACK) if self.play_state == PlayStates.INVENTORY and self.g.current_option == i and self.g.current_sub_option == j else (C.WHITE, C.BLACK)
            item_obj = enum_class[item].value
            stat = "ERROR"
            if enum_class == W:
                stat = f"ATK: {str(item_obj.attack).ljust(4)}"
            elif enum_class == A:
                stat = f"DEF: {str(item_obj.defense).ljust(4)}"
            elif enum_class == R:
                stat = f"Effect : {item_obj.effect.ljust(8)} Value: {str(item_obj.value).ljust(2)}"
            content.append((f"   {item_obj.name.ljust(offset)} - {stat}  ({item_obj.rarity.value.capitalize()})".ljust(i_width), fg_sub, bg_sub)) 
        for _ in range(7 - len(content)):
            content.append(("", C.WHITE, C.BLACK))
        return content

    def battle(self) -> None:
        x, y = self.g.player.position['x'], self.g.player.position['y']
        biome = self.g.map.data[y][x].value
        if not self.g.player.standing and biome.enemy and random.randint(0, 100) <= biome.rate:
            enemy_key = random.choice(list(self.g.enemies.keys()))
            enemy = self.g.enemies[enemy_key]
            if enemy.biome.value.name == biome.name:
                w = self.f_w - 4
                content = [
                    ("", C.RED, C.BLACK),
                    (f"/!\\ ATTENTION /!\\".center(w - 2), C.RED, C.BLACK),
                    (f"You encountered a {enemy.name}!".center(w - 2), C.RED, C.BLACK),
                    ("", C.RED, C.BLACK),
                    ("", C.RED, C.BLACK),
                ]
                display_popup(self, content, self.f_x + 2, self.f_y + 10, w)
                self.current_enemy = enemy
                self.push_state(PlayStates.FIGHTING)
                self.g.player.standing = True
                
    def fight(self) -> None:
        
        while self.play_state == PlayStates.FIGHTING:
            self.draw()
            key = self.g.stdscr.getch()
            
            if key == ord('\x1b'):
                self.g.current_option = 0
                self.push_state(PlayStates.COMMANDS)
            else:
                self.counter += 1
            
                if self.fight_state == FightStates.PLAYER_TURN:
                    if self.counter > self.player_time:
                        self.fight_state = FightStates.ENEMY_TURN
                        self.counter = 0
                    else:
                        if key == ord(' '):
                            if not self.g.player.attack(self.current_enemy):
                                self.fight_state = FightStates.ENEMY_TURN
                                self.counter = 0
                            else:
                                self.g.player.standing = False
                                self.current_enemy = None
                                self.counter = 0
                                self.pop_state()
                                break
                        elif key == ord('1'):
                            self.g.player.use_potion('healing')
                            self.fight_state = FightStates.ENEMY_TURN
                            self.counter = 0
                        elif key == ord('2'):
                            self.g.player.use_potion('mana')
                            self.fight_state = FightStates.ENEMY_TURN
                            self.counter = 0

                else:
                    if self.counter > self.enemy_time:
                        if not self.current_enemy.attack(self.g.player):
                            self.fight_state = FightStates.PLAYER_TURN
                            self.counter = 0
                        else:
                            self.g.player.standing = False
                            self.current_enemy.stats['hp'] = self.current_enemy.stats['max_hp']
                            self.current_enemy = None
                            self.counter = 0

                            gold_lost = random.randint(20, 50)
                            level_before = self.g.player.stats['level']
                            level_lost = random.randint(1, 2) 
                            
                            for _ in range(level_lost):
                                self.g.player.level_down()
                                
                            level_after = self.g.player.stats['level']
                            level_lost = level_before - level_after

                            self.g.player.stats['gold'] -= gold_lost

                            if self.g.player.stats['gold'] < 0:
                                self.g.player.stats['gold'] = 0

                            w = self.f_w - 4
                            content = [
                                ("", C.RED, C.BLACK),
                                (f"/!\\ YOU DIED /!\\".center(w - 2), C.RED, C.BLACK),
                                (f"You lost {gold_lost}$ and {level_lost} level(s)!".center(w - 2), C.RED, C.BLACK),
                                ("", C.RED, C.BLACK),
                                ("", C.RED, C.BLACK),
                            ]
                            display_popup(self, content, self.f_x + 2, self.f_y + 10, w)
                            self.pop_state()
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
            case 1:
                save_game(self.g)
                add_notif(self, f"Saved game as '{self.g.player.name}'", C.GREEN)
            case 2:
                self.toogle_colors()
            case 3:
                if not self.state_stack[-2] == PlayStates.FIGHTING:
                    self.push_state(PlayStates.QUITTING)
                    self.push_state(PlayStates.QUITTING)
                
    def draw_try(self, msg, error) -> None:
        self.g.stdscr.addstr(0, 0, f"{msg} An error occurred: {error}", p(C.RED))
        self.g.stdscr.refresh()
        time.sleep(4)
        self.push_state(PlayStates.QUITTING)           

    def handle_playing_state(self, key):
        directions = {
            ord('w'): ( 0, -1, Direction.NORTH),
            ord('s'): ( 0,  1, Direction.SOUTH),
            ord('a'): (-1,  0, Direction.WEST),
            ord('d'): ( 1,  0, Direction.EAST)
        }

        def update_explored_area(x, y, radius=3):
            for i in range(max(0, x - radius), min(self.g.map.width, x + radius + 1)):
                for j in range(max(0, y - radius), min(self.g.map.height, y + radius + 1)):
                    if (i - x) ** 2 + (j - y) ** 2 <= radius ** 2:
                        self.g.map.data_explored[j][i] = 1

        if key in directions:
            dx, dy, direction = directions[key]
            player_pos = self.g.player.position
            new_x, new_y = player_pos['x'] + dx, player_pos['y'] + dy

            if self.g.player.move(dx, dy):
                update_explored_area(new_x, new_y)
            else:
                # Player is moving to a new map
                self.g.player.move_direction(direction)
                update_explored_area(self.g.player.position['x'], self.g.player.position['y'])

            if not self.g.player.standing:
                self.battle()
                self.check_tile()

        elif key == ord('1'):
            self.g.player.use_potion('healing')
        elif key == ord('2'):
            self.g.player.use_potion('mana')
        elif key == ord('\x1b'):
            self.g.current_option = 0
            self.push_state(PlayStates.COMMANDS)
        elif key == ord('i'):
            self.g.current_option = 0
            self.push_state(PlayStates.INVENTORY)
            

    def handle_commands_state(self, key):
        if key in (curses.KEY_UP, ord('w')):
            self.g.current_option = max(0, self.g.current_option - 1)
        elif key in (curses.KEY_DOWN, ord('s')):
            self.g.current_option = min(3, self.g.current_option + 1)
        elif key == ord('\x1b'):
            self.pop_state()
        elif key == ord('\n'):
            self.execute_command()
            self.pop_state()
        elif key == ord('i'):
            self.g.current_option = 0
            if self.state_stack[-2] == PlayStates.INVENTORY:
                self.pop_state()

    def handle_shopping_state(self, key):
        if self.g.current_sub_option == -1:
            self.handle_shopping_main_options(key)
        else:
            self.handle_shopping_sub_options(key)

    def handle_shopping_main_options(self, key):
        if key == ord('\x1b'):
            self.g.current_option = 0
            self.push_state(PlayStates.COMMANDS)
        elif key in (curses.KEY_UP, ord('w')):
            self.g.current_option = max(0, self.g.current_option - 1)
        elif key in (curses.KEY_DOWN, ord('s')):
            self.g.current_option = min(2, self.g.current_option + 1)
        elif key == ord('\n'):
            self.g.current_sub_option = 0
        elif key == ord('i'):
            self.g.current_option = 0
            self.push_state(PlayStates.INVENTORY)
        elif key == ord('b'):
            self.g.current_option = 0
            self.pop_state()

    def handle_shopping_sub_options(self, key):
        if key == ord('\x1b'):
            self.g.current_sub_option = -1
        elif key in (curses.KEY_UP, ord('w')):
            self.g.current_sub_option = max(0, self.g.current_sub_option - 1)
        elif key in (curses.KEY_DOWN, ord('s')):
            max_option = len(SHOP_WEAPONS) - 1 if self.g.current_option == 0 else len(SHOP_ARMORS) - 1
            self.g.current_sub_option = min(max_option, self.g.current_sub_option + 1)
        elif key == ord('\n'):
            self.purchase_item()

    def purchase_item(self):
        try:
            if self.g.current_option == 0:
                weapon, price = list(SHOP_WEAPONS)[self.g.current_sub_option].value
                if self.g.player.stats['gold'] >= price:
                    self.g.player.stats['gold'] -= price
                    self.g.player.inventory['weapons'].append(weapon.name)
                    add_notif(self, f"You bought a {weapon.value.name} for {price}$", C.GREEN)
                else:
                    add_notif(self, "You don't have enough gold!", C.RED)
            elif self.g.current_option == 1:
                armor, price = list(SHOP_ARMORS)[self.g.current_sub_option].value
                if self.g.player.stats['gold'] >= price:
                    self.g.player.stats['gold'] -= price
                    self.g.player.inventory['armors'].append(armor.name)
                    add_notif(self, f"You bought a {armor.value.name} for {price}$", C.GREEN)
                else:
                    add_notif(self, "You don't have enough gold!", C.RED)
            elif self.g.current_option == 2:
                if self.g.current_sub_option == 0:
                    self.purchase_potion('healing', 10)
                elif self.g.current_sub_option == 1:
                    self.purchase_potion('mana', 5)
        except Exception as e:
            self.g.stdscr.addstr(1, 0, f"(play.py -> run, buy) An error occurred: {e}", p(C.RED))
            self.g.stdscr.refresh()
            time.sleep(4)

    def purchase_potion(self, potion_type, price):
        if self.g.player.stats['gold'] >= price:
            self.g.player.stats['gold'] -= price
            self.g.player.equipment['potions'][potion_type] += 1
            add_notif(self, f"You bought a {potion_type} potion for {price}$", C.GREEN)
        else:
            add_notif(self, "You don't have enough gold!", C.RED)

    def handle_inventory_state(self, key):
        if self.g.current_sub_option == -1:
            self.handle_inventory_main_options(key)
        else:
            self.handle_inventory_sub_options(key)

    def handle_inventory_main_options(self, key):
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
            self.g.current_option = min(2, self.g.current_option + 1)

    def handle_inventory_sub_options(self, key):
        if key == ord('\x1b'):
            self.g.current_sub_option = -1
        elif key in (curses.KEY_UP, ord('w')):
            self.g.current_sub_option = max(0, self.g.current_sub_option - 1)
        elif key in (curses.KEY_DOWN, ord('s')):
            match self.g.current_option:
                case 0:
                    max_option = len(self.g.player.inventory['weapons']) - 1
                case 1:
                    max_option = len(self.g.player.inventory['armors']) - 1
                case 2:
                    max_option = len(self.g.player.inventory['rings']) - 1
        
            self.g.current_sub_option = min(max_option, self.g.current_sub_option + 1)
            
        elif key == ord('\n'):
            self.equip_item()

    def equip_item(self):
        try:
            if self.g.current_option == 0:
                weapon = self.g.player.inventory['weapons'][self.g.current_sub_option]
                if self.g.player.equipment['weapon'] == weapon:
                    W[weapon].value.apply(self.g.player, remove=True),
                    self.g.player.equipment['weapon'] = None
                    add_notif(self, f"You unequipped a {W[weapon].value.name}", C.RED)
                else:
                    if self.g.player.equipment['weapon']:
                        W[self.g.player.equipment['weapon']].value.apply(self.g.player, remove=True)
                    self.g.player.equipment['weapon'] = weapon
                    W[weapon].value.apply(self.g.player)
                    add_notif(self, f"You equipped a {W[weapon].value.name}", C.GREEN)
                return
            elif self.g.current_option == 1:
                armor = self.g.player.inventory['armors'][self.g.current_sub_option]
                if self.g.player.equipment['armor'] == armor:
                    A[armor].value.apply(self.g.player, remove=True)
                    self.g.player.equipment['armor'] = None
                    add_notif(self, f"You unequipped a {A[armor].value.name}", C.RED)
                else:
                    if self.g.player.equipment['armor']:
                        A[self.g.player.equipment['armor']].value.apply(self.g.player, remove=True)
                    self.g.player.equipment['armor'] = armor
                    A[armor].value.apply(self.g.player)
                    add_notif(self, f"You equipped a {A[armor].value.name}", C.GREEN)
                return
            elif self.g.current_option == 2:
                ring = self.g.player.inventory['rings'][self.g.current_sub_option]
                if self.g.player.equipment['ring'] == ring:
                    R[self.g.player.equipment['ring']].value.apply(self.g.player, remove=True)
                    self.g.player.equipment['ring'] = None
                    add_notif(self, f"You unequipped a {R[ring].value.name}", C.RED)
                else:
                    if self.g.player.equipment['ring']:
                        R[self.g.player.equipment['ring']].value.apply(self.g.player, remove=True)
                    self.g.player.equipment['ring'] = ring
                    R[ring].value.apply(self.g.player)
                    add_notif(self, f"You equipped a {R[ring].value.name}", C.GREEN)
                return

        except Exception as e:
            self.g.stdscr.addstr(0, 0, f"(play.py -> run, equip) An error occurred: {e}", p(C.RED))
            self.g.stdscr.refresh()
            time.sleep(4)

    def quit_game(self) -> bool:
        w = self.f_w - 4
        message = "Do you want to save?"
        options = ["Yes", "No", "Cancel"]
        selected_option = display_confirmation_popup(self.g.stdscr, self.f_x + 2, self.f_y + 10, w, message, options)
        
        match selected_option:
            case 0:
                save_game(self.g)
                add_notif(self, f"Saved game as '{self.g.player.name}'", C.GREEN)
                self.confirm_quit()
                return True
            case 1:
                self.confirm_quit()
                return True
            case 2:
                self.state_stack = [PlayStates.PLAYING]
                return False
            
    def toogle_colors(self) -> None:
        w = self.f_w - 4
        message = "Do you want to toogle colors?"
        options = ["Yes", "No"]
        selected_option = display_confirmation_popup(self.g.stdscr, self.f_x + 2, self.f_y + 10, w, message, options)

        match selected_option:
            case 0:
                utils.BlackAndWhite = not utils.BlackAndWhite
                add_notif(self, "Colors toggled", C.CYAN)
            case 1:
                pass

    def confirm_quit(self):
        add_notif(self, "Quitting the game...", C.RED)
        self.g.current_option = 0
        self.draw()
        time.sleep(1)

    def draw(self) -> None:
        self.g.stdscr.clear()
    
        msg = ""
        s  = self.play_state
        ss = self.state_stack
        ps = PlayStates
        
        try:
            
            if s != ps.HELP:
                
                if s == ps.FIGHTING or (s == ps.COMMANDS and ss[-2] == ps.FIGHTING):
                    msg = "(play, draw, display, fight)"
                    self.display_fight(self.g.stdscr, self.f_x, self.f_y, self.f_w, self.f_h)
                    
                elif s == ps.PLAYING or (s == ps.COMMANDS and ss[-2] == ps.PLAYING):
                    msg = "(play, draw, display, map)"
                    self.display_map(self.g.stdscr, self.m_x, self.m_y)
                    
                elif s == ps.SHOPPING or (s == ps.COMMANDS and ss[-2] == ps.SHOPPING):
                    msg = "(play, draw, display, shop)"
                    display(self.g.stdscr, self.draw_shop(self.sh_w, self.sh_h), self.sh_x, self.sh_y, 2, 2, True)
                    
                elif s == ps.INVENTORY or (s == ps.COMMANDS and ss[-2] == ps.INVENTORY):
                    msg = "(play, draw, display, inventory)"
                    display(self.g.stdscr, self.draw_inventory(self.i_w, self.i_h), self.i_x, self.i_y, 2, 2, True)
                    
                elif s == ps.QUITTING:
                    msg = "(play, draw, display, empty_box)"
                    display(self.g.stdscr, self.empty_box, self.empty_box_x, self.empty_box_y)
                
                msg = "(play, draw, display_stats)"
                self.display_stats(self.g.stdscr, self.s_x, self.s_y, self.s_w, self.s_h)

                msg = "(play, draw, display, commands)"
                display(self.g.stdscr, self.draw_commands(self.c_w, self.c_h), self.c_x, self.c_y, 1, 1)

                msg = "(play, draw, display, notifications)"
                display(self.g.stdscr, draw_outline(self.n_w, self.notifs), self.n_x, self.n_y)

                msg = "(play, draw, display, biome)"
                display(self.g.stdscr, self.draw_biome(self.b_w, self.b_h), self.b_x, self.b_y)
                
                msg = "(play, draw, display, biomes_thumbnail)"
                display(self.g.stdscr, self.draw_biomes_thumbnail(self.bt_w, self.bt_h), self.bt_x, self.bt_y)
            
                msg = "(play, draw, display_equipment)"
                self.display_equipment(self.g.stdscr, self.e_x, self.e_y, self.e_w, self.e_h)
                    
            else:
                for i, line in enumerate(self.commands):
                    self.g.stdscr.addstr(i, 0, line, p(C.CYAN))
                self.g.stdscr.refresh()
        
        except Exception as e:
            self.draw_try(msg, e)

        self.g.stdscr.refresh()

    def run(self) -> None:
        run = True
        while run:
            try:
                self.draw()

                if self.play_state == PlayStates.QUITTING:
                    if self.quit_game():
                        self.state_stack = []
                        run = False
                        break
                
                else:    
                    key = self.g.stdscr.getch()
                        
                    if self.play_state == PlayStates.PLAYING:
                        self.handle_playing_state(key)
                    elif self.play_state == PlayStates.COMMANDS:
                        self.handle_commands_state(key)
                    elif self.play_state == PlayStates.FIGHTING:
                        clear_notif(self)
                        self.g.stdscr.nodelay(1)
                        self.g.stdscr.timeout(100)
                        self.fight()
                        self.g.stdscr.nodelay(0)
                    
                    elif self.play_state == PlayStates.SHOPPING:
                        self.handle_shopping_state(key)
                    elif self.play_state == PlayStates.INVENTORY:
                        self.handle_inventory_state(key)
                    elif self.play_state == PlayStates.HELP:
                        if key in (ord('\x1b'), ord(' '), ord('\n')):
                            self.pop_state()

            except Exception as e:
                self.g.stdscr.addstr(0, 0, f"(play.py -> run) An error occurred: {e})", p(C.RED))
                self.g.stdscr.refresh()
                time.sleep(4)
                run = False
                break
            
    def print_map_visited(self) -> None:
        for row in self.g.map.data_explored:
            print(row)
    