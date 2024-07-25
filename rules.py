from utils import p, create_ui
import time

class Rules:
    def __init__(self, g) -> None:
        self.g = g

    def draw(self) -> None:
        from utils import Colors as C
        rules = create_ui("Rules", [
            '',
            '',
            "     Welcome to the game!",
            "     You can move with the keys 'w', 'a', 's', 'd'.",
            "     To attack an enemy, press the space bar.",
            "     To use a potion, press '1' or '2'.",
            "     Press 'i' to open the inventory.",
            "     Press 'e' to open the equipment view.",
            "     Press 'ESC' to enter the commands menu.",
            "     Press 'q' to quit the game.",
            "     Good luck!",
        ])
        
        for i, line in enumerate(rules):
            self.g.stdscr.addstr(i, 0, line, p(C.CYAN))
            
        self.g.stdscr.addstr(31, 1, "Press 'ENTER' to go back.", p(C.GRAY, italic=True))
        
        self.g.stdscr.refresh()
            
    def run(self) -> None:
        from game import GameState
        from utils import Colors as C
        try:
            self.draw()
        
            while self.g.current_state == GameState.RULES:
                key = self.g.stdscr.getch()
                if key == ord('\n'):
                    self.g.current_state = GameState.MENU
                    break
        except Exception as e:
            self.g.addstr(0, 0, str(e), p(C.RED))
            self.g.stdscr.refresh()
            time.sleep(2)
            
            