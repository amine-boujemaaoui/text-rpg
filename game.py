import curses
import random
import time
import os

from menu import Menu
from map import Map, Direction
from rules import Rules
from entities import Player, ENEMIES, create_enemy
from play import Play
from utils import i, init_colors, p, add_notif, save_game, load_game, Colors as C, fl
from enum import Enum

class GameState(Enum):
    MENU  = 'menu'
    RULES = 'rules'
    PLAY  = 'play'
    QUIT  = 'quit'
    
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

        self.menu  = Menu(self)
        self.rules = Rules(self)
        self.play  = Play(self)   
        self.map   = Map(self)
        
        self.enemies = {}
        for enemy_key in ENEMIES:
            self.enemies[enemy_key] = create_enemy(self, enemy_key)
        

        self.notif = []
        for _ in range(6):
            self.notif.append(('', C.WHITE, C.BLACK))
        add_notif(self, "Press 'ESCAPE' to enter command mode.".center(40 + 20), C.GRAY)
        add_notif(self, 'Welcome to the game!'.center(40 + 20), C.YELLOW)
        add_notif(self, '')

    def cleanup(self):
        if self.stdscr:
            curses.nocbreak()
            self.stdscr.keypad(False)
            curses.echo()
            curses.endwin()

    def new_game(self) -> None:
        rules = [
            "┌────────────────────────────────────────────────────────────────────────────────────────┐",
            "│                                                                                        │",
            "│                          ██████╗  ██████╗ ███╗   ██╗██╗███████╗                        │",
            "│                         ██╔════╝ ██╔═══██╗████╗  ██║██║██╔════╝                        │",
            "│                         ██║  ███╗██║   ██║██╔██╗ ██║██║███████╗                        │",
            "│                         ██║   ██║██║   ██║██║╚██╗██║██║╚════██║                        │",
            "│                         ╚██████╔╝╚██████╔╝██║ ╚████║██║███████║                        │",
            "│                          ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝╚═╝╚══════╝                        │",
            "│                                                                                        │",
            "│                                                                                        │",
            "│                                 ┌─────────────────────┐                                │",
            "│                                 │       New Game      │                                │",
            "│                                 └─────────────────────┘                                │",
            "│                                                                                        │",
            "│                                                                                        │",
            "│                                                                                        │",
            "│                                                                                        │",
            "│                                                                                        │",
            "│                                                                                        │",
            "│                                                                                        │",
            "│                                                                                        │",
            "│                                                                                        │",
            "│                                                                                        │",
            "│                                                                                        │",
            "│                                                                                        │",
            "│                                                                                        │",
            "│                                                                                        │",
            "│                                                                                        │",
            "│                                                                                        │",
            "│                                                                                        │",
            "│                                                                                        │",
            "│                                                                                        │",
            "└────────────────────────────────────────────────────────────────────────────────────────┘",
        ]

        self.stdscr.clear()
        for idx, line in enumerate(rules):
            self.stdscr.addstr(idx, 0, line, p(C.CYAN))
        self.stdscr.refresh()
        
        player_name = i(self.stdscr, 4, 13, 10, "Enter your player's name:")
        
        self.player = Player(self, player_name)
        self.player.position = {
            'x': random.randint(0, self.map.width - 1),
            'y': random.randint(0, self.map.height - 1)
        }
        save_game(self, player_name, True)
        load_game(self, player_name)
        self.current_state = GameState.PLAY

    def load_game(self, stdscr) -> None:
        stdscr.clear()
        for idx, line in enumerate([
            "┌────────────────────────────────────────────────────────────────────────────────────────┐",
            "│                                                                                        │",
            "│                          ██████╗  ██████╗ ███╗   ██╗██╗███████╗                        │",
            "│                         ██╔════╝ ██╔═══██╗████╗  ██║██║██╔════╝                        │",
            "│                         ██║  ███╗██║   ██║██╔██╗ ██║██║███████╗                        │",
            "│                         ██║   ██║██║   ██║██║╚██╗██║██║╚════██║                        │",
            "│                         ╚██████╔╝╚██████╔╝██║ ╚████║██║███████║                        │",
            "│                          ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝╚═╝╚══════╝                        │",
            "│                                                                                        │",
            "│                                                                                        │",
            "│                                 ┌─────────────────────┐                                │",
            "│                                 │      Load Game      │                                │",
            "│                                 └─────────────────────┘                                │",
            "│                                                                                        │",
            "│                                                                                        │",
            "│                                                                                        │",
            "│                                                                                        │",
            "│                                                                                        │",
            "│                                                                                        │",
            "│                                                                                        │",
            "│                                                                                        │",
            "│                                                                                        │",
            "│                                                                                        │",
            "│                                                                                        │",
            "│                                                                                        │",
            "│                                                                                        │",
            "│                                                                                        │",
            "│                                                                                        │",
            "│                                                                                        │",
            "│                                                                                        │",
            "│                                                                                        │",
            "│                                                                                        │",
            "└────────────────────────────────────────────────────────────────────────────────────────┘",
        ]):
            stdscr.addstr(idx, 0, line, p(C.CYAN))

        try:
            save_name = i(stdscr, 4, 14, 10, "Enter the save game name:")
            
            if not os.path.exists(f"saves/{save_name}.json"):
                raise FileNotFoundError
            
            self.player = Player(self, save_name)
            
            fl(self.stdscr, 0.2, C.YELLOW, f"Loading game '{save_name}' ...")
            load_game(self, save_name)
            self.current_state = GameState.PLAY
            fl(self.stdscr, 0.2, C.GREEN,  f"Game '{save_name}' loaded successfully.")
            
        except FileNotFoundError:
            fl(self.stdscr,   2, C.RED, f"Game '{save_name}' not found.")
            self.current_state = GameState.MENU
            
        except Exception as e:
            fl(self.stdscr,  10, C.RED, f"(game.py -> load_game) An error occurred: {e}")
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
                        
                    case GameState.PLAY:
                        match self.current_sub_state:
                            
                            case SubGameState.NEW_GAME:
                                self.new_game()
                                self.current_sub_state = SubGameState.NONE
                                
                            case SubGameState.LOAD_GAME:
                                self.load_game(self.stdscr)
                                self.current_sub_state = SubGameState.NONE
                                
                            case SubGameState.NONE:
                                self.play.run()
                                self.current_state = GameState.MENU
                                
                    case GameState.QUIT:
                        curses.curs_set(1)
                        return 0

        except Exception as e:
            add_notif(self, f"(game.py -> run) An error occurred: {e}", C.RED)
            time.sleep(3)
            curses.curs_set(0)
            return 1
        finally:
            self.cleanup()
