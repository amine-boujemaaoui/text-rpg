import curses
from utils import p, Colors as C


class Menu:
    def __init__(self, g) -> None:
        self.g = g

    def draw(self) -> None:
        menu = [
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
            "│                                 ┌────────────────────┐                                 │",
            "│                                 │   New Game         │                                 │",
            "│                                 │   Load Game        │                                 │",
            "│                                 │   Rules            │                                 │",
            "│                                 │   Quit Game        │                                 │",
            "│                                 └────────────────────┘                                 │",
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
            "└────────────────────────────────────────────────────────────────────────────────────────┘"
        ]
        
        start_x = 25 + 10
        start_y = 45 + 10
        first_option = 11
        for i, line in enumerate(menu):
            if self.g.current_option == i - first_option:
                self.g.stdscr.addstr(i,       0, line[:start_x],        p(C.CYAN))
                self.g.stdscr.addstr(i, start_x, line[start_x:start_y], p(C.BLACK, C.WHITE))
                self.g.stdscr.addstr(i, start_y, line[start_y:],        p(C.CYAN))
            else:
                self.g.stdscr.addstr(i, 0, line,                        p(C.CYAN))
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
                self.g.current_option = min(3, self.g.current_option + 1)
            
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
                        self.g.current_state     = GameState.QUIT
                        run = False
