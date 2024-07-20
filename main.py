import sys
import curses
from game import Game

def main(stdscr):
    game = Game()
    game.run(stdscr)
    return 0

if __name__ == "__main__":
    try:
        sys.exit(curses.wrapper(main))
    except Exception as e:
        print(f"(main.py) An error occurred: {e}")
