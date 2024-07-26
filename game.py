import curses
import random
import time
import os

from menu import Menu
from map import Map, Direction
from rules import Rules
from entities import Player, ENEMIES, create_enemy
from play import Play
from utils import i, init_colors, p, add_notif, save_game, load_game, Colors as C, fl, create_ui, list_saves
from enum import Enum

class GameState(Enum):
    MENU     = 'menu'
    PLAY     = 'play'
    RULES    = 'rules'
    COMMANDS = 'commands'
    QUIT     = 'quit'
    
class SubGameState(Enum):
    NEW_GAME  = 'new_game'
    LOAD_GAME = 'load_game'
    NONE      = 'none'

class Game:
    def __init__(self) -> None:
        self.stdscr = None
        self.player = None
        
        self.first_time = True
        
        self.current_option     = 0
        self.current_sub_option = -1
        self.current_state      = GameState.MENU
        self.current_sub_state  = SubGameState.NONE

        self.exp_table = {
            1: 100,
            2: 200,
            3: 400,
            4: 800,
            5: 1600,
            6: 3200,
            7: 6400,
            8: 12800,
            9: 25600,
            10: 51200,
        }
        
        self.ui_max_length = 115
        self.ui_max_height = 32

        self.menu     = Menu(self)
        self.rules    = Rules(self)
        self.play     = Play(self)   
        self.map      = Map(self)
        self.commands = create_ui("Commands", [
                "┌─────────────────────────────────────────────────────────┐".center(self.ui_max_length),
                "│            MENU, COMMANDS, SHOP, INVENTORY              │".center(self.ui_max_length),
                "├────────────────────────────┬────────────────────────────┤".center(self.ui_max_length),
                "│ up, down, w, s:            │ Navigate through the menu. │".center(self.ui_max_length),
                "│ enter:                     │ Select an option.          │".center(self.ui_max_length),
                "├────────────────────────────┴────────────────────────────┤".center(self.ui_max_length),
                "│                          GAME                           │".center(self.ui_max_length),
                "├────────────────────────────┬────────────────────────────┤".center(self.ui_max_length),
                "│ w, a, s, d:                │ Move the player.           │".center(self.ui_max_length),
                "│ i:                         │ Open the inventory.        │".center(self.ui_max_length),
                "│ ESC:                       │ Enter in commands menu.    │".center(self.ui_max_length),
                "│ e:                         │ Show Equipments view.      │".center(self.ui_max_length),
                "├────────────────────────────┴────────────────────────────┤".center(self.ui_max_length),
                "│                          FIGHT                          │".center(self.ui_max_length),
                "├────────────────────────────┬────────────────────────────┤".center(self.ui_max_length),
                "│ space:                     │ Attack the enemy.          │".center(self.ui_max_length),
                "│ 1, 2:                      │ Use a potion (heal, mana). │".center(self.ui_max_length),
                "│ ESC:                       │ Enter in commands menu.    │".center(self.ui_max_length),
                "└────────────────────────────┴────────────────────────────┘".center(self.ui_max_length),
            ])
        
        self.enemies = {}
        for enemy_key in ENEMIES:
            self.enemies[enemy_key] = create_enemy(self, enemy_key)

    def cleanup(self):
        if self.stdscr:
            curses.nocbreak()
            self.stdscr.keypad(False)
            curses.echo()
            curses.endwin()

    def new_game(self) -> None:
        try:
            rules = create_ui("New Game", [])

            self.stdscr.clear()
            for idx, line in enumerate(rules):
                self.stdscr.addstr(idx, 0, line, p(C.CYAN))
            self.stdscr.refresh()
            
            player_name = i(self.stdscr, 4, 14, 10, "Enter your player's name: ")
            
            if not player_name:
                self.current_state = GameState.MENU
                return
            
            self.player = Player(self, player_name)
            self.player.position = {
                'x': random.randint(0, self.map.width  - 1),
                'y': random.randint(0, self.map.height - 1)
            }
            save_game(self, player_name, True)
            load_game(self, player_name)
            self.map = Map(self)
            self.current_state = GameState.PLAY
        except Exception as e:
            self.stdscr.addstr(31, 1, f"(game.py -> new_game) An error occurred: {e}", p(C.RED))
            self.stdscr.refresh()
            time.sleep(5)
            self.current_state = GameState.MENU
            
    def load_game(self, stdscr) -> None:
        stdscr.clear()
        saves = list_saves()
        empty_load_game = create_ui("Load Game", [])
        if not saves:
            for idx, line in enumerate(empty_load_game):
                    stdscr.addstr(idx, 0, line, p(C.CYAN))
            fl(self.stdscr, 2, C.RED, "No save games found.")
            self.current_state = GameState.MENU
            return

        try:
            selected_index = 0
            start_x = 50
            start_y = 15
            length = self.ui_max_length
            
            while True:
                stdscr.clear()
                for idx, line in enumerate(create_ui("Load Game", saves, box=len(saves))):
                    stdscr.addstr(idx, 0, line, p(C.CYAN))
                
                for idx, save in enumerate(saves):
                    if idx == selected_index:
                        stdscr.addstr(start_y + idx, start_x, f"> {save}", p(C.YELLOW))
                    else:
                        stdscr.addstr(start_y + idx, start_x, f"  {save}", p(C.WHITE))
                    
                stdscr.addstr(31, 1, "Press 'ENTER' to load the selected game or 'ESCAPE' to go back.", p(C.GRAY, italic=True))

                stdscr.refresh()
                key = stdscr.getch()

                if key == ord('\n'):
                    save_name = saves[selected_index]
                    break
                elif (key == curses.KEY_UP or key == ord('w')) and selected_index > 0:
                    selected_index -= 1
                elif (key == curses.KEY_DOWN or key == ord('s')) and selected_index < len(saves) - 1:
                    selected_index += 1
                elif key == ord('\x1b'): 
                    self.current_state = GameState.MENU
                    return

            if not os.path.exists(f"saves/{save_name}.json"):
                raise FileNotFoundError

            self.player = Player(self, save_name)
            
            self.play.notifs = []
            add_notif(self.play, "")
            add_notif(self.play, "")
            add_notif(self.play, "")
            add_notif(self.play, "Press 'ESCAPE' to enter command mode.".center(60), C.GRAY)
            add_notif(self.play, 'Welcome to the game!'.center(60), C.YELLOW)
            add_notif(self.play, "")
            
            stdscr.clear()
            for idx, line in enumerate(empty_load_game):
                    stdscr.addstr(idx, 0, line, p(C.CYAN))
            stdscr.refresh()

            load_game(self, save_name)
            self.current_state = GameState.PLAY

        except FileNotFoundError:
            fl(self.stdscr, 2, C.RED, f"Game '{save_name}' not found.")
            self.current_state = GameState.MENU

        except Exception as e:
            fl(self.stdscr, 10, C.RED, f"(game.py -> load_game) An error occurred: {e}")
            self.current_state = GameState.MENU


    def generate_map(self, dir: Direction) -> None:
        self.map = Map(self)
        match dir:
            case Direction.NORTH:
                self.player.position['y'] = self.map.height - 1
            case Direction.SOUTH:
                self.player.position['y'] = 0
            case Direction.EAST:
                self.player.position['x'] = 0
            case Direction.WEST:
                self.player.position['x'] = self.map.width - 1
            
    def run(self, stdscr) -> int:
        self.stdscr = stdscr
        init_colors()  # Appeler après l'initialisation de l'écran
        
        curses.curs_set(0)
        
        try:
            while True:
                self.stdscr.clear()
                match self.current_state:
                    
                    case GameState.MENU:
                        self.menu.run()
                        
                    case GameState.RULES:
                        self.rules.run()
                    
                    case GameState.COMMANDS:
                        for i, line in enumerate(self.commands):
                            self.stdscr.addstr(i, 0, line, p(C.CYAN))
                        self.stdscr.addstr(self.ui_max_height-1, 1, "Press 'ENTER' to go back.", p(C.GRAY, italic=True))
                        while self.current_state == GameState.COMMANDS:
                            key = self.stdscr.getch()
                            if key == ord('\n') or key == ord('\x1b') or key == ord(' '):
                                self.current_state = GameState.MENU
                                break
                        
                    case GameState.PLAY:
                        match self.current_sub_state:
                            
                            case SubGameState.NEW_GAME:
                                self.new_game()
                                self.current_sub_state = SubGameState.NONE
                                
                            case SubGameState.LOAD_GAME:
                                self.load_game(self.stdscr)
                                self.current_sub_state = SubGameState.NONE
                                
                            case SubGameState.NONE:
                                self.play = Play(self)
                                self.play.run()
                                self.current_state = GameState.MENU
                                
                    case GameState.QUIT:
                        curses.curs_set(1)
                        return 0

        except Exception as e:
            fl(self.stdscr, 10, C.RED, f"(game.py -> run) An error occurred: {e}")
            time.sleep(3)
            curses.curs_set(0)
            return 1
        finally:
            self.cleanup()
