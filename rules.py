from utils import p

class Rules:
    def __init__(self, g) -> None:
        self.g = g

    def draw(self) -> None:
        from utils import Colors
        rules = [
            "┌────────────────────────────────────────────────────────────────────┐",
            "│                                                                    │",
            "│                ██████╗  ██████╗ ███╗   ██╗██╗███████╗              │",
            "│               ██╔════╝ ██╔═══██╗████╗  ██║██║██╔════╝              │",
            "│               ██║  ███╗██║   ██║██╔██╗ ██║██║███████╗              │",
            "│               ██║   ██║██║   ██║██║╚██╗██║██║╚════██║              │",
            "│               ╚██████╔╝╚██████╔╝██║ ╚████║██║███████║              │",
            "│                ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝╚═╝╚══════╝              │",
            "│                                                                    │",
            "│                                                                    │",
            "│                       ┌─────────────────────┐                      │",
            "│                       │        Rules        │                      │",
            "│                       └─────────────────────┘                      │",
            "│                                                                    │",
            "│      1. Rule one description.                                      │",
            "│      2. Rule two description.                                      │",
            "│      3. Rule three description.                                    │",
            "│                                                                    │",
            "│                                                                    │",
            "│                                                                    │",
            "│                                                                    │",
            "│                                                                    │",
            "│                                                                    │",
            "│                                                                    │",
            "│                                                                    │",
            "│                                                                    │",
            "│                                                                    │",
            "│                                                                    │",
            "│                                                                    │",
            "│                                                                    │",
            "│                                                                    │",
            "└────────────────────────────────────────────────────────────────────┘",
        ]
        
        for i, line in enumerate(rules):
            self.g.stdscr.addstr(i, 0, line, p(Colors.CYAN))
        
        self.g.stdscr.refresh()
            
    def run(self) -> None:
        from game import GameState
        self.draw()
        
        while self.g.current_state == GameState.RULES:
            key = self.g.stdscr.getch()
            if key == ord('\n'):
                self.g.current_state = GameState.MENU
                break
            