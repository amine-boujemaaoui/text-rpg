import curses
from utils import p, Colors as C, create_ui
import utils


class Menu:
    def __init__(self, g) -> None:
        self.g = g

    def draw(self) -> None:
        length = self.g.ui_max_length
        options_length = 23
        options = [
            "New Game",
            "Load Game",
            "Rules",
            "Commands",
            "Colors",
            "Quit",
        ]

        menu = create_ui("Menu", options, box=len(options))
        
        start_x = length // 2 - options_length // 2 + 1
        start_y = start_x + options_length
        first_option = 15
        for i, line in enumerate(menu):
            
            if self.g.current_option == i - first_option:
                line_selected = f"> {options [i - first_option]}"
                
                self.g.stdscr.addstr(i,           0, line[:start_x + 3], p(C.CYAN))
                self.g.stdscr.addstr(i, start_x + 3, line_selected,      p(C.YELLOW))
                self.g.stdscr.addstr(i,     start_y, line[start_y:],     p(C.CYAN))
                
            elif i >= first_option and i < first_option + len(options):
                line_selected = f"  {options [i - first_option]}"  
                
                self.g.stdscr.addstr(i,           0, line[:start_x + 3], p(C.CYAN))
                self.g.stdscr.addstr(i, start_x + 3, line_selected,      p(C.WHITE))
                self.g.stdscr.addstr(i,     start_y, line[start_y:],     p(C.CYAN))
                 
            else:
                self.g.stdscr.addstr(i, 0, line, p(C.CYAN))
        
        self.g.stdscr.addstr(self.g.ui_max_height-1, 1, "Press 'ENTER' to select an option and 'w', 's' to scroll.", p(C.GRAY, italic=True))
                
        self.g.stdscr.refresh()

    def run(self) -> None:
        from game import GameState, SubGameState

        run = True
        while run:
            self.draw()
            key = self.g.stdscr.getch()
            
            if key == curses.KEY_UP or key == ord('w'):
                self.g.current_option = max(0, self.g.current_option - 1)
            elif key == curses.KEY_DOWN or key == ord('s'):
                self.g.current_option = min(5, self.g.current_option + 1)
            
            elif key == ord('\n'):
                match self.g.current_option:
                    case 0:
                        self.g.current_state     = GameState.PLAY
                        self.g.current_sub_state = SubGameState.NEW_GAME
                        run = False
                    case 1:
                        self.g.current_state     = GameState.PLAY
                        self.g.current_sub_state = SubGameState.LOAD_GAME
                        run = False
                    case 2:
                        self.g.current_state     = GameState.RULES
                        run = False
                    case 3:
                        self.g.current_state     = GameState.COMMANDS
                        run = False
                    case 4:
                        utils.BlackAndWhite = not utils.BlackAndWhite
                    case 5:
                        self.g.current_state     = GameState.QUIT
                        run = False
