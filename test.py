import curses
import random

def main(stdscr):

    sh, sw = stdscr.getmaxyx()
    w = curses.newwin(sh, sw, 0, 0)
    curses.curs_set(0)
    w.nodelay(1)
    w.timeout(100)

    x = 4
    y = 2
    player = '@'

    obstacles = []
    for _ in range(5):
        ox = random.randint(0, sw - 1)
        oy = random.randint(0, sh - 1)
        obstacles.append((ox, oy))
        
    for ox, oy in obstacles:
        w.addch(oy, ox, '#')

    score = 0

    while True:
        w.border(0)
        w.addstr(0, 2, f'Score: {score}')
        w.addch(y, x, player)
        
        w.refresh()
        
        key = w.getch()
        if key == ord('w'):
            y -= 1
        elif key == ord('s'):
            y += 1
        elif key == ord('a'):
            x -= 1
        elif key == ord('d'):
            x += 1
        elif key == ord('q'):
            break
        
        score += 1

if __name__ == '__main__':
    curses.wrapper(main)
